from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (AUDIT_TRAIL_ACTION_CREATED, AUDIT_TRAIL_ACTION_EDITED)
from app.management.utilities.functions import (bad_json, audit_trail, get_ip_address, ok_json, query_range,
                                                datatable_handler)
from app.management.utilities.globals import addGlobalData
from erms.models import IndirectCustomer, Contract, Item
from django.db.models import Q, QuerySet


@login_required(redirect_field_name='ret', login_url='/login')
def views(request):
    data = {'title': 'Indirect Customers', 'header_title': 'My Indirect Customers'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['menu_option'] = 'menu_indirect_customers'
    return render(request, "customers/indirect/views.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:
        # queryset
        queryset = IndirectCustomer.objects.all()
        total = queryset.count()
        total_filtered = total
        is_list = False
        search_fields = ['company_name', 'location_number', 'address1', 'zip_code']
        search = request.POST.get('search[value]', '')
        if search:
            q_objects = Q()  # Create an empty Q object to start with
            for field_name in search_fields:
                q_objects |= Q(**{f'{field_name}__icontains': search})
            if not is_list:
                queryset = queryset.filter(q_objects)
            total_filtered = queryset.count()

        if request.POST and request.POST['order[0][column]']:
            ord_index = int(request.POST['order[0][column]'])
            ord_asc = False if request.POST['order[0][dir]'] == 'asc' else True
            ord_column = request.POST[f'columns[{ord_index}][data]']
            if not ord_asc:
                ord_column = f"-{ord_column}"
                queryset = queryset.order_by(ord_column)

        # response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', -1))
        if length > 0:
            queryset = queryset[start:start + length]
            is_summary = True
            data = [elem.dict_for_datatable(is_summary) for elem in queryset]

        # response
        response = {
            'data': data,
            'recordsTotal': total,
            'recordsFiltered': total_filtered,
        }

        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def details_info(request, indirect_customer_id):
    """
        Company's Indirect Customers (Details Info)
    """
    data = {
        'title': 'Indirect Customer Details - Information',
        'header_title': 'Indirect Customer > Info',
        'header_target': '/customers/indirect'
    }
    addGlobalData(request, data)
    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['indirect_customer'] = indirect_customer = IndirectCustomer.objects.get(id=indirect_customer_id)

    # Total Product Revenue (MTD)
    data['total_product_revenue_mtd'] = indirect_customer.get_total_product_revenue_by_range(query_range('MTD'))

    data['menu_option'] = 'menu_indirect_customers'
    return render(request, "customers/indirect/details/info.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def details_contracts(request, indirect_customer_id):
    """
        Company's Indirect Customers (Details Contracts)
    """
    data = {
        'title': 'Indirect Customer Details - Contracts',
        'header_title': 'Indirect Customer > Related Contracts',
        'header_target': '/customers/indirect'
    }
    addGlobalData(request, data)
    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['indirect_customer'] = indirect_customer = IndirectCustomer.objects.get(id=indirect_customer_id)

    # Related Contracts
    data['related_contracts'] = indirect_customer.get_related_contracts_from_history()

    data['menu_option'] = 'menu_indirect_customers'
    return render(request, "customers/indirect/details/contracts.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def details_products(request, indirect_customer_id):
    """
        Company's Indirect Customers (Details Products)
    """
    data = {
        'title': 'Indirect Customer Details - Products',
        'header_title': 'Indirect Customer > Related Products',
        'header_target': '/customers/indirect'
    }
    addGlobalData(request, data)
    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['indirect_customer'] = indirect_customer = IndirectCustomer.objects.get(id=indirect_customer_id)

    # Related Products
    data['related_products'] = indirect_customer.get_related_products_from_history()

    data['menu_option'] = 'menu_indirect_customers'
    return render(request, "customers/indirect/details/products.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def create(request):
    """
        Company's Indirect Customers (manual)
    """
    data = {'title': 'Create Indirect Customer'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    if request.method == 'POST':
        try:
            with transaction.atomic():

                location_number = request.POST.get('location_no', '')
                if not location_number:
                    return bad_json(message='Location number is required')

                company_name = request.POST.get('company_name', '')
                if not company_name:
                    return bad_json(message='Company name is required')

                # EA-957 - Duplicate Location Number.
                existing_indc = IndirectCustomer.objects.filter(location_number=location_number)
                if existing_indc:
                    return bad_json(message='Location number already exists!')

                # create indirect customer
                indirect_customer = IndirectCustomer(company_name=company_name,
                                                     location_number=location_number,
                                                     address1=request.POST.get('address1', ''),
                                                     address2=request.POST.get('address2', ''),
                                                     city=request.POST.get('city', ''),
                                                     state=request.POST.get('state', ''),
                                                     zip_code=request.POST.get('zip_code', ''),
                                                     cot_id=request.POST.get('cot_id', ''),
                                                     gln_no=request.POST.get('gln_no', ''),
                                                     bid_340=request.POST.get('bid_340', ''))
                indirect_customer.save()

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_ACTION_CREATED,
                #             ip_address=get_ip_address(request),
                #             entity1_name=indirect_customer.__class__.__name__,
                #             entity1_id=indirect_customer.get_id_str(),
                #             entity1_reference=indirect_customer.company_name)

                return ok_json(data={'message': 'Customer successfully created!'})
        except Exception as ex:
            return bad_json(message=ex.__str__())
    return HttpResponseRedirect(f"/{data['db_name']}/customers/indirect")


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def edit(request, indirect_customer_id):
    """
        Company's Indirect Customers (Edit)
    """
    data = {'title': 'Edit Indirect Customer', 'header_title': 'Edit Indirect Customer'}
    addGlobalData(request, data)
    if request.method == 'POST':
        try:
            with transaction.atomic():

                history_dict = {}

                # Get Customer from uuid
                indirect_customer = IndirectCustomer.objects.get(id=indirect_customer_id)

                # get current data Before changes to store in history dict for audit
                history_dict['before'] = indirect_customer.get_current_info_for_audit()

                location_number = request.POST.get('location_no', '')
                if not location_number:
                    return bad_json(message='Location number is required')

                company_name = request.POST.get('company_name', '')
                if not company_name:
                    return bad_json(message='Company name is required')

                # edit indirect customer
                indirect_customer.location_number = location_number
                indirect_customer.company_name = company_name
                indirect_customer.address1 = request.POST.get('address1', '')
                indirect_customer.address2 = request.POST.get('address2', '')
                indirect_customer.city = request.POST.get('city', '')
                indirect_customer.state = request.POST.get('state', '')
                indirect_customer.zip_code = request.POST.get('zip_code', '')
                indirect_customer.cot_id = request.POST.get('cot_id', '')
                indirect_customer.gln_no = request.POST.get('gln_no', '')
                indirect_customer.bid_340 = request.POST.get('bid_340', '')
                indirect_customer.save()

                # get current data Before changes to store in history dict for audit
                history_dict['after'] = indirect_customer.get_current_info_for_audit()

                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_ACTION_EDITED,
                #             ip_address=get_ip_address(request),
                #             entity1_name=indirect_customer.__class__.__name__,
                #             entity1_id=indirect_customer.get_id_str(),
                #             entity1_reference=indirect_customer.company_name)
                # EA-869 - Unable to cancel indirect customer changes.
                return ok_json(data={
                    'message': 'Indirect Customer successfully updated!',
                    'redirect_url': f"/{data['db_name']}/customers/indirect/{indirect_customer_id}/details/info"
                })
        except Exception as ex:
            return bad_json(message=ex.__str__())


# EA-869 - Unable to cancel indirect customer changes.
@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def edit_details(request, indirect_customer_id):
    """
        Company's Indirect Customers (Edit Indirect Customer Details)
    """
    data = {
        'title': 'Edit Indirect Customer Details',
        'header_title': 'Edit Indirect Customer',
        'header_target': '/customers/indirect'
    }
    addGlobalData(request, data)
    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['indirect_customer'] = indirect_customer = IndirectCustomer.objects.get(id=indirect_customer_id)

    # Total Product Revenue (MTD)
    data['total_product_revenue_mtd'] = indirect_customer.get_total_product_revenue_by_range(query_range('MTD'))

    data['menu_option'] = 'menu_indirect_customers'
    return render(request, "customers/indirect/edit_details.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_contracts_data(request):
    """
    Load IndirectCustomer's Contracts data
    call DT Handler function with the required params: request, model_obj and search_fields
    """
    try:
        indirect_customer_id = request.POST.get('indirect_customer_id', '')
        if not indirect_customer_id:
            return bad_json(message='No Indirect customer found')

        queryset = Contract.objects.filter(chargebacklinehistory__indirect_customer_ref_id=indirect_customer_id).distinct()
        search_fields = ['number']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=False, indirect_customer_id=indirect_customer_id, indirect_customer_option="contract")
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_products_data(request):
    """
    Load IndirectCustomer's Product data
    call DT Handler function with the required params: request, model_obj and search_fields
    """
    try:
        indirect_customer_id = request.POST.get('indirect_customer_id', '')
        if not indirect_customer_id:
            return bad_json(message='No Indirect customer found')

        queryset = Item.objects.filter(chargebacklinehistory__indirect_customer_ref_id=indirect_customer_id).distinct()
        search_fields = ['ndc']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=False, indirect_customer_id=indirect_customer_id, indirect_customer_option="item")
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())