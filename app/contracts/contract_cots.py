import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import bad_json, ok_json, datatable_handler
from app.management.utilities.globals import addGlobalData
from erms.models import ClassOfTrade, ContractCoT


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_active_cots(request, contract_id):
    try:
        queryset = ClassOfTrade.objects.filter(is_active=True).order_by('trade_class')
        search_fields = ['trade_class', 'description']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, contract_id=contract_id)
        return JsonResponse(response)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def save(request, contract_id):
    """
        Save relation with Contract anc CoT
    """
    try:
        with transaction.atomic():
            # get cots elements
            cots = json.loads(request.POST['cots'])
            for elem in cots:
                cot_id = elem['id']
                cot_name = elem['name']
                cot_description = elem['description']
                cot_is_assigned = True if elem['enabled'] == 1 else False

                cot = ClassOfTrade.objects.get(id=cot_id)
                cot.trade_class = cot_name
                cot.description = cot_description
                cot.save()

                if cot_is_assigned:
                    ContractCoT.objects.get_or_create(contract_id=contract_id, cot_id=cot_id)
                else:
                    ContractCoT.objects.filter(contract_id=contract_id, cot_id=cot_id).delete()

            return ok_json(data={'message': 'Contract and CoTs succesfully updated!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def remove(request, contract_id, cot_id):
    """
        Remove CoT action
    """
    data = {'title': 'Remove CoT'}
    addGlobalData(request, data)
    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))
    try:
        with transaction.atomic():
            ContractCoT.objects.filter(contract_id=contract_id, cot_id=cot_id).delete()
            ClassOfTrade.objects.get(id=cot_id).delete()
            return ok_json(data={'message': 'CoT succesfully removed!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def add_new_cots(request, contract_id):
    """
        Create new CoTs items and relate with Contract
    """
    try:
        with transaction.atomic():
            cots = json.loads(request.POST['cots'])
            for elem in cots:
                cot_name = elem['name']
                cot_description = elem['description']
                if ClassOfTrade.objects.filter(trade_class=cot_name).exists():
                    return bad_json(message=f'CoT already exist with the name: {cot_name}')
                cot = ClassOfTrade.objects.create(trade_class=cot_name, description=cot_description)
                ContractCoT.objects.create(contract_id=contract_id, cot_id=cot.get_id_str())
            return ok_json(data={'message': 'CoT created and associated with Contract'})
    except Exception as ex:
        return bad_json(message=ex.__str__())
