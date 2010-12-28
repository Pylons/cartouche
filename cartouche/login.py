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

from colander import Schema
from colander import SchemaNode
from colander import String
from colander import null
from deform import Form
from deform import ValidationFailure
from deform.widget import PasswordWidget
from pyramid.renderers import get_renderer
from pyramid.url import model_url
from repoze.who.api import get_api
from webob.exc import HTTPFound


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
                return HTTPFound(location=model_url(context, request),
                                 headers=headers)
            message = 'Login failed'

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'rendered_form': rendered_form,
            'message': message
           }

def logout_view(context, request):
    api = get_api(request.environ)
    headers =  api.logout()
    return HTTPFound(location=model_url(context, request), headers=headers)
