import os
import sys

from pyramid.exceptions import HTTPNotFound
from pyramid.renderers import get_renderer
from pyramid.paster import bootstrap
import transaction

from cartouche.interfaces import IRegistrations
from cartouche.persistence import ConfirmedRegistrations
from cartouche.persistence import PendingRegistrations

def admin_overview(context, request):
    pending = request.registry.queryAdapter(context, IRegistrations,
                                            name='pending')
    if pending is None:
        pending = PendingRegistrations(context)

    confirmed = request.registry.queryAdapter(context, IRegistrations,
                                              name='confirmed')
    if confirmed is None:
        confirmed = ConfirmedRegistrations(context)

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'pending': sorted(pending),
            'confirmed': sorted(confirmed),
           }


def admin_pending(context, request):
    # Edit one pending registration
    pending = request.registry.queryAdapter(context, IRegistrations,
                                            name='pending')
    if pending is None:
        pending = PendingRegistrations(context)
    email = request.params['pending']
    record = pending.get(email)
    if record is None:
        return HTTPNotFound()
    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'page_title': 'Edit Pending Registration',
            'email': email,
            'token': record.token,
           }


def admin_confirmed(context, request):
    # Edit one pending registration
    confirmed = request.registry.queryAdapter(context, IRegistrations,
                                              name='confirmed')
    if confirmed is None:
        confirmed = ConfirmedRegistrations(context)

    login = request.params['confirmed']
    record = confirmed.get_by_login(login)
    if record is None:
        return HTTPNotFound()

    main_template = get_renderer('templates/main.pt')
    return {'main_template': main_template.implementation(),
            'page_title': 'Edit Confirmed Registration',
            'login': login,
            'uuid': record.uuid,
            'password': record.password,
            'token': record.token,
            'security_question': record.security_question,
            'security_answer': record.security_answer,
           }


def add_admin_user():
    __doc__ = """ Make an existing cartouche user a member of the 'admin' group.

    Usage:  %s config_uri login
    """
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
