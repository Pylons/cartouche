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

from pyramid.threadlocal import get_current_registry
from pyramid.threadlocal import get_current_request
from repoze.who.interfaces import IAuthenticator
from repoze.zodbconn.finder import PersistentApplicationFinder
from zope.interface import implements
from zope.password.password import SSHAPasswordManager

from cartouche import appmaker
from cartouche.interfaces import IRegistrations
from cartouche.persistence import ConfirmedRegistrations

class WhoPlugin(object):
    implements(IAuthenticator)
    _finder = None

    def __init__(self, zodb_uri):
        self._zodb_uri = zodb_uri
        self._pwd_mgr = SSHAPasswordManager()

    def _getFinder(self):
        if self._finder is None:
            self._finder = PersistentApplicationFinder(self._zodb_uri, appmaker)
        return self._finder

    def authenticate(self, environ, identity):
        """ See IAuthenticator.
        """
        login = identity.get('login')
        password = identity.get('password')
        if login is not None and password is not None:
            request = get_current_request()
            context = getattr(request, 'context', None)
            registry = get_current_registry()
            confirmed = registry.queryAdapter(context, IRegistrations,
                                              name='confirmed')
            if confirmed is None:
                app = self._getFinder()(environ)
                confirmed = ConfirmedRegistrations(app)
            record = confirmed.get_by_login(login)
            if record and self._pwd_mgr.checkPassword(record.password,
                                                      password):
                return record.uuid

def make_plugin(zodb_uri):
    return WhoPlugin(zodb_uri)
