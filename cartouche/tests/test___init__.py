##############################################################################
#
# Copyright (c) 2013 Agendaless Consulting and Contributors.
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

class Test_appmaker(unittest.TestCase):

    def _callFUT(self, zodb_root):
        from cartouche import appmaker
        return appmaker(zodb_root)

    def test_w_existing_attr(self):
        ROOT = object()
        zodb_root = {'app_root': ROOT}
        self.assertTrue(self._callFUT(zodb_root) is ROOT)

    def test_wo_existing_attr(self):
        from cartouche.models import Root
        zodb_root = {}
        root = self._callFUT(zodb_root)
        self.assertTrue(isinstance(root, Root))

class Test_main(unittest.TestCase):

    def _callFUT(self, global_config, **settings):
        from cartouche import main
        return main(global_config, **settings)

    def test_wo_zodb_uri(self):
        self.assertRaises(ValueError, self._callFUT, None)

    def test_w_zodb_uri(self):
        class DummyRequest(object):
            def __init__(self, **kw):
                self.environ = kw
        app = self._callFUT(None, zodb_uri='memory://')
        request = DummyRequest()
        root = app.root_factory(request)
        self.assertEqual(root.data, {})
