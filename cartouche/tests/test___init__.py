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
