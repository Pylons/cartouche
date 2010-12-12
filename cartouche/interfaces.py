from zope.interface import Interface

class ITokenGenerator(Interface):
    """ Utility interface:  generate tokens for confirmation e-mails.
    """
    def getToken():
        """ Return a unique, quasi-random token as a string.
        """
