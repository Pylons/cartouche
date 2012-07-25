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
import os

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Authenticated
from pyramid.security import Everyone

try:
    from pyramid_zcml import with_context
except ImportError:
    from pyramid.config import Configurator
    def with_context(_context):
        return Configurator.with_context(_context)
    
from repoze.who.config import make_api_factory_with_config as FactoryFactory
from zope.interface import Interface
from zope.interface import implements
from zope.schema import ASCIILine
from zope.schema import TextLine

from cartouche.interfaces import IRegistrations
from cartouche.persistence import ConfirmedRegistrations


class ICartouchePolicyDirective(Interface):
    config_file = ASCIILine(title=u'config_file', required=True)
    identifier_name = TextLine(title=u'identitfier_name', required=True)


class PyramidPolicy(object):
    implements(IAuthenticationPolicy)

    def __init__(self, config_file, identifier_id):
        config_file = self._config_file = os.path.abspath(
                                            os.path.normpath(config_file))
        config_dir, _ = os.path.split(config_file)
        global_conf = {'here': config_dir}
        self._api_factory = FactoryFactory(global_conf, config_file)
        self._identifier_id = identifier_id

    def unauthenticated_userid(self, request):
        """ See IAuthenticationPolicy.
        """
        raise NotImplementedError()

    def authenticated_userid(self, request):
        """ See IAuthenticationPolicy.
        """
        identity = self._getIdentity(request)

        if identity is not None:
            confirmed = self._getConfirmed(request)
            uuid = identity['repoze.who.userid']
            record = confirmed.get(uuid)
            if record is not None:
                return uuid

    def effective_principals(self, request):
        """ See IAuthenticationPolicy.
        """
        uuid = self.authenticated_userid(request)
        if uuid is not None:
            groups = ([uuid] +
                      self._getGroups(uuid, request) +
                      [Authenticated, Everyone])
        else:
            groups = [Everyone]
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
        identity = self._getIdentity(request)
        return api.forget(identity)

    def _getAPI(self, request):
        return self._api_factory(request.environ)

    def _getIdentity(self, request):
        identity = request.environ.get('repoze.who.identity')
        if identity is None:
            api = self._getAPI(request)
            identity = api.authenticate()
        return identity

    def _getConfirmed(self, request):
        context = request.context
        confirmed = request.registry.queryAdapter(context, IRegistrations,
                                                  name='confirmed')
        if confirmed is None:
            confirmed = ConfirmedRegistrations(context)

        return confirmed

    def _getGroups(self, uuid, request):
        confirmed = self._getConfirmed(request)
        confirmed._getCartouche()
        return confirmed._getMapping('user_groups').get(uuid) or []


def cartoucheAuthenticationPolicy(_context, config_file, identifier_name):
    policy = PyramidPolicy(config_file, identifier_name)
    # authentication policies must be registered eagerly so they can
    # be found by the view registration machinery
    config = with_context(_context)
    config._set_authentication_policy(policy)
