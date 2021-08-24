from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse

from app.management.utilities.constants import INTEGRATION_SYSTEM_ACUMATICA_ID, INTEGRATION_SYSTEM_QUICKBOOKS_ID, \
    INTEGRATION_SYSTEM_DYNAMICS365_ID
from app.management.utilities.functions import ok_json, bad_json
from app.management.utilities.globals import addGlobalData
from ermm.models import IntegrationSystem


@login_required(redirect_field_name='ret', login_url='/login')
def update_integration_system(request):
    """
        Update Integration System for the Company
    """
    data = {'title': 'Update Integration System'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():

            integration_config = None
            integration_system_id = request.POST['integration_system_id']

            # acumatica
            if integration_system_id == INTEGRATION_SYSTEM_ACUMATICA_ID:
                integration_config = {
                    'base_url': request.POST['acc_base_url'],
                    'auth': {
                        'username': request.POST['acc_username'],
                        'password': request.POST['acc_password'],
                        'company':  request.POST['acc_company_name'],
                        'branch':   request.POST['acc_branch']
                    }
                }

            # quickbooks
            if integration_system_id == INTEGRATION_SYSTEM_QUICKBOOKS_ID:
                qb_path = request.POST['qb_path']
                integration_config = {
                    'qb_path': qb_path,
                }
                # update QBConfig obj for that company and path field
                qb_config = data['company'].get_my_quickbooks_configuration()
                qb_config.path = qb_path
                qb_config.save()

            # dynamics365
            if integration_system_id == INTEGRATION_SYSTEM_DYNAMICS365_ID:
                integration_config = {
                    'login_url': request.POST['ds365_login_url'],
                    'resource_url': request.POST['ds365_resource_url'],
                    'client_id': request.POST['ds365_client_id'],
                    'client_secret': request.POST['ds365_client_secret'],
                }

            data['company'].integration_system_id = integration_system_id
            data['company'].integration_config = integration_config
            data['company'].save()

            return ok_json(data={'message': 'Integration system updated!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())
