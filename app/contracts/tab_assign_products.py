import datetime
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (CONTRACT_TYPE_DIRECT,
                                                STATUS_ACTIVE,
                                                AUDIT_TRAIL_ACTION_ADDED,
                                                CONTRACT_TYPE_INDIRECT, CONTRACT_TYPE_BOTH, STATUS_INACTIVE,
                                                STATUS_PENDING, )
from app.management.utilities.functions import (bad_json, convert_string_to_date, ok_json,
                                                audit_trail, get_ip_address, valid_range, datatable_handler,
                                                contract_audit_trails)
from erms.models import Contract, ContractLine, Item


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request, contract_id):
    try:
        # Get Contract and lines
        contract = Contract.objects.get(id=contract_id)
        # EA-1216 - On the Assign Products tab, show all items that are not currently active on the contract
        # So exclude only active items from Assign products tab
        clines = contract.get_my_contract_lines_active()
        # query Items (that are not in the contract yet)
        queryset = Item.objects.exclude(contractline__in=clines).distinct()
        search_fields = ['ndc']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add_items_to_contract(request, contract_id):
    try:
        user = request.user
        with transaction.atomic():

            # Get Contract
            contract = Contract.objects.get(id=contract_id)

            processing_errors = []

            # Items
            items_list = json.loads(request.POST['items'])
            for item in items_list:
                item_obj = Item.objects.get(pk=item['iid'])

                item_price = Decimal(item['price'])
                item_start_date = convert_string_to_date(item['start_date'])
                item_end_date = convert_string_to_date(item['end_date'])
                item_status = STATUS_ACTIVE

                # Get overlapping lines
                # EA-1245 - Add modal to Contract edit when dates overlap existing lines
                overlapping_contract_lines_obj = ContractLine.objects.filter(Q(contract=contract), Q(item=item_obj), Q(start_date__range=[item_start_date, item_end_date]) | Q(end_date__range=[item_start_date, item_end_date]))
                overlapping_contract_lines = overlapping_contract_lines_obj if overlapping_contract_lines_obj.exists() else None

                if overlapping_contract_lines:
                    for ocl in overlapping_contract_lines:
                        processing_errors.append({
                            'ndc': ocl.item.ndc,
                            'price': str(ocl.price),
                            'start_date': ocl.start_date.strftime("%m/%d/%Y"),
                            'end_date': ocl.end_date.strftime("%m/%d/%Y"),
                            'status': ocl.get_status_display()
                        })
                else:
                    # EA-1216 - Add the date checking logic to properly update overlapping dates
                    # Set Inactive or Pending status (based on dates range) - By default Active
                    if item_end_date < datetime.datetime.now().date():
                        item_status = STATUS_INACTIVE
                    elif item_start_date > datetime.datetime.now().date():
                        item_status = STATUS_PENDING

                    if item_obj.status == STATUS_INACTIVE:
                        item_status = STATUS_INACTIVE

                    if not valid_range(item_start_date, item_end_date):
                        return bad_json(message='The end date cannot be earlier than the start date')

                    contract_line = ContractLine(contract=contract,
                                                 item=item_obj,
                                                 price=item_price,
                                                 start_date=item_start_date,
                                                 end_date=item_end_date,
                                                 status=item_status)
                    contract_line.save()

                    if contract.type == CONTRACT_TYPE_DIRECT:
                        # ContractLine (Direct)
                        contract_line.type = CONTRACT_TYPE_DIRECT
                        contract_line.save()

                    elif contract.type == CONTRACT_TYPE_INDIRECT:
                        # ContractLine (InDirect)
                        contract_line.type = CONTRACT_TYPE_INDIRECT
                        contract_line.save()

                    if contract.type == CONTRACT_TYPE_BOTH:
                        # Store 2 records (one for Direct and other for inDirect)

                        # create record for direct
                        contract_line.type = CONTRACT_TYPE_DIRECT
                        contract_line.save()

                        # create new record for indirect (django clone built in)
                        contract_line.pk = None
                        contract_line.type = CONTRACT_TYPE_INDIRECT
                        contract_line.save()

                    change_text = f"For Contract {contract.number} line {contract_line.item.get_formatted_ndc()} is added with price {item_price}"
                    contract_audit_trails(contract=contract_id,
                                          product=contract_line.item.id if contract_line.item else None,
                                          user_email=user.email,
                                          change_type='line',
                                          field_name='',
                                          change_text=change_text)
                    # Audit Trail
                    # audit_trail(username=request.user.username,
                    #             action=AUDIT_TRAIL_ACTION_ADDED,
                    #             ip_address=get_ip_address(request),
                    #             entity1_name=item_obj.__class__.__name__,
                    #             entity1_id=item_obj.get_id_str(),
                    #             entity1_reference=item_obj.get_formatted_ndc(),
                    #             entity2_name=contract.__class__.__name__,
                    #             entity2_id=contract.get_id_str(),
                    #             entity2_reference=contract.number)
            if processing_errors:
                return ok_json(data={'error': 'y',
                                     'error_type': 'processing_errors',
                                     'message': f'There are {len(processing_errors)} pending conflicts that need to be resolved to continue.',
                                     'processing_errors': processing_errors})
            return ok_json(data={'error': 'n', 'message': 'Items successfully added to the Contract'})

    except Exception as ex:
        return bad_json(message=ex.__str__())
