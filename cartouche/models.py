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
from zope.interface import implements

from cartouche.interfaces import ICartouche
from cartouche.interfaces import IRegistrationInfo


class Root(PersistentMapping):
    __parent__ = __name__ = None


class Cartouche(Persistent):
    implements(ICartouche)

    def __init__(self):
        self.pending = OOBTree()


class RegistrationInfo(Persistent):
    implements(IRegistrationInfo)

    def __init__(self, email, security_question, security_answer, token):
        self.email = email
        self.security_question = security_question
        self.security_answer = security_answer
        self.token = token
