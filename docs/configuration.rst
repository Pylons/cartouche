Configuring ``cartouche``
=========================

Views
+++++

By default, :mod:`cartouche` provides a stock set of :mod:`pyramid` views
for user registration, login / logout, password / account recovery, and
user administration:

.. code-block:: xml

   <configure xmlns="http://pylonshq.com/pyramid">

    <!-- this must be included for the view declarations to work -->
    <include package="pyramid.includes" />

    <view
        context="*"
        name="register.html"
        view="cartouche.registration.register_view"
        renderer="templates/register.pt"
        />

    <view
        context="*"
        name="confirm_registration.html"
        view="cartouche.registration.confirm_registration_view"
        renderer="templates/register.pt"
        />

    <view
        context="*"
        name="edit_account.html"
        view="cartouche.registration.edit_account_view"
        renderer="templates/register.pt"
        />

    <view
        context="*"
        name="login.html"
        view="cartouche.login.login_view"
        renderer="templates/login.pt"
        />

    <view
        context="*"
        name="recover_login.html"
        view="cartouche.login.recover_login_view"
        renderer="templates/login.pt"
        />

    <view
        context="*"
        name="recover_password.html"
        view="cartouche.login.recover_password_view"
        renderer="templates/login.pt"
        />

    <view
        context="*"
        name="logout.html"
        view="cartouche.login.logout_view"
        />

   </configure>


Replacing the "O-wrap"
----------------------

:mod:`cartouche` views are defined using the :mod:`chameleon` implementation
of Zope Page Templates.  The views expect to be wrapped in a "main template",
looked up using the standard :mod:`pyramid` :func:`get_renderer` API.  Your
application can replace that template using :mod:`pyramid` "template overrides".

E.g., via imperative Python code:

.. code-block:: python

   config.override_asset('cartouche:templates/main.pt',
                         'yourpackage:templates/cartouche_main.pt')

or via ZCML:

.. code-block:: xml

    <asset to_overide="cartouche:templates/main.pt"
           override_with="yourpackage:templates/cartouche_main.pt"/>


See http://docs.pylonshq.com/pyramid/dev/narr/assets.html#overriding-assets
for details on overriding templates as "assets".

The template used to override the :mod:`cartouche` main template must provide
a ``ZPT`` "slot" named ``main``, which will be filled by the :mod:`cartouche`
view templates.


Global settings
+++++++++++++++

Some policies can be configured as simple scalar values in the
global ``PasteDeploy`` configuration file:

.. code-block:: ini

   [app:yourapp]
   cartouche.from_addr = site-admin@example.com
   cartouche.after_confirmation_url = /thank_you_for_registering.html
   cartouche.auth_tkt_plugin_id = auth_tkt_id


``cartouche.from_addr``
    The e-mail address which is the ``From:`` address for e-mails sent
    to users about their site registration / account information. 
    **Required.**

``cartouche.after_confirmation_url``
    The URL to which users are redirected after successfully confirming
    their site registration.  If a relative URL, it will be prepended with
    the Pyramid site root URL.  *Default:  /edit_account.html*

``cartouche.auth_tkt_plugin_id``
    The ID of the ``auth_tkt`` plugin used to auto-login newly-registered
    users.  Used only if no utility is registered for the
    ``cartouche.interfaces.IAutoLogin`` interface.


Utilities
+++++++++

Some :mod:`cartouche` policies are configured as quasi-global "utilities"
(see http://docs.pylonshq.com/pyramid/dev/narr/zca.html).

The :class:`repoze.sendmail.IMailDelivery` utility
--------------------------------------------------

This utility is used to send emails for registration, account recovery,
and password reset.

By default, :mod:`cartouche` uses an implementation which expects to
connect to an MTA on port 25 of ``localhost``.

To implement your own auto-login utility, you must register a function
or a class which provides the :class:`repoze.sendmail.IMailDelivery` interface.

E.g., via imperative Python code:

.. code-block:: python

   from repoze.sendmail import IMailDelivery
   from yourpackage.mail import MailDelivery
   config.registerUtility(factory=MailDelivery, provided=IMailDelivery)

or ZCML:

.. code-block:: xml

   <utility
        provides="repoze.sendmail.IMailDelivery"
        factory="yourpackage.mail.MailDelivery"/>


The :class:`cartouche.interfaces.IAutoLogin` utility
----------------------------------------------------

This utility is used to log the user in automatically at the end of
registration.

By default, :mod:`cartouche` does *not* log the user in.  If you are using
:mod:`repoze.who`'s ``auth_tkt`` plugin, you may wish to configure
:func:`cartouche.registration.autoLoginViaAuthTkt` to enable this feature.

E.g., via imperative Python code:

.. code-block:: python

   from cartouche.interfaces import IAutoLogin
   from cartouche.registration import autoLoginViaAuthTkt
   config.registerUtility(autoLoginViaAuthTkt, IAutoLogin)
    
or ZCML:

.. code-block:: xml

   <utility
        provides="cartouche.interfaces.IAutoLogin"
        component="cartouche.registration.autoLoginViaAuthTkt"/>

To implement your own auto-login utility, you must register a function
providing the :class:`cartouche.interfaces.IAutoLogin` interface,
or a class whose instances provide it.

The :class:`cartouche.interfaces.ITokenGenerator` utility
---------------------------------------------------------

:mod:`cartouche` uses this utility generate random tokens for use in
registration confirmation and password reset e-mails, as well as to create
opaque / immutable IDs for users.

By default, :mod:`cartouche` uses an implementation which generates
random UUIDs using :func:`uuid.uuid4`.

To implement your own token generation utility, you must register a function
providing the :class:`cartouche.interfaces.ITokenGenerator` interface,
or a class whose instances provide it.

E.g., via imperative Python code:

.. code-block:: python

   from cartouche.interfaces import ITokenGenerator
   from yourpackage.utilities import myTokenGenerator
   config.registerUtility(myTokenGenerator, ITokenGenerator)
    
or ZCML:

.. code-block:: xml

   <utility
        provides="cartouche.interfaces.IAutoLogin"
        component="cartouche.registration.autoLoginViaAuthTkt"/>


Adapters
++++++++

Some :mod:`cartouche` policies are configured as "adapters" (see
http://docs.pylonshq.com/pyramid/dev/narr/zca.html).

Persistent Storage
-----------------

By default, :mod:`cartouche` expects to store information about users
in and attribute of the "traversal root" named ``cartouche``.  This strategy
is aimed at applications using traversal and :mod:`ZODB` or another
"transparent" persistence machinery.

To override this strategy, you must register two named adapters for the
"root" object of your routes / traversal, implementing the
:class:`cartouche.interfaces.IRegistrations` interface.

E.g., via imperative Python code:

.. code-block:: python

   from cartouche.interfaces import IRegistrations
   from yourpackage.userstore import PendingStore
   from yourpackage.userstore import ConfirmedStore
   config.registerAdapter(PendingStore, required=(None,),
                          provided=IRegistrations, name='pending')
   config.registerAdapter(ConfirmedStore, required=(None,),
                          provided=IRegistrations, name='confirmed')

or ZCML:

.. code-block:: xml

   <configure xmlns="http://pylonshq.com/pyramid">

    <!-- this must be included for the adapter declarations to work -->
    <include package="pyramid.includes" />

    <adapter
        provides="cartouche.interfaces.IRegistrations"
        name="pending"
        for="*"
        factory="yourpackage.userstore.PendingStore" />

    <adapter
        provides="cartouche.interfaces.IRegistrations"
        name="confirmed"
        for="*"
        factory="yourpackage.userstore.ConfirmedStore" />

   </configure>
