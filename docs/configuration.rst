Configuring ``cartouche``
=========================

Views
+++++

Default Configuration
---------------------

You can include the default :mod:`cartouche` view configuration, either
directly via imperative Python code:

.. code-block:: python

   config.load_zcml('cartouche:configure.zcml')

or via ZCML in your package:

.. code-block:: xml

   <configure xmlns="http://pylonshq.com/pyramid">

    <!-- this must be included for the view declarations to work -->
    <include package="pyramid.includes"/>

    <include package="cartouche"/>

   </configure>

Either way, the following views get registered:

``/register.html``
    Renders a form to collect the user's e-mail address.  On POST,
    generates and saves a token for the user in the "pending" store,
    and sends the user a confirmation e-mail including the token, then
    redirects to ``/confirm_registration.html``.

``/confirm_registration.html``
    Renders a form to collect the token mailed to the user, along with
    user's e-mail address.  On POST, moves the registration information
    for the user to the "confirmed" store under a unique, opaque ID,
    then redirects to ``/edit_account.html``.

``/edit_account.html``
    Allows the user to update their login name and e-mail, as well as
    setting their own password and security question / answer.  If the user
    already has a password set, requires that it be supplied.

``/login.html``
    Prompts the user for login name and password.  On POST, if provided
    values match, uses the :mod:`repoze.who` API to "remember" the user.

``/logout.html``
    Uses the :mod:`repoze.who` API to "forget" the user.

``/recover_login.html``
    Prompts the user for their e-mail address.  On POST, sends the user an
    e-mail reminding them of their login name, and redirects to
    ``/login.html``.

``/reset_pasword.html``
    Prompts the user for their login name, token, and new password.  On POST
    without a token, generates and saves a token for the user, and sends
    the user a confirmation e-mail containing the token.  On POST with a
    matching token, saves the supplied password for the user and redirects
    to ``/login.html``.


Overriding the View Configuration
---------------------------------

To override the stock configuration (e.g., to change the view names,
provide your own view implementations, etc.), copy the stock ZCML file into
your own package and tweak it.  E.g.:

.. code-block:: sh

   $ cp $cartouche_egg/cartouche/configure.zcml yourpackage/cartouche.zcml

Then include the tweaked version instead of the stock version, either via
imperative Python code:

.. code-block:: python

   config.load_zcml('yourpackage:cartouche.zcml')

or via ZCML in your package:

.. code-block:: xml

   <configure xmlns="http://pylonshq.com/pyramid">

    <!-- this must be included for the view declarations to work -->
    <include package="pyramid.includes"/>

    <include file="cartouche.zcml"/>

   </configure>

.. note::

   If you change the view names, you need to configure the new URLs into
   :mod:`cartouche` using :ref:`global_settings`.

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

    <asset to_override="cartouche:templates/main.pt"
           override_with="yourpackage:templates/cartouche_main.pt"/>


See http://docs.pylonshq.com/pyramid/dev/narr/assets.html#overriding-assets
for details on overriding templates as "assets".

The template used to override the :mod:`cartouche` main template must provide
a ``ZPT slot`` " named ``main``, which will be filled by the :mod:`cartouche`
view templates.

.. _global_settings:

Global Settings
+++++++++++++++

Some policies can be configured as simple scalar values in the
global ``PasteDeploy`` configuration file:

.. code-block:: ini

   [app:yourapp]
   cartouche.from_addr = site-admin@example.com
   cartouche.register_url = /site_registration.html
   cartouche.confirmation_url = /confirm.html
   cartouche.after_confirmation_url = /thank_you_for_registering.html
   cartouche.after_edit_url = /after_account_edit.html
   cartouche.login_url = /site_login.html
   cartouche.recover_account_url = /account_recovery.html
   cartouche.reset_password_url = /password_reset.html
   cartouche.auto_login_identifier = auth_tkt_id


``cartouche.from_addr``
    The e-mail address which is the ``From:`` address for e-mails sent
    to users about their site registration / account information. 
    **Required.**

``cartouche.register_url``
    The URL to which users are redirected to start the registration
    process.  If a relative URL, it will be prepended with
    the Pyramid site root URL.  *Default:  /register.html*

``cartouche.confirmation_url``
    The URL to which users are redirected after starting the registration
    process.  If a relative URL, it will be prepended with
    the Pyramid site root URL.  *Default:  /confirm_registration.html*

``cartouche.after_confirmation_url``
    The URL to which users are redirected after successfully confirming
    their site registration.  If a relative URL, it will be prepended with
    the Pyramid site root URL.  *Default:  /edit_account.html*

``cartouche.after_edit_url``
    The URL to which users are redirected after successfully editing
    their accout.  If a relative URL, it will be prepended with
    the Pyramid site root URL.  *Default:  /edit_account.html*

``cartouche.login_url``
    The URL of the login form.  Users are redirected here after recovering
    the login name for their accounts.  If a relative URL, it will be
    prepended with the Pyramid site root URL.  *Default:  /login.html*

``cartouche.recover_account_url``
    The URL to which users are directed for recovering the login name
    for their accounts.  If a relative URL, it will be prepended with the
    Pyramid site root URL.  *Default:  /recover_account.html*

``cartouche.reset_password_url``
    The URL to which users are directed to reset their passwords.
    If a relative URL, it will be prepended with the Pyramid site root URL.
    *Default:  /reset_password.html*

``cartouche.after_reset_url``
    The URL to which users are directed after resetting their passwords.
    If a relative URL, it will be prepended with the Pyramid site root URL.
    *Default:  /edit_account.html (only useful if a utility is configured
    for the :class:`cartouche.interfaces.IAutoLogin` interface)*

``cartouche.auto_login_identifier``
    The ID of the ``repoze.who`` authenticator plugin used to auto-login
    users after the confirm registration or password reset via an e-mailed
    token.  Used only by the :func:`cartouche.util.autoLoginViaWhoAPI`
    utility, registered for the :class:`cartouche.interfaces.IAutoLogin`
    interface.  *Default:  auth_tkt*


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

To implement your own mail delivery utility, you must register a function
or a class which provides the :class:`repoze.sendmail.IMailDelivery` interface.

E.g., via imperative Python code:

.. code-block:: python

   from repoze.sendmail import IMailDelivery
   from yourpackage.mail import CustomMailDelivery
   config.registerUtility(factory=CustomMailDelivery, provided=IMailDelivery)

or ZCML:

.. code-block:: xml

   <utility
        provides="repoze.sendmail.IMailDelivery"
        factory="yourpackage.mail.CustomMailDelivery"/>


The :class:`cartouche.interfaces.IAutoLogin` utility
----------------------------------------------------

This utility is used to log the user in automatically after confirming a
registration or password reset token.

By default, :mod:`cartouche` does *not* log the user in;  instead, it e-mails
the user a random password.  If you are using :mod:`repoze.who`, you may wish
to configure :func:`cartouche.util.autoLoginViaWhoAPI` to enable this
feature.

E.g., via imperative Python code:

.. code-block:: python

   from cartouche.interfaces import IAutoLogin
   from cartouche.util import autoLoginViaWhoAPI
   config.registerUtility(autoLoginViaWhoAPI, IAutoLogin)
    
or ZCML:

.. code-block:: xml

   <utility
        provides="cartouche.interfaces.IAutoLogin"
        component="cartouche.util.autoLoginViaWhoAPI"/>

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
        component="yourpackage.utilities.myTokenGenerator"/>


Adapters
++++++++

Some :mod:`cartouche` policies are configured as "adapters" (see
http://docs.pylonshq.com/pyramid/dev/narr/zca.html).

Persistent Storage
------------------

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
    <include package="pyramid.includes"/>

    <adapter
        provides="cartouche.interfaces.IRegistrations"
        name="pending"
        for="*"
        factory="yourpackage.userstore.PendingStore"/>

    <adapter
        provides="cartouche.interfaces.IRegistrations"
        name="confirmed"
        for="*"
        factory="yourpackage.userstore.ConfirmedStore"/>

   </configure>
