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

__version__ = '0.1'

import os
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
 
setup(name='cartouche',
      version=__version__,
      description='Reusable user registration  / profile management',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: System :: Installation/Setup",
        "Framework :: Pylons",
        "Framework :: BFG",
        "License :: Repoze Public License",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      keywords='web application repoze user registration',
      author="Agendaless Consulting",
      author_email="reopze-dev@lists.repoze.org",
      dependency_links=['http://dist.repoze.org'],
      url="http://www.repoze.org/cartouche",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require = [
               ],
      install_requires=[
               'setuptools >= 0.6c7',
               'ZODB3',
               'chameleon',
               'deform',
               'pyramid',
               'pyramid_who',
               'pyramid_zcml',
               'repoze.sendmail',
               'repoze.tm2',
               'repoze.who >= 2.0dev',
               'repoze.zodbconn',
               'WebError',
               'zope.password',
               ],
      test_suite="cartouche.tests",
      entry_points = """\
      [paste.app_factory]
      main = cartouche:main
      [console_scripts]
      add_cartouche_admin = cartouche.admin:add_admin_user
      """,
      paster_plugins=['pyramid'],
)
