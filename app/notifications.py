import time

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from empowerb.middleware import db_ctx
from erms.models import AuditTrail


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
        Notifications
    """
    entity = request.POST.get('entity', '')

    audits = None
    if entity:
        if entity == 'Contract':
            # check also items added to contract
            audits = AuditTrail.objects.filter(entity1_name='Item', entity2_name=entity)
        else:
            audits = AuditTrail.objects.filter(entity1_name=entity)

    html = render_to_string('notifications/audits.html', {'audits': audits, 'db_name': db_ctx.get()})
    return HttpResponse(html)
