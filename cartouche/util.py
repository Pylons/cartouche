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
from urllib import urlencode
from urlparse import parse_qsl
from urlparse import urljoin
from urlparse import urlparse
from urlparse import urlunparse
from uuid import uuid4

from pyramid.url import model_url
from repoze.sendmail.delivery import DirectMailDelivery
from repoze.sendmail.mailer import SMTPMailer
from repoze.who.api import get_api
from zope.interface import directlyProvides

from cartouche.interfaces import IAutoLogin
from cartouche.interfaces import ITokenGenerator

# By default, deliver e-mail via localhost, port 25.
localhost_mta = DirectMailDelivery(SMTPMailer())


def _fixup_url(context, request, base_url, **extra_qs):
    if base_url.startswith('/'):
        base_url = urljoin(model_url(context, request), base_url)
    (sch, netloc, path, parms, qs, frag) = urlparse(base_url)
    qs_items = parse_qsl(qs) + extra_qs.items()
    qs = urlencode(qs_items, 1)
    return urlunparse((sch, netloc, path, parms, qs, frag))


def view_url(context, request, key, default_name, **extra_qs):
    configured = request.registry.settings.get('cartouche.%s' % key)
    if configured is None:
        if extra_qs:
            return model_url(context, request, default_name, query=extra_qs)
        return model_url(context, request, default_name)
    return _fixup_url(context, request, configured, **extra_qs)


def getRandomToken(request):
    generator = request.registry.queryUtility(ITokenGenerator)
    if generator:
        return generator.getToken()
    return str(uuid4())


def autoLoginViaWhoAPI(userid, request):
    api = get_api(request.environ)
    if api is None:
        raise ValueError("Couldn't find / create repoze.who API object")
    credentials = {'repoze.who.plugins.auth_tkt.userid': userid}
    settings = request.registry.settings
    plugin_id = settings.get('cartouche.auto_login_identifier', 'auth_tkt')
    identity, headers = api.login(credentials, plugin_id)
    return headers
directlyProvides(autoLoginViaWhoAPI, IAutoLogin)
