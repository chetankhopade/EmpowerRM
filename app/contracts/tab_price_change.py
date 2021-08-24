import datetime
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (CONTRACT_TYPE_DIRECT,
                                                STATUS_ACTIVE,
                                                STATUS_PENDING,
                                                STATUS_INACTIVE, AUDIT_TRAIL_ACTION_EDITED, STATUSES)
from app.management.utilities.functions import (bad_json, convert_string_to_date, ok_json,
                                                audit_trail, get_ip_address, valid_range, datatable_handler,
                                                contract_audit_trails)
from erms.models import Contract, ContractLine


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request, contract_id):
    try:
        # Get Contract
        contract = Contract.objects.get(id=contract_id)
        # Return only active contract lines
        queryset = contract.get_my_contract_lines_active()
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

            # Contract Lines (with changed prices)
            clines = json.loads(request.POST['clines'])
            for elem in clines:

                # for audit trail
                history_dict = {}
                contract_line_history_dict = {}

                contract_line = ContractLine.objects.get(pk=elem['iid'])

                contract_line_history_dict['before'] = contract_line.get_current_info_for_audit()

                cl_price = elem.get('price', None)
                if not cl_price:
                    return bad_json(message='Price is required')

                start_date = elem.get('start_date', '')
                if not start_date:
                    return bad_json(message='Start date is required')

                cl_start_date = convert_string_to_date(start_date)
                cl_end_date = convert_string_to_date(elem.get('end_date', '12/31/2099'))

                if not valid_range(start_date=cl_start_date, end_date=cl_end_date):
                    return bad_json('Please enter a valid date range')

                c_type = int(elem.get('ctype', CONTRACT_TYPE_DIRECT))

                new_contract_line = ContractLine(contract=contract,
                                                 item=contract_line.item,
                                                 type=c_type,
                                                 price=Decimal(cl_price),
                                                 start_date=cl_start_date,
                                                 end_date=cl_end_date)
                new_contract_line.save()

                # get current data Before changes to store in history dict for audit
                history_dict['before'] = new_contract_line.get_current_info_for_audit()

                # Set Active, Inactive or Pending status (based on dates range)
                if new_contract_line.start_date <= datetime.datetime.now().date() <= new_contract_line.end_date:

                    # new CLine is active
                    new_contract_line.status = STATUS_ACTIVE
                    new_contract_line.save()

                    # current CLine will be inactive
                    contract_line.status = STATUS_INACTIVE
                    contract_line.end_date = new_contract_line.start_date - timedelta(days=1)
                    contract_line.save()

                    new_contract_line.status = STATUS_ACTIVE
                    new_contract_line.save()

                elif new_contract_line.end_date < datetime.datetime.now().date():

                    # new CLine will be inactive
                    new_contract_line.status = STATUS_INACTIVE
                    new_contract_line.save()

                else:
                    # if in the future, current active CLine stays Active and new CLine becomes Pending
                    new_contract_line.status = STATUS_PENDING
                    new_contract_line.save()

                    # EA-1180 - If new line is pending then move active line end date to new line start date -1 day
                    if contract_line.status == STATUS_ACTIVE:
                        contract_line.end_date = new_contract_line.start_date - timedelta(days=1)
                        contract_line.save()

                # get current data After changes to store in history dict for audit
                history_dict['after'] = new_contract_line.get_current_info_for_audit()
                contract_line_history_dict['after'] = contract_line.get_current_info_for_audit()

                change_text = f"For Contract {contract.number} while updating line {contract_line.item.get_formatted_ndc() if contract_line.item else ''} with status {contract_line.get_status_display()} new line with price {new_contract_line.price} , status {new_contract_line.get_status_display()} and dates {new_contract_line.start_date.strftime('%m/%d/%Y') if new_contract_line.start_date else ''} - {new_contract_line.end_date.strftime('%m/%d/%Y') if new_contract_line.end_date else ''} is added"
                contract_audit_trails(contract=contract.id,
                                      product=new_contract_line.item.id if new_contract_line.item else None,
                                      user_email=user.email,
                                      change_type='line',
                                      field_name='',
                                      change_text=change_text)

                changed_items = [(k, contract_line_history_dict['after'][k], v) for k, v in contract_line_history_dict['before'].items() if contract_line_history_dict['after'][k] != v]
                if changed_items:
                    for elem in changed_items:
                        s1 = elem[1]
                        if s1 == STATUS_ACTIVE or s1 == STATUS_INACTIVE or s1 == STATUS_PENDING:
                            s1 = str(dict(STATUSES)[elem[1]])
                        s2 = elem[2]
                        if s2 == STATUS_ACTIVE or s2 == STATUS_INACTIVE or s2 == STATUS_PENDING:
                            s2 = str(dict(STATUSES)[elem[2]])
                        if elem[0] == 'status':
                            change_text = f"For Contract {contract.number} line {contract_line.item.get_formatted_ndc() if contract_line.item else ''} with status {contract_line.get_status_display()}. Status is changed from {s2} to {s1}"
                        else:
                            change_text = f"For Contract {contract.number} line {contract_line.item.get_formatted_ndc() if contract_line.item else ''} with status {contract_line.get_status_display()}, {elem[0]} is changed from {s2} to {s1}"


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
                #             entity1_name=new_contract_line.__class__.__name__,
                #             entity1_id=new_contract_line.get_id_str(),
                #             entity1_reference=new_contract_line.item.get_formatted_ndc(),
                #             entity2_name=contract.__class__.__name__,
                #             entity2_id=contract.get_id_str(),
                #             entity2_reference=contract.number,
                #             history_dict=history_dict)

            return ok_json(data={'message': 'Price Changes has been succesfully applied to Contract!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())
