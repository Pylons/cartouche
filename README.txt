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

- ``cartouche`` stores users, profiles, and groups in a ``ZODB`` database.

- ``cartouche`` uses ``zope.password`` to do password hashing / checking.

- ``cartouche`` plugs into ``repoze.who`` as an authenticator, a challenger,
  and a metadata provider.

Please see ``docs/index.rst`` for the documentation, which can also be
read online at:
 
 http://packages.python.org/cartouche
