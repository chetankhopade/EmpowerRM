import datetime

import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status

from app.management.utilities.functions import convert_timestamp_to_datetime, ok_json, bad_json
from app.management.utilities.globals import addGlobalData
from empowerb.settings import EDI_API_URL, EDI_API_TOKEN
from ermm.models import Company
from erms.models import DirectCustomer, ChargeBack


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'Administration - Service Status', 'header_title': 'Administration > Service Status'}
    addGlobalData(request, data)

    data['menu_option'] = 'menu_administration_service_status'
    return render(request, "administration/service_status/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_count_of_open_cbs_by_partner(request):
    try:
        database = Company.objects.get(id=request.GET['cid']).database
        direct_customer = DirectCustomer.objects.using(database).get(account_number=request.GET['accno'])
        count_of_cbs = ChargeBack.objects.using(database).filter(customer_id=direct_customer.id).count()
        return ok_json(data={'data': count_of_cbs})
    except Exception as ex:
        return ok_json(data={'data': 0})


def get_parser_activity_from_edi_api(request):
    data = {'title': 'Administration - Get Parser Activity Data'}
    addGlobalData(request, data)

    try:
        response = requests.get(f"{EDI_API_URL}/parser_activity", params={'token': EDI_API_TOKEN})
        if response.status_code == status.HTTP_200_OK:
            return ok_json(data={'items': response.json()})
        return bad_json(message=f'Error getting parser activity data. Status Code: {response.status_code}')

    except Exception:
        return bad_json(message='ConnectionError: API is not working')


def get_last_inbound_transaction_from_edi_api(request):
    data = {'title': 'Administration - Get Last Inbound Transaction'}
    addGlobalData(request, data)

    try:
        response = requests.get(f"{EDI_API_URL}/last_inbound_transaction", params={'token': EDI_API_TOKEN})
        if response.status_code == status.HTTP_200_OK:
            obj = response.json()
            last_file_received_timestamp = convert_timestamp_to_datetime(obj['created_at'])
            return ok_json(data={
                'last_file_received_timestamp': last_file_received_timestamp.strftime("%Y/%m/%d %H:%m"),
                'last_file_received_timestamp_older_than_4hrs': (datetime.datetime.now() - last_file_received_timestamp).seconds > 14400  # 4hrs
            })
        return bad_json(message=f'Error getting last inbound transaction. Status Code: {response.status_code}')

    except Exception:
        return bad_json(message='ConnectionError: API is not working')


def get_last_outbound_transaction_from_edi_api(request):
    data = {'title': 'Administration - Get Last Outbound Transaction'}
    addGlobalData(request, data)

    try:
        response = requests.get(f"{EDI_API_URL}/last_outbound_transaction", params={'token': EDI_API_TOKEN})
        if response.status_code == status.HTTP_200_OK:
            obj = response.json()
            last_file_sent_timestamp = convert_timestamp_to_datetime(obj['created_at'])
            return ok_json(data={
                'last_file_sent_timestamp': last_file_sent_timestamp.strftime("%Y/%m/%d %H:%m"),
                'last_file_sent_timestamp_older_than_4hrs': (datetime.datetime.now() - last_file_sent_timestamp).seconds > 14400
            })
        return bad_json(message=f'Error getting last outbound transaction. Status Code: {response.status_code}')

    except Exception:
        return bad_json(message='ConnectionError: API is not working')
