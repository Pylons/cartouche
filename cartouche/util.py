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
from random import choice
from random import randrange
from string import digits
from uuid import uuid4

from pyramid.url import resource_url
from repoze.sendmail.delivery import DirectMailDelivery
from repoze.sendmail.mailer import SMTPMailer
from repoze.sendmail.interfaces import IMailDelivery
from repoze.who.api import get_api
from zope.interface import directlyProvides
from zope.password.password import SSHAPasswordManager

from .interfaces import IAutoLogin
from .interfaces import ICameFromURL
from .interfaces import IPasswordGenerator
from .interfaces import ITokenGenerator
from ._compat import letters
from ._compat import url_encode
from ._compat import parse_qsl
from ._compat import urljoin
from ._compat import urlparse
from ._compat import urlunparse

# By default, deliver e-mail via localhost, port 25.
localhost_mta = DirectMailDelivery(SMTPMailer())


def _fixup_url(context, request, base_url, **extra_qs):
    if base_url.startswith('/'):
        base_url = urljoin(resource_url(context, request), base_url)
    (sch, netloc, path, parms, qs, frag) = urlparse(base_url)
    qs_items = parse_qsl(qs) + list(extra_qs.items())
    qs = url_encode(qs_items, 1)
    return urlunparse((sch, netloc, path, parms, qs, frag))


def view_url(context, request, key, default_name, **extra_qs):
    configured = request.registry.settings.get('cartouche.%s' % key)
    if configured is None:
        if extra_qs:
            return resource_url(context, request, default_name, query=extra_qs)
        return resource_url(context, request, default_name)
    return _fixup_url(context, request, configured, **extra_qs)


def uuidRandomToken():
    return str(uuid4())
directlyProvides(uuidRandomToken, ITokenGenerator)


def getRandomToken(request):
    generator = request.registry.queryUtility(ITokenGenerator,
                                              default=uuidRandomToken)
    return generator()


def randomPassword():
    result = []
    for _ in range(randrange(6, 8)):
        result.append(choice(_CHARS))
    result.append(choice(_SYMBOLS))
    for _ in range(randrange(6, 8)):
        result.append(choice(_CHARS))
    return ''.join(result)
directlyProvides(randomPassword, IPasswordGenerator)


def autoLoginViaWhoAPI(uuid, request):
    api = get_api(request.environ)
    if api is None:
        raise ValueError("Couldn't find / create repoze.who API object")
    credentials = {'repoze.who.plugins.auth_tkt.userid': uuid}
    settings = request.registry.settings
    plugin_id = settings.get('cartouche.auto_login_identifier', 'auth_tkt')
    identity, headers = api.login(credentials, plugin_id)
    return headers
directlyProvides(autoLoginViaWhoAPI, IAutoLogin)


PASSWORD_EMAIL = """\
Your new password is:

  %(password)s

You can login to the site at the following URL:

  %(login_url)s
"""

_SYMBOLS = '~!@#$%^&*'
_CHARS = letters + digits

def sendGeneratedPassword(request, uuid, confirmed):
    record = confirmed.get(uuid)
    if record is None:
        raise KeyError
    pwd_mgr = SSHAPasswordManager()
    generator = request.registry.queryUtility(IPasswordGenerator,
                                              default=randomPassword)
    new_password = generator()
    encoded = pwd_mgr.encodePassword(new_password)
    confirmed.set(uuid,
                  email=record.email,
                  login=record.login,
                  password=encoded,
                  security_question=record.security_question,
                  security_answer=record.security_answer,
                  token=record.token,
                 )
    from_addr = request.registry.settings['cartouche.from_addr']
    delivery = request.registry.queryUtility(IMailDelivery,
                                             default=localhost_mta)
    login_url = view_url(request.context, request, 'login_url', 'login.html')
    body = PASSWORD_EMAIL % {'password': new_password, 'login_url': login_url}
    message = Message()
    message['Subject'] = 'Your new site password'
    message.set_payload(body)
    delivery.send(from_addr, [record.email], message)


def defaultCameFromURL(request):
    came_from = request.GET.get('came_from')
    if came_from is None:
        came_from = request.environ.get('HTTP_REFERER') #sic
    if came_from is None:
        came_from = resource_url(request.context, request, request.view_name)
    return came_from
directlyProvides(defaultCameFromURL, ICameFromURL)
