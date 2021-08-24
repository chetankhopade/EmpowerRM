from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (AUDIT_TRAIL_ACTION_CREATED, AUDIT_TRAIL_ACTION_ADDED,
                                                AUDIT_TRAIL_ACTION_EDITED, CUSTOMER_TYPES)
from app.management.utilities.functions import (bad_json, audit_trail, get_ip_address, ok_json,
                                                convert_string_to_date_imports, query_range, datatable_handler)
from app.management.utilities.globals import addGlobalData
from ermm.models import DirectCustomer as GlobalCustomer
from erms.models import DirectCustomer, Contract, Item, Contact, DirectCustomerContact, DistributionCenter


@login_required(redirect_field_name='ret', login_url='/login')
def views(request):
    """
        Company's Customers (View)
    """
    data = {'title': 'Direct Customers', 'header_title': 'My Direct Customers'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['menu_option'] = 'menu_direct_customers'
    return render(request, "customers/direct/views.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    Load Direct Customer data
    call DT Handler function with the required params: request, model_obj and search_fields
    """
    try:
        queryset = DirectCustomer.objects.all()
        search_fields = ['name']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=False)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_distribution_centers_data(request, customer_id):
    """
    Load Customer's Distribution Centers data
    call DT Handler function with the required params: request, model_obj and search_fields
    """
    try:
        direct_customer = DirectCustomer.objects.get(id=customer_id)
        queryset = direct_customer.get_distribution_centers()
        search_fields = ['dea_number', 'name', 'address1', 'address2', 'zip_code']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_distribution_center_json(request, customer_id):
    """
        Company Distributions Centers (JSON response)
    """
    direct_customer = DirectCustomer.objects.get(id=customer_id)
    distribution_centers = serializers.serialize("json", direct_customer.get_distribution_centers())
    return HttpResponse(distribution_centers, content_type="application/javascript")


@login_required(redirect_field_name='ret', login_url='/login')
def serialized_list(request):
    data = {'title': 'Customers API', 'header_title': 'My Customers API'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    q = request.GET.get('term', '')
    indirect_customers = DirectCustomer.objects.all()
    if q:
        indirect_customers = indirect_customers.filter(name__icontains=q)

    # Direct Customers of the company
    results = []
    for customer in indirect_customers:
        results.append({
            'id': customer.id,
            'text': customer.name
        })

    # data = serializers.serialize("json", DirectCustomer.objects.all())
    results.append({"id": 1, "text": "Assign new Customer"})
    return JsonResponse({"results": results}, safe=False)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def create(request):
    """
        Company's Direct Customers (Create)
    """
    data = {'title': 'Create Direct Customer'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    if request.method == 'POST':
        try:
            with transaction.atomic():
                c_account_number = request.POST.get('c_account_number', '')
                c_name = request.POST.get('c_name', '')
                c_type = request.POST.get('c_type', None)
                c_email = request.POST.get('c_email', '')
                c_phone = request.POST.get('c_phone', '')
                c_address1 = request.POST.get('c_address1', '')
                c_address2 = request.POST.get('c_address2', '')
                c_city = request.POST.get('c_city', '')
                c_state = request.POST.get('c_state', '')
                c_zip_code = request.POST.get('c_zip_code', '')

                if not c_name:
                    return bad_json(message="Name field is required")

                exist = GlobalCustomer.objects.filter(name__icontains=c_name).first()
                if exist:
                    return JsonResponse({
                        'result': 'existing',
                        'message': 'We found a match in our master list, would you like to use these details?',
                        'existing_customer': {
                            'id': exist.id,
                            'name': exist.name,
                            'type': exist.type,
                            'email': exist.email,
                            'phone': exist.phone,
                            'address1': exist.address1,
                            'address2': exist.address2,
                            'city': exist.city,
                            'state': exist.state,
                            'zip_code': exist.zip_code,
                        },
                        'new_customer': {
                            'account_number': c_account_number,
                            'name': c_name,
                            'type': c_type,
                            'email': c_email,
                            'phone': c_phone,
                            'address1': c_address1,
                            'address2': c_address2,
                            'city': c_city,
                            'state': c_state,
                            'zip_code': c_zip_code,
                        }
                    })

                direct_customer = DirectCustomer(account_number=c_account_number,
                                                 name=c_name,
                                                 type=c_type,
                                                 email=c_email,
                                                 phone=c_phone,
                                                 address1=c_address1,
                                                 address2=c_address2,
                                                 city=c_city,
                                                 state=c_state,
                                                 zip_code=c_zip_code)
                direct_customer.save()

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_ACTION_CREATED,
                #             ip_address=get_ip_address(request),
                #             entity1_name=direct_customer.__class__.__name__,
                #             entity1_id=direct_customer.get_id_str(),
                #             entity1_reference=direct_customer.name)

                return ok_json(data={'message': 'Customer successfully updated!',
                                     'redirect_url': f"/{data['db_name']}/customers/direct/"})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    data['menu_option'] = 'menu_direct_customers'
    return HttpResponseRedirect(f"/{data['db_name']}/customers/direct/")


@login_required(redirect_field_name='ret', login_url='/login')
def edit(request, customer_id):
    """
        Company's Customers (Edit)
    """
    data = {'title': 'Edit Customer', 'header_title': 'Edit Direct Customer'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['direct_customer'] = direct_customer = DirectCustomer.objects.get(id=customer_id)

    if request.method == 'POST':
        try:
            with transaction.atomic():

                # for audit
                history_dict = {}

                c_account_number = request.POST.get('c_account_number', '')
                c_type = request.POST.get('c_type', None)
                c_name = request.POST.get('c_name', '')
                c_email = request.POST.get('c_email', '')
                c_phone = request.POST.get('c_phone', '')
                c_address1 = request.POST.get('c_address1', '')
                c_address2 = request.POST.get('c_address2', '')
                c_city = request.POST.get('c_city', '')
                c_state = request.POST.get('c_state', '')
                c_zip_code = request.POST.get('c_zip_code', '')

                if not c_name:
                    return bad_json(message="Name is required")

                # check if email is valid
                if c_email:
                    try:
                        validate_email(c_email)
                    except Exception:
                        return bad_json(message='Invalid email address')

                # get current data Before changes to store in history dict for audit
                history_dict['before'] = direct_customer.get_current_info_for_audit()

                # update Local Direct Customer (company db)
                direct_customer.account_number = c_account_number
                direct_customer.name = c_name
                direct_customer.type = int(c_type) if c_type else None
                direct_customer.email = c_email
                direct_customer.phone = c_phone
                direct_customer.address1 = c_address1
                direct_customer.address2 = c_address2
                direct_customer.city = c_city
                direct_customer.state = c_state
                direct_customer.zip_code = c_zip_code
                direct_customer.save()

                # get current data After changes to store in history dict for audit
                history_dict['after'] = direct_customer.get_current_info_for_audit()

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_ACTION_EDITED,
                #             ip_address=get_ip_address(request),
                #             entity1_name=direct_customer.__class__.__name__,
                #             entity1_id=direct_customer.get_id_str(),
                #             entity1_reference=direct_customer.name)

                return ok_json(data={'message': 'Customer successfully updated!',
                                     'redirect_url': f"/{data['db_name']}/customers/direct/{customer_id}/details/info"})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    data['menu_option'] = 'menu_direct_customers'
    return render(request, "customers/direct/edit.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add(request):
    """
        Company's Customers (Add Customers from Global List)
    """
    data = {'title': 'Add Customers', 'header_title': 'Direct Customers - Assign'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    if request.method == 'POST':
        try:
            with transaction.atomic():
                direct_customer = None
                for customer_id in request.POST['customers_ids_list'].split(','):
                    if not DirectCustomer.objects.filter(customer_id=customer_id).exists():
                        # get the global customer
                        global_customer = GlobalCustomer.objects.get(id=customer_id)
                        # manual a direct customer with global customer fields values as default
                        direct_customer = DirectCustomer(customer_id=customer_id,
                                                         name=global_customer.name,
                                                         email=global_customer.email,
                                                         phone=global_customer.phone,
                                                         address1=global_customer.address1,
                                                         address2=global_customer.address2,
                                                         city=global_customer.city,
                                                         state=global_customer.state,
                                                         zip_code=global_customer.zip_code)
                        direct_customer.save()

                        # Audit Trail
                        # audit_trail(username=request.user.username,
                        #             action=AUDIT_TRAIL_ACTION_ADDED,
                        #             ip_address=get_ip_address(request),
                        #             entity1_name=direct_customer.__class__.__name__,
                        #             entity1_id=direct_customer.get_id_str(),
                        #             entity1_reference=direct_customer.name)

                return ok_json(data={
                    'message': 'Customer(s) successfully added!',
                    'redirect_url': f'/{data["db_name"]}/customers/direct/',
                    'new_customer_id': str(direct_customer.id) if direct_customer else '',
                    'new_customer_name': direct_customer.name
                })

        except Exception as ex:
            return bad_json(message=ex.__str__())

    # current DirectCustomer ID list
    current_customers_ids = [x.customer_id for x in DirectCustomer.objects.all() if x.customer_id]

    # Global Customers (exclude those customer that are already in the company Direct Customer table)
    data['global_customers'] = GlobalCustomer.objects.exclude(id__in=current_customers_ids).all()

    data['menu_option'] = 'menu_direct_customers'
    return render(request, "customers/direct/add.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add_existing(request):
    """
        Company's Direct Customers (Create)
    """
    data = {'title': 'Create Direct Customer'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    if request.method == 'POST':
        try:
            with transaction.atomic():
                c_account_number = request.POST.get('c_account_number', '')
                c_name = request.POST.get('c_name', '')
                c_type = request.POST.get('c_type', None)
                c_email = request.POST.get('c_email', '')
                c_phone = request.POST.get('c_phone', '')
                c_address1 = request.POST.get('c_address1', '')
                c_address2 = request.POST.get('c_address2', '')
                c_city = request.POST.get('c_city', '')
                c_state = request.POST.get('c_state', '')
                c_zip_code = request.POST.get('c_zip_code', '')

                if not c_name:
                    return bad_json(message="Name field is required")

                direct_customer = DirectCustomer(name=c_name,
                                                 account_number=c_account_number,
                                                 type=c_type,
                                                 email=c_email,
                                                 phone=c_phone,
                                                 address1=c_address1,
                                                 address2=c_address2,
                                                 city=c_city,
                                                 state=c_state,
                                                 zip_code=c_zip_code)
                direct_customer.save()

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_ACTION_ADDED,
                #             ip_address=get_ip_address(request),
                #             entity1_name=direct_customer.__class__.__name__,
                #             entity1_id=direct_customer.get_id_str(),
                #             entity1_reference=direct_customer.name)

                return ok_json(data={'message': 'Customer successfully added!',
                                     'new_customer_id': direct_customer.get_id_str(),
                                     'new_customer_name': direct_customer.name})
        except Exception as ex:
            return bad_json(message=ex.__str__())
    return HttpResponseRedirect(f"/{data['db_name']}/customers/direct/")


@login_required(redirect_field_name='ret', login_url='/login')
def metadata(request, customer_id):
    """
        Company's Customers (Add Metadata for local Customer)
    """
    data = {'title': 'Add Metadata'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    direct_customer = DirectCustomer.objects.get(id=customer_id)

    if request.method == 'POST':

        try:
            with transaction.atomic():

                c_field = request.POST['c_field']
                c_value = request.POST['c_value']

                direct_customer.metadata[c_field] = c_value
                direct_customer.save()

                return ok_json(data={'message': 'Metadata successfully added!'})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    return HttpResponseRedirect(f"/{data['db_name']}/customers/direct/")


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def remove_metadata(request, customer_id, key):
    """
        Company's Customers (Remove Metadata for local Customer)
    """
    data = {'title': 'Add Metadata'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    direct_customer = DirectCustomer.objects.get(id=customer_id)

    if request.method == 'POST':

        try:
            with transaction.atomic():

                direct_customer.metadata.pop(key)
                direct_customer.save()

                return ok_json(data={'message': 'Metadata successfully removed!'})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    return HttpResponseRedirect(f"/{data['db_name']}/customers/direct/")


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def details_info(request, customer_id):
    """
        Company's Customers (Details)
    """
    data = {'title': 'Customer Details - Information'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['direct_customer'] = direct_customer = DirectCustomer.objects.get(id=customer_id)
    try:
        direct_customer_type = CUSTOMER_TYPES[direct_customer.type - 1]
    except:
        direct_customer_type = None

    data['direct_customer_type'] = direct_customer_type

    data['menu_option'] = 'menu_direct_customers'
    data['header_title'] = f'{direct_customer.name} > Info'
    data['active_tab'] = 'i'
    return render(request, "customers/direct/details/dcinfo.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def details_contracts(request, customer_id):
    """
        Company's Customers (Details Contracts)
    """
    data = {'title': 'Customer Details - Contracts'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['direct_customer'] = direct_customer = DirectCustomer.objects.get(id=customer_id)

    data['menu_option'] = 'menu_direct_customers'
    data['header_title'] = f'{direct_customer.name} > Contracts'
    data['customer_has_contracts'] = Contract.objects.filter(Q(customer=direct_customer) |
                                                             Q(contractcustomer__customer=direct_customer)).exists()
    data['active_tab'] = 'c'
    return render(request, "customers/direct/details/dccontracts.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_contracts_data(request, customer_id):
    """
    Load Customer's Contracts data
    call DT Handler function with the required params: request, model_obj and search_fields
    """
    try:
        direct_customer = DirectCustomer.objects.get(id=customer_id)
        queryset = Contract.objects.filter(Q(customer=direct_customer) |
                                           Q(contractcustomer__customer=direct_customer)).distinct()
        search_fields = ['number']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def details_products(request, customer_id):
    """
        Company's Customers (Details Products)
    """
    data = {'title': 'Direct Customer Details - Products'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['direct_customer'] = direct_customer = DirectCustomer.objects.get(id=customer_id)

    data['menu_option'] = 'menu_direct_customers'
    data['header_title'] = f'{direct_customer.name} > Products'
    data['customer_has_products'] = Item.objects.filter(Q(contractline__contract__customer=direct_customer) |
                                                        Q(contractline__contract__contractcustomer__customer=direct_customer)).exists()
    data['active_tab'] = 'p'
    return render(request, "customers/direct/details/dcproducts.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_products_data(request, customer_id):
    """
    Load Customer's Products data
    call DT Handler function with the required params: request, model_obj and search_fields
    """
    try:
        direct_customer = DirectCustomer.objects.get(id=customer_id)
        queryset = Item.objects.filter(Q(contractline__contract__customer=direct_customer) |
                                       Q(contractline__contract__contractcustomer__customer=direct_customer)).distinct()
        search_fields = ['description', 'ndc']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def details_distributors(request, customer_id):
    """
        Company's Customers (Details Distributions Centers)
    """
    data = {'title': 'Direct Customer Details - Distributions Centers'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['direct_customer'] = direct_customer = DirectCustomer.objects.get(id=customer_id)

    if request.method == 'POST':
        try:
            with transaction.atomic():

                dc_id = request.POST.get('dc_id', '')

                dc_dea = request.POST.get('dc_dea', '')
                if not dc_dea:
                    return bad_json(message='DEA field is required')
                if not dc_id and DistributionCenter.objects.filter(dea_number=dc_dea.strip()).exists():
                    return bad_json(message="Distribution Center already exist with that DEA No. in this company")
                if dc_id and DistributionCenter.objects.filter(dea_number=dc_dea.strip()).exclude(id=dc_id).exists():
                    return bad_json(message="Distribution Center already exist with that DEA No. in this company")
                dc_name = request.POST.get('dc_name', '')
                if not dc_name:
                    return bad_json(message='Name field is required')

                dc_address1 = request.POST.get('dc_address1', '')
                if not dc_address1:
                    return bad_json(message='Address1 field is required')

                dc_address2 = request.POST.get('dc_address2', '')
                dc_city = request.POST.get('dc_city', '')
                dc_state = request.POST.get('dc_state', '')
                dc_zip_code = request.POST.get('dc_zip_code', '')

                # New or Existing Distro
                if dc_id:
                    dc = DistributionCenter.objects.get(id=dc_id)
                    dc.dea_number = dc_dea
                    dc.name = dc_name
                    dc.address1 = dc_address1
                    dc.address2 = dc_address2
                    dc.city = dc_city
                    dc.state = dc_state
                    dc.zip_code = dc_zip_code
                else:
                    dc = DistributionCenter(customer=direct_customer,
                                            dea_number=dc_dea,
                                            name=dc_name,
                                            address1=dc_address1,
                                            address2=dc_address2,
                                            city=dc_city,
                                            state=dc_state,
                                            zip_code=dc_zip_code)
                # save
                dc.save()

                return ok_json({'message': f'DistributionCenter successfully {"udpated" if dc_id else "created"}'})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    data['customer_has_distribution_centers'] = direct_customer.has_distribution_centers()
    data['menu_option'] = 'menu_direct_customers'
    data['header_title'] = f'{direct_customer.name} > Distributors'
    data['active_tab'] = 'd'
    return render(request, "customers/direct/details/dcdistributors.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def details_contacts(request, customer_id):
    """
        Company's Customer (Details Contacts)
    """
    data = {'title': 'Direct Customer Details - Contacts'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['direct_customer'] = direct_customer = DirectCustomer.objects.get(id=customer_id)

    if request.method == 'POST':
        try:
            with transaction.atomic():

                contact_id = request.POST.get('cid', '')

                first_name = request.POST.get('first_name', '')
                if not first_name:
                    return bad_json(message='Firstname field is required')

                email = request.POST.get('email', '')
                if not email:
                    return bad_json(message='Email field is required')

                # check if email is valid
                try:
                    validate_email(email)
                except Exception:
                    return bad_json(message='Invalid email address')

                # check if email is unique for this contact
                if (not contact_id and Contact.objects.filter(email=email).exists()) or (contact_id and Contact.objects.filter(email=email).exclude(id=contact_id).exists()):
                    return bad_json(message='The email already exist for other Contact in this company')

                last_name = request.POST.get('last_name', '')
                phone = request.POST.get('phone', '')
                job_title = request.POST.get('job_title', '')

                # New or Existing Contact
                if contact_id:
                    contact = Contact.objects.get(id=contact_id)
                    contact.first_name = first_name
                    contact.last_name = last_name
                    contact.email = email
                    contact.phone = phone
                    contact.job_title = job_title
                else:
                    contact = Contact(first_name=first_name,
                                      last_name=last_name,
                                      email=email,
                                      phone=phone,
                                      job_title=job_title)
                # save
                contact.save()

                # Direct Customer - Contact relationship
                DirectCustomerContact.objects.get_or_create(direct_customer=direct_customer, contact=contact)

                return ok_json({'message': f'Contact successfully {"udpated" if contact_id else "created"}'})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    # Get all Contacts related with the Customer
    data['contacts'] = Contact.objects.filter(directcustomercontact__direct_customer=direct_customer).distinct()

    data['menu_option'] = 'menu_direct_customers'
    data['header_title'] = f'{direct_customer.name} > Contacts'
    data['active_tab'] = 't'
    return render(request, "customers/direct/details/dccontacts.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_contacts_data(request, customer_id):
    """
    Load Customer's Contacts data
    call DT Handler function with the required params: request, model_obj and search_fields
    """
    try:
        direct_customer = DirectCustomer.objects.get(id=customer_id)
        queryset = Contact.objects.filter(directcustomercontact__direct_customer=direct_customer).distinct()
        search_fields = ['first_name', 'last_name', 'email', 'phone', 'job_title']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def delete_contact(request, customer_id, contact_id):
    """
        Delete Contact
    """
    try:
        with transaction.atomic():
            contact = Contact.objects.get(id=contact_id)
            DirectCustomerContact.objects.filter(direct_customer_id=customer_id, contact_id=contact_id).delete()
            contact.delete()
            return ok_json(data={'message': 'Contact succesfully deleted!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def create_distribution_center(request, customer_id):
    """
        Company's Distribution Centers (Create)
    """
    data = {'title': 'Create Distribution Center'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    direct_customer = DirectCustomer.objects.get(id=customer_id)

    try:
        with transaction.atomic():

            dc_dea_number = request.POST.get('dc_dea_number', '')
            if not dc_dea_number:
                return bad_json(message='DEA Number is required')

            if DistributionCenter.objects.filter(dea_number=dc_dea_number).exists():
                return bad_json(message="Distribution Center already exist with that DEA No. in this company")

            dc_name = request.POST.get('dc_name', '')
            if not dc_name:
                return bad_json(message='Name is required')

            dc_address1 = request.POST.get('dc_address1', '')
            if not dc_address1:
                return bad_json(message='Address1 is required')

            dc_address2 = request.POST.get('dc_address2', '')
            dc_city = request.POST.get('dc_city', '')
            dc_state = request.POST.get('dc_state', '')
            dc_zip_code = request.POST.get('dc_zip_code', '')

            distribution_center = DistributionCenter(customer=direct_customer,
                                                     name=dc_name,
                                                     dea_number=dc_dea_number,
                                                     address1=dc_address1,
                                                     address2=dc_address2,
                                                     city=dc_city,
                                                     state=dc_state,
                                                     zip_code=dc_zip_code)
            distribution_center.save()

            # Audit Trail
            # audit_trail(username=request.user.username,
            #             action=AUDIT_TRAIL_ACTION_CREATED,
            #             ip_address=get_ip_address(request),
            #             entity1_name=distribution_center.__class__.__name__,
            #             entity1_id=distribution_center.get_id_str(),
            #             entity1_reference=distribution_center.name,
            #             entity2_name=direct_customer.__class__.__name__,
            #             entity2_id=direct_customer.get_id_str(),
            #             entity2_reference=direct_customer.name)

            return ok_json(data={'message': 'Distribution Center has been successfully created!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def edit_distribution_center(request, customer_id, distribution_center_id):
    """
        Company's Distribution Centers (Edit)
    """
    data = {'title': 'Edit Distribution Center', 'header_title': 'Edit Distribution Center'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get DistributionCenter from request
    distribution_center = DistributionCenter.objects.get(id=distribution_center_id, customer_id=customer_id)

    try:
        with transaction.atomic():

            history_dict = {}

            dc_dea_number = request.POST.get('dc_dea_number', '')
            if not dc_dea_number:
                return bad_json(message='DEA Number is required')

            if DistributionCenter.objects.filter(dea_number=dc_dea_number).exclude(id=distribution_center_id).exists():
                return bad_json(message="Distribution Center already exist with that DEA No. in this company")

            dc_name = request.POST.get('dc_name', '')
            if not dc_name:
                return bad_json(message='Name is required')

            dc_address1 = request.POST.get('dc_address1', '')
            if not dc_address1:
                return bad_json(message='Address1 is required')

            dc_address2 = request.POST.get('dc_address2', '')
            dc_city = request.POST.get('dc_city', '')
            dc_state = request.POST.get('dc_state', '')
            dc_zip_code = request.POST.get('dc_zip_code', '')

            # Ticket EA-726: Only Allow Save if a field was edited.
            if distribution_center.dea_number == dc_dea_number and \
                    distribution_center.name == dc_name and \
                    distribution_center.address1 == dc_address1 and \
                    distribution_center.address2 == dc_address2 and \
                    distribution_center.city == dc_city and \
                    distribution_center.state == dc_state and \
                    distribution_center.zip_code == dc_zip_code:
                return ok_json({'result': 'no_changes'})

            # get current data Before changes to store in history dict for audit
            history_dict['before'] = distribution_center.get_current_info_for_audit()

            distribution_center.dea_number = dc_dea_number
            distribution_center.name = dc_name
            distribution_center.address1 = dc_address1
            distribution_center.address2 = dc_address2
            distribution_center.city = dc_city
            distribution_center.state = dc_state
            distribution_center.zip_code = dc_zip_code
            distribution_center.save()

            # get current data After changes to store in history dict for audit
            history_dict['after'] = distribution_center.get_current_info_for_audit()

            # Audit Trail
            # audit_trail(username=request.user.username,
            #             action=AUDIT_TRAIL_ACTION_EDITED,
            #             ip_address=get_ip_address(request),
            #             entity1_name=distribution_center.__class__.__name__,
            #             entity1_id=distribution_center.get_id_str(),
            #             entity1_reference=distribution_center.name,
            #             entity2_name=distribution_center.direct_customer.__class__.__name__,
            #             entity2_id=distribution_center.direct_customer.get_id_str(),
            #             entity2_reference=distribution_center.direct_customer.name)

            return ok_json(data={'message': 'Distribution Center successfully updated!',
                                 'redirect_url': f'/{data["db_name"]}/customers/'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


def get_direct_customer_data(request, customer_id):
    data = {'title': 'Dashboard', 'header_title': 'My Dashboard'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['direct_customer_obj'] = direct_customer = DirectCustomer.objects.get(id=customer_id)

    start_date = None
    if 's' in request.GET and request.GET['s']:
        data['start_date'] = start_date = convert_string_to_date_imports(request.GET['s'])

    end_date = None
    if 'e' in request.GET and request.GET['e']:
        data['end_date'] = end_date = convert_string_to_date_imports(request.GET['e'])

    range = None
    if 'r' in request.GET and request.GET['r']:
        data['range'] = range = convert_string_to_date_imports(request.GET['r'])

    if range:
        query = query_range(range)
    else:
        query = [start_date, end_date]

    distribution_centers = []
    for dc in direct_customer.get_distribution_centers():
        revenue = dc.get_my_revenue_by_range(query)
        if revenue:
            distribution_centers.append({
                'name': dc.name,
                'color': dc.get_random_color_for_charts(),
                'revenue': revenue
            })

    contracts = []
    for ct in direct_customer.get_active_contracts():
        revenue = ct.get_my_revenue_by_range(query)
        if revenue:
            contracts.append({
                'name': ct.number,
                'color': ct.get_random_color(),
                'revenue': revenue
            })

    items = []
    for it in direct_customer.get_my_items_from_history():
        revenue = it.get_my_revenue_by_range(query)
        if revenue:
            items.append({
                'name': it.ndc,
                'color': it.get_random_color(),
                'revenue': revenue
            })

    direct_customer_data_dict = {
        'distros': distribution_centers,
        'contracts': contracts,
        'items': items
    }

    data['menu_option'] = 'menu_direct_customers'
    data['direct_customer_data_dict'] = direct_customer_data_dict
    return render(request, 'dashboard/includes/charts.html', data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def duplicate_distributors(request, customer_id):
    """
        Company's Customers (Details Distributions Centers)
    """
    data = {'title': 'Direct Customer Details - Distributions Centers'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Customer from uuid
    data['direct_customer'] = direct_customer = DirectCustomer.objects.get(id=customer_id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                dc_dea = request.POST.get('dc_dea', '')
                dc_id = request.POST.get('dc_id', '')
                if not dc_dea:
                    return bad_json(message='DEA field is required')
                if dc_id and DistributionCenter.objects.filter(dea_number=dc_dea.strip()).exclude(id=dc_id).exists():
                    return bad_json(message="Duplicate DEA No.")
                if not dc_id and DistributionCenter.objects.filter(dea_number=dc_dea.strip()).exists():
                    return bad_json(message="Duplicate DEA No.")
                return ok_json(data={'message': 'No Duplicate'})

        except Exception as ex:
            return bad_json(message=ex.__str__())
