
from pyramid.exceptions import HTTPNotFound
from pyramid.renderers import get_renderer

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
            'email': record.email,
            'password': record.password,
            'token': record.token,
            'security_question': record.security_question,
            'security_answer': record.security_answer,
           }
