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
from deform import Form
from deform.template import default_dir as deform_templates_dir
from deform.widget import SelectWidget
from deform.widget import TextInputWidget
from pyramid.renderers import get_renderer
from pyramid.url import model_url
from repoze.sendmail.interfaces import IMailDelivery
from repoze.sendmail.delivery import DirectMailDelivery
from repoze.sendmail.mailer import SMTPMailer
from webob.exc import HTTPFound
from zope.interface import implements

from cartouche.interfaces import IPendingRegistrations
from cartouche.interfaces import ITokenGenerator


class PendingRegistrations(object):
    """ Default implementation for ZODB-based storage.

    Stores registration info in a BTree named 'pending', an attribute of the
    root object's 'cartouche' attribute.
    """
    implements(IPendingRegistrations)

    def __init__(self, context):
        self.context = context

    def set(self, email, security_question, security_answer, token):
        """ See IPendingRegistrations.
        """
        info = self._makeInfo(email,
                              security_question, security_answer, token)
        self._getCartouche(True).pending[email] = info

    def get(self, email, default=None):
        """ See IPendingRegistrations.
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

    def _makeInfo(self, email, security_question, security_answer, token):
        # Import here to allow reuse of views without stock models.
        from cartouche.models import RegistrationInfo as RI
        return RI(email, security_question, security_answer, token)


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
    security = SecurityQuestion(title=" ")


class ReadonlyTextWidget(TextInputWidget):
    template = readonly_template = 'readonly_text_input'


class Confirm(Schema):
    email = SchemaNode(String(),
                       validator=Email(),
                       widget=ReadonlyTextWidget(),
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
    if 'register' in request.POST:
        pending = request.registry.queryAdapter(context,
                                                IPendingRegistrations)
        if pending is None:
            pending = PendingRegistrations(context)
        email = request.POST['email']
        security = request.POST['security']
        token = getRandomToken(request)
        pending.set(email, security['question'], security['answer'], token)

        from_addr = request.registry.settings['from_addr']
        delivery = request.registry.queryUtility(IMailDelivery) or _delivery
        confirmation_url = model_url(context, request, request.view_name,
                                     query=dict(email=email))
        body = REGISTRATION_EMAIL % {'token': token,
                                     'confirmation_url': confirmation_url}
        message = Message()
        message.set_payload(body)
        delivery.send(from_addr, [email], message)
        confirmation_url = model_url(context, request, request.view_name,
                                     query=dict(email=email))
        return HTTPFound(location=confirmation_url)

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'form': Form(Signup(), buttons=('register',)),
            'appstruct': None,
            'message': request.GET.get('message'),
           }



REGISTER_FIRST = 'Please register first.'
REGISTER_OR_VISIT = ('Please register first '
                     'or visit the link in your confirmation e-mail.')

def confirm_registration_view(context, request):
    if 'confirm' in request.POST:
        email = request.POST['email']
        token = request.POST['token']
        # TODO

    email = request.GET.get('email')
    if email is None:
        return HTTPFound(location=model_url(context, request, 'register.html',
                                            query={'message':
                                                        REGISTER_OR_VISIT}))
    pending = request.registry.queryAdapter(context,
                                            IPendingRegistrations)
    if pending is None:
        pending = PendingRegistrations(context)

    if pending.get(email) is None:
        return HTTPFound(location=model_url(context, request, 'register.html',
                                            query={'message':
                                                        REGISTER_FIRST}))

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'form': Form(Confirm(), buttons=('confirm',)),
            'appstruct': {'email': email},
           }
