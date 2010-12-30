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


class Test_view_url(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None,
                 key='view_url', default_name='view.html', **extra_qs):
        from cartouche.util import view_url
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return view_url(context, request, key, default_name, **extra_qs)

    def test_wo_utility_wo_extra_query(self):
        self.assertEqual(self._callFUT(), 'http://example.com/view.html')

    def test_wo_utility_w_extra_query(self):
        self.assertEqual(self._callFUT(foo='bar'),
                         'http://example.com/view.html?foo=bar')

    def test_w_utility_relative_wo_extra_query(self):
        self.config.registry.settings['cartouche.view_url'] = '/somewhere.html'
        self.assertEqual(self._callFUT(), 'http://example.com/somewhere.html')

    def test_w_utility_absolute_wo_extra_query(self):
        self.config.registry.settings['cartouche.view_url'
                                     ] = 'http://other.example.com/'
        self.assertEqual(self._callFUT(), 'http://other.example.com/')

    def test_w_utility_relative_w_extra_query(self):
        self.config.registry.settings['cartouche.view_url'
                                     ] = '/somewhere.html?foo=bar'
        self.assertEqual(self._callFUT(baz='qux'),
                         'http://example.com/somewhere.html?foo=bar&baz=qux')

    def test_w_utility_absolute_w_extra_query(self):
        self.config.registry.settings['cartouche.view_url'
                                     ] = 'http://other.example.com/?foo=bar'
        self.assertEqual(self._callFUT(baz='qux'),
                         'http://other.example.com/?foo=bar&baz=qux')


class Test_getRandomToken(_Base, unittest.TestCase):

    def _callFUT(self, request=None):
        from cartouche.util import getRandomToken
        if request is None:
            request = self._makeRequest()
        return getRandomToken(request)

    def test_wo_utility(self):
        from uuid import UUID
        token = self._callFUT()
        uuid = UUID(token)
        self.assertEqual(uuid.version, 4)

    def test_w_utility(self):
        from cartouche.interfaces import ITokenGenerator
        self.config.registry.registerUtility(DummyTokenGenerator(),
                                             ITokenGenerator)
        token = self._callFUT()
        self.assertEqual(token, 'RANDOM')


class DummyTokenGenerator:
    def getToken(self):
        return 'RANDOM'
