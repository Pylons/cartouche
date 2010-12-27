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


class RootTests(unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.models import Root
        return Root

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_conforms_to_IRoot(self):
        from zope.interface.verify import verifyClass
        from cartouche.interfaces import IRoot
        verifyClass(IRoot, self._getTargetClass())

    def test_instance_conforms_to_IRoot(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import IRoot
        verifyObject(IRoot, self._makeOne())

    def test___repr___empty(self):
        root = self._makeOne()
        self.assertEqual(repr(root), '<Root object;  keys: >')

    def test___repr___non_empty(self):
        root = self._makeOne()
        root['a'] = object()
        root['b'] = object()
        self.assertEqual(repr(root), '<Root object;  keys: a, b>')


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


class PendingRegistrationInfoTests(unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.models import PendingRegistrationInfo
        return PendingRegistrationInfo

    def _makeOne(self, email='phred@example.com', token='token'):
        return self._getTargetClass()(email, token)

    def test_class_conforms_to_IPendingRegistrationInfo(self):
        from zope.interface.verify import verifyClass
        from cartouche.interfaces import IPendingRegistrationInfo
        verifyClass(IPendingRegistrationInfo, self._getTargetClass())

    def test_instance_conforms_to_IPendingRegistrationInfo(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import IPendingRegistrationInfo
        verifyObject(IPendingRegistrationInfo, self._makeOne())


class RegistrationInfoTests(unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.models import RegistrationInfo
        return RegistrationInfo

    def _makeOne(self,
                 email='phred@example.com',
                 login='login',
                 password='password',
                 security_question='question',
                 security_answer='answer',
                ):
        return self._getTargetClass()(email, login, password,   
                                      security_question, security_answer)

    def test_class_conforms_to_IRegistrationInfo(self):
        from zope.interface.verify import verifyClass
        from cartouche.interfaces import IRegistrationInfo
        verifyClass(IRegistrationInfo, self._getTargetClass())

    def test_instance_conforms_to_IRegistrationInfo(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import IRegistrationInfo
        verifyObject(IRegistrationInfo, self._makeOne())
