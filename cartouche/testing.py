# Testing app / config
from repoze.sendmail.interfaces import IMailDelivery
from zope.interface import implements
from cartouche.interfaces import IPendingRegistrations

DIVIDER =  "#" * 80

class FauxMailDelivery(object):
    implements(IMailDelivery)

    def send(self, from_addr, to_addrs, message):
        print DIVIDER
        print 'From:    %s' % from_addr
        print 'To:      %s' % ', '.join(to_addrs)
        print '-' * 80
        print message
        print DIVIDER


class Dummy(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FauxPendingRegistrations(object):
    implements(IPendingRegistrations)
    _pending_store = {} # yes, a mutable default

    def __init__(self, context):
        pass


    def set(self, email, security_question, security_answer, token):
        print DIVIDER
        print 'Setting pending registration for email: %s' % email
        print DIVIDER
        info = Dummy(email=email,
                     security_question=security_question,
                     security_answer=security_answer,
                     token=token)
        self._pending_store[email] = info

    def get(self, email, default=None):
        return self._pending_store.get(email, default)
