# Testing app / config

from pyramid.renderers import get_renderer
from repoze.sendmail.interfaces import IMailDelivery
from zope.interface import implementer
from zope.password.password import SSHAPasswordManager

from cartouche.interfaces import IRegistrations

DIVIDER =  "#" * 80

@implementer(IMailDelivery)
class FauxMailDelivery(object):

    def send(self, from_addr, to_addrs, message):
        print(DIVIDER)
        print('From:    %s' % from_addr)
        print('To:      %s' % ', '.join(to_addrs))
        print('-' * 80)
        print(message)
        print(DIVIDER)


class Dummy(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

def _factory(_make_info):
    @implementer(IRegistrations)
    class FauxRegistrations(object):
        _store = {} # yes, a mutable default

        def __init__(self, context):
            pass

        def set(self, key, **kw):
            try:
                self.remove(key)
            except KeyError:
                pass
            print(DIVIDER)
            print('Setting registration for key: %s' % key)
            info = _make_info(key, kw)
            self._store[key] = info
            login = kw.get('login')
            if login is not None:
                print('-' * 80)
                print('login:', login)
                self._store[login] = key
            email = kw.get('email')
            if email is not None:
                print('-' * 80)
                print('email:', email)
                self._store[email] = key
            print(DIVIDER)

        def get(self, key, default=None):
            return self._store.get(key, default)

        def get_by_login(self, login, default=None):
            key = self._store.get(login)
            if key is None:
                return default
            return self._store.get(key, default)

        def get_by_email(self, email, default=None):
            key = self._store.get(email)
            if key is None:
                return default
            return self._store.get(key, default)

        def remove(self, key, default=None):
            old_info = self._store.get(key)
            if old_info is not None:
                print(DIVIDER)
                print('Removing registration for key: %s' % key)
                print(DIVIDER)
                del self._store[key]
                login = getattr(old_info, 'login', None)
                if login is not None and login in self._store:
                    del self._store[login]
                email = getattr(old_info, 'email', None)
                if email is not None and email in self._store:
                    del self._store[email]

        def __iter__(self):
            return iter(self._store.items())

    return FauxRegistrations


def _make_pending(key, kw):
    token = kw['token']
    return Dummy(email=key, token=token)


def _make_confirmed(key, kw):
    email = kw.get('email')
    login = kw.get('login', email)
    password = kw.get('password')
    question = kw.get('security_question')
    answer = kw.get('security_answer')
    token = kw.get('token')
    return Dummy(uuid=key, email=email, login=login, password=password,
                 security_question=question, security_answer=answer,
                 token=token)


FauxPendingRegistrations = _factory(_make_pending)
FauxConfirmedRegistrations = _factory(_make_confirmed)
FauxByLoginRegistrations = _factory(_make_confirmed)


class FauxAuthentication(object):
    def authenticate(self, environ, identity):
        try:
            login = identity['login']
            password = identity['password']
        except KeyError:
            return None
        pwd_mgr = SSHAPasswordManager()
        record = FauxConfirmedRegistrations(None).get_by_login(login)
        if (record is not None and
            pwd_mgr.checkPassword(record.password, password)):
            return record.uuid


def homepage_view(context, request):
    confirmed = request.registry.queryAdapter(context, IRegistrations,
                                              name='confirmed')
    if confirmed is None:
        confirmed = FauxConfirmedRegistrations(context)
    identity = request.environ.get('repoze.who.identity')
    authenticated_user = login_name = email = None
    if identity is not None:
        authenticated_user = identity['repoze.who.userid']
        account_info = confirmed.get(authenticated_user) 
        if account_info is None:
            authenticated_user = login_name = email = None
        else:
            login_name = account_info.login
            email = account_info.email
    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'authenticated_user': authenticated_user,
            'login_name': login_name,
            'email': email,
           }

def debug_view(context, request):
    pending = request.registry.queryAdapter(context, IRegistrations,
                                            name='pending')
    if pending is None:
        pending = FauxPendingRegistrations(context)
    confirmed = request.registry.queryAdapter(context, IRegistrations,
                                              name='confirmed')
    if confirmed is None:
        confirmed = FauxConfirmedRegistrations(context)
    identity = request.environ.get('repoze.who.identity')
    authenticated_user = login_name = email = None
    if identity is not None:
        authenticated_user = identity['repoze.who.userid']
        account_info = confirmed.get(authenticated_user) 
        if account_info is None:
            authenticated_user = login_name = email = None
        else:
            login_name = account_info.login
            email = account_info.email
    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'authenticated_user': authenticated_user,
            'login_name': login_name,
            'email': email,
            'pending': sorted(pending),
            'confirmed': sorted(confirmed),
           }
