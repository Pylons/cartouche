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
        from pyramid.config import Configurator
        self.config = Configurator(autocommit=True)
        self.config.begin()

    def tearDown(self):
        self.config.end()

    def _makeContext(self, **kw):
        from pyramid.testing import DummyModel
        return DummyModel(**kw)

    def _makeRequest(self, **kw):
        from pyramid.testing import DummyModel
        from pyramid.testing import DummyRequest
        request = DummyRequest(**kw)
        request.context = DummyModel()
        return request



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


class Test_uuidRandomToken(unittest.TestCase):

    def _callFUT(self):
        from cartouche.util import uuidRandomToken
        return uuidRandomToken()

    def test_provides_ITokenGenerator(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import ITokenGenerator
        from cartouche.util import uuidRandomToken
        verifyObject(ITokenGenerator, uuidRandomToken)

    def test_it(self):
        from uuid import UUID
        token = self._callFUT()
        uuid = UUID(token)
        self.assertEqual(uuid.version, 4)


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
        def _tokenGenerator():
            return 'RANDOM'
        from cartouche.interfaces import ITokenGenerator
        self.config.registry.registerUtility(_tokenGenerator, ITokenGenerator)
        token = self._callFUT()
        self.assertEqual(token, 'RANDOM')


class Test_randomPassword(unittest.TestCase):

    def _callFUT(self):
        from cartouche.util import randomPassword
        return randomPassword()

    def test_provides_IPasswordGenerator(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import IPasswordGenerator
        from cartouche.util import randomPassword
        verifyObject(IPasswordGenerator, randomPassword)

    def test_it(self):
        import re
        RANDOM_PATTERN = re.compile(r'[A-Za-z0-9]{6,8}'
                                     '[~!@#$%^&*]'
                                     '[A-Za-z0-9]{6,8}'
                                   )
        self.failUnless(RANDOM_PATTERN.match(self._callFUT()))


class Test_autoLoginViaAuthTkt(_Base, unittest.TestCase):

    def _callFUT(self, userid='testing', request=None):
        from cartouche.util import autoLoginViaWhoAPI
        if request is None:
            request = self._makeRequest()
        return autoLoginViaWhoAPI(userid, request)

    def test_provides_IAutoLogin(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import IAutoLogin
        from cartouche.util import autoLoginViaWhoAPI
        verifyObject(IAutoLogin, autoLoginViaWhoAPI)

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

    def test_w_API_in_environ_w_plugin_id_override(self):
        HEADERS = [('Faux-Cookie', 'gingersnap')]
        settings = self.config.registry.settings
        settings['cartouche.auto_login_identifier'] = 'test'
        api = FauxAPI(HEADERS)
        request = self._makeRequest(environ={'repoze.who.api': api})

        result = self._callFUT('testing', request)

        self.assertEqual(result, HEADERS)
        self.assertEqual(api._called_with[0],
                         {'repoze.who.plugins.auth_tkt.userid': 'testing'})
        self.assertEqual(api._called_with[1], 'test')


class Test_sendGeneratedPassword(_Base, unittest.TestCase):

    def _callFUT(self, request=None, userid='testing', confirmed=None):
        from cartouche.util import sendGeneratedPassword
        if request is None:
            request = self._makeRequest()
        if confirmed is None:
            confirmed = DummyConfirmed()
        return sendGeneratedPassword(request, userid, confirmed)

    def test_miss(self):
        self.assertRaises(KeyError, self._callFUT, userid='nonesuch')

    def test_hit_w_password_utility(self):
        import re
        from repoze.sendmail.interfaces import IMailDelivery
        from zope.password.password import SSHAPasswordManager
        from cartouche.interfaces import IPasswordGenerator
        GENERATED = re.compile(r'Your new password is:\s+(?P<password>[^\s]+)',
                    re.MULTILINE)
        FROM_EMAIL = 'admin@example.com'
        TO_EMAIL = 'phred@example.com'
        def _password():
            return 'PASSWORD'
        self.config.registry.registerUtility(_password, IPasswordGenerator)
        self.config.registry.settings['cartouche.from_addr'] = FROM_EMAIL
        delivery = DummyMailer()
        self.config.registry.registerUtility(delivery, IMailDelivery)
        confirmed = DummyConfirmed()
        confirmed.set('UUID',
                      email=TO_EMAIL,
                      login='phred',
                      password='old_password',
                      security_question='question',
                      security_answer='answer',
                      token=None,
                     )

        self._callFUT(userid='UUID', confirmed=confirmed)

        record = confirmed.get('UUID')
        self.assertEqual(record.uuid, 'UUID')
        self.assertEqual(record.email, TO_EMAIL)
        self.assertEqual(record.login, 'phred')
        password = record.password
        self.assertNotEqual(password, 'old_password')
        self.failUnless(password.startswith(b'{SSHA}'))
        self.assertEqual(record.security_question, 'question')
        self.assertEqual(record.security_answer, 'answer')
        self.assertEqual(record.token, None)
        login_url = 'http://example.com/login.html'
        self.assertEqual(delivery._sent[0], FROM_EMAIL)
        self.assertEqual(list(delivery._sent[1]), [TO_EMAIL])
        payload = delivery._sent[2].get_payload()
        self.failUnless(login_url in payload)
        found = GENERATED.search(payload)
        generated = found.group('password') 
        self.assertEqual(generated, 'PASSWORD')
        pwd_mgr = SSHAPasswordManager()
        self.failUnless(pwd_mgr.checkPassword(password, generated))

    def test_hit_wo_password_utility(self):
        import re
        from repoze.sendmail.interfaces import IMailDelivery
        from zope.password.password import SSHAPasswordManager
        GENERATED = re.compile(r'Your new password is:\s+(?P<password>[^\s]+)',
                    re.MULTILINE)
        RANDOM_PATTERN = re.compile(r'[A-Za-z0-9]{6,8}'
                                     '[~!@#$%^&*]'
                                     '[A-Za-z0-9]{6,8}'
                                   )
        FROM_EMAIL = 'admin@example.com'
        TO_EMAIL = 'phred@example.com'
        self.config.registry.settings['cartouche.from_addr'] = FROM_EMAIL
        delivery = DummyMailer()
        self.config.registry.registerUtility(delivery, IMailDelivery)
        confirmed = DummyConfirmed()
        confirmed.set('UUID',
                      email=TO_EMAIL,
                      login='phred',
                      password='old_password',
                      security_question='question',
                      security_answer='answer',
                      token=None,
                     )

        self._callFUT(userid='UUID', confirmed=confirmed)

        record = confirmed.get('UUID')
        self.assertEqual(record.uuid, 'UUID')
        self.assertEqual(record.email, TO_EMAIL)
        self.assertEqual(record.login, 'phred')
        password = record.password
        self.assertNotEqual(password, 'old_password')
        self.failUnless(password.startswith(b'{SSHA}'))
        self.assertEqual(record.security_question, 'question')
        self.assertEqual(record.security_answer, 'answer')
        self.assertEqual(record.token, None)
        login_url = 'http://example.com/login.html'
        self.assertEqual(delivery._sent[0], FROM_EMAIL)
        self.assertEqual(list(delivery._sent[1]), [TO_EMAIL])
        payload = delivery._sent[2].get_payload()
        self.failUnless(login_url in payload)
        found = GENERATED.search(payload)
        generated = found.group('password') 
        pwd_mgr = SSHAPasswordManager()
        self.failUnless(pwd_mgr.checkPassword(password, generated))
        self.failUnless(RANDOM_PATTERN.match(generated))


class Test_defaultCameFromURL(_Base, unittest.TestCase):

    def _callFUT(self, request):
        from cartouche.util import defaultCameFromURL
        return defaultCameFromURL(request)

    def test_provides_ICameFromURL(self):
        from zope.interface.verify import verifyObject
        from cartouche.interfaces import ICameFromURL
        from cartouche.util import defaultCameFromURL
        verifyObject(ICameFromURL, defaultCameFromURL)

    def test_no_qs_or_referrer(self):
        EXPECTED = 'http://example.com/view.html'
        request = self._makeRequest(view_name='view.html')
        self.assertEqual(self._callFUT(request), EXPECTED)

    def test_no_qs_use_referrer(self):
        EXPECTED = 'http://example.com/expected'
        request = self._makeRequest(environ={'HTTP_REFERER': EXPECTED})
        self.assertEqual(self._callFUT(request), EXPECTED)

    def test_prefer_query_string_to_referrer(self):
        EXPECTED = 'http://example.com/expected'
        UNEXPECTED = 'http://example.com/unexpected'
        request = self._makeRequest(GET={'came_from': EXPECTED},
                                    environ={'HTTP_REFERER': UNEXPECTED})
        self.assertEqual(self._callFUT(request), EXPECTED)



class FauxAPI:
    def __init__(self, headers):
        self._headers = headers
    def login(self, credentials, identifier_name=None):
        self._called_with = (credentials, identifier_name)
        return 'testing', self._headers


class Dummy:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class DummyConfirmed:
    def __init__(self, records=None):
        if records is None:
            records = {}
        self._records = records
    def get(self, uuid, default=None):
        return self._records.get(uuid, default)
    def set(self, uuid, **kw):
        self._records[uuid] = Dummy(uuid=uuid, **kw)


class DummyMailer:
    _sent = None

    def send(self, from_addr, to_addrs, message):
        self._sent = (from_addr, to_addrs, message)
