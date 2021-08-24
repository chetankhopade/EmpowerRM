import os

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.globals import addGlobalData
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_849_ERM_OUT

from app.management.utilities.functions import bad_json, ok_json
from erms.models import (DirectCustomer)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def update_edi_option(request):
    """
        Settings EDI - Update 844, 849, 852, 867 enabled (EDI option) for Direct Customers
    """
    try:
        with transaction.atomic():

            direct_customer = DirectCustomer.objects.get(id=request.POST['dcid'])
            option = request.POST['opt']
            value = True if int(request.POST['value']) == 1 else False

            if option == '844_enabled':
                direct_customer.enabled_844 = value
                direct_customer.save()

            if option == '849_enabled':
                direct_customer.enabled_849 = value
                direct_customer.save()

                # Ticket EA-730
                if not direct_customer.enabled_849:
                    # If 849 is disabled imported CBs from that DC are marked as Manual (is_received_edi = false)
                    direct_customer.get_my_chargebacks().update(is_received_edi=False)
                else:
                    # If 849 is enabled
                    # imported CBs from that DC are marked is_received_edi = True, including manually created CBs
                    direct_customer.get_my_chargebacks().update(is_received_edi=True)

            if option == '852_enabled':
                direct_customer.enabled_852 = value
                direct_customer.save()

            if option == '867_enabled':
                direct_customer.enabled_867 = value
                direct_customer.save()

            if option == 'nocredit':
                direct_customer.nocredit = value
                direct_customer.save()

            return ok_json(data={'message': f'{direct_customer.name.capitalize()} {option} updated'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def all_outbound_folder(request):
    """
        Settings EDI - Update 844 and 849 enabled (EDI option) for Direct Customers
    """
    data = {'title': 'Company Settings - All Outbound Folder'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():

            dc = DirectCustomer.objects.get(id=request.POST['dcid'])

            # ticket EA-1382 Create the folder if it does not exist in the company folder
            dc.all_outbound_folder = request.POST.get('value', '')
            dc.save()

            if dc.all_outbound_folder:
                path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{data['company'].get_id_str()}", f"{dc.all_outbound_folder}")
                if not os.path.exists(path):
                    os.makedirs(path)

            return ok_json(data={'message': f'All Outbound Folder updated for customer: {dc.name.capitalize()}'})

    except Exception as ex:
        return bad_json(message=ex.__str__())
