import os
import sys

from pyramid.paster import bootstrap
import transaction


def main(argv=None):
    __doc__ = """ Make an existing cartouche user a member of the 'admin' group.

    Usage:  %s config_uri login
    """
    if argv is None:
        argv = sys.argv[1:]
    try:
        config_uri, login = sys.argv[1:]
    except:
        print __doc__ % sys.argv[0]
        sys.exit[2]

    ini_file = config_uri.split('#')[0]

    if not os.path.isfile(ini_file):
        print __doc__ % sys.argv[0]
        print
        print 'Invalid config file:', ini_file
        print
        sys.exit[2]

    env = bootstrap(config_uri)
    request, root = env['request'], env['root']
    confirmed = request.registry.queryAdapter(root, IRegistrations,
                                              name='confirmed')
    if confirmed is None:
        confirmed = ConfirmedRegistrations(root)

    info = confirmed.get_by_login(login)
    if info is None:
        print __doc__ % sys.argv[0]
        print
        print 'Invalid login:', login
        print
        sys.exit[2]

    admins = confirmed._getMapping('group_users').get('g:admin') or []
    if info.uuid not in admins:
        admins.append(info.uuid)
        confirmed._getMapping('group_users')['g:admin'] = admins
        groups = confirmed._getMapping('user_groups').get(info.uuid) or []
        groups.append('g:admin')
        confirmed._getMapping('user_groups')[info.uuid] = groups

    transaction.commit()
    env['closer']()

