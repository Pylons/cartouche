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

from pyramid.traversal import find_root
from zope.interface import implements

from cartouche.interfaces import IRegistrations
from cartouche.models import Cartouche
from cartouche.models import PendingRegistrationInfo
from cartouche.models import RegistrationInfo


class _RegistrationsBase(object):
    """ Default implementation for ZODB-based storage.

    Finds / creates a 'cartouche' attribute of the traversal root.

    Stores registration info in mapping attributes of the 'cartouche' object.
    """
    cartouche = None

    def __init__(self, context):
        self.context = context

    def set(self, key, **kw):
        """ See IRegistrations.
        """
        info = self._makeInfo(key, **kw)
        self.set_record(key, info)

    def set_record(self, key, record):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche(True)
        self._getMapping()[key] = record

    def get(self, key, default=None):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            return default
        return self._getMapping().get(key, default)

    def remove(self, key):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            raise KeyError(key)
        del self._getMapping()[key]

    def _getCartouche(self, create=False):
        if self.cartouche is not None:
            return self.cartouche
        root = find_root(self.context)
        cartouche = getattr(root, 'cartouche', None)
        if cartouche is None:
            if create:
                cartouche = self.cartouche = root.cartouche = Cartouche()
        else:
            self.cartouche = cartouche
        return cartouche

    def _getMapping(self, attr=None):
        if self.cartouche is None:
            raise ValueError('Call _getCartouche first!')
        if attr is None:
            attr = self.ATTR
        return getattr(self.cartouche, attr)


class PendingRegistrations(_RegistrationsBase):
    """ Adapter for looking up pending registrations, keyed by email.
    """
    implements(IRegistrations)
    ATTR = 'pending'

    def _makeInfo(self, key, **kw):
        # Import here to allow reuse of views without stock models.
        token = kw['token']
        return PendingRegistrationInfo(email=key, token=token)

    def get_by_email(self, email, default=None):
        """ See IRegistrations.
        """
        return self.get(email, default)

    def get_by_login(self, login, default=None):
        """ See IRegistrations.
        """
        raise NotImplementedError


class ConfirmedRegistrations(_RegistrationsBase):
    """ Adapter for looking up confirmed registrations, keyed by UUID.
    """
    implements(IRegistrations)
    ATTR = 'by_uuid'

    def _makeInfo(self, key, **kw):
        email = kw['email']
        login = kw['login']
        password = kw.get('password')
        security_question = kw.get('security_question')
        security_answer = kw.get('security_answer')
        return RegistrationInfo(email=email,
                                login=login,
                                password=password,
                                security_question=security_question,
                                security_answer=security_answer,
                               )

    def set_record(self, key, record):
        """ See IRegistrations.
        """
        self._getCartouche(True)
        self._getMapping()[key] = record
        self._getMapping('by_login')[record.login] = key
        self._getMapping('by_email')[record.email] = key

    def get_by_email(self, email, default=None):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            return default
        uuid = self._getMapping('by_email').get(email)
        if uuid is None:
            return default
        return self.get(uuid)

    def get_by_login(self, login, default=None):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            return default
        uuid = self._getMapping('by_login').get(login)
        if uuid is None:
            return default
        return self.get(uuid)

    def remove(self, key):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            raise KeyError(key)
        record = self._getMapping()[key]
        del self._getMapping()[key]
        del self._getMapping('by_login')[record.login]
        del self._getMapping('by_email')[record.email]
