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

from colander import Email
from colander import Schema
from colander import SchemaNode
from colander import String
from colander import null
from deform import Form
from deform import ValidationFailure
from deform.widget import HiddenWidget
from deform.widget import PasswordWidget
from pyramid.renderers import get_renderer
from pyramid.url import resource_url
from repoze.sendmail.interfaces import IMailDelivery
from repoze.who.api import get_api
from webob.exc import HTTPFound

from cartouche.interfaces import IAutoLogin
from cartouche.interfaces import ICameFromURL
from cartouche.interfaces import IRegistrations
from cartouche.persistence import ConfirmedRegistrations
from cartouche.util import getRandomToken
from cartouche.util import localhost_mta
from cartouche.util import sendGeneratedPassword
from cartouche.util import view_url

class Login(Schema):
    login_name = SchemaNode(String())
    password = SchemaNode(String(), widget=PasswordWidget())
    came_from = SchemaNode(String(), missing=None, widget=HiddenWidget())


def login_view(context, request):
    whence = request.registry.queryUtility(ICameFromURL)
    if whence is not None:
        came_from = whence(request)
    else:
        came_from = resource_url(context, request)
    form = Form(Login(), buttons=('login',))
    rendered_form = form.render({'came_from': came_from})
    message = request.GET.get('message')

    if 'login' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e:
            rendered_form = e.render()
            message = 'Please supply required values'
        else:
            credentials = {'login': appstruct['login_name'],
                           'password': appstruct['password'],
                          }
            api = get_api(request.environ)
            identity, headers =  api.login(credentials)
            if identity is not None:
                came_from = appstruct.get('came_from')
                if came_from is None:
                    came_from = resource_url(context, request)
                return HTTPFound(location=came_from, headers=headers)
            message = 'Login failed'

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'came_from': came_from,
            'rendered_form': rendered_form,
            'message': message,
            'register_url': view_url(context, request,
                                     'register_url',
                                     'register.html'),
            'recover_account_url': view_url(context, request,
                                            'recover_account_url',
                                            'recover_account.html'),
            'reset_password_url': view_url(context, request,
                                           'reset_password_url',
                                           'reset_password.html'),
           }


def logout_view(context, request):
    if 'logout' in request.POST:
        api = get_api(request.environ)
        headers =  api.logout()
        after_logout_url = view_url(context, request, 'after_logout_url', '')
        return HTTPFound(location=after_logout_url, headers=headers)
    identity = request.environ.get('repoze.who.identity', {})
    return {'userid': identity.get('repoze.who.userid')}


RECOVERY_EMAIL = """
Your login name on this site is:

  %(login)s

If you do not still have the login page open, you can visit it via
this URL:

  %(login_url)s

"""


class RecoverAccount(Schema):
    email = SchemaNode(String(), validator=Email())


def recover_account_view(context, request):
    form = Form(RecoverAccount(), buttons=('recover',))
    rendered_form = form.render(null)
    confirmed = request.registry.queryAdapter(context, IRegistrations,
                                              name='confirmed')
    if confirmed is None:  #pragma NO COVERAGE
        confirmed = ConfirmedRegistrations(context)
    login_url = view_url(context, request, 'login_url', 'login.html')
    registry = request.registry
    message = request.GET.get('message')

    if 'recover' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e: #pragma NO COVER
            rendered_form = e.render()
        else:
            email = appstruct['email']
            record = confirmed.get_by_email(email)
            if record is not None:
                from_addr = registry.settings['cartouche.from_addr']
                login = record.login
                body = RECOVERY_EMAIL % {'login': login,
                                         'login_url': login_url}
                delivery = registry.queryUtility(IMailDelivery,
                                                 default=localhost_mta)
                email_message = Message()
                email_message['Subject'] = 'Account recovery'
                email_message.set_payload(body)
                delivery.send(from_addr, [email], email_message)
            #else: # DO NOT report lookup errors
            return HTTPFound(location=login_url)

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'rendered_form': rendered_form,
            'reset_password_url': view_url(context, request,
                                           'reset_password_url',
                                           'reset_password.html'),
            'message': message,
           }


RESET_EMAIL = """
You have requested a password reset.

In your browser, please copy and paste the following string
into the 'Token' field:

  %(token)s

If you do not still have that page open, you can visit it via
this URL:

  %(reset_url)s

Once you have entered the token, click the "Reset" button to
be logged in to change your password.
"""

CHECK_TOKEN = ('Please copy the token from your password reset e-mail.')


class ResetPassword(Schema):
    login_name = SchemaNode(String())
    token = SchemaNode(String(), missing='')


def reset_password_view(context, request):
    form = Form(ResetPassword(), buttons=('reset',))
    rendered_form = form.render(null)
    confirmed = request.registry.queryAdapter(context, IRegistrations,
                                              name='confirmed')
    if confirmed is None:  #pragma NO COVERAGE
        confirmed = ConfirmedRegistrations(context)
    login_url = view_url(context, request, 'login_url', 'login.html')
    reset_url = resource_url(context, request, request.view_name)
    registry = request.registry
    message = request.GET.get('message')

    if 'reset' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e:
            rendered_form = e.render()
        else:
            login = appstruct['login_name']
            token = appstruct['token']
            record = confirmed.get_by_login(login)
            if record is None:
                # DO NOT report lookup errors
                return HTTPFound(location=login_url)
            if token == '':
                # send the e-mail
                new_token = getRandomToken(request)
                confirmed.set(record.uuid,
                              email=record.email,
                              login=login, 
                              password=record.password,
                              security_question=record.security_question,
                              security_answer=record.security_answer,
                              token=new_token,
                             )
                from_addr = registry.settings['cartouche.from_addr']
                body = RESET_EMAIL % {'token': new_token,
                                      'reset_url': reset_url}
                delivery = registry.queryUtility(IMailDelivery,
                                                 default=localhost_mta)
                message = Message()
                message['Subject'] = 'Password reset confirmation'
                message.set_payload(body)
                delivery.send(from_addr, [record.email], message)
                return HTTPFound(location=reset_url)
            else:
                if token != record.token:
                    message = CHECK_TOKEN
                    # fall through to 'GET'
                else:
                    confirmed.set(record.uuid,
                                  email=record.email,
                                  login=record.login, 
                                  password=None,  # clear it to allow update
                                  security_question=record.security_question,
                                  security_answer=record.security_answer,
                                  token=None,     # clear it
                                 )
                    after_reset_url = view_url(context, request,
                                               'after_reset_url',
                                               'edit_account.html',
                                              )
                    auto_login = request.registry.queryUtility(IAutoLogin)
                    if auto_login is not None:
                        headers = auto_login(record.uuid, request)
                        return HTTPFound(location=after_reset_url,
                                         headers=headers)
                    else:
                        # TODO:  generate random password and send e-mail.
                        sendGeneratedPassword(request, record.uuid, confirmed)
                        return HTTPFound(location=after_reset_url)

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'message': message,
            'rendered_form': rendered_form,
            'recover_account_url': view_url(context, request,
                                            'recover_account_url',
                                            'recover_account.html'),
           }
