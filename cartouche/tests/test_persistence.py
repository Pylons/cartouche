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


class _Base(object):

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

    def _makeInfo(self, email='phred@example.com',
                  question='question', answer='answer', token='token'):
        class DummyRegistrationInfo(object):
            def __init__(self, **kw):
                self.__dict__.update(kw)
        return DummyRegistrationInfo(email=email,
                                     security_question=question,
                                     security_answer=answer,
                                     token=token)

    def _registerPendingRegistrations(self):
        from cartouche.interfaces import IRegistrations
        pending = {}
        class DummyRegistrationsByEmail:
            def __init__(self, context):
                pass
            def get(self, key, default=None):
                return pending.get(key, default)
            def set(self, key, **kw):
                pending[key] = Dummy(email=key, **kw)
            def set_record(self, key, record):
                pending[key] = record
            def remove(self, key):
                del pending[key]
        self.config.registry.registerAdapter(DummyRegistrationsByEmail,
                                             (None,), IRegistrations,
                                             name='pending')
        return pending

    def _registerByLogin(self):
        from cartouche.interfaces import IRegistrations
        by_login = {}
        class DummyRegistrationsByLogin:
            def __init__(self, context):
                pass
            def get(self, key, default=None):
                return by_login.get(key, default)
            def set(self, key, **kw):
                by_login[key] = Dummy(login=key, **kw)
            def set_record(self, key, record):
                by_login[key] = record
            def remove(self, key):
                del by_login[key]
        self.config.registry.registerAdapter(DummyRegistrationsByLogin,
                                             (None,), IRegistrations,
                                             name='by_login')
        return by_login

    def _registerByEmail(self):
        from cartouche.interfaces import IRegistrations
        by_email = {}
        class DummyPendingRegistrations:
            def __init__(self, context):
                pass
            def get(self, key, default=None):
                return by_email.get(key, default)
            def set(self, key, **kw):
                by_email[key] = Dummy(email=key, **kw)
            def set_record(self, key, record):
                by_email[key] = record
            def remove(self, key):
                del by_email[key]
        self.config.registry.registerAdapter(DummyPendingRegistrations,
                                             (None,), IRegistrations,
                                             name='by_email')
        return by_email


class _RegistrationsBase(_Base):

    def _makeOne(self, context=None):
        if context is None:
            context = self._makeContext()
        return self._getTargetClass()(context)

    def _makeCartouche(self):
        class DummyCartouche(object):
            def __init__(self):
                self.pending = {}
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

    def test_set_record_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        record = object()
        adapter.set_record('phred@example.com', record)

        self.failUnless(context.cartouche.pending['phred@example.com']
                            is record)

    def test_set_record_context_is_root_w_cartouche(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        record = object()
        adapter.set_record('phred@example.com', record)

        self.failUnless(cartouche.pending['phred@example.com'] is record)

    def test_set_record_context_is_not_root(self):
        root = self._makeContext()
        cartouche = root.cartouche = self._makeCartouche()
        parent = root['parent'] = self._makeContext()
        context = parent['context'] = self._makeContext()
        adapter = self._makeOne(context)

        record = object()
        adapter.set_record('phred@example.com', record)

        self.failUnless(cartouche.pending['phred@example.com'] is record)

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


class ByEmailRegistrationsTests(_RegistrationsBase, unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.persistence import ByEmailRegistrations
        return ByEmailRegistrations

    def _verifyInfo(self, info, email='phred@example.com',
                    login='login', password='password',
                    question='question', answer='answer'):
        from cartouche.interfaces import IRegistrationInfo
        self.failUnless(IRegistrationInfo.providedBy(info))
        self.assertEqual(info.email, email)
        self.assertEqual(info.login, login)
        self.assertEqual(info.password, password)
        self.assertEqual(info.security_question, question)
        self.assertEqual(info.security_answer, answer)

    def test_set_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('phred@example.com', login='login', password='password',
                    security_question='question', security_answer='answer')

        self._verifyInfo(context.cartouche.by_email['phred@example.com'])

    def test_set_context_is_root_w_cartouche(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        adapter.set('phred@example.com', login='login', password='password',
                    security_question='question', security_answer='answer')

        self._verifyInfo(cartouche.by_email['phred@example.com'])

    def test_set_context_is_not_root(self):
        root = self._makeContext()
        cartouche = root.cartouche = self._makeCartouche()
        parent = root['parent'] = self._makeContext()
        context = parent['context'] = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('phred@example.com', login='login', password='password',
                    security_question='question', security_answer='answer')

        self._verifyInfo(cartouche.by_email['phred@example.com'])

    def test_set_record_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        record = object()
        adapter.set_record('phred@example.com', record)

        self.failUnless(context.cartouche.by_email['phred@example.com']
                            is record)

    def test_set_record_context_is_root_w_cartouche(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        record = object()
        adapter.set_record('phred@example.com', record)

        self.failUnless(cartouche.by_email['phred@example.com'] is record)

    def test_set_record_context_is_not_root(self):
        root = self._makeContext()
        cartouche = root.cartouche = self._makeCartouche()
        parent = root['parent'] = self._makeContext()
        context = parent['context'] = self._makeContext()
        adapter = self._makeOne(context)

        record = object()
        adapter.set_record('phred@example.com', record)

        self.failUnless(cartouche.by_email['phred@example.com'] is record)

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

        self.failIf('phred@example.com' in cartouche.by_email)

    def test_get_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        info = self._makeInfo()
        cartouche.by_email['phred@example.com'] = info

        adapter = self._makeOne(context)

        self.failUnless(adapter.get('phred@example.com') is info)

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
        cartouche.by_email['phred@example.com'] = object()
        adapter = self._makeOne(context)

        adapter.remove('phred@example.com')

        self.failIf('phred@example.com' in cartouche.by_email)


class ByLoginRegistrationsTests(_RegistrationsBase, unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.persistence import ByLoginRegistrations
        return ByLoginRegistrations

    def _verifyInfo(self, info, email='phred@example.com',
                    login='login', password='password',
                    question='question', answer='answer'):
        from cartouche.interfaces import IRegistrationInfo
        self.failUnless(IRegistrationInfo.providedBy(info))
        self.assertEqual(info.email, email)
        self.assertEqual(info.login, login)
        self.assertEqual(info.password, password)
        self.assertEqual(info.security_question, question)
        self.assertEqual(info.security_answer, answer)

    def test_set_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('login', email='phred@example.com', password='password',
                    security_question='question', security_answer='answer')

        self._verifyInfo(context.cartouche.by_login['login'])

    def test_set_context_is_root_w_cartouche(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        adapter.set('login', email='phred@example.com', password='password',
                    security_question='question', security_answer='answer')

        self._verifyInfo(cartouche.by_login['login'])

    def test_set_context_is_not_root(self):
        root = self._makeContext()
        cartouche = root.cartouche = self._makeCartouche()
        parent = root['parent'] = self._makeContext()
        context = parent['context'] = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('login', email='phred@example.com', password='password',
                    security_question='question', security_answer='answer')

        self._verifyInfo(cartouche.by_login['login'])

    def test_set_record_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        record = object()
        adapter.set_record('login', record)

        self.failUnless(context.cartouche.by_login['login'] is record)

    def test_set_record_context_is_root_w_cartouche(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        record = object()
        adapter.set_record('login', record)

        self.failUnless(cartouche.by_login['login'] is record)

    def test_set_record_context_is_not_root(self):
        root = self._makeContext()
        cartouche = root.cartouche = self._makeCartouche()
        parent = root['parent'] = self._makeContext()
        context = parent['context'] = self._makeContext()
        adapter = self._makeOne(context)

        record = object()
        adapter.set_record('login', record)

        self.failUnless(cartouche.by_login['login'] is record)

    def test_get_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get('login'), None)

        self.failIf('cartouche' in context.__dict__)

    def test_get_context_is_root_w_cartouche_miss(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        self.assertEqual(adapter.get('login'), None)

        self.failIf('login' in cartouche.by_login)

    def test_get_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        info = self._makeInfo()
        cartouche.by_login['login'] = info

        adapter = self._makeOne(context)

        self.failUnless(adapter.get('login') is info)

    def test_remove_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        self.assertRaises(KeyError, adapter.remove, 'login')

    def test_remove_context_is_root_w_cartouche_miss(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        self.assertRaises(KeyError, adapter.remove, 'login')

    def test_remove_context_is_root_w_cartouche_hit(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        cartouche.by_login['login'] = object()
        adapter = self._makeOne(context)

        adapter.remove('login')

        self.failIf('login' in cartouche.by_login)

