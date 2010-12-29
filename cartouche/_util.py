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

from pyramid.url import model_url
from repoze.sendmail.delivery import DirectMailDelivery
from repoze.sendmail.mailer import SMTPMailer

# By default, deliver e-mail via localhost, port 25.
_delivery = DirectMailDelivery(SMTPMailer())

def _fixup_url(context, request, base_url, **extra_qs):
    if base_url.startswith('/'):
        base_url = urljoin(model_url(context, request), base_url)
    (sch, netloc, path, parms, qs, frag) = urlparse(base_url)
    qs_items = parse_qsl(qs) + extra_qs.items()
    qs = urlencode(qs_items, 1)
    return urlunparse((sch, netloc, path, parms, qs, frag))

def _view_url(context, request, key, default_name, **extra_qs):
    configured = request.registry.settings.get('cartouche.%s' % key)
    if configured is None:
        if extra_qs:
            return model_url(context, request, default_name, query=extra_qs)
        return model_url(context, request, default_name)
    return _fixup_url(context, request, configured, **extra_qs)
