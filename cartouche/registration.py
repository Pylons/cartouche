##############################################################################
#
# Copyright (c) 2010 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################
from email.message import Message
from pkg_resources import resource_filename
from uuid import uuid4

from colander import Email
from colander import Invalid
from colander import Schema
from colander import SchemaNode
from colander import String
from colander import deferred
from colander import null
from deform import Form
from deform import ValidationFailure
from deform.template import default_dir as deform_templates_dir
from deform.widget import CheckedPasswordWidget
from deform.widget import HiddenWidget
from deform.widget import PasswordWidget
from deform.widget import SelectWidget
from pyramid.renderers import get_renderer
from pyramid.url import model_url
from repoze.sendmail.interfaces import IMailDelivery
from repoze.sendmail.delivery import DirectMailDelivery
from repoze.sendmail.mailer import SMTPMailer
from repoze.who.api import get_api
from webob.exc import HTTPForbidden
from webob.exc import HTTPFound
from webob.exc import HTTPUnauthorized
from zope.password.password import SSHAPasswordManager

from cartouche.interfaces import IAutoLogin
from cartouche.interfaces import IRegistrations
from cartouche.interfaces import ITokenGenerator
from cartouche.persistence import ConfirmedRegistrations
from cartouche.persistence import PendingRegistrations


templates_dir = resource_filename('cartouche', 'templates/')
Form.set_zpt_renderer([templates_dir, deform_templates_dir])


class Signup(Schema):
    email = SchemaNode(String(), validator=Email())


class Confirm(Schema):
    email = SchemaNode(String(),
                       validator=Email(),
                      )
    token = SchemaNode(String(),
                       description="Enter the token from the registration "
                                   "confirmation e-mail you received.")


QUESTIONS = [
    ('color', 'What is your favorite color?'),
    ('borncity', 'In what city were you born?'),
    ('petname', 'What was the name of your favorite childhood pet?'),
]


class SecurityQuestion(Schema):
    question = SchemaNode(String(), widget=SelectWidget(values=QUESTIONS))
    answer = SchemaNode(String())

@deferred
def login_name_validator(node, kw):
    current_login_name = kw.get('current_login_name')
    confirmed = kw.get('confirmed')
    if current_login_name is not None and confirmed is not None:
        def _check(node, value):
            if value != current_login_name:
                if confirmed.get_by_login(value, None) is not None:
                    raise Invalid('Login name not available')
        return _check

@deferred
def old_password_widget(node, kw):
    if kw.get('old_password') is None:
        return HiddenWidget()
    return PasswordWidget()

@deferred
def old_password_missing(node, kw):
    if kw.get('old_password') is None:
        return ''

@deferred
def old_password_validator(node, kw):
    old_password = kw.get('old_password')
    if old_password is not None:
        pwd_mgr = SSHAPasswordManager()
        def _check(node, value):
            if not pwd_mgr.checkPassword(old_password, value):
                raise Invalid('Old password incorrect')
        return _check

class EditAccount(Schema):
    login_name = SchemaNode(String(),
                            validator=login_name_validator,
                           )
    old_password = SchemaNode(String(),
                              widget=old_password_widget,
                              missing=old_password_missing,
                              validator=old_password_validator,
                             )
    password = SchemaNode(String(),
                          widget=CheckedPasswordWidget())
    security = SecurityQuestion()


def getRandomToken(request):
    generator = request.registry.queryUtility(ITokenGenerator)
    if generator:
        return generator.getToken()
    return str(uuid4())


def autoLoginViaAuthTkt(userid, request):
    api = get_api(request.environ)
    if api is None:
        raise ValueError("Couldn't find / create repoze.who API object")
    credentials = {'repoze.who.plugins.auth_tkt.userid': userid}
    plugin_id = request.registry.settings.get('auth_tkt_plugin_id', 'auth_tkt')
    identity, headers = api.login(credentials, plugin_id)
    return headers

# By default, deliver e-mail via localhost, port 25.
_delivery = DirectMailDelivery(SMTPMailer())


REGISTRATION_EMAIL = """
Thank you for registering.  

In your browser, please copy and paste the following string
into the 'Token' field:

  %(token)s

If you do not still have that page open, you can visit it via
this URL (you will need to re-enter the same security question and
answer as you used on the initial registration form):

  %(confirmation_url)s

Once you have entered the token, click the "Confirm" button to
complete your registration.
"""


def register_view(context, request):
    form = Form(Signup(), buttons=('register',))
    rendered_form = form.render(null)
    if 'register' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e:
            rendered_form = e.render()
        else:
            pending = request.registry.queryAdapter(context, IRegistrations,
                                                    name='pending')
            if pending is None:  #pragma NO COVERAGE
                pending = PendingRegistrations(context)
            email = appstruct['email']
            token = getRandomToken(request)
            pending.set(email, token=token)

            from_addr = request.registry.settings['from_addr']
            delivery = request.registry.queryUtility(IMailDelivery) or _delivery
            confirmation_url = model_url(context, request,
                                        "confirm_registration.html",
                                        query=dict(email=email))
            body = REGISTRATION_EMAIL % {'token': token,
                                        'confirmation_url': confirmation_url}
            message = Message()
            message.set_payload(body)
            delivery.send(from_addr, [email], message)
            return HTTPFound(location=confirmation_url)

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'rendered_form': rendered_form,
            'message': request.GET.get('message'),
           }



REGISTER_FIRST = 'Please register first.'
REGISTER_OR_VISIT = ('Please register first '
                     'or visit the link in your confirmation e-mail.')
CHECK_TOKEN = ('Please copy the token from your confirmation e-mail.')

def confirm_registration_view(context, request):
    form = Form(Confirm(), buttons=('confirm',))
    pending = request.registry.queryAdapter(context, IRegistrations,
                                            name='pending')
    if pending is None:  #pragma NO COVERAGE
        pending = PendingRegistrations(context)
    if 'confirm' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e:
            rendered_form = e.render()
        else:
            email = appstruct['email']
            token = appstruct['token']
            info = pending.get(email)
            if info is None:
                return HTTPFound(location=model_url(context, request,
                                                    'register.html',
                                                    query={'message':
                                                            REGISTER_FIRST}))
            if token != info.token:
                return HTTPFound(location=model_url(context, request,
                                                'confirm_registration.html',
                                                query={'message':
                                                        CHECK_TOKEN}))
            confirmed = request.registry.queryAdapter(context, IRegistrations,
                                                      name='confirmed')
            if confirmed is None:  #pragma NO COVERAGE
                confirmed = ConfirmedRegistrations(context)
            pending.remove(email)
            uuid = getRandomToken(request)
            confirmed.set(uuid, email=email, login=email, password=None,
                          security_question=None, security_answer=None)
            info = confirmed.get(uuid)
            # TODO:  use who API to remember identity.
            auto_login = (request.registry.queryUtility(IAutoLogin)
                            or autoLoginViaAuthTkt)
            headers = auto_login(uuid, request)

            welcome_url = request.registry.settings.get('welcome_url')
            if welcome_url is None:
                welcome_url = model_url(context, request,
                                        'welcome.html')
            return HTTPFound(location=welcome_url, headers=headers)
    else:
        email = request.GET.get('email')
        if email is None:
            return HTTPFound(location=model_url(context, request,
                                                'register.html',
                                                query={'message':
                                                        REGISTER_OR_VISIT}))
        if pending.get(email) is None:
            return HTTPFound(location=model_url(context, request,
                                                'register.html',
                                                query={'message':
                                                            REGISTER_FIRST}))
        rendered_form = form.render({'email': email})

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'rendered_form': rendered_form,
           }


def welcome_view(context, request):
    identity = request.environ.get('repoze.who.identity')
    if identity is None:
        return HTTPFound(location=model_url(context, request,
                                            'register.html',
                                            query={'message':
                                                        REGISTER_FIRST}))
    userid = identity['repoze.who.userid']
    confirmed = request.registry.queryAdapter(context, IRegistrations,
                                              name='confirmed')
    if confirmed is None:  #pragma NO COVERAGE
        confirmed = ConfirmedRegistrations(context)
    account_info = confirmed.get(userid)
    if account_info is None:
        return HTTPForbidden()
    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'authenticated_user': userid,
            'login': account_info.login,
            'email': account_info.email,
           }


def edit_account_view(context, request):
    confirmed = request.registry.queryAdapter(context, IRegistrations,
                                              name='confirmed')
    if confirmed is None:  #pragma NO COVERAGE
        confirmed = ConfirmedRegistrations(context)

    identity = request.environ.get('repoze.who.identity')
    if identity is None:
        return HTTPUnauthorized()

    userid = identity['repoze.who.userid']
    account_info = confirmed.get(userid)
    if account_info is None:
        return HTTPForbidden()

    # TODO:  allow editing email
    appstruct = {'login_name': account_info.login,
                 'security': {'question': account_info.security_question or '',
                              'answer': account_info.security_answer or '',
                             },
                }
    schema = EditAccount().bind(current_login_name=account_info.login,
                                confirmed=confirmed,
                                old_password=account_info.password)
    form = Form(schema, buttons=('update',))
    rendered_form = form.render(appstruct)

    if 'update' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e:
            rendered_form = e.render()
        else:
            login = appstruct['login_name']
            #email = appstruct['email'] #XXX
            email = account_info.email
            pwd_mgr = SSHAPasswordManager()
            password = pwd_mgr.encodePassword(
                                            appstruct['password'])
            security_question = appstruct['security']['question']
            security_answer = appstruct['security']['answer']
            confirmed.set(userid,
                          email=email,
                          login=login, 
                          password=password,
                          security_question=security_question,
                          security_answer=security_answer,
                         )
            return HTTPFound(location=model_url(context, request,
                                                request.view_name))

    main_template = get_renderer('templates/main.pt')

    return {'main_template': main_template.implementation(),
            'rendered_form': rendered_form,
           }
