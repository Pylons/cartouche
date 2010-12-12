from pyramid.configuration import Configurator
from repoze.zodbconn.finder import PersistentApplicationFinder


def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        from cartouche.models import Root
        app_root = Root()
        zodb_root['app_root'] = app_root
        import transaction
        transaction.commit()
    return zodb_root['app_root']


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    zodb_uri = settings.get('zodb_uri')
    zcml_file = settings.get('configure_zcml', 'configure.zcml')
    if zodb_uri is None:
        raise ValueError("No 'zodb_uri' in application configuration.")

    finder = PersistentApplicationFinder(zodb_uri, appmaker)
    def get_root(request):
        return finder(request.environ)
    config = Configurator(root_factory=get_root, settings=settings)
    config.load_zcml(zcml_file)
    return config.make_wsgi_app()
