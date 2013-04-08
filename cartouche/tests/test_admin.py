##############################################################################
#
# Copyright (c) 2013 Agendaless Consulting and Contributors.
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
        from pyramid.config import Configurator
        self.config = Configurator(autocommit=True)
        self.config.begin()

    def tearDown(self):
        self.config.end()

    def _makeContext(self, **kw):
        from pyramid.testing import DummyModel
        cartouche = kw.pop('cartouche', DummyCartouche())
        return DummyModel(cartouche=cartouche, **kw)

    def _makeRequest(self, **kw):
        from pyramid.testing import DummyRequest
        return DummyRequest(**kw)


class Test_admin_overview(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.admin import admin_overview
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return admin_overview(context, request)

    def test_wo_adapters_wo_pending_wo_confirmed(self):
        context = self._makeContext()
        request = self._makeRequest()
        info = self._callFUT(context, request)
        self.assertEqual(info['pending'], [])
        self.assertEqual(info['confirmed'], [])

    def test_wo_adapters_w_pending_w_confirmed(self):
        cartouche = DummyCartouche()
        cartouche.pending['abc'] = abc = object()
        cartouche.by_uuid['xyz'] = xyz = object()
        context = self._makeContext(cartouche=cartouche)
        request = self._makeRequest()
        info = self._callFUT(context, request)
        self.assertEqual(info['pending'], [('abc', abc)])
        self.assertEqual(info['confirmed'], [('xyz', xyz)])

    def test_w_pending_adapter(self):
        from cartouche.interfaces import IRegistrations
        PENDING = [('abc', object())]
        self.config.registry.registerAdapter(lambda x: PENDING,
                                             (None,), IRegistrations,
                                             name='pending')
        context = self._makeContext()
        request = self._makeRequest()
        info = self._callFUT(context, request)
        self.assertEqual(info['pending'], PENDING)

    def test_w_confirmed_adapter(self):
        from cartouche.interfaces import IRegistrations
        CONFIRMED = [('abc', object())]
        self.config.registry.registerAdapter(lambda x: CONFIRMED,
                                             (None,), IRegistrations,
                                             name='confirmed')
        context = self._makeContext()
        request = self._makeRequest()
        info = self._callFUT(context, request)
        self.assertEqual(info['confirmed'], CONFIRMED)


class Test_admin_pending(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.admin import admin_pending
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return admin_pending(context, request)

    def test_wo_request_param(self):
        context = self._makeContext()
        request = self._makeRequest()
        self.assertRaises(KeyError, self._callFUT, context, request)

    def test_w_request_param_miss(self):
        from pyramid.exceptions import HTTPNotFound
        context = self._makeContext()
        request = self._makeRequest(params={'pending': 'nonesuch@example.com'})
        response = self._callFUT(context, request)
        self.assertTrue(isinstance(response, HTTPNotFound))

    def test_w_request_param_hit_wo_adapter(self):
        EMAIL = 'abc@example.com'
        TOKEN = '12345'
        class DummyPending(object):
            email = EMAIL
            token = TOKEN
        cartouche = DummyCartouche()
        cartouche.pending[EMAIL] = DummyPending()
        context = self._makeContext(cartouche=cartouche)
        request = self._makeRequest(params={'pending': EMAIL})
        info = self._callFUT(context, request)
        self.assertEqual(info['email'], EMAIL)
        self.assertEqual(info['token'], TOKEN)

    def test_w_request_param_hit_w_adapter(self):
        from cartouche.interfaces import IRegistrations
        EMAIL = 'abc@example.com'
        TOKEN = '12345'
        class DummyPending(object):
            email = EMAIL
            token = TOKEN
        PENDING = {EMAIL: DummyPending()}
        self.config.registry.registerAdapter(lambda x: PENDING,
                                             (None,), IRegistrations,
                                             name='pending')
        context = self._makeContext()
        request = self._makeRequest(params={'pending': EMAIL})
        info = self._callFUT(context, request)
        self.assertEqual(info['email'], EMAIL)
        self.assertEqual(info['token'], TOKEN)


class Test_admin_confirmed(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.admin import admin_confirmed
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return admin_confirmed(context, request)

    def test_wo_request_param(self):
        context = self._makeContext()
        request = self._makeRequest()
        self.assertRaises(KeyError, self._callFUT, context, request)

    def test_w_request_param_miss(self):
        from pyramid.exceptions import HTTPNotFound
        context = self._makeContext()
        request = self._makeRequest(params={'confirmed': 'nonesuch'})
        response = self._callFUT(context, request)
        self.assertTrue(isinstance(response, HTTPNotFound))

    def test_w_request_param_hit_wo_adapter(self):
        UUID = '1234-5678-9012-3456'
        EMAIL = 'abc@example.com'
        LOGIN = 'abc'
        PASSWORD = 'PASSWORD'
        SECURITY_QUESTION = 'Color?'
        SECURITY_ANSWER = 'Blue'
        TOKEN = '12345'
        class DummyConfirmed(object):
            uuid = UUID
            email = EMAIL
            login = LOGIN
            password = PASSWORD
            security_question = SECURITY_QUESTION
            security_answer = SECURITY_ANSWER
            token = TOKEN
        dummy = DummyConfirmed()
        cartouche = DummyCartouche()
        cartouche.by_uuid[UUID] = dummy
        cartouche.by_login[LOGIN] = UUID
        context = self._makeContext(cartouche=cartouche)
        request = self._makeRequest(params={'confirmed': LOGIN})
        info = self._callFUT(context, request)
        self.assertEqual(info['uuid'], UUID)
        self.assertEqual(info['login'], LOGIN)
        self.assertEqual(info['password'], PASSWORD)
        self.assertEqual(info['security_question'], SECURITY_QUESTION)
        self.assertEqual(info['security_answer'], SECURITY_ANSWER)
        self.assertEqual(info['email'], EMAIL)
        self.assertEqual(info['token'], TOKEN)

    def test_w_request_param_hit_w_adapter(self):
        from cartouche.interfaces import IRegistrations
        UUID = '1234-5678-9012-3456'
        EMAIL = 'abc@example.com'
        LOGIN = 'abc'
        PASSWORD = 'PASSWORD'
        SECURITY_QUESTION = 'Color?'
        SECURITY_ANSWER = 'Blue'
        TOKEN = '12345'
        class DummyConfirmed(object):
            uuid = UUID
            email = EMAIL
            login = LOGIN
            password = PASSWORD
            security_question = SECURITY_QUESTION
            security_answer = SECURITY_ANSWER
            token = TOKEN
        class Adapter(object):
            def __init__(self, context):
                pass
            def get_by_login(self, key):
                assert key == LOGIN
                return DummyConfirmed()
        CONFIRMED = {EMAIL: DummyConfirmed()}
        self.config.registry.registerAdapter(Adapter,
                                             (None,), IRegistrations,
                                             name='confirmed')
        context = self._makeContext()
        request = self._makeRequest(params={'confirmed': LOGIN})
        info = self._callFUT(context, request)
        self.assertEqual(info['uuid'], UUID)
        self.assertEqual(info['login'], LOGIN)
        self.assertEqual(info['password'], PASSWORD)
        self.assertEqual(info['security_question'], SECURITY_QUESTION)
        self.assertEqual(info['security_answer'], SECURITY_ANSWER)
        self.assertEqual(info['email'], EMAIL)
        self.assertEqual(info['token'], TOKEN)


class DummyCartouche(object):
    def __init__(self):
        self.pending = {}
        self.by_uuid = {}
        self.by_login = {}
        self.by_email = {}
