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
from repoze.sendmail.interfaces import IMailDelivery
from repoze.who.api import get_api
from webob.exc import HTTPForbidden
from webob.exc import HTTPFound
from webob.exc import HTTPUnauthorized
from zope.interface import directlyProvides
from zope.password.password import SSHAPasswordManager

from cartouche.interfaces import IAutoLogin
from cartouche.interfaces import IRegistrations
from cartouche.persistence import ConfirmedRegistrations
from cartouche.persistence import PendingRegistrations
from cartouche.util import getRandomToken
from cartouche.util import localhost_mta
from cartouche.util import view_url


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
    email = SchemaNode(String(), validator=Email())
    old_password = SchemaNode(String(),
                              widget=old_password_widget,
                              missing=old_password_missing,
                              validator=old_password_validator,
                             )
    password = SchemaNode(String(),
                          widget=CheckedPasswordWidget())
    security = SecurityQuestion()


def autoLoginViaAuthTkt(userid, request):
    api = get_api(request.environ)
    if api is None:
        raise ValueError("Couldn't find / create repoze.who API object")
    credentials = {'repoze.who.plugins.auth_tkt.userid': userid}
    plugin_id = request.registry.settings.get('cartouche.auth_tkt_plugin_id',
                                              'auth_tkt')
    identity, headers = api.login(credentials, plugin_id)
    return headers
directlyProvides(autoLoginViaAuthTkt, IAutoLogin)


REGISTRATION_EMAIL = """
Thank you for registering.  

In your browser, please copy and paste the following string
into the 'Token' field:

  %(token)s

If you do not still have that page open, you can visit it via
this URL:

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

            from_addr = request.registry.settings['cartouche.from_addr']
            delivery = request.registry.queryUtility(IMailDelivery,
                                                     default=localhost_mta)
            confirmation_url = view_url(context, request, 'confirmation_url',
                                        'confirm_registration.html',
                                        email=email)
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
                return HTTPFound(
                        location=view_url(context, request,
                                          'register_url',
                                          'register.html',
                                          message=REGISTER_FIRST,
                                         ))
            if token != info.token:
                return HTTPFound(
                        location=view_url(context, request,
                                          'confirmation_url',
                                          'confirm_registration.html',
                                          email=email,
                                          message=CHECK_TOKEN,
                                         ))
            confirmed = request.registry.queryAdapter(context, IRegistrations,
                                                      name='confirmed')
            if confirmed is None:  #pragma NO COVERAGE
                confirmed = ConfirmedRegistrations(context)
            pending.remove(email)
            uuid = getRandomToken(request)
            confirmed.set(uuid, email=email, login=email, password=None,
                          security_question=None, security_answer=None)
            info = confirmed.get(uuid)

            auto_login = request.registry.queryUtility(IAutoLogin)
            if auto_login is not None:
                headers = auto_login(uuid, request)
            else:
                headers = ()

            after_confirmation_url = view_url(context, request,
                                              'after_confirmation_url',
                                              'edit_account.html',
                                             )
            return HTTPFound(location=after_confirmation_url, headers=headers)
    else:
        email = request.GET.get('email')
        if email is None:
            return HTTPFound(
                        location=view_url(context, request,
                                          'register_url',
                                          'register.html',
                                          message=REGISTER_OR_VISIT,
                                         ))
        if pending.get(email) is None:
            return HTTPFound(
                        location=view_url(context, request,
                                          'register_url',
                                          'register.html',
                                          message=REGISTER_FIRST,
                                         ))
        rendered_form = form.render({'email': email})

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'rendered_form': rendered_form,
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

    appstruct = {'login_name': account_info.login,
                 'email': account_info.email,
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
            email = appstruct['email']
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
            return HTTPFound(
                        location=view_url(context, request,
                                          'after_edit_url',
                                          request.view_name,
                                         ))

    main_template = get_renderer('templates/main.pt')

    return {'main_template': main_template.implementation(),
            'rendered_form': rendered_form,
           }
