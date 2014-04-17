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

_marker = object()

class WhoPluginTests(unittest.TestCase):

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

    def _getTempdir(self):
        if self._tempdir is None:
            from tempfile import mkdtemp
            self._tempdir = mkdtemp()
        return self._tempdir

    def _makeContext(self, **kw):
        from pyramid.testing import DummyModel
        return DummyModel(**kw)

    def _makeRequest(self, **kw):
        from pyramid.testing import DummyRequest
        return DummyRequest(**kw)

    def _getTargetClass(self):
        from cartouche.whoplugin import WhoPlugin
        return WhoPlugin

    def _makeOne(self, zodb_uri=_marker):
        if zodb_uri is _marker:
            import os
            filename = os.path.join(self._getTempdir(), 'Data.fs')
            zodb_uri = 'file://%s' % filename
        return self._getTargetClass()(zodb_uri)

    def _populate(self, app):
        from zope.password.password import SSHAPasswordManager
        pwd_mgr = SSHAPasswordManager()
        encoded = pwd_mgr.encodePassword('password')
        cartouche = app.cartouche = FauxCartouche()
        cartouche.by_uuid['UUID'] = Dummy(uuid='UUID', password=encoded)
        cartouche.by_login['login'] = 'UUID'

    def _registerConfirmed(self):
        from zope.password.password import SSHAPasswordManager
        from cartouche.interfaces import IRegistrations
        pwd_mgr = SSHAPasswordManager()
        encoded = pwd_mgr.encodePassword('password')
        class DummyConfirmed:
            def __init__(self, context):
                pass
            def get_by_login(self, login, default=None):
                if login == 'login':
                    return Dummy(uuid='UUID', password=encoded)
                return default
        self.config.registry.registerAdapter(DummyConfirmed,
                                             (None,), IRegistrations,
                                             name='confirmed')

    def _makeFauxConn(self):
        conn = FauxConnection()
        app = conn._root['app_root']
        self._populate(app)
        return conn

    def _makeFilestorage(self):
        import os
        from persistent import Persistent
        import transaction
        from ZODB import DB
        from ZODB.FileStorage import FileStorage
        global Root
        class Root(Persistent):
            __name__ = __parent__ = None
        db = DB(FileStorage(os.path.join(self._getTempdir(), 'Data.fs')))
        conn = db.open()
        root = conn.root()
        app = root['app_root'] = Root()
        self._populate(app)
        transaction.commit()
        db.close()

    def test_class_conforms_to_IAuthenticationPlugin(self):
        from zope.interface.verify import verifyClass
        from repoze.who.interfaces import IAuthenticator
        verifyClass(IAuthenticator, self._getTargetClass())

    def test_instance_conforms_to_IAuthenticationPlugin(self):
        from zope.interface.verify import verifyObject
        from repoze.who.interfaces import IAuthenticator
        verifyObject(IAuthenticator, self._makeOne())

    def test_missing_credentials(self):
        plugin = self._makeOne()
        self.assertEqual(plugin.authenticate({}, {}), None)

    def test_miss_w_configured_IRegistrations_adapter(self):
        self._registerConfirmed()
        environ = {}
        credentials = {'login': 'login', 'password': 'bogus'}
        plugin = self._makeOne('file:///dev/null') # Don't fall back!
        self.assertEqual(plugin.authenticate(environ, credentials), None)

    def test_hit_w_configured_IRegistrations_adapter(self):
        self._registerConfirmed()
        environ = {}
        credentials = {'login': 'login', 'password': 'password'}
        plugin = self._makeOne('file:///dev/null') # Don't fall back!
        self.assertEqual(plugin.authenticate(environ, credentials), 'UUID')

    def test_miss_w_persistent_context(self):
        from pyramid.threadlocal import manager
        context = self._makeContext(_p_jar=object())
        request = self._makeRequest(context=context)
        manager.get()['request'] = request
        environ = request.environ
        credentials = {'login': 'login', 'password': 'bogus'}
        plugin = self._makeOne()
        self.assertEqual(plugin.authenticate(environ, credentials), None)

    def test_hit_w_persistent_context_non_root(self):
        from pyramid.threadlocal import manager
        root = self._makeContext(_p_jar=object())
        self._populate(root)
        context = self._makeContext(_p_jar=object(),
                                    __parent__=root,
                                    cartouche=object(), # ignored
                                   )
        request = self._makeRequest(context=context)
        manager.get()['request'] = request
        environ = request.environ
        credentials = {'login': 'login', 'password': 'password'}
        plugin = self._makeOne()
        self.assertEqual(plugin.authenticate(environ, credentials), 'UUID')

    def test_miss_w_conn_in_environ(self):
        environ = {'repoze.zodbconn.connection': self._makeFauxConn()}
        credentials = {'login': 'login', 'password': 'bogus'}
        plugin = self._makeOne()
        self.assertEqual(plugin.authenticate(environ, credentials), None)

    def test_hit_w_conn_in_environ(self):
        environ = {'repoze.zodbconn.connection': self._makeFauxConn()}
        credentials = {'login': 'login', 'password': 'password'}
        plugin = self._makeOne()
        self.assertEqual(plugin.authenticate(environ, credentials), 'UUID')

    def test_miss_no_conn_in_environ(self):
        self._makeFilestorage()
        plugin = self._makeOne()
        environ = {}
        credentials = {'login': 'login', 'password': 'bogus'}
        self.assertEqual(plugin.authenticate(environ, credentials), None)

    def test_hit_no_conn_in_environ(self):
        self._makeFilestorage()
        environ = {}
        credentials = {'login': 'login', 'password': 'password'}
        plugin = self._makeOne()
        self.assertEqual(plugin.authenticate(environ, credentials), 'UUID')


class Test_make_plugin(unittest.TestCase):

    def test_it(self):
        URI = "file:///tmp/Data.fs"
        from cartouche.whoplugin import WhoPlugin
        from cartouche.whoplugin import make_plugin
        plugin = make_plugin(URI)
        self.assertTrue(isinstance(plugin, WhoPlugin))
        self.assertEqual(plugin._zodb_uri, URI)


class Dummy(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

class FauxConnection(object):
    def __init__(self):
        self._root = {'app_root': Dummy(__parent__=None)}
    def root(self):
        return self._root

class FauxCartouche(object):
    def __init__(self):
        self.by_uuid = {}
        self.by_login = {}
