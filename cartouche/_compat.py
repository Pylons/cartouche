##############################################################################
#
# Copyright (c) 2014 Agendaless Consulting and Contributors.
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
import sys

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3


if PY3: #pragma NO COVER
    from string import ascii_letters as letters
    from urllib.parse import parse_qs
    from urllib.parse import parse_qsl
    from urllib.parse import urljoin
    from urllib.parse import urlparse
    from urllib.parse import urlunparse
    from urllib.parse import quote as url_quote
    from urllib.parse import urlencode as url_encode
else:
    from string import letters
    from urllib import quote as url_quote
    from urllib import urlencode as url_encode
    from urlparse import parse_qs
    from urlparse import parse_qsl
    from urlparse import urljoin
    from urlparse import urlparse
    from urlparse import urlunparse

try:
    STRING_TYPES = (str, unicode)
except NameError: #pragma NO COVER Python >= 3.0
    STRING_TYPES = (str,)

try:
    u = unicode
except NameError: #pragma NO COVER Python >= 3.0
    u = str
    b = bytes
else: #pragma NO COVER Python < 3.0
    b = str
