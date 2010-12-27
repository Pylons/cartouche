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
from webob.exc import HTTPFound
from zope.interface import implements

from cartouche.interfaces import IRegistrations
from cartouche.interfaces import ITokenGenerator


class PendingRegistrations(object):
    """ Default implementation for ZODB-based storage.

    Stores registration info in a BTree named 'pending', an attribute of the
    root object's 'cartouche' attribute.
    """
    implements(IRegistrations)

    def __init__(self, context):
        self.context = context

    def set(self, email, **kw):
        """ See IRegistrations.
        """
        token = kw['token']
        info = self._makeInfo(email, token)
        self._getCartouche(True).pending[email] = info

    def get(self, email, default=None):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            return default
        return cartouche.pending.get(email, default)

    def _getCartouche(self, create=False):
        # Import here to allow reuse of views without stock models.
        from pyramid.traversal import find_root
        from cartouche.models import Cartouche
        root = find_root(self.context)
        cartouche = getattr(root, 'cartouche', None)
        if cartouche is None and create:
            cartouche = root.cartouche = Cartouche()
        return cartouche

    def _makeInfo(self, email, token):
        # Import here to allow reuse of views without stock models.
        from cartouche.models import PendingRegistrationInfo as PRI
        return PRI(email, token)


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
            # TODO:  transfer pending info to permanent store
            # TODO:  use who API to remember identity.
            welcome_url = request.registry.settings.get('welcome_url')
            if welcome_url is None:
                welcome_url = model_url(context, request,
                                        'welcome.html')
            return HTTPFound(location=welcome_url)
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
