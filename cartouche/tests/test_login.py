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

    def _registerConfirmed(self):
        from cartouche.interfaces import IRegistrations
        by_uuid = {}
        by_login = {}
        by_email = {}
        class DummyConfirmed:
            def __init__(self, context):
                pass
            def get(self, key, default=None):
                return by_uuid.get(key, default)
            def get_by_login(self, login, default=None):
                uuid = by_login.get(login)
                if uuid is None:
                    return default
                return by_uuid.get(uuid, default)
            def get_by_email(self, email, default=None):
                uuid = by_email.get(email)
                if uuid is None:
                    return default
                return by_uuid.get(uuid, default)
            def set(self, key, **kw):
                old_record = by_uuid.get(key)
                if old_record is not None:
                    del by_login[old_record.login]
                    del by_email[old_record.email]
                record =  Dummy(**kw)
                by_uuid[key] = record
                by_login[record.login] = key
                by_email[record.email] = key
            def remove(self, key):
                info = by_uuid[key]
                del by_uuid[key]
                del by_login[info.login]
                del by_email[info.email]
        self.config.registry.registerAdapter(DummyConfirmed,
                                             (None,), IRegistrations,
                                             name='confirmed')
        return by_uuid, by_login, by_email


class Test_login(_Base, unittest.TestCase):

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


class Test_logout(_Base, unittest.TestCase):

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


class Test_recover_account(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.login import recover_account_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return recover_account_view(context, request)

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
        self.assertEqual(info['reset_password_url'],
                         'http://example.com/reset_password.html')

    def test_POST_w_errors(self):
        import re
        SUMMARY_ERROR = re.compile('<h3[^>]*>There was a problem', re.MULTILINE)
        FIELD_ERROR = re.compile('<p class="error"', re.MULTILINE)
        POST = {'email': '',
                'recover': '',
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

    def test_POST_email_miss_still_redirects(self):
        from repoze.sendmail.interfaces import IMailDelivery
        from webob.exc import HTTPFound

        FROM_EMAIL = 'admin@example.com'
        TO_EMAIL = 'phred@example.com'
        POST = {'email': TO_EMAIL,
                'recover': '',
               }
        self.config.registry.settings['cartouche.from_addr'] = FROM_EMAIL
        delivery = DummyMailer()
        self.config.registry.registerUtility(delivery, IMailDelivery)
        context = self._makeContext()
        request = self._makeRequest(POST=POST)

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        login_url = 'http://example.com/login.html'
        self.assertEqual(response.location, login_url)
        self.assertEqual(delivery._sent, None)

    def test_POST_email_hit_no_login_url_override(self):
        from repoze.sendmail.interfaces import IMailDelivery
        from webob.exc import HTTPFound

        FROM_EMAIL = 'admin@example.com'
        TO_EMAIL = 'phred@example.com'
        POST = {'email': TO_EMAIL,
                'recover': '',
               }
        self.config.registry.settings['cartouche.from_addr'] = FROM_EMAIL
        delivery = DummyMailer()
        self.config.registry.registerUtility(delivery, IMailDelivery)
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['UUID'] = Dummy(login='login')
        by_email[TO_EMAIL] = 'UUID'
        context = self._makeContext()
        request = self._makeRequest(POST=POST)

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        login_url = 'http://example.com/login.html'
        self.assertEqual(response.location, login_url)
        self.assertEqual(delivery._sent[0], FROM_EMAIL)
        self.assertEqual(list(delivery._sent[1]), [TO_EMAIL])
        self.failUnless(login_url in delivery._sent[2].get_payload())

    def test_POST_email_hit_w_login_url_override(self):
        from repoze.sendmail.interfaces import IMailDelivery
        from webob.exc import HTTPFound

        LOGIN = '/login_form.html'
        FROM_EMAIL = 'admin@example.com'
        TO_EMAIL = 'phred@example.com'
        POST = {'email': TO_EMAIL,
                'recover': '',
               }
        self.config.registry.settings['cartouche.from_addr'] = FROM_EMAIL
        self.config.registry.settings['cartouche.login_url'] = LOGIN
        delivery = DummyMailer()
        self.config.registry.registerUtility(delivery, IMailDelivery)
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['UUID'] = Dummy(login='login')
        by_email[TO_EMAIL] = 'UUID'
        context = self._makeContext()
        request = self._makeRequest(POST=POST)

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        login_url = 'http://example.com%s' % LOGIN
        self.assertEqual(response.location, login_url)
        self.assertEqual(delivery._sent[0], FROM_EMAIL)
        self.assertEqual(list(delivery._sent[1]), [TO_EMAIL])
        self.failUnless(login_url in delivery._sent[2].get_payload())


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


class DummyMailer:
    _sent = None

    def send(self, from_addr, to_addrs, message):
        self._sent = (from_addr, to_addrs, message)


class Dummy:
    def __init__(self, **kw):
        self.__dict__.update(kw)
