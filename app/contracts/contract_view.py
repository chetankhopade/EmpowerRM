import json
import datetime
import os
from datetime import timedelta
from decimal import Decimal

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.models import Q, DecimalField, Sum, F, Min
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str

from app.management.utilities.constants import (CONTRACT_TYPE_DIRECT,
                                                STATUS_ACTIVE,
                                                CONTRACT_TYPE_INDIRECT,
                                                STATUS_PENDING,
                                                AUDIT_TRAIL_ACTION_CREATED,
                                                AUDIT_TRAIL_ACTION_EDITED,
                                                STATUS_INACTIVE, STATUS_PROPOSED, AUDIT_TRAIL_ACTION_DELETED,
                                                CONTRACT_THRESHOLD_VALUE)
from app.management.utilities.exports import export_contract_upload, export_contract_upload_template
from app.management.utilities.functions import (bad_json, convert_string_to_date, ok_json,
                                                audit_trail, get_ip_address, query_range, datatable_handler,
                                                get_contract_status_from_date_ranges, convert_string_to_date_imports,
                                                contract_audit_trails)
from app.management.utilities.globals import addGlobalData
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_FILES_STORAGE
from ermm.models import DirectCustomer as GlobalCustomer
from erms.models import (Contract, Item, AuditTrail, DirectCustomer, ChargeBackLineHistory, ContractCustomer,
                         ContractLine, ContractAlias,ContractMember)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
        Company's Contracts (View)
    """
    data = {'title': 'Contracts', 'header_title': 'My Contracts'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # All Contracts of the company
    data['all_contracts'] = all_contracts = Contract.objects.all()

    # Ticket EA-793 Change Expiring contract validation based on Contract Header end date, not contract lines end dates
    data['company_settings'] = company_settings = data['company'].my_company_settings()
    # EA-597 Add Setting to set expiration alert range for expiring contracts
    contract_notification_threshold = CONTRACT_THRESHOLD_VALUE[0]
    if company_settings.enable_contract_expiration_threshold:
        contract_notification_threshold = company_settings.contract_expiration_threshold

    limit_date = data['today'] + timedelta(days=contract_notification_threshold)  # default 30 days from today

    data['expiring_contracts_count'] = all_contracts.filter(Q(end_date__range=[data['today'].date(), limit_date.date()])).distinct().count()

    # Required for upload add contracts pop-up
    data['my_customers'] = DirectCustomer.objects.all()
    # Existing Products of the company
    data['existing_products'] = Item.objects.all()

    data['menu_option'] = 'menu_contracts'

    return render(request, "contracts/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    try:
        # Get all Contracts
        queryset = Contract.objects.select_related('customer').only(
            'number', 'description', 'type', 'customer', 'status', 'start_date', 'end_date'
        )

        # filter by status
        q_sf = int(request.POST['q_sf'])
        if q_sf > 0:
            if q_sf == STATUS_ACTIVE:
                queryset = queryset.filter(status=STATUS_ACTIVE)
            elif q_sf == STATUS_INACTIVE:
                queryset = queryset.filter(status=STATUS_INACTIVE)
            elif q_sf == STATUS_PROPOSED:
                queryset = queryset.filter(status=STATUS_PROPOSED)
            else:
                queryset = queryset.filter(status=STATUS_PENDING)

        # filter by customers (ticket EA-1359)
        q_cf = int(request.POST['q_cf'])
        if q_cf > 0:
            if q_cf == 1:
                queryset = queryset.filter(type=CONTRACT_TYPE_DIRECT)
            else:
                queryset = queryset.filter(type=CONTRACT_TYPE_INDIRECT)

        if not queryset:
            return JsonResponse({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
            })

        search_fields = ['number', 'description', 'type', 'status_name', 'customer_name']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=True)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_expiring_data(request):
    try:
        data = {'title': 'Contracts', 'header_title': 'My Contracts'}
        addGlobalData(request, data)
        data['company_settings'] = company_settings = data['company'].my_company_settings()
        # Get all Contracts
        queryset = Contract.objects.select_related('customer').only(
            'number', 'description', 'type', 'customer', 'status', 'start_date', 'end_date'
        )


        # filter by status
        q_sf = int(request.POST['q_sf'])
        if q_sf > 0:
            if q_sf == STATUS_ACTIVE:
                queryset = queryset.filter(status=STATUS_ACTIVE)
            elif q_sf == STATUS_INACTIVE:
                queryset = queryset.filter(status=STATUS_INACTIVE)
            elif q_sf == STATUS_PROPOSED:
                queryset = queryset.filter(status=STATUS_PROPOSED)
            else:
                queryset = queryset.filter(status=STATUS_PENDING)

        # filter by customers (ticket EA-1359)
        q_cf = int(request.POST['q_cf'])
        if q_cf > 0:
            if q_cf == 1:
                queryset = queryset.filter(type=CONTRACT_TYPE_DIRECT)
            else:
                queryset = queryset.filter(type=CONTRACT_TYPE_INDIRECT)
        today = datetime.datetime.now()
        # EA-597 Add Setting to set expiration alert range for expiring contracts
        contract_notification_threshold = CONTRACT_THRESHOLD_VALUE[0]
        if company_settings.enable_contract_expiration_threshold:
            contract_notification_threshold = company_settings.contract_expiration_threshold
        limit_date = today + timedelta(days=contract_notification_threshold)  # 2 weeks from today
        queryset = queryset.filter(Q(end_date__range=[today, limit_date.date()])).distinct()
        if not queryset:
            return JsonResponse({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
            })
        search_fields = ['number', 'description', 'type', 'status_name', 'customer_name']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=True)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())

@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def create(request):
    """
        Company's Contracts (Create)
    """
    data = {'title': 'Create Contract', 'header_title': 'Create Contract'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    if request.method == 'POST':

        try:
            with transaction.atomic():

                number = request.POST.get('number', '')
                if not number:
                    return bad_json('Contract number is required')

                if Contract.objects.filter(number=number).exists():
                    return bad_json('A Contract with the same number already exist in the system')

                # EA-1323 - Dont allow the user to create a new contract or edit an existing contract number with a contract number that is already used as an alias
                if ContractAlias.objects.filter(alias=number).exists():
                    return bad_json('A Contract alias with the same number already exist in the system')

                customer_id = request.POST.get('customer_id', None)
                if not customer_id:
                    return bad_json('Customer is required')

                start_date_str = request.POST.get('start_date', '')
                if not start_date_str:
                    return bad_json(message="Start date is required.")

                ctype = request.POST.get('ctype', '')
                if not ctype:
                    return bad_json(message="Type is required.")

                if int(ctype) == CONTRACT_TYPE_DIRECT:
                    direct_contracts_with_same_owner = Contract.objects.filter(type=CONTRACT_TYPE_DIRECT,
                                                                               customer_id=customer_id)
                    if direct_contracts_with_same_owner.exists():
                        existing_contract_id = direct_contracts_with_same_owner[0].get_id_str()
                        existing_contract_number = direct_contracts_with_same_owner[0].number
                        return bad_json(
                            extradata={'edit_url': f"/{data['db_name']}/contracts/{existing_contract_id}/edit",
                                       'existing_contract_no': existing_contract_number})

                end_date_str = request.POST.get('end_date', '12/31/2099')
                start_date = convert_string_to_date(start_date_str)
                end_date = convert_string_to_date(end_date_str)
                if start_date > end_date:
                    return bad_json(message="The start date must be before the end date.")

                description = request.POST.get('description', '')
                eligibility = request.POST.get('eligibility', '')
                cots = request.POST.get('cots', '')
                member_eval = request.POST.get('member_eval', '')
                cot_eval = request.POST.get('cot_eval', '')

                # Contract
                contract = Contract(number=number,
                                    type=ctype,
                                    description=description,
                                    customer_id=customer_id,
                                    start_date=start_date,
                                    end_date=end_date,
                                    eligibility=int(eligibility) if eligibility else None,
                                    status=get_contract_status_from_date_ranges(start_date, end_date),
                                    cots=cots,
                                    member_eval=member_eval,
                                    cot_eval=cot_eval)
                contract.save()

                change_text = f"Contract {contract.number} is created"
                contract_audit_trails(contract=contract.id,
                                      user_email=data['user'].email,
                                      change_type='header',
                                      field_name='number',
                                      change_text=change_text)

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_ACTION_CREATED,
                #             ip_address=get_ip_address(request),
                #             entity1_name=contract.__class__.__name__,
                #             entity1_id=contract.get_id_str(),
                #             entity1_reference=contract.number)

                return ok_json(data={'message': 'Contract successfully created !',
                                     'redirect_url': f"/{data['db_name']}/contracts/{contract.id}/edit"})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    current_customers_ids = [x.customer_id for x in DirectCustomer.objects.all() if x.customer_id]
    data['global_customers'] = GlobalCustomer.objects.exclude(id__in=current_customers_ids).all()
    data['my_customers'] = DirectCustomer.objects.all()
    # EA-499 Contract Edit: Manage Membership
    company_settings = data['company'].my_company_settings()
    data['membership_validation'] = company_settings.membership_validation_enable
    data['menu_option'] = 'menu_contracts'
    return render(request, "contracts/handler/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def edit(request, contract_id):
    """
        Company's Contract (Edit)
    """
    data = {'title': 'Edit Contract', 'header_title': 'Edit Contract'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Contract
    data['contract'] = contract = Contract.objects.get(id=contract_id)


    if request.method == 'POST':

        try:
            with transaction.atomic():

                history_dict = {}

                number = request.POST.get('number', '')
                if not number:
                    return bad_json('Contract number is required')

                if Contract.objects.filter(number=number).exclude(id=contract.id).exists():
                    return bad_json('A Contract with the same number already exist in the system')

                # EA-1323 - Dont allow the user to create a new contract or edit an existing contract number with a contract number that is already used as an alias
                if ContractAlias.objects.filter(alias=number).exists():
                    return bad_json('A Contract alias with the same number already exist in the system')

                customer_id = request.POST.get('customer_id', None)
                if not customer_id:
                    return bad_json('Customer is required')

                ctype = request.POST.get('ctype', '')
                if not ctype:
                    return bad_json(message="Type is required.")

                if int(ctype) == CONTRACT_TYPE_DIRECT:
                    direct_contracts_with_same_owner = Contract.objects.filter(type=CONTRACT_TYPE_DIRECT,
                                                                               customer_id=customer_id).exclude(
                        id=contract.id)
                    if direct_contracts_with_same_owner.exists():
                        existing_contract_id = direct_contracts_with_same_owner[0].get_id_str()
                        existing_contract_number = direct_contracts_with_same_owner[0].number
                        return bad_json(
                            extradata={'edit_url': f"/{data['db_name']}/contracts/{existing_contract_id}/edit",
                                       'existing_contract_no': existing_contract_number})

                end_date_str = request.POST.get('end_date', '12/31/2099')
                start_date_str = request.POST.get('start_date', '')
                if not start_date_str:
                    return bad_json(message="Start date is required.")

                start_date = convert_string_to_date(start_date_str)
                end_date = convert_string_to_date(end_date_str)
                if start_date > end_date:
                    return bad_json(message="The start date must be before the end date.")

                description = request.POST.get('description', '')
                eligibility = request.POST.get('eligibility', '')
                cots = request.POST.get('cots', '')
                member_eval = request.POST.get('member_eval', '')
                cot_eval = request.POST.get('cot_eval', '')

                # get current data Before changes to store in history dict for audit
                history_dict['before'] = contract.get_current_info_for_audit()

                # Contract
                contract.number = number
                contract.type = int(ctype)
                contract.description = description
                contract.customer_id = customer_id
                contract.start_date = start_date
                contract.end_date = end_date
                contract.status = get_contract_status_from_date_ranges(start_date, end_date)
                contract.eligibility = int(eligibility) if eligibility else None
                contract.cots = cots
                contract.member_eval = member_eval
                contract.cot_eval = cot_eval
                contract.save()
                # EA-1460 Extending Contract End Date extends Contract Lines and Membership, Servers
                is_line_item_update = request.POST.get('is_line_item_update', '')
                pending_contract_line = []
                if is_line_item_update == 'true':
                    contract_line_item = json.loads(request.POST['contract_line_item'])
                    if contract_line_item:
                        for elem in contract_line_item:
                            contract_line_item_id = elem['clid']
                            contract_line = ContractLine.objects.get(id=contract_line_item_id)
                            pending_contract_line = ContractLine.objects.order_by().annotate(
                                min_pending_line_start_date=Min('start_date')).filter(contract=contract_line.contract,
                                                                                      item=contract_line.item,
                                                                                      status=STATUS_PENDING)
                            if pending_contract_line:
                                if pending_contract_line[0].min_pending_line_start_date < end_date:
                                    end_date = pending_contract_line[0].min_pending_line_start_date - datetime.timedelta(days=1)

                            contract_line.end_date = end_date
                            contract_line.save()
                    # Server line items update
                    contract_server_line_items = json.loads(request.POST['contract_server_line_items'])
                    if contract_server_line_items:
                        for selem in contract_server_line_items:
                            contract_server_line_item_id = selem['sid']
                            contract_server_line = ContractCustomer.objects.get(id=contract_server_line_item_id)
                            contract_server_line.end_date = contract.end_date
                            contract_server_line.save()
                    # Membership line items update
                    contract_membership_line_items = json.loads(request.POST['contract_membership_line_items'])
                    pending_contract_membership_line = []
                    if contract_membership_line_items:
                        for melem in contract_membership_line_items:
                            contract_membership_line_item_id = melem['mid']
                            member_end_date = contract.end_date
                            contract_member_line = ContractMember.objects.get(id=contract_membership_line_item_id)
                            pending_contract_membership_line = ContractMember.objects.order_by().annotate(
                                min_pending_membership_line_start_date=Min('start_date')).filter(
                                contract=contract_member_line.contract,
                                indirect_customer=contract_member_line.indirect_customer,
                                status=STATUS_PENDING)
                            if pending_contract_membership_line:
                                if pending_contract_membership_line[0].min_pending_membership_line_start_date < member_end_date :
                                    member_end_date = pending_contract_membership_line[0].min_pending_membership_line_start_date - datetime.timedelta(days=1)

                            contract_member_line.end_date = member_end_date
                            contract_member_line.save()


                # End here EA-1460
                # get current data After changes to store in history dict for audit
                history_dict['after'] = contract.get_current_info_for_audit()

                # update contract lines with the same type of its contract
                contract.get_my_contract_lines().update(type=contract.type)

                # # update contract lines based on status if status == Proposed
                # if contract.status == STATUS_PROPOSED:
                #     contract.get_my_contract_lines().update(status=STATUS_PROPOSED)

                changed_items = [(k, history_dict['after'][k], v) for k, v in history_dict['before'].items() if history_dict['after'][k] != v]
                if changed_items:

                    for elem in changed_items:
                        change_text = f"For Contract {contract.number} {elem[0]} is changed from {elem[2]} to {elem[1]}"
                        contract_audit_trails(contract=contract_id,
                                              user_email=data['user'].email,
                                              change_type='header',
                                              field_name=elem[0],
                                              change_text=change_text)

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_ACTION_EDITED,
                #             ip_address=get_ip_address(request),
                #             entity1_name=contract.__class__.__name__,
                #             entity1_id=contract.get_id_str(),
                #             entity1_reference=contract.number,
                #             history=history_dict)

                return ok_json(data={'message': 'Contract succesfully updated !',
                                     'redirect_url': f"/{data['db_name']}/contracts/{contract.id}/edit"})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    current_customers_ids = [x.customer_id for x in DirectCustomer.objects.all() if x.customer_id]
    data['global_customers'] = GlobalCustomer.objects.exclude(id__in=current_customers_ids).all()
    data['my_customers'] = DirectCustomer.objects.all()
    data['menu_option'] = 'menu_contracts'
    if 'tab' in request.GET and request.GET['tab'] == 'assign_product':
        data['show_assign_product_tab'] = True
    # EA-499 Contract Edit: Manage Membership
    company_settings = data['company'].my_company_settings()
    data['membership_validation'] = company_settings.membership_validation_enable
    data['class_of_trade_validation_enabled'] = company_settings.class_of_trade_validation_enabled
    data['contract_line_count'] = contract.get_my_contract_lines().filter(status=STATUS_ACTIVE,
                                                                          end_date=contract.end_date).count()
    data['contract_my_membership_count'] = contract.get_my_membership().filter(status=STATUS_ACTIVE,end_date=contract.end_date).count()
    data['contract_my_servers_count'] = contract.get_my_servers_to_manage().filter(status=STATUS_ACTIVE,end_date=contract.end_date).count()

    return render(request, "contracts/handler/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def details(request, contract_id):
    """
        Company's Contract (Details)
    """
    data = {'title': 'Contract Details'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Contract from uuid
    data['contract'] = contract = Contract.objects.get(id=contract_id)

    # Generating chargeback data
    data['query'] = query = request.GET.get('range', 'MTD')
    chargeback_count = contract.get_chargebacklines_by_range(query).count()
    issued_cbs = contract.sum_of_all_chageback_issued(query)
    total_wac_revenue = contract.total_wac_revenue(query)
    items_sold = contract.get_my_items_sold()
    total_revenue = Decimal(total_wac_revenue - issued_cbs).quantize(Decimal(10) ** -2)

    data['chargeback_count'] = chargeback_count if chargeback_count else 'N/A'
    data['issued_cbs'] = issued_cbs if issued_cbs else 'N/A'
    data['items_sold'] = items_sold if items_sold else 'N/A'
    data['total_wac_revenue'] = total_wac_revenue if total_wac_revenue else 'N/A'
    data['total_revenue'] = total_revenue if total_revenue else 'N/A'

    # Get ContractCustomer
    data['active_customers_data'] = [
        {
            "name": c.name,
            "revenue": c.get_my_revenue_by_range(query_range(query)),
            "color": c.get_random_color_for_charts(),
        } for c in contract.get_my_servers_active()
    ]

    # Get Aliases
    data['contract_aliases'] = contract.get_my_contract_aliases()
    # CoT
    data['class_of_trade_validation_enabled'] = data['company'].my_company_settings().class_of_trade_validation_enabled

    # Latest Audit Trails records filtered by entity=Contract
    data['latest_audit_trails'] = AuditTrail.objects.filter(entity='Contract', reference=contract.number)[:4]
    data['header_title'] = f"Contracts > Detail: #{contract.number}"
    data['menu_option'] = 'menu_contracts'
    data['active_tab'] = 'i'
    return render(request, "contracts/details/details.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_contract_lines_data(request, contract_id):
    try:
        contract = Contract.objects.get(id=contract_id)
        queryset = contract.get_my_contract_lines()

        # query by status
        q = int(request.POST.get('q', 0))
        if q:
            if q == STATUS_ACTIVE:
                queryset = queryset.filter(status=STATUS_ACTIVE)
            elif q == STATUS_INACTIVE:
                queryset = queryset.filter(status=STATUS_INACTIVE)
            elif q == STATUS_PROPOSED:
                queryset = queryset.filter(status=STATUS_PROPOSED)
            else:
                queryset = queryset.filter(status=STATUS_PENDING)

        search_fields = ['item__ndc__formatted', 'item__description']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=True)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def chart_contract_performance(request):
    try:
        # Contract chart
        range_key = request.POST.get('range', 'MTD')

        # Finding 10 highest revenue contracts
        top_ten_contracts = ChargeBackLineHistory.objects.filter(updated_at__date__range=query_range(range_key),
                                                                 contract_ref__type=CONTRACT_TYPE_INDIRECT).values(
            'contract_ref').annotate(
            revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).order_by('-revenue')[
                            :10]
        labels = []
        revenues = []

        for c in top_ten_contracts:
            try:
                contract = Contract.objects.get(id=c["contract_ref"])
            except:
                contract = None

            labels.append(contract.number if contract else '')
            revenues.append(c["revenue"])

        response = {
            'labels': labels,
            'datasets': [{
                'label': 'Revenue',
                'data': revenues,
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)',
                    'rgba(255, 0, 0, 0.2)',
                    'rgba(0, 255, 0, 0.2)',
                    'rgba(0, 0, 255, 0.2)',
                    'rgba(103, 0, 0, 0.2)'
                ],
                'borderColor': [
                    'rgba(255,99,132,1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(255, 0, 0, 1)',
                    'rgba(0, 255, 0, 1)',
                    'rgba(0, 0, 255, 1)',
                    'rgba(103, 0, 0, 1)'
                ],
                'borderWidth': 1
            }]
        }

        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def contracts_performance_information(request):
    try:
        # range_key = request.POST.get('range', 'MTD')
        # query contracts because calculations will be using cblinehistory data
        # queryset = Contract.objects.order_by('number')

        # EA-1145 - On the Contract Performance bottom right chart only show Indirect contracts
        queryset = Contract.objects.filter(type=CONTRACT_TYPE_INDIRECT).order_by('number')

        search_fields = ['number']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=False)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def contract_lines_load_data(request):
    try:
        contract_id = request.POST.get('contract_id')
        # Get all Contracts
        contract = Contract.objects.get(id=contract_id)
        queryset = contract.get_my_contract_lines()
        # query by status
        q = int(request.POST.get('q', 1))
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
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=True)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def contract_servers_load_data(request):
    try:
        contract_id = request.POST.get('contract_id')
        # Get all Contracts
        contract = Contract.objects.get(id=contract_id)
        queryset = ContractCustomer.objects.filter(status=STATUS_ACTIVE, contract=contract)

        search_fields = ['customer__name']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=False, contract_id=contract.id)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def products_on_contracts(request, contract_id):
    data = {'title': 'Contract Details'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Contract from uuid
    data['contract'] = contract = Contract.objects.get(id=contract_id)

    contract_lines = contract.get_my_contract_lines()
    # Company Items
    data['all_contract_lines'] = contract_lines

    data['header_title'] = f"Contracts > Detail: #{contract.number} > Products"
    data['menu_option'] = 'menu_contracts'
    data['active_tab'] = 'p'
    company_settings = data['company'].my_company_settings()
    data['class_of_trade_validation_enabled'] = company_settings.class_of_trade_validation_enabled
    return render(request, "contracts/details/products_on_contracts.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def servers_on_contracts(request, contract_id):
    data = {'title': 'Contract Details'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Contract from uuid
    data['contract'] = contract = Contract.objects.get(id=contract_id)

    # Get ContractCustomer
    # data['contract_customers'] = ContractCustomer.objects.filter(status=STATUS_ACTIVE, contract=contract)

    data['header_title'] = f"Contracts > Detail: #{contract.number} > Servers"
    data['menu_option'] = 'menu_contracts'
    data['active_tab'] = 's'
    company_settings = data['company'].my_company_settings()
    data['class_of_trade_validation_enabled'] = company_settings.class_of_trade_validation_enabled
    return render(request, "contracts/details/servers_on_contracts.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def members_on_contracts(request, contract_id):
    data = {'title': 'Contract Details'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Contract from uuid
    data['contract'] = contract = Contract.objects.get(id=contract_id)

    data['header_title'] = f"Contracts > Detail: #{contract.number} > Members"
    data['menu_option'] = 'menu_contracts'
    data['active_tab'] = 'm'
    company_settings = data['company'].my_company_settings()
    data['class_of_trade_validation_enabled'] = company_settings.class_of_trade_validation_enabled
    return render(request, "contracts/details/members_on_contracts.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def history(request, contract_id):
    data = {'title': 'Contract Details'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Contract from uuid
    data['contract'] = contract = Contract.objects.get(id=contract_id)

    data['header_title'] = f"Contracts > Detail: #{contract.number} > History"
    data['menu_option'] = 'menu_contracts'
    data['active_tab'] = 'h'
    company_settings = data['company'].my_company_settings()
    data['class_of_trade_validation_enabled'] = company_settings.class_of_trade_validation_enabled
    return render(request, "contracts/details/history.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def upload_update(request):
    try:
        data = {'title': 'Contract Upload Update'}
        addGlobalData(request, data)

        check_missing = request.POST.get('check_missing', '0')
        confirm_upload = request.POST.get('confirm_upload', '0')
        # today = datetime.datetime.now().date()
        # Read the file and its sheets and returns an OrderedDict of DataFrames
        required_headers = ['CONTRACT ID', 'PRODUCT ID', 'PRICE', 'STATUS', 'START DATE', 'END DATE']
        if check_missing == "1":

            missing_contract_list = json.loads(request.POST['missing_contract_list'])
            missing_item_list = json.loads(request.POST['missing_item_list'])

            for mcl in missing_contract_list:
                try:
                    Contract.objects.get(number=mcl["entity"])
                except:
                    return bad_json(message="Please add all entities to continue!")

            for mil in missing_item_list:
                try:
                    Item.objects.get(ndc=mil["entity"])
                except:
                    return bad_json(message="Please add all entities to continue!")

            filename = request.POST['filename']
            file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE, filename)

            file_to_processed = file_path
        elif confirm_upload == "1":
            filename = request.POST['filename']
            file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE, filename)

            file_to_processed = file_path
        else:
            file_to_processed = request.FILES['file']

        df = pd.read_excel(file_to_processed, dtype=str, usecols=required_headers)
        # 2. Confirm that the file has the correct headers
        headers = pd.read_excel(file_to_processed).columns.ravel()

        for rh in required_headers:
            if rh not in headers:
                return bad_json(message='Required headers are no present. Please check the file and upload again')

        # 3. Confirm that each row has a contract number, ndc, price, start, and end date filled in
        # 4. Confirm that each row in the file has one of the following Change Indicators , A, U, D
        primary_validation_errors = []
        empty_contract_id_df = df.loc[df["CONTRACT ID"].isnull()]
        empty_product_id_df = df.loc[df["PRODUCT ID"].isnull()]
        status_df = df.loc[~df["STATUS"].isin(['A', 'D', 'U'])]
        empty_price_df = df.loc[df["PRICE"].isnull()]
        empty_start_date_df = df.loc[df["START DATE"].isnull()]
        empty_end_date_df = df.loc[df["END DATE"].isnull()]

        if len(empty_contract_id_df) > 0:
            primary_validation_errors.append("CONTRACT ID column missing values.")
        if len(empty_product_id_df) > 0:
            primary_validation_errors.append("PRODUCT ID column missing values.")
        if len(status_df) > 0:
            primary_validation_errors.append("STATUS column should contain values only from A, U, D.")
        if len(empty_price_df) > 0:
            primary_validation_errors.append("PRICE column missing values.")
        if len(empty_start_date_df) > 0:
            primary_validation_errors.append("START DATE column missing values.")
        if len(empty_end_date_df) > 0:
            primary_validation_errors.append("END DATE column missing values.")

        if primary_validation_errors:
            return ok_json(data={'error': 'y',
                                 'error_type': 'primary_validations',
                                 'message': 'We could not processed the file due to following errors!',
                                 'errors': primary_validation_errors})

        # If Primary validations is empty go ahead
        # List down the contracts and line items show to the customer
        # For EA-1436 below changes start
        if not primary_validation_errors and confirm_upload == '0':
            file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE)
            file = file_to_processed
            fs = FileSystemStorage(location=file_path)
            basename, extension = os.path.splitext(file.name)
            filename = f"c_upload_{basename}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}{extension}"
            fs.save(filename, file)
            contract_list = df.groupby(['CONTRACT ID']).size().to_dict()
            # grpd = df.groupby(['CONTRACT ID']).size().to_frame('ctlist').to_json()
            return ok_json(data={'error': 'y',
                                 'error_type': 'confirm_validations',
                                 'message': 'Contract Unique List count',
                                 'contract_list': contract_list,
                                 'filename': filename})
        # For EA-1436 below changes end
        # Get unique values from contracts and items to check if they exists in the system or not
        unique_contracts = df["CONTRACT ID"].unique()
        unique_items = df["PRODUCT ID"].unique()

        missing_contracts = []
        missing_items = []

        # collect those contracts which are not in the system
        for uc in unique_contracts:
            try:
                contract = Contract.objects.get(number=uc)
            except:
                contract = None
                missing_contracts.append({
                    'type': 'Contract',
                    'entity': uc,
                })

        # collect those Items which are not in the system
        for ui in unique_items:
            try:
                item = Item.objects.get(ndc=ui)
            except:
                item = None
                missing_items.append({
                    'type': 'Product',
                    'entity': ui,
                })

        # If there are missing items send that information to user and save the file to directory to process it later
        if missing_contracts or missing_items:
            # For EA-1436 ticket comment below code
            # file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE)
            # file = file_to_processed
            # fs = FileSystemStorage(location=file_path)
            # basename, extension = os.path.splitext(file.name)
            # filename = f"c_upload_{basename}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}{extension}"
            # fs.save(filename, file)

            return ok_json(data={'error': 'y',
                                 'error_type': 'missing_error',
                                 'message': 'We could not process the file due to following missing entities',
                                 'errors_missing_contracts': missing_contracts,
                                 'errors_missing_items': missing_items,
                                 'filename': filename})

        processing_errors = []
        for _, row in df.iterrows():
            save_new_line = True
            today = datetime.datetime.now().date()

            contract_number = row.get('CONTRACT ID', '')
            item_ndc = row.get('PRODUCT ID', '')
            action = row.get('STATUS', '')
            head, sep, tail = row.get('START DATE', '').partition(' ')
            # EA-1686 :- HOTFIX: Unable to use Bulk Contract Upload - Error Index out of range
            line_start_date = convert_string_to_date_imports(head)
            start_date_obj = convert_string_to_date_imports(head)
            head, sep, tail = row.get('END DATE', '').partition(' ')
            # EA-1686 :- HOTFIX: Unable to use Bulk Contract Upload - Error Index out of range
            line_end_date = convert_string_to_date_imports(head)
            end_date_obj = convert_string_to_date_imports(head)

            price = row.get('PRICE', '')

            # Contract Validation
            try:
                contract = Contract.objects.get(number=contract_number)
            except:
                contract = None
                processing_errors.append({
                    'type': 'contract',
                    'type_text': 'Contract Not Found',
                    'message': 'Contract does not exists',
                    'contract': contract_number,
                    'product': item_ndc,
                    'submitted_price': price,
                    'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                    'submitted_end_date': end_date_obj.strftime("%m/%d/%Y"),
                    'price': price
                })
                # Go to next line
                continue

            # Item Validation
            try:
                item = Item.objects.get(ndc=item_ndc)
            except:
                item = None
                processing_errors.append({
                    'type': 'item',
                    'type_text': 'Product Not Found',
                    'message': 'Item does not exists',
                    'contract': contract_number,
                    'product': item_ndc,
                    'submitted_price': price,
                    'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                    'submitted_end_date': end_date_obj.strftime("%m/%d/%Y"),
                    'price': price
                })
                # Go to next line
                continue

            # check submitted dates - start date should not be > than end date
            if start_date_obj > end_date_obj:
                e_messages = []
                e_messages.append(
                    f'Submitted Line start date is greater than end date {start_date_obj.strftime("%m/%d/%Y")}-{end_date_obj.strftime("%m/%d/%Y")}')

                processing_errors.append({
                    'type': 'overlapping_ranges',
                    'type_text': 'Range Conflict',
                    'message': e_messages,
                    'contract': contract_number,
                    'product': item_ndc,
                    'status': action,
                    'submitted_price': price,
                    'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                    'submitted_end_date': end_date_obj.strftime("%m/%d/%Y"),
                    'price': price
                })
                # Go to next line
                continue

            # Overlapping Validation
            # Get overlapping lines with non active lines
            contract_lines_other = ContractLine.objects.filter(Q(contract=contract), Q(
                status__in=[STATUS_INACTIVE, STATUS_PENDING, STATUS_PROPOSED]), Q(item=item), Q(
                start_date__range=[line_start_date, line_end_date]) | Q(
                end_date__range=[line_start_date, line_end_date]))
            contract_line_other = contract_lines_other if contract_lines_other.exists() else None
            if contract_line_other:
                e_messages = []
                for clo in contract_line_other:
                    e_messages.append(
                        f'Submitted Line conflicts with existing {clo.get_status_display()} line: {clo.item.get_formatted_ndc()}: Price: {clo.price} with range {clo.start_date.strftime("%m/%d/%Y")}-{clo.end_date.strftime("%m/%d/%Y")}')

                processing_errors.append({
                    'type': 'overlapping_ranges',
                    'type_text': 'Range Conflict',
                    'message': e_messages,
                    'contract': contract_number,
                    'product': item_ndc,
                    'status': action,
                    'submitted_price': price,
                    'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                    'submitted_end_date': end_date_obj.strftime("%m/%d/%Y"),
                    'price': price
                })
                # Go to next line
                continue

            if action == 'D':
                contract_lines_active = ContractLine.objects.filter(contract=contract, item=item)
                contract_line_active = contract_lines_active[0] if contract_lines_active.exists() else None
                if contract_line_active:
                    contract_line_active.end_date = end_date_obj
                    contract_line_active.status = STATUS_INACTIVE
                    contract_line_active.save()

                    change_text = f"For Contract {contract.number} status of line {contract_line_active.item.get_formatted_ndc() if contract_line_active.item else ''} is set to INACTIVE"
                    contract_audit_trails(contract=contract.id,
                                          product=contract_line_active.item.id if contract_line_active.item else None,
                                          user_email=data['user'].email,
                                          change_type='line',
                                          field_name='status',
                                          change_text=change_text)
            else:
                # Checking overlapping with active line(s)
                contract_lines_active = ContractLine.objects.filter(Q(contract=contract), Q(status=STATUS_ACTIVE),
                                                                    Q(item=item), Q(
                        start_date__range=[line_start_date, line_end_date]) | Q(
                        end_date__range=[line_start_date, line_end_date]))
                contract_line_active = contract_lines_active if contract_lines_active.exists() else None
                if contract_line_active:
                    # To-Do , how we should report back this to user? In for loop(?)
                    if len(contract_line_active) > 1:  # Means overlapping with more than 1 Active line , which is not correct
                        e_messages = []
                        for cla in contract_line_active:
                            e_messages.append(
                                f'Submitted Line conflicts with existing {cla.get_status_display()} line: {cla.item.get_formatted_ndc()}: Price: {cla.price} with range {cla.start_date.strftime("%m/%d/%Y")}-{cla.end_date.strftime("%m/%d/%Y")}')

                        processing_errors.append({
                            'type': 'overlapping_ranges',
                            'type_text': 'Range Conflict',
                            'message': e_messages,
                            'contract': contract_number,
                            'product': item_ndc,
                            'status': action,
                            'submitted_price': price,
                            'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                            'submitted_end_date': end_date_obj.strftime("%m/%d/%Y"),
                            'price': price
                        })
                        # Go to next line
                        continue
                    else:
                        existing_cline = contract_line_active[0]
                        # EA-1686 :- HOTFIX: Unable to use Bulk Contract Upload - Error Index out of range
                        # start_date = convert_string_to_date_imports(line_start_date)
                        # end_date = convert_string_to_date_imports(line_end_date)
                        start_date = line_start_date
                        end_date = line_end_date
                        # if dates are exact matches
                        if start_date > existing_cline.start_date and end_date >= existing_cline.end_date:
                            day_to_adjust = datetime.timedelta(1)
                            # Ending existing line one day prior new start date
                            existing_cline.end_date = start_date - day_to_adjust
                            existing_cline.status = STATUS_INACTIVE
                            # If new submitted line is in Pending and existing line still in active range , just change dates not status
                            if existing_cline.start_date <= today <= existing_cline.end_date:
                                existing_cline.status = STATUS_ACTIVE
                            if today < existing_cline.start_date:
                                existing_cline.status = STATUS_PENDING
                            existing_cline.save()

                            change_text = f"For Contract {contract.number} status of existing line {existing_cline.item.get_formatted_ndc() if existing_cline.item else ''} is set to {existing_cline.get_status_display()}"
                            contract_audit_trails(contract=contract.id,
                                                  product=contract_line_active.item.id if contract_line_active.item else None,
                                                  user_email=data['user'].email,
                                                  change_type='line',
                                                  field_name='status',
                                                  change_text=change_text)

                        else:
                            e_messages = [
                                f'Submitted Line conflicts with existing {existing_cline.get_status_display()} line: {existing_cline.item.get_formatted_ndc()}: Price: {existing_cline.price} with range {existing_cline.start_date.strftime("%m/%d/%Y")}-{existing_cline.end_date.strftime("%m/%d/%Y")}']
                            processing_errors.append({
                                'type': 'overlapping_ranges',
                                'type_text': 'Range Conflict',
                                'message': e_messages,
                                'contract': contract_number,
                                'product': item_ndc,
                                'status': action,
                                'submitted_price': price,
                                'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                                'submitted_end_date': end_date_obj.strftime("%m/%d/%Y"),
                                'price': price
                            })
                            # Go to next line
                            continue
                else:
                    contract_line = ContractLine.objects.filter(contract=contract, item=item)
                    contract_line_active = contract_line
                    #EA-1686 :- HOTFIX: Unable to use Bulk Contract Upload - Error Index out of range
                    if len(contract_line_active) > 0:
                        existing_cline = contract_line_active[0]
                        # EA-1686 :- HOTFIX: Unable to use Bulk Contract Upload - Error Index out of range
                        # start_date = convert_string_to_date_imports(line_start_date)
                        # end_date = convert_string_to_date_imports(line_end_date)
                        start_date = line_start_date
                        end_date = line_end_date
                        # if dates are exact matches
                        if start_date > existing_cline.start_date and end_date >= existing_cline.end_date:
                            day_to_adjust = datetime.timedelta(1)
                            # Ending existing line one day prior new start date
                            existing_cline.end_date = start_date - day_to_adjust
                            existing_cline.status = STATUS_INACTIVE
                            # If new submitted line is in Pending and existing line still in active range , just change dates not status
                            if existing_cline.start_date <= today <= existing_cline.end_date:
                                existing_cline.status = STATUS_ACTIVE
                            if today < existing_cline.start_date:
                                existing_cline.status = STATUS_PENDING
                            existing_cline.save()
                        elif start_date > existing_cline.start_date and end_date <= existing_cline.end_date:
                            day_to_adjust = datetime.timedelta(1)
                            # Ending existing line one day prior new start date
                            existing_cline.end_date = start_date - day_to_adjust
                            existing_cline.status = STATUS_INACTIVE
                            # If new submitted line is in Pending and existing line still in active range , just change dates not status
                            if existing_cline.start_date <= today <= existing_cline.end_date:
                                existing_cline.status = STATUS_ACTIVE
                            if today < existing_cline.start_date:
                                existing_cline.status = STATUS_PENDING
                            existing_cline.save()
                        else:
                            e_messages = [
                                f'Submitted Line conflicts with existing {existing_cline.get_status_display()} line: {existing_cline.item.get_formatted_ndc()}: Price: {existing_cline.price} with range {existing_cline.start_date.strftime("%m/%d/%Y")}-{existing_cline.end_date.strftime("%m/%d/%Y")}']
                            processing_errors.append({
                                'type': 'overlapping_ranges',
                                'type_text': 'Range Conflict',
                                'message': e_messages,
                                'contract': contract_number,
                                'product': item_ndc,
                                'status': action,
                                'submitted_price': price,
                                'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                                'submitted_end_date': end_date_obj.strftime("%m/%d/%Y"),
                                'price': price
                            })
                            # Go to next line
                            continue

            if action in ['A', 'U']:
                if save_new_line:
                    if today < start_date_obj:
                        new_status = STATUS_PENDING
                    elif today > end_date_obj:
                        new_status = STATUS_INACTIVE
                    else:
                        new_status = STATUS_ACTIVE

                # create Contract line instance
                contract_line = ContractLine(contract=contract,
                                             item=item,
                                             price=price,
                                             start_date=start_date_obj,
                                             end_date=end_date_obj,
                                             status=new_status,
                                             type=contract.type)
                contract_line.save()

                change_text = f"For Contract {contract.number} line {contract_line.item.get_formatted_ndc() if contract_line.item else ''} with status {contract_line.get_status_display()} and dates {start_date_obj.strftime('%m/%d/%Y') if start_date_obj else ''} - {end_date_obj.strftime('%m/%d/%Y') if end_date_obj else ''} is added"
                contract_audit_trails(contract=contract.id,
                                      product=contract_line.item.id if contract_line.item else None,
                                      user_email=data['user'].email,
                                      change_type='line',
                                      field_name='',
                                      change_text=change_text)

        if processing_errors:
            excel_file_path, excel_file_name = export_contract_upload(data=processing_errors, company=data['company'])
            return ok_json(data={'error': 'y',
                                 'error_type': 'processing_errors',
                                 'message': 'We could not complete all updates due to conflicts or missing information. Please correct the following items!',
                                 'file': excel_file_path,
                                 'filename': excel_file_name,
                                 'errors': processing_errors})

        # Remove file which was processed after clicking continue
        if check_missing == "1":
            file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE, filename)
            os.remove(file_path)

        # Everything went well so return success message
        return ok_json(data={'error': 'n', 'message': 'Contracts updated successfully!'})

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def download_contract_upload(request, filename):
    data = {'title': 'Download Contract Update Upload'}
    addGlobalData(request, data)

    file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE, filename)
    with open(file_path, 'rb') as f:
        response = HttpResponse(f, content_type="application/force-download")
        response['Content-Disposition'] = f'attachment; filename=%s' % smart_str(filename)
        response['X-Sendfile'] = smart_str(file_path)

    return response


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def contract_upload_file_delete(request, filename):
    data = {'title': 'Contract upload file delete'}
    addGlobalData(request, data)

    try:
        file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE, filename)
        os.remove(file_path)
        return ok_json()

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def download_sample_upload(request):
    # EA-1336 -Add the ability to download an empty template or display to the user what headers they need to include in the file
    response = export_contract_upload_template()
    return response


# Ticket EA-1270 Add the ability to Delete an item from a contract
@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def delete_contract_line(request, contract_id, contract_line_id):
    try:
        data = {}
        data['user'] = request.user
        contract = Contract.objects.get(id=contract_id)
        contract_line = ContractLine.objects.get(contract=contract, id=contract_line_id)

        history = {
            'ndc': contract_line.item.ndc if contract_line.item else '',
            'type': contract_line.get_type_display(),
            'price': float(contract_line.price),
            'status': contract_line.get_status_display(),
            'start_date': contract_line.start_date.strftime('%m/%d/%Y') if contract_line.start_date else '',
            'end_date': contract_line.end_date.strftime('%m/%d/%Y') if contract_line.end_date else '',
        }

        change_text = f"For contract {contract.number} product line {contract_line.item.get_formatted_ndc() if contract_line.item else ''} with status {contract_line.get_status_display()}, price {float(contract_line.price)} and dates {contract_line.start_date.strftime('%m/%d/%Y') if contract_line.start_date else ''} - {contract_line.end_date.strftime('%m/%d/%Y') if contract_line.end_date else ''} is deleted"
        contract_audit_trails(contract=contract.id,
                              product=contract_line.item.id if contract_line.item else None,
                              user_email=data['user'].email,
                              change_type='line',
                              field_name='',
                              change_text=change_text)

        # Audit Trail
        # audit_trail(username=request.user.username,
        #             action=AUDIT_TRAIL_ACTION_DELETED,
        #             ip_address=get_ip_address(request),
        #             entity1_name=contract_line.__class__.__name__,
        #             entity1_id=contract_line_id,
        #             entity1_reference=contract_line.__str__(),
        #             entity2_name=contract.__class__.__name__,
        #             entity2_id=contract_id,
        #             entity2_reference=contract.number,
        #             history=history)

        # delete the cline
        contract_line.delete()

        return ok_json(data={"message": "Contract Line succesfully deleted"})

    except Exception as ex:
        return bad_json(message=ex.__str__())
