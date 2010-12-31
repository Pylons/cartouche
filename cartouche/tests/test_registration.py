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
            def setRecord(self, key, record):
                pending[key] = record
            def remove(self, key):
                del pending[key]
        self.config.registry.registerAdapter(DummyRegistrationsByEmail,
                                             (None,), IRegistrations,
                                             name='pending')
        return pending

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

    def _registerAutoLogin(self):
        from cartouche.registration import autoLoginViaAuthTkt
        self.config.registry.registerUtility(autoLoginViaAuthTkt)


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

    def test_POST_no_errors_no_confirmation_url(self):
        from urllib import quote
        from repoze.sendmail.interfaces import IMailDelivery
        from webob.exc import HTTPFound
        from cartouche.interfaces import ITokenGenerator

        FROM_EMAIL = 'admin@example.com'
        TO_EMAIL = 'phred@example.com'
        POST = {'email': TO_EMAIL,
                'register': '',
               }
        self.config.registry.settings['cartouche.from_addr'] = FROM_EMAIL
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

    def test_POST_no_errors_w_confirmation_url(self):
        from urllib import quote
        from repoze.sendmail.interfaces import IMailDelivery
        from webob.exc import HTTPFound
        from cartouche.interfaces import ITokenGenerator

        FROM_EMAIL = 'admin@example.com'
        TO_EMAIL = 'phred@example.com'
        CONF_URL = '/confirm.html?foo=bar'
        POST = {'email': TO_EMAIL,
                'register': '',
               }
        self.config.registry.settings['cartouche.from_addr'] = FROM_EMAIL
        self.config.registry.settings['cartouche.confirmation_url'] = CONF_URL
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
                         'http://example.com/confirm.html'
                           '?foo=bar&email=%s' % quote(TO_EMAIL))
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

    def test_GET_w_email_miss_w_register_url(self):
        from webob.exc import HTTPFound
        REG_URL = '/site_registration.html?foo=bar'
        EMAIL = 'phred@example.com'
        self.config.registry.settings['cartouche.register_url'] = REG_URL
        pending = self._registerPendingRegistrations()
        request = self._makeRequest(GET={'email': EMAIL})

        response = self._callFUT(request=request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/site_registration.html'
                         '?foo=bar&message=Please+register+first.')

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
        from urllib import quote
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
                         '+confirmation+e-mail.&email=%s' % quote(EMAIL))

    def test_POST_w_token_hit_no_auto_login(self):
        from webob.exc import HTTPFound
        EMAIL = 'phred@example.com'
        POST = {'email': EMAIL,
                'token': 'TOKEN',
                'confirm': '',
               }
        pending = self._registerPendingRegistrations()
        pending[EMAIL] = Dummy(token='TOKEN')
        by_uuid, by_login, by_email = self._registerConfirmed()
        HEADERS = [('Faux-Cookie', 'gingersnap')]
        api = FauxAPI(HEADERS)
        context = self._makeContext()
        request = self._makeRequest(POST=POST,
                                    environ={'repoze.who.api': api})

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        for key, value in HEADERS:
            self.assertEqual(response.headers.get(key), None)
        self.assertEqual(response.location,
                         'http://example.com/edit_account.html')

        self.failIf(EMAIL in pending)
        uuid = by_email[EMAIL]
        self.assertEqual(by_login[EMAIL], uuid)
        self.assertEqual(by_uuid[uuid].email, EMAIL)
        self.assertEqual(by_uuid[uuid].login, EMAIL)
        self.assertEqual(by_uuid[uuid].password, None)
        self.assertEqual(by_uuid[uuid].security_question, None)
        self.assertEqual(by_uuid[uuid].security_answer, None)
        self.failIf('_called_with' in api.__dict__)

    def test_POST_w_token_hit_no_after_confirmation_url_setting(self):
        from webob.exc import HTTPFound
        EMAIL = 'phred@example.com'
        POST = {'email': EMAIL,
                'token': 'TOKEN',
                'confirm': '',
               }
        self._registerAutoLogin()
        pending = self._registerPendingRegistrations()
        pending[EMAIL] = Dummy(token='TOKEN')
        by_uuid, by_login, by_email = self._registerConfirmed()
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
                         'http://example.com/edit_account.html')

        self.failIf(EMAIL in pending)
        uuid = by_email[EMAIL]
        self.assertEqual(by_login[EMAIL], uuid)
        self.assertEqual(by_uuid[uuid].email, EMAIL)
        self.assertEqual(by_uuid[uuid].login, EMAIL)
        self.assertEqual(by_uuid[uuid].password, None)
        self.assertEqual(by_uuid[uuid].security_question, None)
        self.assertEqual(by_uuid[uuid].security_answer, None)
        self.assertEqual(api._called_with[0],
                         {'repoze.who.plugins.auth_tkt.userid': uuid})

    def test_POST_w_token_hit_w_after_confirmation_url_setting(self):
        from webob.exc import HTTPFound
        EMAIL = 'phred@example.com'
        AFTER = '/after.html'
        POST = {'email': EMAIL,
                'token': 'TOKEN',
                'confirm': '',
               }
        self._registerAutoLogin()
        settings = self.config.registry.settings
        settings['cartouche.after_confirmation_url'] = AFTER
        pending = self._registerPendingRegistrations()
        pending[EMAIL] = Dummy(token='TOKEN')
        by_uuid, by_login, by_email = self._registerConfirmed()
        HEADERS = [('Faux-Cookie', 'gingersnap')]
        api = FauxAPI(HEADERS)
        context = self._makeContext()
        request = self._makeRequest(POST=POST,
                                    environ={'repoze.who.api': api})

        response = self._callFUT(context, request)

        self.failUnless(isinstance(response, HTTPFound))
        for key, value in HEADERS:
            self.assertEqual(response.headers[key], value)
        self.assertEqual(response.location, 'http://example.com/after.html')


class Test_edit_account_view(_Base, unittest.TestCase):

    def _callFUT(self, context=None, request=None):
        from cartouche.registration import edit_account_view
        if context is None:
            context = self._makeContext()
        if request is None:
            request = self._makeRequest()
        return edit_account_view(context, request)

    def test_GET_wo_credentials(self):
        from webob.exc import HTTPUnauthorized
        response = self._callFUT()
        self.failUnless(isinstance(response, HTTPUnauthorized))

    def test_GET_w_unknown_credentials(self):
        from webob.exc import HTTPForbidden
        EMAIL = 'phred@example.com'
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': EMAIL}}
        by_uuid, by_login, by_email = self._registerConfirmed()
        request = self._makeRequest(environ=ENVIRON)

        response = self._callFUT(request=request)

        self.failUnless(isinstance(response, HTTPForbidden))

    def test_GET_w_known_credentials_initial_edit(self):
        import re
        INPUT = re.compile('<input.* name="(?P<name>\w+)" '
                           'value="(?P<value>[^"]*)"', re.MULTILINE)
        SELECT = re.compile('<select.* name="(?P<name>\w+)" ', re.MULTILINE)
        OPTIONS = re.compile('<option.*? value="(?P<value>[^"]+)"')
        OPTIONS_SEL = re.compile('<option.*? value="(?P<value>\w+)" '
                                 'selected="(?P<selected>\w*)" ', re.MULTILINE)
        EMAIL = 'phred@example.com'
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'UUID'}}
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['UUID'] = Dummy(login=EMAIL,
                                email=EMAIL,
                                password=None,
                                security_question=None,
                                security_answer=None,
                               )
        by_email[EMAIL] = by_login[EMAIL] = 'UUID'
        mtr = self.config.testing_add_template('templates/main.pt')
        request = self._makeRequest(environ=ENVIRON)

        info = self._callFUT(request=request)

        self.failUnless(info['main_template'] is mtr.implementation())
        rendered_form = info['rendered_form']
        inputs = [x for x in INPUT.findall(rendered_form)
                        if not x[0].startswith('_')]
        self.assertEqual(inputs, [('login_name', EMAIL),
                                  ('email', EMAIL),
                                  ('old_password', ''), # hidden
                                  ('value', ''),
                                  ('confirm', ''),
                                  ('answer', ''),
                                 ])
        selects = [x for x in SELECT.findall(rendered_form)]
        self.assertEqual(selects, ['question'])
        options = [x for x in OPTIONS.findall(rendered_form)]
        self.assertEqual(options, ['color', 'borncity', 'petname'])
        options_sel = [x for x in OPTIONS_SEL.findall(rendered_form)]
        self.assertEqual(options_sel, [])

    def test_GET_w_known_credentials_later_edit(self):
        import re
        from zope.password.password import SSHAPasswordManager
        INPUT = re.compile('<input.* name="(?P<name>\w+)" '
                           'value="(?P<value>[^"]*)"', re.MULTILINE)
        SELECT = re.compile('<select.* name="(?P<name>\w+)" ', re.MULTILINE)
        OPTIONS = re.compile('<option.*? value="(?P<value>[^"]+)"')
        OPTIONS_SEL = re.compile('<option.*? value="(?P<value>[^"]+)" '
                                 'selected="(?P<selected>\w+)"', re.MULTILINE)
        EMAIL = 'phred@example.com'
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'UUID'}}
        pwd_mgr = SSHAPasswordManager()
        encoded = pwd_mgr.encodePassword('old_password')
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['UUID'] = Dummy(login='before',
                                email=EMAIL,
                                password=encoded,
                                security_question='borncity',
                                security_answer='FXBG',
                               )
        by_email[EMAIL] = by_login['login'] = 'UUID'
        mtr = self.config.testing_add_template('templates/main.pt')
        request = self._makeRequest(environ=ENVIRON)

        info = self._callFUT(request=request)

        self.failUnless(info['main_template'] is mtr.implementation())
        rendered_form = info['rendered_form']
        inputs = [x for x in INPUT.findall(rendered_form)
                        if not x[0].startswith('_')]
        self.assertEqual(inputs, [('login_name', 'before'),
                                  ('email', EMAIL),
                                  ('old_password', ''),
                                  ('value', ''),
                                  ('confirm', ''),
                                  ('answer', 'FXBG'),
                                 ])
        selects = [x for x in SELECT.findall(rendered_form)]
        self.assertEqual(selects, ['question'])
        options = [x for x in OPTIONS.findall(rendered_form)]
        self.assertEqual(options, ['color', 'borncity', 'petname'])
        options_sel = [x for x in OPTIONS_SEL.findall(rendered_form)]
        self.assertEqual(options_sel, [('borncity', 'True')])

    def test_POST_w_old_password_miss(self):
        import re
        from webob.multidict import MultiDict
        from zope.password.password import SSHAPasswordManager
        SUMMARY_ERROR = re.compile('<h3[^>]*>There was a problem', re.MULTILINE)
        FIELD_ERROR = re.compile('<p class="error"', re.MULTILINE)
        OLD_EMAIL = 'old_phred@example.com'
        NEW_EMAIL = 'new_phred@example.com'
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'UUID'}}
        pwd_mgr = SSHAPasswordManager()
        encoded = pwd_mgr.encodePassword('old_password')
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['UUID'] = Dummy(login='before',
                                email=OLD_EMAIL,
                                password=encoded,
                                security_question='borncity',
                                security_answer='FXBG')
        by_email[OLD_EMAIL] = by_login['before'] = 'UUID'
        POST = MultiDict([('login_name', 'after'),
                          ('email', NEW_EMAIL),
                          ('old_password', 'bogus'),
                          ('__start__', 'password:mapping'),
                          ('value', 'newpassword'),
                          ('confirm', 'newpassword'),
                          ('__end__', 'password:mapping'),
                          ('__start__', 'security:mapping'),
                          ('question', 'petname'),
                          ('answer', 'Fido'),
                          ('__end__', 'security:mapping'),
                          ('update', ''),
                         ])
        request = self._makeRequest(POST=POST, environ=ENVIRON)

        info = self._callFUT(request=request)

        rendered_form = info['rendered_form']
        self.failUnless(SUMMARY_ERROR.search(rendered_form))
        self.failUnless(FIELD_ERROR.search(rendered_form))
        self.failUnless(OLD_EMAIL in by_email)
        self.failIf(NEW_EMAIL in by_email)
        self.failUnless('before' in by_login)
        self.failIf('after' in by_login)

    def test_POST_w_password_confirm_mismatch(self):
        import re
        from webob.multidict import MultiDict
        from zope.password.password import SSHAPasswordManager
        SUMMARY_ERROR = re.compile('<h3[^>]*>There was a problem', re.MULTILINE)
        FIELD_ERROR = re.compile('<p class="error"', re.MULTILINE)
        OLD_EMAIL = 'old_phred@example.com'
        NEW_EMAIL = 'new_phred@example.com'
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'UUID'}}
        pwd_mgr = SSHAPasswordManager()
        encoded = pwd_mgr.encodePassword('old_password')
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['UUID'] = Dummy(login='before',
                                email=OLD_EMAIL,
                                password=encoded,
                                security_question='borncity',
                                security_answer='FXBG')
        by_email[OLD_EMAIL] = by_login['before'] = 'UUID'
        POST = MultiDict([('login_name', 'after'),
                          ('email', NEW_EMAIL),
                          ('old_password', 'old_password'),
                          ('__start__', 'password:mapping'),
                          ('value', 'newpassword'),
                          ('confirm', 'mismatch'),
                          ('__end__', 'password:mapping'),
                          ('__start__', 'security:mapping'),
                          ('question', 'petname'),
                          ('answer', 'Fido'),
                          ('__end__', 'security:mapping'),
                          ('update', ''),
                         ])
        request = self._makeRequest(POST=POST, environ=ENVIRON)

        info = self._callFUT(request=request)

        rendered_form = info['rendered_form']
        self.failUnless(SUMMARY_ERROR.search(rendered_form))
        self.failUnless(FIELD_ERROR.search(rendered_form))
        self.failUnless(OLD_EMAIL in by_email)
        self.failIf(NEW_EMAIL in by_email)
        self.failUnless('before' in by_login)
        self.failIf('after' in by_login)

    def test_POST_w_password_match_new_login_not_unique(self):
        import re
        from webob.multidict import MultiDict
        from zope.password.password import SSHAPasswordManager
        SUMMARY_ERROR = re.compile('<h3[^>]*>There was a problem', re.MULTILINE)
        FIELD_ERROR = re.compile('<p class="error"', re.MULTILINE)
        OLD_EMAIL = 'old_phred@example.com'
        NEW_EMAIL = 'new_phred@example.com'
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'UUID'}}
        pwd_mgr = SSHAPasswordManager()
        encoded = pwd_mgr.encodePassword('old_password')
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['UUID'] = Dummy(login='before',
                                email=OLD_EMAIL,
                                password=encoded,
                                security_question='borncity',
                                security_answer='FXBG')
        by_email[OLD_EMAIL] = by_login['before'] = 'UUID'
        by_uuid['OTHER_UUID'] = Dummy(login='taken')
        by_login['taken'] = 'OTHER_UUID'
        POST = MultiDict([('login_name', 'taken'),
                          ('email', NEW_EMAIL),
                          ('old_password', 'old_password'),
                          ('__start__', 'password:mapping'),
                          ('value', 'newpassword'),
                          ('confirm', 'newpassword'),
                          ('__end__', 'password:mapping'),
                          ('__start__', 'security:mapping'),
                          ('question', 'petname'),
                          ('answer', 'Fido'),
                          ('__end__', 'security:mapping'),
                          ('update', ''),
                         ])
        request = self._makeRequest(POST=POST, environ=ENVIRON)

        info = self._callFUT(request=request)

        rendered_form = info['rendered_form']
        self.failUnless(SUMMARY_ERROR.search(rendered_form))
        self.failUnless(FIELD_ERROR.search(rendered_form))
        self.failUnless(OLD_EMAIL in by_email)
        self.failIf(NEW_EMAIL in by_email)
        self.assertEqual(by_login['before'], 'UUID')
        self.assertEqual(by_login['taken'], 'OTHER_UUID')

    def test_POST_w_password_match(self):
        from webob.exc import HTTPFound
        from webob.multidict import MultiDict
        from zope.password.password import SSHAPasswordManager
        OLD_EMAIL = 'old_phred@example.com'
        NEW_EMAIL = 'new_phred@example.com'
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'UUID'}}
        pwd_mgr = SSHAPasswordManager()
        encoded = pwd_mgr.encodePassword('old_password')
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['UUID'] = Dummy(login='before',
                                email=OLD_EMAIL,
                                password=encoded,
                                security_question='borncity',
                                security_answer='FXBG')
        by_email[OLD_EMAIL] = by_login['before'] = 'UUID'
        POST = MultiDict([('login_name', 'after'),
                          ('email', NEW_EMAIL),
                          ('old_password', 'old_password'),
                          ('__start__', 'password:mapping'),
                          ('value', 'newpassword'),
                          ('confirm', 'newpassword'),
                          ('__end__', 'password:mapping'),
                          ('__start__', 'security:mapping'),
                          ('question', 'petname'),
                          ('answer', 'Fido'),
                          ('__end__', 'security:mapping'),
                          ('update', ''),
                         ])
        request = self._makeRequest(POST=POST, environ=ENVIRON,
                                    view_name='edit_account.html')

        response = self._callFUT(request=request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location,
                         'http://example.com/edit_account.html')

        new_record = by_uuid['UUID']
        self.assertEqual(new_record.login, 'after')
        self.failUnless(pwd_mgr.checkPassword(new_record.password,
                                              'newpassword'))
        self.assertEqual(new_record.security_question, 'petname')
        self.assertEqual(new_record.security_answer, 'Fido')
        self.failIf(OLD_EMAIL in by_email)
        self.assertEqual(by_email[NEW_EMAIL], 'UUID')
        self.failIf('before' in by_login)
        self.assertEqual(by_login['after'], 'UUID')

    def test_POST_w_password_match_w_after_edit_url(self):
        from webob.exc import HTTPFound
        from webob.multidict import MultiDict
        from zope.password.password import SSHAPasswordManager
        AFTER = '/'
        OLD_EMAIL = 'old_phred@example.com'
        NEW_EMAIL = 'new_phred@example.com'
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'UUID'}}
        self.config.registry.settings['cartouche.after_edit_url'] = AFTER
        pwd_mgr = SSHAPasswordManager()
        encoded = pwd_mgr.encodePassword('old_password')
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['UUID'] = Dummy(login='before',
                                email=OLD_EMAIL,
                                password=encoded,
                                security_question='borncity',
                                security_answer='FXBG')
        by_email[OLD_EMAIL] = by_login['before'] = 'UUID'
        POST = MultiDict([('login_name', 'after'),
                          ('email', NEW_EMAIL),
                          ('old_password', 'old_password'),
                          ('__start__', 'password:mapping'),
                          ('value', 'newpassword'),
                          ('confirm', 'newpassword'),
                          ('__end__', 'password:mapping'),
                          ('__start__', 'security:mapping'),
                          ('question', 'petname'),
                          ('answer', 'Fido'),
                          ('__end__', 'security:mapping'),
                          ('update', ''),
                         ])
        request = self._makeRequest(POST=POST, environ=ENVIRON,
                                    view_name='edit_account.html')

        response = self._callFUT(request=request)

        self.failUnless(isinstance(response, HTTPFound))
        self.assertEqual(response.location, 'http://example.com/')

        new_record = by_uuid['UUID']
        self.assertEqual(new_record.login, 'after')
        self.failUnless(pwd_mgr.checkPassword(new_record.password,
                                              'newpassword'))
        self.assertEqual(new_record.security_question, 'petname')
        self.assertEqual(new_record.security_answer, 'Fido')
        self.failIf(OLD_EMAIL in by_email)
        self.assertEqual(by_email[NEW_EMAIL], 'UUID')
        self.failIf('before' in by_login)
        self.assertEqual(by_login['after'], 'UUID')


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
