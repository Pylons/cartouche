``cartouche`` README
====================

This package provides a set of applications which can be used to drive
"registration-based" sites:

- registration

- login / logout

- change password

- password recovery

- profile editing

- user / group administration


``cartouche`` is built on the following components:

- The ``cartouche`` applications run atop the ``pyramid`` framework, using
  ``chameleon`` for their templating, and ``deform`` for form schema /
  validation handling.

- ``cartouche`` stores users, profiles, and groups in a ``ZODB`` database
  (you can override this by registering adapters which use different
  persistence).

- ``cartouche`` uses ``zope.password`` to do password hashing / checking.

- ``cartouche`` plugs into ``repoze.who`` as an authenticator, a challenger,
  and a metadata provider.

- If your app doesn't use the ``repoze.who`` middleware, you can plug
  ``cartouche`` in as a ``pyramid`` "authentication policy (cartouche still
  uses the ``repoze.who`` API in this case).

Please see ``docs/index.rst`` for the documentation, which can also be
read online at:
 
 http://packages.python.org/cartouche


Quick Start
-----------

Install into your virtualenv::

  $ /path/to/virtualenv/bin/python setup.py develop

If you have a working MTA on localhost:25::

  $ /path/to/venv/bin/paster serve development.ini

If you don't have working MTA on localhost:25, the ``no_mail`` configuration
prints any sent mail to the console::

  $ /path/to/venv/bin/paster serve development.ini --app-name=no_mail
