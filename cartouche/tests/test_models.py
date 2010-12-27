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
import unittest


class CartoucheTests(unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.models import Cartouche
        return Cartouche

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_conforms_to_ICartouche(self):
        from zope.interface.verify import verifyClass
        from cartouche.interfaces import ICartouche
        verifyClass(ICartouche, self._getTargetClass())

    def test_instance_conforms_to_ICartouche(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import ICartouche
        verifyObject(ICartouche, self._makeOne())


class RegistrationInfoTests(unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.models import RegistrationInfo
        return RegistrationInfo

    def _makeOne(self, email='phred@example.com', token='token'):
        return self._getTargetClass()(email, token)

    def test_class_conforms_to_IRegistrationInfo(self):
        from zope.interface.verify import verifyClass
        from cartouche.interfaces import IRegistrationInfo
        verifyClass(IRegistrationInfo, self._getTargetClass())

    def test_instance_conforms_to_IRegistrationInfo(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import IRegistrationInfo
        verifyObject(IRegistrationInfo, self._makeOne())
