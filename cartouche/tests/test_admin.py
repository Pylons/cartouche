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


class Test_admin_overview(unittest.TestCase):

    def setUp(self):
        from pyramid.config import Configurator
        self.config = Configurator(autocommit=True)
        self.config.begin()

    def tearDown(self):
        self.config.end()

    def _callFUT(self, context=None, request=None):
        from cartouche.admin import admin_overview
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return admin_overview(context, request)

    def _makeContext(self, **kw):
        from pyramid.testing import DummyModel
        cartouche = kw.pop('cartouche', DummyCartouche())
        return DummyModel(cartouche=cartouche, **kw)

    def _makeRequest(self, **kw):
        from pyramid.testing import DummyRequest
        return DummyRequest(**kw)

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


class DummyCartouche(object):
    def __init__(self):
        self.pending = {}
        self.by_uuid = {}
