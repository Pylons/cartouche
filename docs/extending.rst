Extending :mod:`cartouche`
==========================

By default, :mod:`cartouche` stores its pending and confirmed
registrations on the ``cartouche`` attribute of the :mod:``pyramid``
"root object".  This policy is implemented in two adapters registered
in the ``homepage.zcml`` example configuration:

- :class:`cartouche.persistence.PendingRegistrations` is registered as
  the adapter for the root object for the interface,
  :class:`cartouche.interfaces.IRegistrations`, with name ``pending``.

- :class:`cartouche.persistence.ConfirmedRegistrations` is registered as
  the adapter for the root object for the interface,
  :class:`cartouche.interfaces.IRegistrations`, with name ``confirmed``.
