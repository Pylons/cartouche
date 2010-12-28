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

""" Form for testing the password confirm widget:

        from webob.multidict import MultiDict
        POST = MultiDict([('login_name', 'known'),
                          ('__start__', 'password:mapping'),
                          ('value', 'valid'),
                          ('confirm', 'valid'),
                          ('__end__', 'password:mapping'),
                          ('login', ''),
                         ])

"""

class LoginTests(unittest.TestCase):

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
        for key, value in api.HEADERS:
            self.failUnless(response.headers[key] is value)


class FauxAPI(object):
    HEADERS = [('Faux-Cookie', 'gingersnap')]
    def __init__(self, known=None):
        if known is None:
            known = {}
        self._known = known
    def login(self, credentials, identifier_name=None):
        self._called_with = (credentials, identifier_name)
        login = credentials.get('login')
        password = credentials.get('password')
        if self._known.get(login) == password:
            return login, self.HEADERS
        return None, ()
