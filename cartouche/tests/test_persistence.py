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


class _RegistrationsBase(object):

    def setUp(self):
        from pyramid.configuration import Configurator
        self.config = Configurator()
        self.config.begin()

    def tearDown(self):
        self.config.end()

    def _makeContext(self, **kw):
        from pyramid.testing import DummyModel
        return DummyModel(**kw)

    def _makeRequest(self, **kw):
        from pyramid.testing import DummyRequest
        return DummyRequest(**kw)

    def _makeOne(self, context=None):
        if context is None:
            context = self._makeContext()
        return self._getTargetClass()(context)

    def _makeCartouche(self):
        class DummyCartouche(object):
            def __init__(self):
                self.pending = {}
                self.by_uuid = {}
                self.by_login = {}
                self.by_email = {}
        return DummyCartouche()

    def test_class_conforms_to_IRegistrations(self):
        from zope.interface.verify import verifyClass
        from cartouche.interfaces import IRegistrations
        verifyClass(IRegistrations, self._getTargetClass())

    def test_instance_conforms_to_IRegistrations(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import IRegistrations
        verifyObject(IRegistrations, self._makeOne())


class PendingRegistrationsTests(_RegistrationsBase, unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.persistence import PendingRegistrations
        return PendingRegistrations

    def _makeInfo(self, email='phred@example.com', token='token'):
        return Dummy(email=email, token=token)

    def _verifyInfo(self, info, email='phred@example.com', token='token'):
        from cartouche.interfaces import IPendingRegistrationInfo
        self.failUnless(IPendingRegistrationInfo.providedBy(info))
        self.assertEqual(info.email, email)
        self.assertEqual(info.token, token)

    def test_set_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('phred@example.com', token='token')

        self._verifyInfo(context.cartouche.pending['phred@example.com'])

    def test_set_context_is_root_w_cartouche(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        adapter.set('phred@example.com', token='token')

        self._verifyInfo(cartouche.pending['phred@example.com'])

    def test_set_context_is_not_root(self):
        root = self._makeContext()
        cartouche = root.cartouche = self._makeCartouche()
        parent = root['parent'] = self._makeContext()
        context = parent['context'] = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('phred@example.com', token='token')

        self._verifyInfo(cartouche.pending['phred@example.com'])

    def test_get_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get('phred@example.com'), None)

        self.failIf('cartouche' in context.__dict__)

    def test_get_context_is_root_w_cartouche_miss(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get('phred@example.com'), None)

        self.failIf('phred@example.com' in cartouche.pending)

    def test_get_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        info = self._makeInfo()
        cartouche.pending['phred@example.com'] = info

        adapter = self._makeOne(context)

        self.failUnless(adapter.get('phred@example.com') is info)

    def test_get_by_login_raises(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertRaises(NotImplementedError, adapter.get_by_login, 'login')

    def test_get_by_email_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get_by_email('phred@example.com'), None)

        self.failIf('cartouche' in context.__dict__)

    def test_get_by_email_context_is_root_w_cartouche_miss(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get_by_email('phred@example.com'), None)

        self.failIf('phred@example.com' in cartouche.pending)

    def test_get_by_email_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        info = self._makeInfo()
        cartouche.pending['phred@example.com'] = info

        adapter = self._makeOne(context)

        self.failUnless(adapter.get_by_email('phred@example.com') is info)

    def test_remove_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertRaises(KeyError, adapter.remove, 'phred@example.com')

    def test_remove_context_is_root_w_cartouche_miss(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        self.assertRaises(KeyError, adapter.remove, 'phred@example.com')

    def test_remove_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        cartouche.pending['phred@example.com'] = object()
        adapter = self._makeOne(context)

        adapter.remove('phred@example.com')

        self.failIf('phred@example.com' in cartouche.pending)

    def test___iter___empty(self):
        adapter = self._makeOne()
        self.assertEqual(list(adapter), [])

    def test___iter___non_empty(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        phred = object()
        cartouche.pending['phred@example.com'] = phred
        adapter = self._makeOne(context)

        self.assertEqual(list(adapter), [('phred@example.com', phred)])


class ConfirmedRegistrationsTests(_RegistrationsBase, unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.persistence import ConfirmedRegistrations
        return ConfirmedRegistrations

    def _makeInfo(self, login='login', email='phred@example.com'):
        return Dummy(login=login, email=email)

    def _verifyInfo(self,
                    info,
                    email='phred@example.com',
                    login='login',
                    password='password',
                    security_question='question',
                    security_answer='answer',
                    token='token',
                   ):
        from cartouche.interfaces import IRegistrationInfo
        self.failUnless(IRegistrationInfo.providedBy(info))
        self.assertEqual(info.email, email)
        self.assertEqual(info.login, login)
        self.assertEqual(info.password, password)
        self.assertEqual(info.security_question, security_question)
        self.assertEqual(info.security_answer, security_answer)
        self.assertEqual(info.token, token)

    def test_set_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('UUID',
                    login='login',
                    email='phred@example.com',
                    password='password',
                    security_question='question',
                    security_answer='answer',
                    token='token',
                   )

        cartouche = context.cartouche
        self._verifyInfo(cartouche.by_uuid['UUID'])
        self.assertEqual(cartouche.by_email['phred@example.com'], 'UUID')
        self.assertEqual(cartouche.by_login['login'], 'UUID')

    def test_set_context_is_root_w_cartouche(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        adapter.set('UUID',
                    login='login',
                    email='phred@example.com',
                    password='password',
                    security_question='question',
                    security_answer='answer',
                    token='token',
                   )

        self._verifyInfo(cartouche.by_uuid['UUID'])
        self.assertEqual(cartouche.by_email['phred@example.com'], 'UUID')
        self.assertEqual(cartouche.by_login['login'], 'UUID')

    def test_set_context_is_not_root(self):
        root = self._makeContext()
        cartouche = root.cartouche = self._makeCartouche()
        parent = root['parent'] = self._makeContext()
        context = parent['context'] = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('UUID',
                    login='login',
                    email='phred@example.com',
                    password='password',
                    security_question='question',
                    security_answer='answer',
                    token='token',
                   )

        self._verifyInfo(cartouche.by_uuid['UUID'])
        self.assertEqual(cartouche.by_email['phred@example.com'], 'UUID')
        self.assertEqual(cartouche.by_login['login'], 'UUID')

    def test_set_unindexes_old_login_and_email(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        adapter.set('UUID', email='old_phred@example.com', login='old_login')
        adapter.set('UUID', email='new_phred@example.com', login='new_login')

        record = cartouche.by_uuid['UUID']
        self.assertEqual(record.email, 'new_phred@example.com')
        self.assertEqual(record.login, 'new_login')
        self.assertEqual(cartouche.by_login['new_login'], 'UUID')
        self.assertEqual(cartouche.by_email['new_phred@example.com'], 'UUID')
        self.failIf('old_login' in cartouche.by_login)
        self.failIf('old_phred@example.com' in cartouche.by_email)

    def test_get_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get('UUID'), None)

        self.failIf('cartouche' in context.__dict__)

    def test_get_context_is_root_w_cartouche_miss(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get('UUID'), None)

        self.failIf('UUID' in cartouche.by_uuid)

    def test_get_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        info = self._makeInfo()
        cartouche.by_uuid['UUID'] = info

        adapter = self._makeOne(context)

        self.failUnless(adapter.get('UUID') is info)

    def test_get_by_login_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get_by_login('login'), None)

        self.failIf('cartouche' in context.__dict__)

    def test_get_by_login_context_is_root_w_cartouche_miss(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get_by_login('login'), None)

        self.failIf('UUID' in cartouche.by_uuid)

    def test_get_by_login_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        info = self._makeInfo()
        cartouche.by_uuid['UUID'] = info
        cartouche.by_login['login'] = 'UUID'

        adapter = self._makeOne(context)

        self.failUnless(adapter.get_by_login('login') is info)

    def test_get_by_email_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get_by_email('phred@example.com'), None)

        self.failIf('cartouche' in context.__dict__)

    def test_get_by_email_context_is_root_w_cartouche_miss(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get_by_email('phred@example.com'), None)

        self.failIf('UUID' in cartouche.by_uuid)

    def test_get_by_email_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        info = self._makeInfo()
        cartouche.by_uuid['UUID'] = info
        cartouche.by_email['phred@example.com'] = 'UUID'

        adapter = self._makeOne(context)

        self.failUnless(adapter.get_by_email('phred@example.com') is info)

    def test_remove_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertRaises(KeyError, adapter.remove, 'UUID')

    def test_remove_context_is_root_w_cartouche_miss(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        self.assertRaises(KeyError, adapter.remove, 'UUID')

    def test_remove_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        record = Dummy(login='login', email='phred@example.com')
        cartouche.by_uuid['UUID'] = record
        cartouche.by_login[record.login] = 'UUID'
        cartouche.by_email[record.email] = 'UUID'
        adapter = self._makeOne(context)

        adapter.remove('UUID')

        self.failIf('UUID' in cartouche.by_uuid)
        self.failIf(record.login in cartouche.by_login)
        self.failIf(record.email in cartouche.by_email)

    def test___iter___empty(self):
        adapter = self._makeOne()
        self.assertEqual(list(adapter), [])

    def test___iter___non_empty(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        record = Dummy(login='login', email='phred@example.com')
        cartouche.by_uuid['UUID'] = record
        adapter = self._makeOne(context)
        self.assertEqual(list(adapter), [('UUID', record)])

class Dummy(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
