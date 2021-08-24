import datetime
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.exports import export_report_to_excel, export_report_to_csv
from app.management.utilities.functions import convert_string_to_date, datatable_handler, bad_json, dates_exceeds_range
from app.management.utilities.globals import addGlobalData
from app.reports.reports_structures import get_amp_report_structure
from erms.models import (ChargeBackLineHistory)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
        User's AMP Report
    """
    data = {'title': 'AMP Data Report', 'header_title': 'AMP Data Report'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # activate menu option
    data['menu_option'] = 'menu_reports'
    return render(request, "reports/amp.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:
        # all ChargeBackLineHistory
        start_date_str = request.POST.get('start_date', '')
        end_date_str = request.POST.get('end_date', '')

        start_date = None
        end_date = None
        if start_date_str and end_date_str:
            start_date = convert_string_to_date(start_date_str)
            end_date = convert_string_to_date(end_date_str)

            # EA-1355 - limit all reports to pull only 2 years of data at most
            date_range_exceeds = dates_exceeds_range(start_date, end_date, 2)
            if date_range_exceeds:
                return bad_json(message="Date range should not exceed beyond 2 years")

        if start_date_str and not end_date_str:
            start_date = convert_string_to_date(start_date_str)
            end_date = convert_string_to_date(datetime.datetime.now().date().strftime('%m/%d/%Y'))

        if end_date_str and not start_date_str:
            end_date = convert_string_to_date(end_date_str)
            start_date = end_date - timedelta(days=365)

        queryset = None
        if start_date and end_date:
            queryset = ChargeBackLineHistory.objects.filter(updated_at__date__range=[start_date, end_date]).exclude(claim_amount_issue=0).order_by('cblnid')

        if not queryset:
            return JsonResponse({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
            })

        search_fields = ['cbtype', 'cb_cm_number', 'customer', 'distributor', 'distributor_city', 'distributor_state',
                         'distributor_zipcode', 'contract_name', 'contract_no', 'invoice_no', 'indirect_customer_name',
                         'indirect_customer_location_no', 'indirect_customer_address1', 'indirect_customer_address2',
                         'indirect_customer_city', 'indirect_customer_state', 'indirect_customer_zipcode', 'item_ndc',
                         'item_brand', 'item_description', 'item_uom', 'item_qty', 'wac_system', 'wac_submitted',
                         'claim_amount_system', 'claim_amount_submitted', 'cbnumber']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def export(request):
    try:
        export_to = request.GET.get('export_to', 'excel')
        start_date_str = request.GET.get('sd', '')
        end_date_str = request.GET.get('ed', '')

        start_date = None
        end_date = None
        if start_date_str and end_date_str:
            start_date = convert_string_to_date(start_date_str)
            end_date = convert_string_to_date(end_date_str)

        if start_date_str and not end_date_str:
            start_date = convert_string_to_date(start_date_str)
            end_date = convert_string_to_date(datetime.datetime.now().date().strftime('%m/%d/%Y'))

        if end_date_str and not start_date_str:
            end_date = convert_string_to_date(end_date_str)
            start_date = end_date - timedelta(days=365)

        cblines_history = []
        if start_date and end_date:
            cblines_history = ChargeBackLineHistory.objects.filter(updated_at__date__range=[start_date, end_date]).exclude(claim_amount_issue=0).order_by('cblnid')

        time1 = datetime.datetime.now()

        # Structure
        structure = get_amp_report_structure()
        # Export to excel or csv
        if export_to == 'excel':
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_amp_report.xlsx"
            response = export_report_to_excel(cblines_history, filename, structure)
        else:
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_amp_report.csv"
            response = export_report_to_csv(cblines_history, filename, structure)

        time2 = datetime.datetime.now()
        delta = (time2 - time1).total_seconds()
        print(f"Delta Time Export: {delta} sec")

        return response

    except Exception as ex:
        print(ex.__str__())
