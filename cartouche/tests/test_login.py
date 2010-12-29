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

class LoginTests(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.login import login_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return login_view(context, request)

    def test_GET(self):
        import re
        INPUT = re.compile('<input.*name="(?P<name>\w+)"', re.MULTILINE)
        mtr = self.config.testing_add_template('templates/main.pt')

        info = self._callFUT()

        main_template = info['main_template']
        self.failUnless(main_template is mtr.implementation())
        rendered_form = info['rendered_form']
        inputs = [x for x in INPUT.findall(rendered_form)
                        if not x.startswith('_')]
        self.assertEqual(inputs, ['login_name', 'password'])
        self.assertEqual(info['message'], None)
        self.assertEqual(info['recover_account_url'],
                         'http://example.com/recover_account.html')
        self.assertEqual(info['reset_password_url'],
                         'http://example.com/reset_password.html')

    def test_GET_w_url_overrides(self):
        import re
        INPUT = re.compile('<input.*name="(?P<name>\w+)"', re.MULTILINE)
        mtr = self.config.testing_add_template('templates/main.pt')
        settings = self.config.registry.settings 
        settings['cartouche.recover_account_url'] = '/recover.html'
        settings['cartouche.reset_password_url'] = '/reset.html'

        info = self._callFUT()

        main_template = info['main_template']
        self.failUnless(main_template is mtr.implementation())
        rendered_form = info['rendered_form']
        inputs = [x for x in INPUT.findall(rendered_form)
                        if not x.startswith('_')]
        self.assertEqual(inputs, ['login_name', 'password'])
        self.assertEqual(info['message'], None)
        self.assertEqual(info['recover_account_url'],
                         'http://example.com/recover.html')
        self.assertEqual(info['reset_password_url'],
                         'http://example.com/reset.html')

    def test_GET_w_message(self):
        request = self._makeRequest(GET={'message': 'Foo'})
        mtr = self.config.testing_add_template('templates/main.pt')

        info = self._callFUT(request=request)

        self.assertEqual(info['message'], 'Foo')

    def test_POST_w_unknown_login(self):
        POST = {'login_name': 'unknown',
                'password': 'bogus',
                'login': '',
               }
        mtr = self.config.testing_add_template('templates/main.pt')
        context = self._makeContext()
        api = FauxAPI()
        request = self._makeRequest(POST=POST,
                                   environ={'repoze.who.api': api})

        info = self._callFUT(context, request)

        main_template = info['main_template']
        self.failUnless(main_template is mtr.implementation())
        self.assertEqual(info['message'], 'Login failed')

    def test_POST_w_bad_password(self):
        POST = {'login_name': 'known',
                'password': 'bogus',
                'login': '',
               }
        mtr = self.config.testing_add_template('templates/main.pt')
        context = self._makeContext()
        api = FauxAPI({'known': 'valid'})
        request = self._makeRequest(POST=POST,
                                   environ={'repoze.who.api': api})

        info = self._callFUT(context, request)

        main_template = info['main_template']
        self.failUnless(main_template is mtr.implementation())
        self.assertEqual(info['message'], 'Login failed')

    def test_POST_w_good_password_no_came_from(self):
        from webob.exc import HTTPFound
        POST = {'login_name': 'known',
                'password': 'valid',
                'login': '',
               }
        mtr = self.config.testing_add_template('templates/main.pt')
        context = self._makeContext()
        api = FauxAPI({'known': 'valid'})
        request = self._makeRequest(POST=POST,
                                   environ={'repoze.who.api': api})

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location, 'http://example.com/')
        for key, value in api.LOGIN_HEADERS:
            self.failUnless(response.headers[key] is value)


class LogoutTests(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.login import logout_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return logout_view(context, request)

    def test_GET(self):
        from webob.exc import HTTPFound
        api = FauxAPI({'known': 'valid'})
        request = self._makeRequest(environ={'repoze.who.api': api})

        response = self._callFUT(request=request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location, 'http://example.com/')

        for key, value in api.LOGOUT_HEADERS:
            self.assertEqual(response.headers.get(key), value)


class FauxAPI(object):
    LOGIN_HEADERS = [('Faux-Cookie', 'gingersnap')]
    LOGOUT_HEADERS = [('Forget', 'Me')]
    def __init__(self, known=None):
        if known is None:
            known = {}
        self._known = known
    def login(self, credentials, identifier_name=None):
        self._called_with = (credentials, identifier_name)
        login = credentials.get('login')
        password = credentials.get('password')
        if self._known.get(login) == password:
            return login, self.LOGIN_HEADERS
        return None, ()
    def logout(self, identifier_name=None):
        self._called_with = (identifier_name,)
        return self.LOGOUT_HEADERS
