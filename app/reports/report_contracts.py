import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (STATUS_ACTIVE, STATUS_INACTIVE, STATUS_PENDING, STATUS_PROPOSED)
from app.management.utilities.exports import (export_report_to_excel, export_report_to_csv)
from app.management.utilities.functions import (convert_string_to_date, datatable_handler, bad_json,
                                                generate_filename_for_reports)
from app.management.utilities.globals import addGlobalData
from app.reports.reports_structures import get_contracts_report_structure
from erms.models import (Contract, ContractLine, DirectCustomer)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
        User's Contracts Report
    """
    data = {'title': 'Contract Report', 'header_title': 'Contract Report'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['customers'] = DirectCustomer.objects.all()
    data['contracts'] = Contract.objects.all()
    data['is_contract_report'] = True
    data['menu_option'] = 'menu_reports'
    return render(request, "reports/rcontracts.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:
        contract_id = request.POST.get('cid', '')
        customer_id = request.POST.get('customer_id', '')
        status = request.POST.get('status', '')
        start_date = request.POST.get('start_date', '')
        end_date = request.POST.get('end_date', '')
        created_at = request.POST.get('created_at', '')

        kwargs = {}

        if contract_id:
            kwargs['contract__id'] = contract_id

        if customer_id:
            kwargs['contract__customer__id'] = customer_id

        if start_date:
            kwargs['start_date'] = convert_string_to_date(start_date)

        if end_date:
            kwargs['end_date'] = convert_string_to_date(end_date)

        if created_at:
            kwargs['created_at'] = convert_string_to_date(created_at)

        if status:
            if int(status) == STATUS_ACTIVE:
                kwargs['status'] = STATUS_ACTIVE
            elif int(status) == STATUS_INACTIVE:
                kwargs['status'] = STATUS_INACTIVE
            elif int(status) == STATUS_PENDING:
                kwargs['status'] = STATUS_PENDING
            else:
                kwargs['status'] = STATUS_PROPOSED

        # query with dynamics filters
        queryset = ContractLine.objects.filter(**kwargs)

        if not queryset:
            return JsonResponse({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
            })

        search_fields = ['contract__number', 'contract__description', 'item__description', 'item__ndc']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def export(request):
    try:
        export_to = request.GET.get('export_to', 'excel')
        contract_id = request.GET.get('co', '')
        customer_id = request.GET.get('cu', '')
        status = request.GET.get('st', '')
        start_date = request.GET.get('sd', '')
        end_date = request.GET.get('ed', '')
        created_at = request.GET.get('cd', '')

        kwargs = {}

        contract_number = None
        if contract_id:
            contract_number = Contract.objects.get(id=contract_id).number
            kwargs['contract__id'] = contract_id

        if customer_id:
            kwargs['contract__customer__id'] = customer_id

        if start_date:
            kwargs['start_date'] = convert_string_to_date(start_date)

        if end_date:
            kwargs['end_date'] = convert_string_to_date(end_date)

        if created_at:
            kwargs['created_at'] = convert_string_to_date(created_at)

        if status:
            if int(status) == STATUS_ACTIVE:
                kwargs['status'] = STATUS_ACTIVE
            elif int(status) == STATUS_INACTIVE:
                kwargs['status'] = STATUS_INACTIVE
            elif int(status) == STATUS_PENDING:
                kwargs['status'] = STATUS_PENDING
            else:
                kwargs['status'] = STATUS_PROPOSED

        # Queryset
        time1 = datetime.datetime.now()
        contract_lines = ContractLine.objects.filter(**kwargs)
        time2 = datetime.datetime.now()
        delta = (time2 - time1).total_seconds()
        print(f"Delta Time Queryset: {delta} sec")

        # Export
        time1 = datetime.datetime.now()
        structure = get_contracts_report_structure()
        if export_to == 'excel':
            filename = generate_filename_for_reports(obj_name=contract_number if contract_number else 'contracts', ext='xlsx')
            response = export_report_to_excel(contract_lines, filename, structure)
        else:
            filename = generate_filename_for_reports(obj_name=contract_number if contract_number else 'contracts', ext='csv')
            response = export_report_to_csv(contract_lines, filename, structure)

        time2 = datetime.datetime.now()
        delta = (time2 - time1).total_seconds()
        print(f"Delta Time Export: {delta} sec")

        return response

    except Exception as ex:
        print(ex.__str__())
