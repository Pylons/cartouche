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
from deform.widget import PasswordWidget
from pyramid.renderers import get_renderer
from pyramid.url import model_url
from repoze.sendmail.interfaces import IMailDelivery
from repoze.who.api import get_api
from webob.exc import HTTPFound

from cartouche.interfaces import IRegistrations
from cartouche.persistence import ConfirmedRegistrations
from cartouche._util import _delivery
from cartouche._util import _view_url

class Login(Schema):
    login_name = SchemaNode(String())
    password = SchemaNode(String(), widget=PasswordWidget())


def login_view(context, request):
    form = Form(Login(), buttons=('login',))
    rendered_form = form.render(null)
    message = request.GET.get('message')

    if 'login' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e: #pragma NO COVER
            rendered_form = e.render()
        else:
            credentials = {'login': appstruct['login_name'],
                           'password': appstruct['password'],
                          }
            api = get_api(request.environ)
            identity, headers =  api.login(credentials)
            if identity is not None:
                # TODO: came_from handling
                return HTTPFound(location=model_url(context, request),
                                 headers=headers)
            message = 'Login failed'

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'rendered_form': rendered_form,
            'message': message,
            'recover_account_url': _view_url(context, request,
                                             'recover_account_url',
                                             'recover_account.html'),
            'reset_password_url': _view_url(context, request,
                                             'reset_password_url',
                                             'reset_password.html'),
           }


def logout_view(context, request):
    api = get_api(request.environ)
    headers =  api.logout()
    # TODO: make after-logout URL configurable?
    return HTTPFound(location=model_url(context, request), headers=headers)


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
    login_url = _view_url(context, request, 'login_url', 'login.html')
    registry = request.registry

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
                                                 default=_delivery)
                message = Message()
                message.set_payload(body)
                delivery.send(from_addr, [email], message)
            #else: # XXX not reporting lookup errors for now
            return HTTPFound(location=login_url)

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'rendered_form': rendered_form,
            'reset_password_url': _view_url(context, request,
                                             'reset_password_url',
                                             'reset_password.html'),
           }
