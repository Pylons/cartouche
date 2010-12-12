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

class Test_register_view(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.registration import register_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return register_view(context, request)

    def test_initial_GET(self):
        # No variables in QUERY_STRING
        from deform import Form

        mtr = self.config.testing_add_template('templates/main.pt')
        info = self._callFUT()

        main_template = info['main_template']
        self.failUnless(main_template is mtr.implementation())
        self.failUnless(info.get('appstruct') is None)
        form = info['form']
        self.failUnless(isinstance(form, Form))
        self.assertEqual(len(form.children), 2)
        self.assertEqual(form.children[0].name, 'email')
        self.assertEqual(form.children[1].name, 'security')

    def test_initial_POST(self):
        # E-mail, security question posted from first form.
        from urllib import quote
        from repoze.sendmail.interfaces import IMailDelivery
        from webob.exc import HTTPFound
        from cartouche.interfaces import ITokenGenerator

        FROM_EMAIL = 'admin@example.com'
        TO_EMAIL = 'phred@example.com'
        POST = {'email': TO_EMAIL,
                'security': {'question': 'petname',
                             'answer': 'Fido',
                            },
                'register': '',
               }
        self.config.registry.settings['from_addr'] = FROM_EMAIL
        delivery = DummyMailer()
        self.config.registry.registerUtility(delivery, IMailDelivery)
        self.config.registry.registerUtility(DummyTokenGenerator(),
                                             ITokenGenerator)
        context = self._makeContext()
        users = context.users = self._makeContext()
        pending = users.pending_registrations = {}
        request = self._makeRequest(POST=POST, view_name='register.html')

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/register.html?email=%s'
                            % quote(TO_EMAIL))
        self.assertEqual(delivery._sent[0], FROM_EMAIL)
        self.assertEqual(list(delivery._sent[1]), [TO_EMAIL])
        info = pending[TO_EMAIL]
        self.assertEqual(info['token'], 'RANDOM')
        self.assertEqual(info['question'], 'petname')
        self.assertEqual(info['answer'], 'Fido')


class Test_confirm_registration_view(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.registration import confirm_registration_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return confirm_registration_view(context, request)

    def test_GET(self):
        from deform import Form
        EMAIL = 'phred@example.com'
        request = self._makeRequest(GET={'email': EMAIL})

        mtr = self.config.testing_add_template('templates/main.pt')
        info = self._callFUT(request=request)

        appstruct = info['appstruct']
        self.assertEqual(appstruct['email'], EMAIL)
        form = info['form']
        self.failUnless(isinstance(form, Form))
        self.assertEqual(len(form.children), 2)
        self.assertEqual(form.children[0].name, 'email')
        widget = form.children[0].widget
        self.failUnless(widget.template is widget.readonly_template)
        self.assertEqual(form.children[1].name, 'token')


class DummyMailer:
    _sent = None

    def send(self, from_addr, to_addrs, message):
        self._sent = (from_addr, to_addrs, message)


class DummyTokenGenerator:
    def getToken(self):
        return 'RANDOM'
