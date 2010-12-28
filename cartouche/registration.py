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
from colander import Schema
from colander import SchemaNode
from colander import String
from colander import null
from deform import Form
from deform import ValidationFailure
from deform.template import default_dir as deform_templates_dir
from deform.widget import SelectWidget
from pyramid.renderers import get_renderer
from pyramid.url import model_url
from repoze.sendmail.interfaces import IMailDelivery
from repoze.sendmail.delivery import DirectMailDelivery
from repoze.sendmail.mailer import SMTPMailer
from repoze.who.api import get_api
from webob.exc import HTTPFound
from zope.interface import implements

from cartouche.interfaces import IAutoLogin
from cartouche.interfaces import IRegistrations
from cartouche.interfaces import ITokenGenerator


class _RegistrationsBase(object):
    """ Default implementation for ZODB-based storage.

    Stores registration info in a BTree named 'pending', an attribute of the
    root object's 'cartouche' attribute.
    """
    implements(IRegistrations)

    def __init__(self, context):
        self.context = context

    def set(self, key, **kw):
        """ See IRegistrations.
        """
        info = self._makeInfo(key, **kw)
        cartouche = self._getCartouche(True)
        self._getMapping(cartouche)[key] = info

    def set_record(self, key, record):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche(True)
        self._getMapping(cartouche)[key] = record

    def get(self, key, default=None):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            return default
        return self._getMapping(cartouche).get(key, default)

    def remove(self, key):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            raise KeyError(key)
        del self._getMapping(cartouche)[key]

    def _getCartouche(self, create=False):
        # Import here to allow reuse of views without stock models.
        from pyramid.traversal import find_root
        from cartouche.models import Cartouche
        root = find_root(self.context)
        cartouche = getattr(root, 'cartouche', None)
        if cartouche is None and create:
            cartouche = root.cartouche = Cartouche()
        return cartouche

    def _getMapping(self, cartouche):
        return getattr(cartouche, self.ATTR)


class PendingRegistrations(_RegistrationsBase):
    ATTR = 'pending'

    def _makeInfo(self, key, **kw):
        # Import here to allow reuse of views without stock models.
        from cartouche.models import PendingRegistrationInfo as PRI
        token = kw['token']
        return PRI(email=key, token=token)


class ByEmailRegistrations(_RegistrationsBase):
    ATTR = 'by_email'

    def _makeInfo(self, key, **kw):
        # Import here to allow reuse of views without stock models.
        from cartouche.models import RegistrationInfo as RI
        login = kw.get('login', key)
        password = kw.get('password')
        security_question = kw.get('security_question')
        security_answer = kw.get('security_answer')
        return RI(email=key, login=login, password=password,
                  security_question=security_question,
                  security_answer=security_answer,
                 )


class ByLoginRegistrations(_RegistrationsBase):
    ATTR = 'by_login'

    def _makeInfo(self, key, **kw):
        # Import here to allow reuse of views without stock models.
        from cartouche.models import RegistrationInfo as RI
        email = kw.get('email', key)
        password = kw.get('password')
        security_question = kw.get('security_question')
        security_answer = kw.get('security_answer')
        return RI(email=email, login=key, password=password,
                  security_question=security_question,
                  security_answer=security_answer,
                 )


templates_dir = resource_filename('cartouche', 'templates/')
Form.set_zpt_renderer([templates_dir, deform_templates_dir])


QUESTIONS = [
    ('color', 'What is your favorite color?'),
    ('borncity', 'In what city were you born?'),
    ('petname', 'What was the name of your favorite childhood pet?'),
]


class SecurityQuestion(Schema):
    question = SchemaNode(String(), widget=SelectWidget(values=QUESTIONS))
    answer = SchemaNode(String())


class Signup(Schema):
    email = SchemaNode(String(), validator=Email())


class Confirm(Schema):
    email = SchemaNode(String(),
                       validator=Email(),
                      )
    token = SchemaNode(String(),
                       description="Enter the token from the registration "
                                   "confirmation e-mail you received.")


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
            by_email = request.registry.queryAdapter(context, IRegistrations,
                                                     name='by_email')
            if by_email is None:  #pragma NO COVERAGE
                by_email = ByEmailRegistrations(context)
            by_login = request.registry.queryAdapter(context, IRegistrations,
                                                     name='by_login')
            if by_login is None:  #pragma NO COVERAGE
                by_email = ByLoginRegistrations(context)
            pending.remove(email)
            by_email.set(email, login=email, password=None,
                         security_question=None, security_answer=None)
            info = by_email.get(email)
            by_login.set_record(email, info)
            # TODO:  use who API to remember identity.
            auto_login = (request.registry.queryUtility(IAutoLogin)
                            or autoLoginViaAuthTkt)
            headers = auto_login(email, request)

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
    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'authenticated_user': identity['repoze.who.userid'],
           }
