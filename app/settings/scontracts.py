import json
import time

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import bad_json, ok_json, datatable_handler
from app.management.utilities.globals import addGlobalData

from ermm.models import ClassOfTrade as MasterClassOfTrade
from erms.models import ClassOfTrade


@login_required(redirect_field_name='ret', login_url='/login')
def copy_from_master(request):
    """
        Copy CoT data from master to local db
    """
    data = {'title': 'Copy CoT from Master'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():
            for master_cot in MasterClassOfTrade.objects.all():
                ClassOfTrade.objects.get_or_create(trade_class=master_cot.value, group=master_cot.group)
            return ok_json(data={'message': 'Local CoT content copied from master!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def save(request):
    """
        Save all CoT data from frontend
    """
    data = {'title': 'Save CoTs'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():

            cots = json.loads(request.POST['cots'])

            for elem in cots:
                cot_id = elem['id']
                cot_name = elem['name']
                cot_description = elem['description']
                cot_is_active = True if elem['enabled'] == 1 else False

                cot = ClassOfTrade.objects.get(id=cot_id)
                cot.trade_class = cot_name
                cot.description = cot_description
                cot.is_active = cot_is_active
                cot.save()

            time.sleep(0.3)
            return ok_json(data={'message': 'CoTs data have been succesfully saved!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def add_new_cots(request):
    """
        Create new CoTs items
    """
    data = {'title': 'New CoTs'}
    addGlobalData(request, data)
    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))
    try:
        with transaction.atomic():
            cots = json.loads(request.POST['cots'])
            for elem in cots:
                cot_name = elem['name']
                cot_description = elem['description']
                if ClassOfTrade.objects.filter(trade_class=cot_name).exists():
                    return bad_json(message=f'CoT already exist with the name: {cot_name}')
                ClassOfTrade.objects.create(trade_class=cot_name, description=cot_description)
            return ok_json(data={'message': 'CoTs have been succesfully addedd!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def remove(request, cot_id):
    """
        Remove CoT
    """
    data = {'title': 'Remove CoT'}
    addGlobalData(request, data)
    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))
    try:
        with transaction.atomic():
            cot = ClassOfTrade.objects.get(id=cot_id)
            cot.delete()
            return ok_json(data={'message': 'CoT succesfully removed!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:
        queryset = ClassOfTrade.objects.order_by('trade_class')
        search_fields = ['trade_class', 'description']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)
    except Exception as ex:
        return bad_json(message=ex.__str__())
