Using :mod:`cartouche` in :mod:`pyramid` without :mod:`repoze.who`
==================================================================

If you are not using :mod:`repoze.who` in your :mod:`pyramid` application,
you can still use the :mod:`cartouche` authentication machinery
by registering a custom "authentication policy".  The policy object
implements the ``pyramid.interfaces.IAuthenticationPolicy`` interface,
allowing :mod:`pyramid` to authenticate users, as well as remembering /
forgetting user credentials.

The policy object uses two pieces of configuration data:

``config_file``
    The path to a :mod:``repoze.who``-style INI file, configuring
    the plugins which implement the :mod:``repoze.who`` API.

``identifier_name``
    A string nameing the "identifier" plugin used when "remembering"
    user credentials.


To register this polcy via imperative Python code with the :mod:`pyramid`
configurator:

.. code-block:: python

   from cartouche.pyramidpolicy import PyramidPolicy

   policy = PyramidPolicy('/path/to/config_file', 'identifier')
   configurator._set_authentication_policy(policy)

To register the policy via ZCML, you need to include the ``meta.zcml``
file which defines the 

.. code-block:: xml

   <configure xmlns="http://pylonshq.com/pyramid">
    <include package="cartouche" file="meta.zcml" />

    <cartoucheauthenticationpolicy
      config_file="/path/to/config_file"
      identifier_name="identifier" />

   </configure>
