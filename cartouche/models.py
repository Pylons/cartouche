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

from BTrees.OOBTree import OOBTree
from persistent import Persistent
from persistent.mapping import PersistentMapping
from pyramid.security import Allow
from pyramid.security import Authenticated
from zope.interface import implements

from cartouche.interfaces import IRoot
from cartouche.interfaces import ICartouche
from cartouche.interfaces import IPendingRegistrationInfo
from cartouche.interfaces import IRegistrationInfo


class Root(PersistentMapping):
    implements(IRoot)
    __parent__ = __name__ = None
    __acl__ = [(Allow, Authenticated, ('view', 'edit_own_account'))]
    def __repr__(self):
        return '<Root object;  keys: %s>' % ', '.join(self.keys())


class Cartouche(Persistent):
    implements(ICartouche)

    def __init__(self):
        self.pending = OOBTree()
        self.by_uuid = OOBTree()
        self.by_email = OOBTree()
        self.by_login = OOBTree()


class PendingRegistrationInfo(Persistent):
    implements(IPendingRegistrationInfo)

    def __init__(self, email, token):
        self.email = email
        self.token = token


class RegistrationInfo(Persistent):
    implements(IRegistrationInfo)

    def __init__(self,
                 uuid,
                 email,
                 login,
                 password,
                 security_question,
                 security_answer,
                 token=None,
                ):
        self.uuid = uuid
        self.email = email
        self.login = login
        self.password = password
        self.security_question = security_question
        self.security_answer = security_answer
        self.token = token
