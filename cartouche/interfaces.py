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
from zope.interface import Attribute
from zope.interface import Interface


class IRoot(Interface):
    """ Marker interface for the object at the traversal root.
    """


class ICartouche(Interface):
    """ Data container, held as an attribute of the root.
    """
    pending = Attribute(u'Pending registrations, keyed by email')
    by_uuid = Attribute(u'Confirmed registrations, keyed by UUID')
    by_email = Attribute(u'Index, email -> UUID')
    by_login = Attribute(u'Index, login name -> UUID')


class ITokenGenerator(Interface):
    """ Utility interface:  generate tokens for confirmation e-mails.
    """
    def __call__():
        """ Return a unique, quasi-random token as an ASCII-only string.
        """


class IPasswordGenerator(Interface):
    """ Utility interface:  generate random passwords for users.
    """
    def __call__():
        """ Return a random / string password string.
        """

class IAutoLogin(Interface):
    """ Utility interface to allow loggin users in automatically.
    """
    def __call__(userid, request):
        """ Return auto-login response headers for newly-confirmed user.
        """

class IPendingRegistrationInfo(Interface):
    """ Model schema of objects tracking pending registrations.
    """
    email = Attribute(u'Registered e-mail address')
    token = Attribute(u'Token generated at registration')


class IRegistrationInfo(Interface):
    """ Model schema of objects tracking confirmed registrations.
    """
    uuid = Attribute(u'Opaque identifier')
    email = Attribute(u'Registered e-mail address')
    password = Attribute(u'Hashed password')
    security_question = Attribute(u'Security question')
    security_answer = Attribute(u'Answer to security question')
    token = Attribute(u'Token generated for password reset')


class IRegistrations(Interface):
    """ Adapter interface:  store / retrieve registration info by key.
    """
    def __iter__():
        """ Return an iterator over our items, (key, info).
        """

    def set(key, **kw):
        """ Store registration info for 'key'.
        """

    def get(key, default=None):
        """ Return info for 'key'.

        Return 'default' if not found
        """

    def get_by_email(email, default=None):
        """ Return info for 'email'.

        Return 'default' if not found
        """

    def get_by_login(login, default=None):
        """ Return info for 'login'.

        Return 'default' if not found
        """

    def remove(key):
        """ Remove info for 'key'.

        Raise KeyError if not found.
        """
