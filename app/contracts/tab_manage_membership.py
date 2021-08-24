import datetime
import json
from empowerb.middleware import db_ctx
from django.contrib.auth.decorators import login_required
from django.db import transaction, connections
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (STATUS_ACTIVE, STATUS_PENDING, STATUS_INACTIVE,
                                                AUDIT_TRAIL_ACTION_ADDED, STATUS_PROPOSED)
from app.management.utilities.functions import (bad_json, convert_string_to_date, ok_json,
                                                datatable_handler, audit_trail, get_ip_address, valid_range, )
from app.management.utilities.globals import addGlobalData
from erms.models import Contract, IndirectCustomer, ContractMember


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request, contract_id):
    try:
        db_name = db_ctx.get()
        # Get Contract and Indirect customers (Membership) through ContractMember relationship
        # contract = Contract.objects.get(id=contract_id)
        # queryset = Contract.objects.get(id=contract_id).get_my_membership().filter(contract_id=contract_id)
        cursor = connections[db_name].cursor()
        contract_id = contract_id.__str__()
        contract_id = contract_id.replace('-', '')
        query = f"SELECT contracts_indirect_customers.id, contracts.number, indirect_customers.location_number, indirect_customers.company_name, indirect_customers.address1, indirect_customers.address2, indirect_customers.city, indirect_customers.state,indirect_customers.zip_code,class_of_trade.trade_class,contracts_indirect_customers.start_date, contracts_indirect_customers.end_date, contracts_indirect_customers.status, indirect_customers.bid_340 FROM contracts_indirect_customers INNER JOIN contracts ON (contracts_indirect_customers.contract_id = contracts.id) LEFT JOIN indirect_customers ON (contracts_indirect_customers.indirect_customer_id = indirect_customers.id) LEFT JOIN class_of_trade ON (indirect_customers.cot_id = class_of_trade.id) WHERE (contracts_indirect_customers.contract_id = '{contract_id}' AND contracts_indirect_customers.contract_id = '{contract_id}'"

        # query by status - By default filter active
        # q = int(request.POST.get('q', STATUS_ACTIVE))
        # if q:
        #     if q == STATUS_ACTIVE:
        #         queryset = queryset.filter(status=STATUS_ACTIVE)
        #     elif q == STATUS_INACTIVE:
        #         queryset = queryset.filter(status=STATUS_INACTIVE)
        #     elif q == STATUS_PENDING:
        #         queryset = queryset.filter(status=STATUS_PENDING)
        #     elif q == STATUS_PROPOSED:
        #         queryset = queryset.filter(status=STATUS_PROPOSED)
        #     else:
        #         queryset = Contract.objects.get(id=contract_id).get_my_membership().filter(contract_id=contract_id)
        #

        q = int(request.POST.get('q', STATUS_ACTIVE))
        if q:
            if q == STATUS_ACTIVE:
                query = query + f" AND contracts_indirect_customers.status={STATUS_ACTIVE})"
            elif q == STATUS_INACTIVE:
                query = query + f" AND contracts_indirect_customers.status={STATUS_INACTIVE})"
            elif q == STATUS_PENDING:
                query = query + f" AND contracts_indirect_customers.status={STATUS_PENDING})"
            elif q == STATUS_PROPOSED:
                query = query + f" AND contracts_indirect_customers.status={STATUS_PROPOSED})"
            else:
                query = query + ")"
        else:
            query = query + ")"
        # search_fields = ['company_name', 'location_number', 'bid_340']
        # total = queryset.count()
        # total_filtered = total
        # is_list = False
        # is_summary = True
        # # search_fields = ['company_name', 'location_number', 'bid_340']
        # search = request.POST.get('search[value]', '')
        # if search:
        #     q_objects = Q()  # Create an empty Q object to start with
        #     for field_name in search_fields:
        #         if field_name == 'number':
        #             q_objects |= Q(**{'contract__number__icontains': search})
        #         elif field_name == 'company_name':
        #             q_objects |= Q(**{'indirect_customer__company_name__icontains': search})
        #         elif field_name == 'location_number':
        #             q_objects |= Q(**{'indirect_customer__location_number__icontains': search})
        #         elif field_name == 'bid_340':
        #             q_objects |= Q(**{'indirect_customer__bid_340__icontains': search})
        #         else:
        #             q_objects |= Q(**{f'{field_name}__icontains': search})
        #     if not is_list:
        #         queryset = queryset.filter(q_objects)
        #     total_filtered = queryset.count()
        search_fields = ['company_name', 'location_number', 'bid_340']
        total = cursor.rowcount
        total_filtered = total
        search = request.POST.get('search[value]', '')
        if search:
            q_objects = Q()  # Create an empty Q object to start with
            for field_name in search_fields:
                if field_name == 'company_name':
                    query = query + f" AND (indirect_customers.company_name LIKE '%{search}%'"
                elif field_name == 'location_number':
                    query = query + f" OR indirect_customers.location_number LIKE '%{search}%'"
                elif field_name == 'bid_340':
                    query = query + f" OR indirect_customers.bid_340 LIKE '%{search}%')"
                else:
                    query = query
        #
        # if request.POST and request.POST['order[0][column]']:
        #     ord_index = int(request.POST['order[0][column]'])
        #     ord_asc = False if request.POST['order[0][dir]'] == 'asc' else True
        #     ord_column = request.POST[f'columns[{ord_index}][data]']
        #
        #     if ord_column == 'location_number':
        #         ord_column = "indirect_customer__location_number"
        #     elif ord_column == 'bid_340':
        #         ord_column = "indirect_customer__bid_340"
        #     elif ord_column == 'company_name':
        #         ord_column = 'indirect_customer__company_name'

        if request.POST and request.POST['order[0][column]']:
            ord_index = int(request.POST['order[0][column]'])
            ord_asc = False if request.POST['order[0][dir]'] == 'asc' else True
            ord_column = request.POST[f'columns[{ord_index}][data]']
            if ord_column == 'location_number':
                ord_column = "indirect_customers.location_number"
            elif ord_column == 'bid_340':
                ord_column = "indirect_customers.bid_340"
            elif ord_column == 'company_name':
                ord_column = "indirect_customers.company_name"
            elif ord_column == 'indirect_customer__address1':
                ord_column = "indirect_customers.address1"
            elif ord_column == 'indirect_customer__city':
                ord_column = "indirect_customers.city"
            elif ord_column == 'indirect_customer__state':
                ord_column = "indirect_customers.state"
            elif ord_column == 'indirect_customer__zip_code':
                ord_column = "indirect_customers.zip_code"
            elif ord_column == 'indirect_customer__cot__trade_class':
                ord_column = "indirect_customers.cot_id"
            elif ord_column == 'start_date':
                ord_column = "contracts_indirect_customers.start_date"
            elif ord_column == 'end_date':
                ord_column = "contracts_indirect_customers.end_date"
            elif ord_column == 'status':
                ord_column = "contracts_indirect_customers.status"

            if not ord_asc:
                query = query + f" ORDER BY {ord_column} DESC"
            else:
                query = query + f" ORDER BY {ord_column} ASC"

        #
        #     if not ord_asc:
        #         ord_column = f"-{ord_column}"
        #     queryset = queryset.order_by(ord_column)
        #
        # start = int(request.POST.get('start', 0))
        # length = int(request.POST.get('length', -1))
        # if length > 0:
        #     queryset = queryset[start:start + length]
        cursor.execute(query)
        total = cursor.rowcount
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', -1))
        if length > 0:
            query = query + f" LIMIT {start},{length}"
        # print(query)
        cursor.execute(query)
        total_filtered = total
        queryset = cursor.fetchall()
        time1 = datetime.datetime.now()
        data = []
        print('start')
        for elem in queryset:
            jsonData = dict()
            status = ''
            if elem[12] == 1:
                status = 'Active'
            elif elem[12] == 2:
                status = 'Inactive'
            elif elem[12] == 3:
                status = 'Pending'
            elif elem[12] == 4:
                status = 'Proposed'

            jsonData.update({'DT_RowId': elem[0], 'id': elem[0], 'number': elem[1], 'location_number': elem[2], 'company_name': elem[3], 'indirect_customer___complete_address': f"{elem[4]} {elem[5]}", 'indirect_customer__address1': elem[4], 'indirect_customer__address2': elem[5], 'indirect_customer__city': elem[6], 'indirect_customer__state': elem[7], 'indirect_customer__zip_code': elem[8], 'indirect_customer__cot__trade_class': elem[9], 'start_date': elem[10].strftime('%m/%d/%Y'), 'end_date': elem[11].strftime('%m/%d/%Y'), 'bid_340': '', 'status': status})
            data.append(jsonData)
        # data = [elem.dict_for_datatable(is_summary) for elem in queryset]
        time2 = datetime.datetime.now()
        delta = (time2 - time1).total_seconds()
        print(f"Delta Time Queryset: {delta} sec")

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
def update_membership_list(request, contract_id):
    try:
        with transaction.atomic():
            # Get Contract
            contract = Contract.objects.get(id=contract_id)

            # Contract Lines (with changed prices)
            membership_list = json.loads(request.POST['membership_list'])
            contract_start_date = contract.start_date
            contract_end_date = contract.end_date

            if membership_list:

                # loop over all checked elements in the list and create relationship with the Contract
                membership_errors = []
                for elem in membership_list:

                    save_new_line = True

                    today = datetime.datetime.now().date()
                    indirect_customer_id = elem['icid']
                    start_date = convert_string_to_date(elem['start_date'])
                    end_date = convert_string_to_date(elem['end_date'])

                    validation_errors = validate_membership_line(contract_id, elem['icid'], contract_start_date,
                                                                 contract_end_date, start_date, end_date)
                    indirect_customer = IndirectCustomer.objects.get(id=indirect_customer_id)
                    if len(validation_errors["message"]) > 0:

                        membership_errors.append({
                            "indirect_customer_id": elem['icid'],
                            "indirect_customer_name": indirect_customer.company_name,
                            "indirect_customer_location_number": indirect_customer.location_number,
                            "start_date": elem['start_date'],
                            "end_date": elem['end_date'],
                            "line_validation": validation_errors["line_validation"],
                            "contract_validation": validation_errors["contract_validation"],
                            "error_messages": validation_errors["message"]
                        })

                    else:

                        existing_membership_lines = ContractMember.objects.filter(contract=contract, indirect_customer=indirect_customer)
                        existing_cm = existing_membership_lines[0] if existing_membership_lines.exists() else None

                        if existing_cm:
                            # 953 - Membership Issues (For same dates)
                            if (start_date == existing_cm.start_date and end_date == existing_cm.end_date) or (start_date > existing_cm.start_date and end_date < existing_cm.end_date):
                                save_new_line = False

                            elif start_date > existing_cm.start_date and end_date >= existing_cm.end_date:
                                day_to_adjust = datetime.timedelta(1)
                                # Ending existing line one day prior new start date
                                existing_cm.end_date = start_date - day_to_adjust
                                existing_cm.status = STATUS_INACTIVE
                                # There can be multiple pending lines.
                                if today < existing_cm.start_date:
                                    existing_cm.status = STATUS_PENDING

                                existing_cm.save()

                            elif start_date <= existing_cm.start_date and end_date < existing_cm.end_date:
                                day_to_adjust = datetime.timedelta(1)
                                # Moving existing start date to day after new end date
                                existing_cm.start_date = end_date + day_to_adjust
                                # There can be multiple pending lines.
                                if today < existing_cm.start_date:
                                    existing_cm.status = STATUS_PENDING
                                elif today > existing_cm.end_date:
                                    existing_cm.status = STATUS_INACTIVE

                                existing_cm.save()
                            # for complete inner overlap i.e. do not take any action
                            elif start_date < existing_cm.start_date and end_date > existing_cm.end_date:
                                # Extend the existing line
                                existing_cm.start_date = start_date
                                existing_cm.end_date = end_date
                                if today < existing_cm.start_date:
                                    existing_cm.status = STATUS_PENDING
                                elif today > existing_cm.end_date:
                                    existing_cm.status = STATUS_INACTIVE
                                else:
                                    existing_cm.status = STATUS_ACTIVE
                                existing_cm.save()
                                save_new_line = False

                        if save_new_line:
                            if today < start_date:
                                new_status = STATUS_PENDING
                            elif today > end_date:
                                new_status = STATUS_INACTIVE
                            else:
                                new_status = STATUS_ACTIVE

                            # create ManageMembership instance
                            manage_membership = ContractMember(contract=contract,
                                                               indirect_customer_id=indirect_customer_id,
                                                               start_date=start_date,
                                                               end_date=end_date,
                                                               status=new_status)
                            manage_membership.save()

                            # Audit Trail
                            # audit_trail(username=request.user.username,
                            #             action=AUDIT_TRAIL_ACTION_ADDED,
                            #             ip_address=get_ip_address(request),
                            #             entity1_name=manage_membership.__class__.__name__,
                            #             entity1_id=manage_membership.get_id_str(),
                            #             entity1_reference=manage_membership.get_id_str(),
                            #             entity2_name=contract.__class__.__name__,
                            #             entity2_id=contract.get_id_str(),
                            #             entity2_reference=contract.number)
                if len(membership_errors) > 0:
                    return ok_json(data={'error': 'y',
                                         'message': 'We found some errors for few Indirect customers!',
                                         'membership_errors_list': membership_errors})
                return ok_json(data={'message': 'Membership has been successfully updated to the Contract!'})

            return bad_json(message='Membership List is empty')
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def update_membership_lines_changes(request, contract_id):
    try:
        with transaction.atomic():

            # Get Contract
            contract = Contract.objects.get(id=contract_id)

            cmembership_list = request.POST.get('cmembership_list')
            if cmembership_list:

                for data in cmembership_list.split("|"):
                    # get elem
                    elem = data.split(':')
                    contract_member = contract.get_my_contract_membership_lines().get(id=elem[0])
                    start_date = None
                    if elem[1]:
                        start_date = convert_string_to_date(elem[1])
                    end_date = convert_string_to_date('2099/12/31')
                    if elem[2]:
                        end_date = convert_string_to_date(elem[2])
                    # print(f"{start_date}========={end_date}")
                    if not valid_range(start_date, end_date):
                        return bad_json('Please enter a valid date ranges')

                    if not start_date:
                        return bad_json(message="Start date cannot be empty")

                    if not valid_range(start_date, end_date):
                        return bad_json(message="Date range is not valid, make sure the start date is before end date")

                    contract_member.start_date = start_date
                    contract_member.end_date = end_date
                    contract_member.status = int(elem[3])
                    contract_member.save()

            return ok_json(data={'message': 'Contract Membership Lines successfully updated!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


def validate_membership_line(contract_id, indirect_customer_id, contract_start_date, contract_end_date, start_date,
                             end_date):
    # contract = Contract.objects.get(id=contract_id)

    # indirect_customer = IndirectCustomer.objects.get(id=indirect_customer_id)
    #
    # membership_line = ContractMember.objects.filter(contract=contract, indirect_customer=indirect_customer,
    #                                                  status=STATUS_ACTIVE)
    # contract_indirect_customer = membership_line[0] if membership_line.exists() else None

    errors = {'message': [], 'line_validation': 0, 'contract_validation': 0}

    # As discussed this should be handled while updating.
    # This can be @To-Do - Membership Line Overlapping Validation
    # Line Overlapping validation
    # if contract_indirect_customer is not None:
    #     membership_start_date = contract_indirect_customer.start_date
    #     membership_end_date = contract_indirect_customer.end_date

    # if start_date > membership_start_date or end_date > membership_start_date:
    #     errors['message'].append(
    #         "Date range cannot overlap an existing range. Range Found: " + membership_start_date.strftime(
    #             '%m/%d/%Y') + " to " + membership_end_date.strftime('%m/%d/%Y'))
    #     errors['line_validation'] = 1

    # Contract start and date validation
    if start_date < contract_start_date or end_date > contract_end_date:
        errors['message'].append(
            "This range is outside the established contract dates, would you like to extend the contract dates to accommodate?")
        errors['contract_validation'] = 1

    return errors


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def autofix_all_membership_errors(request, contract_id):
    try:
        data = {'title': 'Autifix all membership errors'}
        addGlobalData(request, data)
        # Get Contract
        contract = Contract.objects.get(id=contract_id)

        errors_membership_list = json.loads(request.POST['errors_membership_list'])

        if errors_membership_list:
            cv_error_state_date_list = []
            cv_error_end_date_list = []
            for elem in errors_membership_list:
                if elem["cv"] == "1":
                    cv_error_state_date_list.append(convert_string_to_date(elem["start_date"]))
                    cv_error_end_date_list.append(convert_string_to_date(elem["end_date"]))

            # Append contract start date to list because if contract start date is min. then keep it as it is
            cv_error_state_date_list.append(contract.start_date)
            # Getting maximum and minimum of start date to extend the contract
            min_start_date = min(cv_error_state_date_list)

            # Append contract end date to list because if contract end date is max. then keep it as it is
            cv_error_end_date_list.append(contract.end_date)
            # Getting maximum and minimum of start date to extend the contract
            max_end_date = max(cv_error_end_date_list)

            # Update Contract with min start date and max end date to resolve all contract range errors
            contract.start_date = min_start_date
            contract.end_date = max_end_date
            contract.save()

            # Saving membership lines with no errors now
            for elem in errors_membership_list:
                if elem["cv"] == "1":
                    today = datetime.datetime.now().date()
                    indirect_customer_id = elem['icid']
                    start_date = convert_string_to_date(elem['start_date'])
                    end_date = convert_string_to_date(elem['end_date'])

                    if today < start_date:
                        new_status = STATUS_PENDING
                    elif today > end_date:
                        new_status = STATUS_INACTIVE
                    else:
                        new_status = STATUS_ACTIVE

                    # create manage memebrship instance and save the line.
                    manage_membership = ContractMember(contract=contract,
                                                       indirect_customer_id=indirect_customer_id,
                                                       start_date=start_date,
                                                       end_date=end_date,
                                                       status=new_status)
                    manage_membership.save()

        return ok_json(data={'message': 'All membership errors are auto-fixed!',
                             'redirect_url': f"/{data['db_name']}/contracts/{contract.id}/edit"})

    except Exception as ex:
        return bad_json(message=ex.__str__())

@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def active_membership_load_data(request, contract_id):
    try:
        # Get Contract and Indirect customers (Membership) through ContractMember relationship
        contract = Contract.objects.get(id=contract_id)
        contract_end_date = convert_string_to_date(request.POST.get('contract_end_date'))
        if contract_end_date:
            queryset = contract.get_my_membership().filter(contract_id=contract_id,status=STATUS_ACTIVE, end_date=contract_end_date)

        search_fields = ['company_name', 'location_number', 'bid_340']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())

