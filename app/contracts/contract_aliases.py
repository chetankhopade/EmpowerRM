import json
import time

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import bad_json, ok_json, datatable_handler, contract_audit_trails
from app.management.utilities.globals import addGlobalData

from erms.models import ContractAlias, Contract


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_aliases(request, contract_id):
    try:
        contract = Contract.objects.get(id=contract_id)
        queryset = contract.get_my_contract_aliases()
        search_fields = ['alias', ]
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def save(request, contract_id):
    """
        Update/Create aliases for Contract
    """
    data = {'title': 'Save ContractAlias'}
    addGlobalData(request, data)
    try:
        with transaction.atomic():
            contract = Contract.objects.get(id=contract_id)
            aliases = json.loads(request.POST['aliases'])
            existing_contracts = []
            for elem in aliases:
                try:
                    Contract.objects.get(number=elem['alias'])
                    existing_contracts.append(elem['alias'])
                except:
                    history_dict = {}
                    contract_alias = contract.get_my_contract_aliases().get(id=elem['id'])
                    history_dict['before'] = contract_alias.get_current_info_for_audit()
                    contract_alias.alias = elem['alias']
                    contract_alias.save()
                    history_dict['after'] = contract_alias.get_current_info_for_audit()

                    changed_items = [(k, history_dict['after'][k], v) for k, v in history_dict['before'].items() if history_dict['after'][k] != v]
                    if changed_items:
                        for elem in changed_items:
                            change_text = f"For Contract {contract.number} {elem[0]} is changed from {elem[2]} to {elem[1]}"
                            contract_audit_trails(contract=contract_id,
                                                  user_email=data['user'].email,
                                                  change_type='header',
                                                  field_name=elem[0],
                                                  change_text=change_text)
            time.sleep(0.5)
            # EA-1323 Dont allow the user to create a new alias or edit an existing alias with the existing contract number
            if existing_contracts:
                return ok_json(data={
                    'message': f'Following aliases already exist as Contract: {", ".join([x for x in existing_contracts])}',
                    'redirect_url': f"/{data['db_name']}/contracts/{contract_id}/details",
                    'error': 'y'})
            return ok_json(data={
                'message': 'Contract Aliases succesfully updated!',
                'redirect_url': f"/{data['db_name']}/contracts/{contract_id}/details",
                'error': 'n'
            })
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def remove(request, contract_id, contract_alias_id):
    """
        Remove Contract Alias
    """
    try:
        user = request.user
        with transaction.atomic():
            contract = Contract.objects.get(id=contract_id)
            aliasObj = ContractAlias.objects.get(id=contract_alias_id)
            # Audit
            change_text = f"For Contract {contract.number} alias {aliasObj.alias} has been removed"
            contract_audit_trails(contract=contract_id,
                                  user_email=user.email,
                                  change_type='header',
                                  field_name='alias',
                                  change_text=change_text)
            aliasObj.delete()
            return ok_json(data={'message': 'ContractAlias succesfully removed!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def add_new_aliases(request, contract_id):
    """
        Create new Aliases for Contract
    """
    try:
        user = request.user
        with transaction.atomic():
            contract = Contract.objects.get(id=contract_id)
            my_current_aliases_list = set(contract.get_my_contract_aliases().values_list('alias', flat=True))
            new_aliases = set([x['name'] for x in json.loads(request.POST['aliases'])])

            existing_aliases = list(my_current_aliases_list.intersection(new_aliases))
            if existing_aliases:
                return bad_json(message=f'Following aliases already exist: {", ".join([x for x in existing_aliases])}')

            existing_contracts = []
            for alias in list(new_aliases):
                try:
                  Contract.objects.get(number=alias)
                  existing_contracts.append(alias)
                except:
                    ContractAlias.objects.create(contract=contract, alias=alias)

                    # Audit
                    change_text = f"For Contract {contract.number} alias {alias} is added"
                    contract_audit_trails(contract=contract_id,
                                          user_email=user.email,
                                          change_type='header',
                                          field_name='alias',
                                          change_text=change_text)
            time.sleep(0.3)

            # EA-1323 Dont allow the user to create a new alias or edit an existing alias with the existing contract number
            if existing_contracts:
                return ok_json(data={'message': f'Following aliases already exist as Contract: {", ".join([x for x in existing_contracts])}', 'error': 'y'})
            return ok_json(data={'message': 'Aliases created and associated to Contract', 'error': 'n'})
    except Exception as ex:
        return bad_json(message=ex.__str__())
