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

    _tempdir = None

    def setUp(self):
        from pyramid.config import Configurator
        self.config = Configurator(autocommit=True)
        self.config.begin()

    def tearDown(self):
        self.config.end()
        if self._tempdir is not None:
            import shutil
            shutil.rmtree(self._tempdir)

    def _makeWhoConfig(self, filename='who.ini', text=''):
        import os
        if self._tempdir is None:
            import tempfile
            tempdir = self._tempdir = tempfile.mkdtemp()
        fqn = os.path.join(tempdir, filename)
        f = open(fqn, 'w')
        f.write(text)
        f.flush()
        f.close()
        return fqn


class PyramidPolicyTests(_Base, unittest.TestCase):

    def _getTargetClass(self):
        from cartouche.pyramidpolicy import PyramidPolicy
        return PyramidPolicy

    def _makeOne(self):
        config_file = self._makeWhoConfig()
        return self._getTargetClass()(config_file, 'testing')

    def _makeContext(self, **kw):
        from pyramid.testing import DummyModel
        return DummyModel(**kw)

    def _makeRequest(self, **kw):
        from pyramid.testing import DummyRequest
        context = kw.pop('context', None)
        if context is None:
            context = self._makeContext()
        return DummyRequest(context=context, **kw)

    def _makeCartouche(self):
        class DummyCartouche(object):
            def __init__(self):
                self.pending = {}
                self.by_uuid = {}
                self.by_login = {}
                self.by_email = {}
        return DummyCartouche()

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

    def test_class_conforms_to_IAuthenticationPolicy(self):
        from zope.interface.verify import verifyClass
        from pyramid.interfaces import IAuthenticationPolicy
        verifyClass(IAuthenticationPolicy, self._getTargetClass())

    def test_instance_conforms_to_IAuthenticationPolicy(self):
        from zope.interface.verify import verifyObject
        from pyramid.interfaces import IAuthenticationPolicy
        verifyObject(IAuthenticationPolicy, self._makeOne())

    def test_authenticated_userid_no_identity_in_environ(self):
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                  }
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.authenticated_userid(request), None)

    def test_authenticated_userid_w_api_in_environ_wo_adapter_miss(self):
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': DummyAPI('phred'),
                  }
        request = self._makeRequest(environ=ENVIRON)
        cartouche = request.context.cartouche = self._makeCartouche()
        policy = self._makeOne()
        self.assertEqual(policy.authenticated_userid(request), None)

    def test_authenticated_userid_w_api_in_environ_wo_adapter_hit(self):
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': DummyAPI('phred'),
                  }
        request = self._makeRequest(environ=ENVIRON)
        cartouche = request.context.cartouche = self._makeCartouche()
        cartouche.by_uuid['phred'] = Dummy()
        policy = self._makeOne()
        self.assertEqual(policy.authenticated_userid(request), 'phred')

    def test_authenticated_userid_w_api_in_environ_w_adapter_miss(self):
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': DummyAPI('phred'),
                  }
        by_uuid, by_login, by_email = self._registerConfirmed()
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.authenticated_userid(request), None)

    def test_authenticated_userid_w_api_in_environ_w_adapter_hit(self):
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': DummyAPI('phred'),
                  }
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['phred'] = Dummy()
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.authenticated_userid(request), 'phred')

    def test_authenticated_userid_w_identity_in_environ_wo_adapter_miss(self):
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'phred'}}
        request = self._makeRequest(environ=ENVIRON)
        cartouche = request.context.cartouche = self._makeCartouche()
        policy = self._makeOne()
        self.assertEqual(policy.authenticated_userid(request), None)

    def test_authenticated_userid_w_identity_in_environ_wo_adapter_hit(self):
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'phred'}}
        request = self._makeRequest(environ=ENVIRON)
        cartouche = request.context.cartouche = self._makeCartouche()
        cartouche.by_uuid['phred'] = Dummy()
        policy = self._makeOne()
        self.assertEqual(policy.authenticated_userid(request), 'phred')

    def test_authenticated_userid_w_identity_in_environ_w_adapter_miss(self):
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'phred'}}
        by_uuid, by_login, by_email = self._registerConfirmed()
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.authenticated_userid(request), None)

    def test_authenticated_userid_w_identity_in_environ_w_adapter_hit(self):
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'phred'}}
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['phred'] = Dummy()
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.authenticated_userid(request), 'phred')

    def test_effective_principals_no_identity_in_environ(self):
        from pyramid.security import Everyone
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                  }
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.effective_principals(request), [Everyone])

    def test_effective_principals_w_api_in_environ_wo_adapter_miss(self):
        from pyramid.security import Everyone
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': DummyAPI('phred'),
                  }
        request = self._makeRequest(environ=ENVIRON)
        cartouche = request.context.cartouche = self._makeCartouche()
        policy = self._makeOne()
        self.assertEqual(policy.effective_principals(request), [Everyone])

    def test_effective_principals_w_api_in_environ_wo_adapter_hit(self):
        from pyramid.security import Authenticated
        from pyramid.security import Everyone
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': DummyAPI('phred'),
                  }
        request = self._makeRequest(environ=ENVIRON)
        cartouche = request.context.cartouche = self._makeCartouche()
        cartouche.by_uuid['phred'] = Dummy()
        policy = self._makeOne()
        self.assertEqual(policy.effective_principals(request),
                         ['phred', Authenticated, Everyone]) # TODO groups

    def test_effective_principals_w_api_in_environ_w_adapter_miss(self):
        from pyramid.security import Everyone
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': DummyAPI('phred'),
                  }
        by_uuid, by_login, by_email = self._registerConfirmed()
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.effective_principals(request), [Everyone])

    def test_effective_principals_w_api_in_environ_w_adapter_hit(self):
        from pyramid.security import Authenticated
        from pyramid.security import Everyone
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': DummyAPI('phred'),
                  }
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['phred'] = Dummy()
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.effective_principals(request),
                         ['phred', Authenticated, Everyone]) # TODO groups

    def test_effective_principals_w_identity_in_environ_wo_adapter_miss(self):
        from pyramid.security import Everyone
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'phred'}}
        request = self._makeRequest(environ=ENVIRON)
        cartouche = request.context.cartouche = self._makeCartouche()
        policy = self._makeOne()
        self.assertEqual(policy.effective_principals(request), [Everyone])

    def test_effective_principals_w_identity_in_environ_wo_adapter_hit(self):
        from pyramid.security import Authenticated
        from pyramid.security import Everyone
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'phred'}}
        request = self._makeRequest(environ=ENVIRON)
        cartouche = request.context.cartouche = self._makeCartouche()
        cartouche.by_uuid['phred'] = Dummy()
        policy = self._makeOne()
        self.assertEqual(policy.effective_principals(request),
                         ['phred', Authenticated, Everyone]) # TODO groups

    def test_effective_principals_w_identity_in_environ_w_adapter_miss(self):
        from pyramid.security import Everyone
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'phred'}}
        request = self._makeRequest(environ=ENVIRON)
        by_uuid, by_login, by_email = self._registerConfirmed()
        policy = self._makeOne()
        self.assertEqual(policy.effective_principals(request), [Everyone])

    def test_effective_principals_w_identity_in_environ_w_adapter_hit(self):
        from pyramid.security import Authenticated
        from pyramid.security import Everyone
        ENVIRON = {'repoze.who.identity': {'repoze.who.userid': 'phred'}}
        by_uuid, by_login, by_email = self._registerConfirmed()
        by_uuid['phred'] = Dummy()
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.effective_principals(request),
                         ['phred', Authenticated, Everyone])

    def test_remember_w_api_in_environ(self):
        HEADERS = [('Fruit', 'Basket')]
        api = DummyAPI(headers=HEADERS)
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': api,
                  }
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.remember(request, 'phred'), HEADERS)
        self.assertEqual(api._remembered, {'repoze.who.userid': 'phred',
                                           'identifier': 'testing',
                                          })

    def test_forget_w_api_in_environ(self):
        HEADERS = [('Fruit', 'Basket')]
        api = DummyAPI(authenticated='phred', headers=HEADERS)
        ENVIRON = {'wsgi.version': '1.0',
                   'HTTP_USER_AGENT': 'testing',
                   'repoze.who.api': api,
                  }
        request = self._makeRequest(environ=ENVIRON)
        policy = self._makeOne()
        self.assertEqual(policy.forget(request), HEADERS)
        self.assertEqual(api._forgtten, {'repoze.who.userid': 'phred'})


class DummyAPI:

    def __init__(self, authenticated=None, headers=()):
        self._authenticated = authenticated
        self._headers = headers

    def authenticate(self):
        if self._authenticated is not None:
            return {'repoze.who.userid': self._authenticated}

    def remember(self, identity=None):
        self._remembered = identity
        return self._headers

    def forget(self, identity=None):
        self._forgtten = identity
        return self._headers


class Dummy:

    def __init__(self, **kw):
        self.__dict__.update(kw)
