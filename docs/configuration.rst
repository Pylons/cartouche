Configuring ``cartouche``
=========================

Views
+++++


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
        name="welcome.html"
        view="cartouche.registration.welcome_view"
        renderer="templates/welcome.pt"
        />

    <view
        context="*"
        name="login.html"
        view="cartouche.login.login_view"
        renderer="templates/login.pt"
    />

   </configure>

Policies
++++++++

The stock ``cartouche`` views can be configured along a number of different
axes.


Global settings
---------------

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
---------

Some policies are configured as quasi-global "utilities" (see
http://docs.pylonshq.com/pyramid/dev/narr/zca.html).

.. code-block:: xml

   <configure xmlns="http://pylonshq.com/pyramid">

    <!-- this must be included for the view declarations to work -->
    <include package="pyramid.includes" />

    <utility
        provides="repoze.sendmail.interfaces.IMailDelivery"
        factory="yourpackage.mail.MailDelivery"
        />

    <utility
        provides="cartouche.interfaces.IAutoLogin"
        factory="yourpackage.login.AutoLogin"
        />

    <utility
        provides="cartouche.interfaces.ITokenGenerator"
        factory="yourpackage.tokens.TokenGenerator"
        />

   </configure>


Adapters
--------

Some policies are configured as "adapters" (see
http://docs.pylonshq.com/pyramid/dev/narr/zca.html).

.. code-block:: xml

   <configure xmlns="http://pylonshq.com/pyramid">

    <!-- this must be included for the view declarations to work -->
    <include package="pyramid.includes" />

    <adapter
        provides="cartouche.interfaces.IRegistrations"
        name="pending"
        for="*"
        factory="yourpackage.registration.PendingRegistrations" />

    <adapter
        provides="cartouche.interfaces.IRegistrations"
        name="by_email"
        for="*"
        factory="yourpackage.registration.ByEmailRegistrations" />

    <adapter
        provides="cartouche.interfaces.IRegistrations"
        name="by_login"
        for="*"
        factory="yourpackage.registration.ByLoginRegistrations" />

   </configure>
