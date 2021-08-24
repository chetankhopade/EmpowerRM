import datetime
import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (STATUS_ACTIVE, STATUS_PENDING, STATUS_INACTIVE, GLOBAL_CUSTOMER_ABC_ID,
                                                GLOBAL_CUSTOMER_CAR_ID, GLOBAL_CUSTOMER_MCK_ID,
                                                AUDIT_TRAIL_ACTION_ADDED, STATUS_PROPOSED)
from app.management.utilities.functions import (bad_json, convert_string_to_date, ok_json,
                                                datatable_handler, audit_trail, get_ip_address, contract_audit_trails)
from app.management.utilities.globals import addGlobalData
from erms.models import Contract, DirectCustomer, ContractCustomer


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request, contract_id):
    try:
        # Get Contract and DirectCustomers (Servers) thru ContractCustomer relationship
        contract = Contract.objects.get(id=contract_id)
        queryset = contract.get_my_servers_to_manage().filter(contract_id=contract_id)

        # query by status
        q = int(request.POST.get('q', 0))
        if q:
            if q == STATUS_ACTIVE:
                queryset = queryset.filter(status=STATUS_ACTIVE).distinct()
            elif q == STATUS_INACTIVE:
                queryset = queryset.filter(status=STATUS_INACTIVE).distinct()
            elif q == STATUS_PROPOSED:
                queryset = queryset.filter(status=STATUS_PROPOSED).distinct()
            else:
                queryset = queryset.filter(status=STATUS_PENDING).distinct()

        search_fields = ['name']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_servers_list(request, contract_id):
    data = {'title': 'Get Servers List'}
    addGlobalData(request, data)

    # Get Contract
    contract = Contract.objects.get(id=contract_id)

    # Direct Customers
    direct_customers = DirectCustomer.objects.all()

    direct_customers_big3_ids_list = []
    if direct_customers.filter(customer_id=GLOBAL_CUSTOMER_ABC_ID).exists():
        direct_customers_big3_ids_list.append(direct_customers.filter(customer_id=GLOBAL_CUSTOMER_ABC_ID)[0].get_id_str())

    if direct_customers.filter(customer_id=GLOBAL_CUSTOMER_CAR_ID).exists():
        direct_customers_big3_ids_list.append(direct_customers.filter(customer_id=GLOBAL_CUSTOMER_CAR_ID)[0].get_id_str())

    if direct_customers.filter(customer_id=GLOBAL_CUSTOMER_MCK_ID).exists():
        direct_customers_big3_ids_list.append(direct_customers.filter(customer_id=GLOBAL_CUSTOMER_MCK_ID)[0].get_id_str())

    data['direct_customers_big3_ids_list'] = direct_customers_big3_ids_list
    data['direct_customers'] = direct_customers
    data['contract'] = contract

    data['menu_option'] = 'menu_contracts'
    return render(request, "contracts/includes/manage_servers_list.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def update_servers_list(request, contract_id):

    try:
        user = request.user
        with transaction.atomic():
            # Get Contract
            contract = Contract.objects.get(id=contract_id)

            contract_start_date = contract.start_date
            contract_end_date = contract.end_date

            # Contract Lines (with changed prices)
            servers_list = json.loads(request.POST['servers_list'])
            if servers_list:
                # delete all current relations to create again
                ContractCustomer.objects.filter(contract=contract).delete()
                # loop over all checked elements in the list and create relationship with the Contract
                for elem in servers_list:
                    today = datetime.datetime.now().date()
                    customer_id = elem['cid']
                    start_date = convert_string_to_date(elem['start_date'])
                    end_date = convert_string_to_date(elem['end_date'])

                    # EA-1054 - When adding a server to a contract only show Wholesalers/Distributors on the list
                    if start_date < contract_start_date or end_date > contract_end_date:
                        return bad_json(message=f'Dates are out of contract range {contract_start_date} to {contract_end_date}')

                    if today < start_date:
                        new_status = STATUS_PENDING
                    elif today > end_date:
                        new_status = STATUS_INACTIVE
                    else:
                        new_status = STATUS_ACTIVE

                    # create ManageServer instance
                    manage_server = ContractCustomer(contract=contract,
                                                     customer_id=customer_id,
                                                     start_date=start_date,
                                                     end_date=end_date,
                                                     status=new_status)
                    manage_server.save()

                    change_text = f"For Contract {contract.number } new server {manage_server.customer.name} with dates {start_date.strftime('%m/%d/%Y') if start_date else ''} - {end_date.strftime('%m/%d/%Y') if end_date else ''} is added"
                    contract_audit_trails(contract=contract.id,
                                          user_email=user.email,
                                          change_type='server',
                                          field_name='',
                                          change_text=change_text)

                    # Audit Trail
                    # audit_trail(username=request.user.username,
                    #             action=AUDIT_TRAIL_ACTION_ADDED,
                    #             ip_address=get_ip_address(request),
                    #             entity1_name=manage_server.__class__.__name__,
                    #             entity1_id=manage_server.get_id_str(),
                    #             entity1_reference=manage_server.get_id_str(),
                    #             entity2_name=contract.__class__.__name__,
                    #             entity2_id=contract.get_id_str(),
                    #             entity2_reference=contract.number)

                return ok_json(data={'message': 'Servers has been successfully updated to the Contract!'})

            return bad_json(message='Servers List is empty')
    except Exception as ex:
        return bad_json(message=ex.__str__())

@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def active_server_load_data(request, contract_id):
    try:
        # Get Contract and DirectCustomers (Servers) thru ContractCustomer relationship
        contract = Contract.objects.get(id=contract_id)
        contract_end_date = convert_string_to_date(request.POST.get('contract_end_date'))
        if contract_end_date:
            queryset = contract.get_my_servers_to_manage().filter(contract_id=contract_id,status=STATUS_ACTIVE, end_date=contract_end_date)
        search_fields = ['name']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())

