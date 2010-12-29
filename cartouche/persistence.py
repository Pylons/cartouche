from zope.interface import implements

from cartouche.interfaces import IRegistrations


class _RegistrationsBase(object):
    """ Default implementation for ZODB-based storage.

    Stores registration info in a BTree named 'pending', an attribute of the
    root object's 'cartouche' attribute.
    """
    implements(IRegistrations)

    def __init__(self, context):
        self.context = context

    def set(self, key, **kw):
        """ See IRegistrations.
        """
        info = self._makeInfo(key, **kw)
        cartouche = self._getCartouche(True)
        self._getMapping(cartouche)[key] = info

    def set_record(self, key, record):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche(True)
        self._getMapping(cartouche)[key] = record

    def get(self, key, default=None):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            return default
        return self._getMapping(cartouche).get(key, default)

    def remove(self, key):
        """ See IRegistrations.
        """
        cartouche = self._getCartouche()
        if cartouche is None:
            raise KeyError(key)
        del self._getMapping(cartouche)[key]

    def _getCartouche(self, create=False):
        # Import here to allow reuse of views without stock models.
        from pyramid.traversal import find_root
        from cartouche.models import Cartouche
        root = find_root(self.context)
        cartouche = getattr(root, 'cartouche', None)
        if cartouche is None and create:
            cartouche = root.cartouche = Cartouche()
        return cartouche

    def _getMapping(self, cartouche):
        return getattr(cartouche, self.ATTR)


class PendingRegistrations(_RegistrationsBase):
    ATTR = 'pending'

    def _makeInfo(self, key, **kw):
        # Import here to allow reuse of views without stock models.
        from cartouche.models import PendingRegistrationInfo as PRI
        token = kw['token']
        return PRI(email=key, token=token)


class ByEmailRegistrations(_RegistrationsBase):
    ATTR = 'by_email'

    def _makeInfo(self, key, **kw):
        # Import here to allow reuse of views without stock models.
        from cartouche.models import RegistrationInfo as RI
        login = kw.get('login', key)
        password = kw.get('password')
        security_question = kw.get('security_question')
        security_answer = kw.get('security_answer')
        return RI(email=key, login=login, password=password,
                  security_question=security_question,
                  security_answer=security_answer,
                 )


class ByLoginRegistrations(_RegistrationsBase):
    ATTR = 'by_login'

    def _makeInfo(self, key, **kw):
        # Import here to allow reuse of views without stock models.
        from cartouche.models import RegistrationInfo as RI
        email = kw.get('email', key)
        password = kw.get('password')
        security_question = kw.get('security_question')
        security_answer = kw.get('security_answer')
        return RI(email=email, login=key, password=password,
                  security_question=security_question,
                  security_answer=security_answer,
                 )
