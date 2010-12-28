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
        from cartouche.registration import PendingRegistrations
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
        from cartouche.registration import ByEmailRegistrations
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
        from cartouche.registration import ByLoginRegistrations
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


class Test_autoLoginViaAuthTkt(_Base, unittest.TestCase):

    def _callFUT(self, userid='testing', request=None):
        from cartouche.registration import autoLoginViaAuthTkt
        if request is None:
            request = self._makeRequest()
        return autoLoginViaAuthTkt(userid, request)

    def test_no_API_in_environ(self):
        self.assertRaises(ValueError, self._callFUT)

    def test_w_API_in_environ(self):
        HEADERS = [('Faux-Cookie', 'gingersnap')]
        api = FauxAPI(HEADERS)
        request = self._makeRequest(environ={'repoze.who.api': api})

        result = self._callFUT('testing', request)

        self.assertEqual(result, HEADERS)
        self.assertEqual(api._called_with[0],
                         {'repoze.who.plugins.auth_tkt.userid': 'testing'})
        self.assertEqual(api._called_with[1], 'auth_tkt')

class Test_register_view(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.registration import register_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return register_view(context, request)

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
        self.assertEqual(inputs, ['email'])
        self.assertEqual(info['message'], None)

    def test_GET_w_message(self):
        request = self._makeRequest(GET={'message': 'Foo'})
        mtr = self.config.testing_add_template('templates/main.pt')

        info = self._callFUT(request=request)

        self.assertEqual(info['message'], 'Foo')

    def test_POST_w_errors(self):
        import re
        SUMMARY_ERROR = re.compile('<h3[^>]*>There was a problem', re.MULTILINE)
        FIELD_ERROR = re.compile('<p class="error"', re.MULTILINE)
        POST = {'email': '',
                'register': '',
               }
        mtr = self.config.testing_add_template('templates/main.pt')
        context = self._makeContext()
        request = self._makeRequest(POST=POST)

        info = self._callFUT(context, request)

        main_template = info['main_template']
        self.failUnless(main_template is mtr.implementation())
        rendered_form = info['rendered_form']
        self.failUnless(SUMMARY_ERROR.search(rendered_form))
        self.failUnless(FIELD_ERROR.search(rendered_form))

    def test_POST_no_errors(self):
        from urllib import quote
        from repoze.sendmail.interfaces import IMailDelivery
        from webob.exc import HTTPFound
        from cartouche.interfaces import ITokenGenerator

        FROM_EMAIL = 'admin@example.com'
        TO_EMAIL = 'phred@example.com'
        POST = {'email': TO_EMAIL,
                'register': '',
               }
        self.config.registry.settings['from_addr'] = FROM_EMAIL
        delivery = DummyMailer()
        self.config.registry.registerUtility(delivery, IMailDelivery)
        self.config.registry.registerUtility(DummyTokenGenerator(),
                                             ITokenGenerator)
        pending = self._registerPendingRegistrations()
        context = self._makeContext()
        request = self._makeRequest(POST=POST)

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/confirm_registration.html'
                           '?email=%s' % quote(TO_EMAIL))
        self.assertEqual(delivery._sent[0], FROM_EMAIL)
        self.assertEqual(list(delivery._sent[1]), [TO_EMAIL])
        info = pending[TO_EMAIL]
        self.assertEqual(info.email, TO_EMAIL)
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
        pending = self._registerPendingRegistrations()

        response = self._callFUT()

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/register.html?message='
                         'Please+register+first'
                         '+or+visit+the+link+in+your+confirmation+e-mail.')

    def test_GET_w_email_miss(self):
        from webob.exc import HTTPFound
        EMAIL = 'phred@example.com'
        pending = self._registerPendingRegistrations()
        request = self._makeRequest(GET={'email': EMAIL})

        response = self._callFUT(request=request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/register.html?message='
                         'Please+register+first.')

    def test_GET_w_email_hit(self):
        import re
        INPUT = re.compile('<input.*name="(?P<name>\w+)" '
                           'value="(?P<value>[^"]*)"', re.MULTILINE)
        EMAIL = 'phred@example.com'
        mtr = self.config.testing_add_template('templates/main.pt')
        pending = self._registerPendingRegistrations()
        pending[EMAIL] = self._makeInfo()
        context = self._makeContext()
        request = self._makeRequest(GET={'email': EMAIL})

        info = self._callFUT(context, request)

        rendered_form = info['rendered_form']
        inputs = [x for x in INPUT.findall(rendered_form)
                        if not x[0].startswith('_')]
        self.assertEqual(inputs,
                         [('email', 'phred@example.com'), ('token', '')])

    def test_POST_w_validation_errors(self):
        import re
        SUMMARY_ERROR = re.compile('<h3[^>]*>There was a problem', re.MULTILINE)
        FIELD_ERROR = re.compile('<p class="error"', re.MULTILINE)
        POST = {'email': '',
                'token': '',
                'confirm': '',
               }
        pending = self._registerPendingRegistrations()
        mtr = self.config.testing_add_template('templates/main.pt')
        context = self._makeContext()
        request = self._makeRequest(POST=POST)

        info = self._callFUT(context, request)

        main_template = info['main_template']
        self.failUnless(main_template is mtr.implementation())
        rendered_form = info['rendered_form']
        self.failUnless(SUMMARY_ERROR.search(rendered_form))
        self.failUnless(FIELD_ERROR.search(rendered_form))

    def test_POST_w_email_miss(self):
        from webob.exc import HTTPFound
        POST = {'email': 'phred@example.com',
                'token': 'TOKEN',
                'confirm': '',
               }
        pending = self._registerPendingRegistrations()
        context = self._makeContext()
        request = self._makeRequest(POST=POST)

        response = self._callFUT(request=request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/register.html?message='
                         'Please+register+first.')

    def test_POST_w_token_miss(self):
        from webob.exc import HTTPFound
        EMAIL = 'phred@example.com'
        POST = {'email': EMAIL,
                'token': 'TOKEN',
                'confirm': '',
               }
        pending = self._registerPendingRegistrations()
        pending[EMAIL] = Dummy(token='OTHER')
        context = self._makeContext()
        request = self._makeRequest(POST=POST)

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/confirm_registration.html'
                         '?message=Please+copy+the+token+from+your'
                         '+confirmation+e-mail.')

    def test_POST_w_token_hit(self):
        from webob.exc import HTTPFound
        EMAIL = 'phred@example.com'
        POST = {'email': EMAIL,
                'token': 'TOKEN',
                'confirm': '',
               }
        pending = self._registerPendingRegistrations()
        pending[EMAIL] = Dummy(token='TOKEN')
        by_login = self._registerByLogin()
        by_email = self._registerByEmail()
        HEADERS = [('Faux-Cookie', 'gingersnap')]
        api = FauxAPI(HEADERS)
        context = self._makeContext()
        request = self._makeRequest(POST=POST,
                                    environ={'repoze.who.api': api})

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        for key, value in HEADERS:
            self.assertEqual(response.headers[key], value)
        self.assertEqual(response.location,
                         'http://example.com/welcome.html')

        self.failIf(EMAIL in pending)
        self.failUnless(EMAIL in by_login)
        self.failUnless(EMAIL in by_email)
        self.failUnless(by_login[EMAIL] is by_email[EMAIL])
        self.assertEqual(by_login[EMAIL].password, None)
        self.assertEqual(by_login[EMAIL].security_question, None)
        self.assertEqual(by_login[EMAIL].security_answer, None)


class Test_welcome_view(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.registration import welcome_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return welcome_view(context, request)

    def test_GET_wo_credentials(self):
        from webob.exc import HTTPFound
        response = self._callFUT()

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/register.html?message='
                         'Please+register+first.')

    def test_GET_w_credentials(self):
        EMAIL = 'phred@example.com'
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': EMAIL}}
        by_login = self._registerByLogin()
        by_login[EMAIL] = Dummy(login=EMAIL, email=EMAIL, password=None,
                                security_question=None, security_answer=None)
        mtr = self.config.testing_add_template('templates/main.pt')
        request = self._makeRequest(environ=ENVIRON)

        info = self._callFUT(request=request)

        self.failUnless(info['main_template'] is mtr.implementation())
        self.assertEqual(info['authenticated_user'], EMAIL)


class Dummy:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FauxAPI(Dummy):
    def __init__(self, headers):
        self._headers = headers
    def login(self, credentials, identifier_name=None):
        self._called_with = (credentials, identifier_name)
        return 'testing', self._headers


class DummyMailer:
    _sent = None

    def send(self, from_addr, to_addrs, message):
        self._sent = (from_addr, to_addrs, message)


class DummyTokenGenerator:
    def getToken(self):
        return 'RANDOM'
