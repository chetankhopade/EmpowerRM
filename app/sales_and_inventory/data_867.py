import datetime
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.exports import export_report_to_excel, export_report_to_csv, export_data_867_to_excel, \
    export_data_867_to_csv
from app.management.utilities.functions import datatable_handler, bad_json, convert_string_to_date, dates_exceeds_range
from app.management.utilities.globals import addGlobalData
from erms.models import Data867, DirectCustomer, DistributionCenter, Item, Contract


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'Data 867 - Search', 'header_title': 'Data 867 - Search'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['wholesalers'] = DirectCustomer.objects.all()
    data['distributors'] = DistributionCenter.objects.all()
    data['contracts'] = Contract.objects.all()
    data['menu_option'] = 'menu_867_search'
    return render(request, "sales_and_inventory/search_867.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:

        wholesaler = request.POST.get('wholesaler', '')
        distributor = request.POST.get('distributor', '')
        contract_number = request.POST.get('contract_number', '')
        report_start_date_str = request.POST.get('report_start_date', '')
        report_end_date_str = request.POST.get('report_end_date', '')
        created_at = request.POST.get('created_at', '')
        report_run_date = request.POST.get('report_run_date', '')
        invoice_date = request.POST.get('invoice_date', '')
        invoice_number = request.POST.get('invoice_number', '')
        transfer_type = request.POST.get('transfer_type', '')

        report_start_date = None
        report_end_date = None

        kwargs = {}

        if report_start_date_str and report_end_date_str:
            report_start_date = convert_string_to_date(report_start_date_str)
            report_end_date = convert_string_to_date(report_end_date_str)

            # EA-1355 - limit all reports to pull only 2 years of data at most
            date_range_exceeds = dates_exceeds_range(report_start_date, report_end_date, 2)
            if date_range_exceeds:
                return bad_json(message="Date range should not exceed beyond 2 years")

        if report_start_date_str and not report_end_date_str:
            report_start_date = convert_string_to_date(report_start_date_str)
            report_end_date = convert_string_to_date(datetime.datetime.now().date().strftime('%m/%d/%Y'))

        if report_end_date_str and not report_start_date_str:
            report_end_date = convert_string_to_date(report_end_date_str)
            report_start_date = report_end_date - timedelta(days=365)

        if report_start_date:
            kwargs['report_start_date__gte'] = report_start_date
        if report_end_date:
            kwargs['report_end_date__lte'] = report_end_date
        if wholesaler:
            kwargs['wholesaler_name'] = wholesaler
        if distributor:
            kwargs['dist_dea_number'] = distributor
        if contract_number:
            kwargs['contract_number'] = contract_number
        if created_at:
            kwargs['created_at__date'] = convert_string_to_date(created_at)
        if report_run_date:
            kwargs['report_run_date__date'] = convert_string_to_date(report_run_date)
        if invoice_date:
            kwargs['invoice_date'] = convert_string_to_date(invoice_date)
        if transfer_type:
            kwargs['transfer_type'] = transfer_type
        if invoice_number:
            kwargs['invoice_no'] = invoice_number

        queryset = Data867.objects.filter(**kwargs)

        if not queryset:
            return JsonResponse({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
            })

        search_fields = ['wholesaler_name', 'dist_name', 'dist_dea_number', 'ship_to_name', 'ship_to_dea_number', 'invoice_no', 'ship_to_hin_number', 'ship_to_address1', 'ship_to_address2', 'ship_to_city', 'ship_to_state', 'ship_to_zip', 'transfer_type_desc', 'product_ndc', 'product_description', 'contract_number', 'quantity', 'quantity_uom', 'unit_price', 'extended_amount']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def export(request):
    try:
        wholesaler = request.GET.get('wholesaler', '')
        distributor = request.GET.get('distributor', '')
        contract_number = request.GET.get('contract_number', '')
        report_start_date_str = request.GET.get('report_start_date', '')
        report_end_date_str = request.GET.get('report_end_date', '')
        created_at = request.GET.get('created_at', '')
        report_run_date = request.GET.get('report_run_date', '')
        invoice_date = request.GET.get('invoice_date', '')
        invoice_number = request.GET.get('invoice_number', '')
        transfer_type = request.GET.get('transfer_type', '')
        export_to = request.GET.get('export_to', 'excel')

        report_start_date = None
        report_end_date = None

        kwargs = {}

        if report_start_date_str and report_end_date_str:
            report_start_date = convert_string_to_date(report_start_date_str)
            report_end_date = convert_string_to_date(report_end_date_str)

            # EA-1355 - limit all reports to pull only 2 years of data at most
            date_range_exceeds = dates_exceeds_range(report_start_date, report_end_date, 2)
            if date_range_exceeds:
                return bad_json(message="Date range should not exceed beyond 2 years")

        if report_start_date_str and not report_end_date_str:
            report_start_date = convert_string_to_date(report_start_date_str)
            report_end_date = convert_string_to_date(datetime.datetime.now().date().strftime('%m/%d/%Y'))

        if report_end_date_str and not report_start_date_str:
            report_end_date = convert_string_to_date(report_end_date_str)
            report_start_date = report_end_date - timedelta(days=365)

        if report_start_date:
            kwargs['report_start_date__gte'] = report_start_date
        if report_end_date:
            kwargs['report_end_date__lte'] = report_end_date
        if wholesaler:
            kwargs['wholesaler_name'] = wholesaler
        if distributor:
            kwargs['dist_dea_number'] = distributor
        if contract_number:
            kwargs['contract_number'] = contract_number
        if created_at:
            kwargs['created_at__date'] = convert_string_to_date(created_at)
        if report_run_date:
            kwargs['report_run_date__date'] = convert_string_to_date(report_run_date)
        if invoice_date:
            kwargs['invoice_date'] = convert_string_to_date(invoice_date)
        if transfer_type:
            kwargs['transfer_type'] = transfer_type
        if invoice_number:
            kwargs['invoice_no'] = invoice_number

        queryset = Data867.objects.filter(**kwargs)

        # Export to excel or csv
        if export_to == 'excel':
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_data_867.xlsx"
            response = export_data_867_to_excel(queryset, filename)
        else:
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_data_867.csv"
            response = export_data_867_to_csv(queryset, filename)

        return response

    except Exception as ex:
        print(ex.__str__())