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

from repoze.who.interfaces import IAuthenticator
from repoze.zodbconn.finder import PersistentApplicationFinder
from zope.interface import implements
from zope.password.password import SSHAPasswordManager

from cartouche import appmaker
from cartouche.persistence import ConfirmedRegistrations

class WhoPlugin(object):
    implements(IAuthenticator)

    def __init__(self, zodb_uri):
        self._finder = PersistentApplicationFinder(zodb_uri, appmaker)
        self._pwd_mgr = SSHAPasswordManager()

    def authenticate(self, environ, identity):
        """ See IAuthenticator.
        """
        login = identity.get('login')
        password = identity.get('password')
        if login is not None and password is not None:
            app = self._finder(environ)
            confirmed = ConfirmedRegistrations(app)
            record = confirmed.get_by_login(login)
            if record and self._pwd_mgr.checkPassword(record.password,
                                                      password):
                return record.uuid
