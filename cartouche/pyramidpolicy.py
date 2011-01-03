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

from zope.interface import implements

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Authenticated
from pyramid.security import Everyone
from repoze.who.config import make_api_factory_with_config


class PyramidPolicy(object):
    implements(IAuthenticationPolicy)

    def __init__(self, global_conf, config_file, identifier_id,
                 callback=None):
        self._api_factory = make_api_factory_with_config(global_conf,
                                                         config_file)
        self._identifier_id = identifier_id
        if callback is None:
            callback = lambda identity, request: ()
        self._callback = callback

    def authenticated_userid(self, request):
        """ See IAuthenticationPolicy.
        """
        identity = self._get_identity(request)

        if identity is not None:
            groups = self._callback(identity, request)
            if groups is not None:
                return identity['repoze.who.userid']

    def effective_principals(self, request):
        """ See IAuthenticationPolicy.
        """
        identity = self._get_identity(request)
        groups = self._get_groups(identity, request)
        if len(groups) > 1:
            groups.insert(0, identity['repoze.who.userid'])
        return groups

    def remember(self, request, principal, **kw):
        """ See IAuthenticationPolicy.
        """
        api = self._getAPI(request)
        identity = {'repoze.who.userid': principal,
                    'identifier': self._identifier_id,
                   }
        return api.remember(identity)

    def forget(self, request):
        """ See IAuthenticationPolicy.
        """
        api = self._getAPI(request)
        identity = self._get_identity(request)
        return api.forget(identity)

    def _getAPI(self, request):
        return self._api_factory(request.environ)

    def _get_identity(self, request):
        identity = request.environ.get('repoze.who.identity')
        if identity is None:
            api = self._getAPI(request)
            identity = api.authenticate()
        return identity

    def _get_groups(self, identity, request):
        if identity is not None:
            dynamic = self._callback(identity, request)
            if dynamic is not None:
                groups = list(dynamic)
                groups.append(Authenticated)
                groups.append(Everyone)
                return groups
        return [Everyone]
