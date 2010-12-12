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

    def _makeCartouche(self):
        class DummyCartouche(object):
            def __init__(self):
                self.pending = {}
        return DummyCartouche()

    def _verifyInfo(self, info, email='phred@example.com',
                  question='question', answer='answer', token='token'):
        from cartouche.interfaces import IRegistrationInfo
        self.failUnless(IRegistrationInfo.providedBy(info))
        self.assertEqual(info.email, email)
        self.assertEqual(info.security_question, question)
        self.assertEqual(info.security_answer, answer)
        self.assertEqual(info.token, token)


class PendingRegistrationsTests(_Base, unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.registration import PendingRegistrations
        return PendingRegistrations

    def _makeOne(self, context=None):
        if context is None:
            context = self._makeContext()
        return self._getTargetClass()(context)

    def test_class_conforms_to_IPendingRegistrations(self):
        from zope.interface.verify import verifyClass
        from cartouche.interfaces import IPendingRegistrations
        verifyClass(IPendingRegistrations, self._getTargetClass())

    def test_instance_conforms_to_IPendingRegistrations(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import IPendingRegistrations
        verifyObject(IPendingRegistrations, self._makeOne())

    def test_set_context_is_root_no_cartouche(self):
        context = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('phred@example.com', 'question', 'answer', 'token')

        self._verifyInfo(context.cartouche.pending['phred@example.com'])

    def test_set_context_is_root_w_cartouche(self):
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        adapter = self._makeOne(context)

        adapter.set('phred@example.com', 'question', 'answer', 'token')

        self._verifyInfo(cartouche.pending['phred@example.com'])

    def test_set_context_is_not_root(self):
        root = self._makeContext()
        cartouche = root.cartouche = self._makeCartouche()
        parent = root['parent'] = self._makeContext()
        context = parent['context'] = self._makeContext()
        adapter = self._makeOne(context)

        adapter.set('phred@example.com', 'question', 'answer', 'token')

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


class Test_getRandomToken(_Base, unittest.TestCase):

    def _callFUT(self, request=None):
        from cartouche.registration import getRandomToken
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


class Test_register_view(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.registration import register_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return register_view(context, request)

    def test_GET(self):
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

    def test_POST(self):
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
        cartouche = context.cartouche = self._makeCartouche()
        request = self._makeRequest(POST=POST, view_name='register.html')

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/register.html?email=%s'
                            % quote(TO_EMAIL))
        self.assertEqual(delivery._sent[0], FROM_EMAIL)
        self.assertEqual(list(delivery._sent[1]), [TO_EMAIL])
        info = cartouche.pending[TO_EMAIL]
        self.assertEqual(info.email, TO_EMAIL)
        self.assertEqual(info.security_question, 'petname')
        self.assertEqual(info.security_answer, 'Fido')
        self.assertEqual(info.token, 'RANDOM')


class Test_confirm_registration_view(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.registration import confirm_registration_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return confirm_registration_view(context, request)

    def test_GET_wo_email(self):
        from webob.exc import HTTPFound

        response = self._callFUT()

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/register.html?message='
                         'Please+register+first'
                         '+or+visit+the+link+in+your+confirmation+e-mail.')

    def test_GET_w_email_miss(self):
        from webob.exc import HTTPFound
        EMAIL = 'phred@example.com'
        request = self._makeRequest(GET={'email': EMAIL})

        response = self._callFUT(request=request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/register.html?message='
                         'Please+register+first.')

    def test_GET_w_email_hit(self):
        from deform import Form
        EMAIL = 'phred@example.com'
        context = self._makeContext()
        cartouche = context.cartouche = self._makeCartouche()
        cartouche.pending[EMAIL] = self._makeInfo()
        request = self._makeRequest(GET={'email': EMAIL})
        mtr = self.config.testing_add_template('templates/main.pt')

        info = self._callFUT(context, request)

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
