from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (STATUS_ACTIVE, STATUS_PENDING, STATUS_INACTIVE,
                                                AUDIT_TRAIL_ACTION_EDITED, STATUS_PROPOSED)
from app.management.utilities.functions import (bad_json, convert_string_to_date, ok_json,
                                                valid_range, datatable_handler, audit_trail, get_ip_address,
                                                contract_audit_trails)
from erms.models import Contract


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request, contract_id):
    try:
        # Get Contract and all its contract lines
        contract = Contract.objects.get(id=contract_id)
        queryset = contract.get_my_contract_lines()

        # query by status
        q = int(request.POST.get('q', STATUS_ACTIVE))
        if q:
            if q == STATUS_ACTIVE:
                queryset = queryset.filter(status=STATUS_ACTIVE)
            elif q == STATUS_INACTIVE:
                queryset = queryset.filter(status=STATUS_INACTIVE)
            elif q == STATUS_PENDING:
                queryset = queryset.filter(status=STATUS_PENDING)
            elif q == STATUS_PROPOSED:
                queryset = queryset.filter(status=STATUS_PROPOSED)
            else:
                queryset = contract.get_my_contract_lines()

        search_fields = ['item__ndc', 'item__description']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def update_lines_changes(request, contract_id):
    try:
        user = request.user
        with transaction.atomic():

            # Get Contract
            contract = Contract.objects.get(id=contract_id)

            clines_list = request.POST.get('clines_list')
            if clines_list:

                for data in clines_list.split("|"):

                    # store history in audit
                    history_dict = {}

                    # get elem
                    elem = data.split(':')

                    contract_line = contract.get_my_contract_lines().get(id=elem[0])
                    price = Decimal(elem[1])

                    # get current data Before changes to store in history dict for audit
                    history_dict['before'] = contract_line.get_current_info_for_audit()

                    start_date = None
                    if elem[2]:
                        start_date = convert_string_to_date(elem[2])

                    end_date = convert_string_to_date('2099/12/31')
                    if elem[3]:
                        end_date = convert_string_to_date(elem[3])

                    if not valid_range(start_date, end_date):
                        return bad_json('Please enter a valid date ranges')

                    if not price:
                        return bad_json(message="Price value cannot be empty")

                    if not start_date:
                        return bad_json(message="Start date cannot be empty")

                    if not valid_range(start_date, end_date):
                        return bad_json(message="Date range is not valid, make sure the start date is before end date")

                    contract_line.price = price
                    contract_line.start_date = start_date
                    contract_line.end_date = end_date
                    contract_line.status = int(elem[4])
                    contract_line.save()

                    # get current data After changes to store in history dict for audit
                    history_dict['after'] = contract_line.get_current_info_for_audit()

                    changed_items = [(k, history_dict['after'][k], v) for k, v in history_dict['before'].items() if history_dict['after'][k] != v]
                    if changed_items:
                        for elem in changed_items:
                            change_text = f"For Contract {contract.number} line {contract_line.item.get_formatted_ndc() if contract_line.item else ''} {elem[0]} is changed from {elem[2]} to {elem[1]}"
                            contract_audit_trails(contract=contract.id,
                                                  product=contract_line.item.id if contract_line.item else None,
                                                  user_email=user.email,
                                                  change_type='line',
                                                  field_name=elem[0],
                                                  change_text=change_text)

                    # Audit Trail
                    # audit_trail(username=request.user.username,
                    #             action=AUDIT_TRAIL_ACTION_EDITED,
                    #             ip_address=get_ip_address(request),
                    #             entity1_name=contract_line.__class__.__name__,
                    #             entity1_id=contract_line.get_id_str(),
                    #             entity1_reference=contract_line.get_id_str(),
                    #             entity2_name=contract.__class__.__name__,
                    #             entity2_id=contract.get_id_str(),
                    #             entity2_reference=contract.number,
                    #             history_dict=history_dict)

                return ok_json(data={'message': 'Contract Lines succesfully updated!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())

@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_contract_line_items(request, contract_id):
    try:
        # Get Contract and all its contract lines
        contract = Contract.objects.get(id=contract_id)
        # query by date
        contract_new_end_date = convert_string_to_date(request.POST.get('contract_new_end_date'))
        contract_end_date = convert_string_to_date(request.POST.get('contract_end_date'))
        if contract_end_date:
            queryset = contract.get_my_contract_lines().filter(status=STATUS_ACTIVE,end_date=contract_end_date)

        search_fields = ['item__ndc', 'item__description']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())

