from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Avg, F, DecimalField, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (AUDIT_TRAIL_ACTION_CREATED, AUDIT_TRAIL_ACTION_EDITED,
                                                STATUS_ACTIVE, CONTRACT_TYPE_DIRECT, CONTRACT_TYPE_INDIRECT,
                                                STATUS_INACTIVE, STATUS_PENDING, STATUS_PROPOSED)
from app.management.utilities.functions import (bad_json,
                                                audit_trail,
                                                get_ip_address,
                                                ok_json,
                                                query_range,
                                                strip_all_none_number_in_string,
                                                datatable_handler)
from app.management.utilities.globals import addGlobalData
from erms.models import Item, AuditTrail, ContractLine, ChargeBackLineHistory


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
        Company's Products (View)
    """
    data = {'title': 'Products', 'header_title': 'My Products'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['menu_option'] = 'menu_products'
    return render(request, "products/products.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    try:
        # Get all items
        queryset = Item.objects.all()

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

        search_fields = ['ndc', 'description']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=True)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def chart_product_performance(request):
    data = {'title': 'Products Chart Performance'}
    addGlobalData(request, data)

    try:
        # Product chart
        query = request.POST.get('range', 'MTD')

        top_ten_items = ChargeBackLineHistory.objects.filter(updated_at__date__range=query_range(query)).values('item_ref').annotate(revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).order_by('-revenue')[:10]
        labels = []
        revenues = []

        for i in top_ten_items:
            try:
                item = Item.objects.get(id=i["item_ref"])
            except:
                item = None

            labels.append(item.ndc if item else '')
            revenues.append(i["revenue"])

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
                    'rgba(255, 159, 64, 0.2)'
                ],
                'borderColor': [
                    'rgba(255,99,132,1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                'borderWidth': 1
            }]
        }

        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def create(request):
    """
        Company's Products (Create)
    """
    data = {'title': 'Create Product'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():

            item_ndc = request.POST.get('item_ndc', '')
            if not item_ndc:
                return bad_json(message="Item NDC is required")

            if len(item_ndc.split('-')) < 3:
                return bad_json(message="Please add all digits in the NDC number")

            if Item.objects.filter(ndc=strip_all_none_number_in_string(item_ndc)).exists():
                return bad_json(message="Item already exist with that NDC number")

            item_account_number = request.POST.get('item_account_number', '')
            if not item_account_number:
                return bad_json(message="Item Account Number is required")

            item_description = request.POST.get('item_description', '')
            item_strength = request.POST.get('item_strength', '')
            item_size = request.POST.get('item_size', None)
            item_brand = request.POST.get('item_brand', '')
            item_upc = request.POST.get('item_upc', '')
            item_status = int(request.POST.get('item_status', STATUS_ACTIVE))

            item = Item(ndc=strip_all_none_number_in_string(item_ndc),
                        description=item_description,
                        account_number=item_account_number,
                        strength=item_strength,
                        size=float(item_size) if item_size else None,
                        brand=item_brand,
                        upc=item_upc,
                        status=item_status)
            item.save()

            # Audit Trail
            # audit_trail(username=request.user.username,
            #             ip_address=get_ip_address(request),
            #             action=AUDIT_TRAIL_ACTION_CREATED,
            #             entity1_name=item.__class__.__name__,
            #             entity1_id=item.get_id_str(),
            #             entity1_reference=item.get_formatted_ndc())

            return ok_json(data={'message': 'Item succesfully created!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def edit(request, item_id):
    """
        Company's Products (Edit)
    """
    data = {'title': 'Edit Product'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():
            history_dict = {}
            item = Item.objects.get(id=item_id)

            item_ndc = request.POST.get('item_ndc', '')
            if not item_ndc:
                return bad_json(message="Item NDC is required")

            if len(item_ndc.split('-')) < 3:
                return bad_json(message="Please add all digits in the NDC number")

            if Item.objects.exclude(id=item.id).filter(ndc=item_ndc).exists():
                return bad_json(message="Another Product exist with the same NDC number")

            item_account_number = request.POST.get('item_account_number', '')
            if not item_account_number:
                return bad_json(message="Item Account Number is required")

            # get current data Before changes to store in history dict for audit
            history_dict['before'] = item.get_current_info_for_audit()

            item.ndc = strip_all_none_number_in_string(item_ndc)
            item.description = request.POST.get('item_description', '')
            item.account_number = request.POST.get('item_account_number', '')
            item.strength = request.POST.get('item_strength', '')
            item.brand = request.POST.get('item_brand', '')
            item.upc = request.POST.get('item_upc', '')
            item.status = int(request.POST.get('item_status', STATUS_ACTIVE))
            item.size = float(request.POST['item_size']) if request.POST['item_size'] and request.POST['item_size'] != 'null' else None
            item.save()

            # get current data After changes to store in history dict for audit
            history_dict['after'] = item.get_current_info_for_audit()

            # Audit Trail
            # audit_trail(username=request.user.username,
            #             ip_address=get_ip_address(request),
            #             action=AUDIT_TRAIL_ACTION_EDITED,
            #             entity1_name=item.__class__.__name__,
            #             entity1_id=item.get_id_str(),
            #             entity1_reference=item.get_formatted_ndc(),
            #             history=history_dict)

            return ok_json(data={'message': 'Item has been successfully udpated!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def details(request, item_id):
    """
        Company's Products - Detail
    """
    data = {'title': 'Product Details', 'header_title': 'Product Detail', 'header_target': '/products'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Company Items
    data['items'] = items = Item.objects.all()
    data['item'] = item = items.get(pk=item_id)

    # Local vars
    total_sold = 0
    contract_price_system = 0
    total_claim_issued = 0

    cb_line_history = ChargeBackLineHistory.objects.filter(updated_at__range=query_range('MTD'), item_id=item_id)

    if cb_line_history:
        item_qty_sum = cb_line_history.aggregate(sum=Sum('item_qty'))['sum']
        total_sold = item_qty_sum if item_qty_sum else 0

        cp_sys_sum = cb_line_history.aggregate(sum=Sum('contract_price_system'))['sum']
        contract_price_system = Decimal(cp_sys_sum).quantize(Decimal(10) ** -2) if cp_sys_sum else 0

        claim_amt_issue = cb_line_history.aggregate(sum=Sum('claim_amount_issue'))['sum']
        total_claim_issued = Decimal(claim_amt_issue).quantize(Decimal(10) ** -2) if claim_amt_issue else 0

    data['total_sold'] = total_sold
    data['contract_price_system'] = contract_price_system
    data['total_claim_issued'] = total_claim_issued

    # data['contract_revenue_mtd'] = Decimal(contract_price_system * total_sold).quantize(Decimal(10) ** -2)
    revenue = cb_line_history.annotate(revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(sum=Sum('revenue'))['sum']
    data['contract_revenue_mtd'] = Decimal(revenue).quantize(Decimal(10) ** -2) if revenue else 0

    # data['avg_contract_price_system'] = Decimal(total_claim_issued / total_sold).quantize(Decimal(10) ** -2) if total_sold else 0
    # EA-1084 - avg CB amount = avg(claim_ammount_issue) where item_ndc/product is in range
    avg_contract_price_system = cb_line_history.aggregate(avg=Avg('claim_amount_issue'))['avg']
    data['avg_contract_price_system'] = Decimal(avg_contract_price_system).quantize(Decimal(10) ** -2) if avg_contract_price_system else 0

    cp_sys_avg = cb_line_history.aggregate(avg=Avg('contract_price_system'))['avg']
    data['avg_claim_issued'] = Decimal(cp_sys_avg).quantize(Decimal(10) ** -2) if cp_sys_avg else 0

    # Get all contract line for this product and direct price
    contract_lines = ContractLine.objects.filter(status=STATUS_ACTIVE)
    data['direct_contracts_lines'] = contract_lines.filter(Q(item__id=item_id), Q(type=CONTRACT_TYPE_DIRECT) | Q(contract__type=CONTRACT_TYPE_DIRECT))
    data['indirect_contracts_lines'] = contract_lines.filter(Q(item__id=item_id), Q(type=CONTRACT_TYPE_INDIRECT) | Q(contract__type=CONTRACT_TYPE_INDIRECT))

    data['latest_audit_trails'] = AuditTrail.objects.filter(entity='Item')[:4]

    data['breadcrumb_title1'] = f' > {item.get_formatted_ndc()}'
    data['menu_option'] = 'menu_products'
    return render(request, "products/details.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def contracts_lines_load_data(request):
    try:
        item_id = request.POST.get('item_id')
        requested_type = request.POST.get('type', 'direct')
        contract_type = CONTRACT_TYPE_DIRECT  # By default filter direct

        if requested_type == 'indirect':
            contract_type = CONTRACT_TYPE_INDIRECT
        # Get all items
        # queryset = ContractLine.objects.filter(status=STATUS_ACTIVE, item__id=item_id, type=contract_type)
        queryset = ContractLine.objects.filter(Q(status=STATUS_ACTIVE), Q(item__id=item_id), Q(type=contract_type) | (Q(contract__type=contract_type)))

        search_fields = ['number', 'price']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=True)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())
