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


class IRegistrationInfo(Interface):
    email = Attribute(u'Registered e-mail address')
    security_question = Attribute(u'Question selected at registration')
    security_answer = Attribute(u'Answer provided at registration')
    token = Attribute(u'Token generated at registration')


class IPendingRegistrations(Interface):
    """ Adapter interface:  store / retrieve pending registration info.
    """
    def set(email, security_qusetion, security_answer, token):
        """ Store registration info for 'email'.
        """

    def get(email, default=None):
        """ Return IRegistrationInfo for 'email'.

        Return 'default' if not found
        """

class ITokenGenerator(Interface):
    """ Utility interface:  generate tokens for confirmation e-mails.
    """
    def getToken():
        """ Return a unique, quasi-random token as a string.
        """
