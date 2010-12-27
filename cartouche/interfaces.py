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
    pass


class ICartouche(Interface):
    pending = Attribute(u'Pending registrations, keyed by email')


class ITokenGenerator(Interface):
    """ Utility interface:  generate tokens for confirmation e-mails.
    """
    def getToken():
        """ Return a unique, quasi-random token as a string.
        """


class IPendingRegistrationInfo(Interface):
    email = Attribute(u'Registered e-mail address')
    token = Attribute(u'Token generated at registration')


class IRegistrationInfo(Interface):
    email = Attribute(u'Registered e-mail address')
    password = Attribute(u'Hashed password')
    security_question = Attribute(u'Security question')
    security_answer = Attribute(u'Answer to security question')


class IRegistrations(Interface):
    """ Adapter interface:  store / retrieve pending registration info.
    """
    def set(key, **kw):
        """ Store registration info for 'key'.
        """

    def get(key, default=None):
        """ Return info for 'key'.

        Return 'default' if not found
        """
