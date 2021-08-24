import datetime
from datetime import timedelta
from itertools import chain

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import LINE_STATUS_PENDING
from app.management.utilities.exports import (export_report_to_excel, export_report_to_csv)
from app.management.utilities.functions import convert_string_to_date, bad_json, list_datatable_handler, dates_exceeds_range
from app.management.utilities.functions import query_range
from app.management.utilities.globals import addGlobalData
from app.reports.reports_structures import get_manual_report_structure
from empowerb.middleware import db_ctx
from ermm.models import Company
from erms.models import (DirectCustomer, ChargeBackLineHistory, ChargeBack, ChargeBackLine, ChargeBackHistory)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
        User's Manual Report
    """
    data = {'title': 'Manual Report', 'header_title': 'Manual Report'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['customers'] = DirectCustomer.objects.all()
    data['menu_option'] = 'menu_reports'
    return render(request, "reports/manual.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:
        start_date_str = request.POST.get('start_date', '')
        end_date_str = request.POST.get('end_date', '')
        customer_id = request.POST.get('customer_id', '')
        range = request.POST.get('range', '')
        status = int(request.POST.get('status', 0))
        via_edi = int(request.POST['via_edi']) == 1

        # queryset of CBs (Manual and Archived)
        chargebacks_open = ChargeBack.objects.filter(is_received_edi=via_edi).order_by('cbid')
        chargebacks_history = ChargeBackHistory.objects.filter(is_received_edi=via_edi).order_by('cbid')

        if customer_id:
            chargebacks_open = chargebacks_open.filter(customer_ref_id=customer_id)
            chargebacks_history = chargebacks_history.filter(customer_ref_id=customer_id)

        # 0 All, 1 Open, 2 Archived
        if status:
            if status == 1:
                chargebacks = chargebacks_open
            else:
                chargebacks = chargebacks_history
        else:
            chargebacks = list(chain(chargebacks_open, chargebacks_history))

        # get cblines (ticket 1044 Chargebacks that dont have pending lines)
        open_cblines = ChargeBackLine.objects.exclude(line_status=LINE_STATUS_PENDING).filter(chargeback_id__in=[x.id for x in chargebacks]).order_by('cblnid')
        archived_cblines = ChargeBackLineHistory.objects.exclude(line_status=LINE_STATUS_PENDING).filter(chargeback_id__in=[x.id for x in chargebacks]).order_by('cblnid')

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

        if range:
            open_cblines = open_cblines.filter(updated_at__date__range=query_range(range))
            archived_cblines = archived_cblines.filter(updated_at__date__range=query_range(range))
        else:
            if start_date and end_date:
                open_cblines = open_cblines.filter(updated_at__date__range=[start_date, end_date])
                archived_cblines = archived_cblines.filter(updated_at__date__range=[start_date, end_date])

        queryset = list(chain(open_cblines, archived_cblines))

        search_fields = ['cblnid', 'cbnumber', 'distributor', 'contract_no', 'indirect_customer_location_no', 'item_nd']
        response = list_datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def export(request):
    try:
        export_to = request.GET.get('export_to', 'excel')
        start_date_str = request.GET.get('sd', '')
        end_date_str = request.GET.get('ed', '')
        customer_id = request.GET.get('cu', '')
        range = request.GET.get('rg', '')
        status = int(request.GET.get('st', 0))
        via_edi = int(request.GET['ve']) == 1

        # queryset of CBs (Manual and Archived)
        chargebacks_open = ChargeBack.objects.filter(is_received_edi=via_edi).order_by('cbid')
        chargebacks_history = ChargeBackHistory.objects.filter(is_received_edi=via_edi).order_by('cbid')

        if customer_id:
            chargebacks_open = chargebacks_open.filter(customer_id=customer_id)
            chargebacks_history = chargebacks_history.filter(customer_id=customer_id)

        # 0 All, 1 Open, 2 Archived
        if status:
            if status == 1:
                chargebacks = chargebacks_open
            else:
                chargebacks = chargebacks_history
        else:
            chargebacks = list(chain(chargebacks_open, chargebacks_history))

        # get cblines
        open_cblines = ChargeBackLine.objects.exclude(line_status=LINE_STATUS_PENDING).filter(chargeback_id__in=[x.id for x in chargebacks]).order_by('cblnid')
        archived_cblines = ChargeBackLineHistory.objects.exclude(line_status=LINE_STATUS_PENDING).filter(chargeback_id__in=[x.id for x in chargebacks]).order_by('cblnid')

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

        if range:
            open_cblines = open_cblines.filter(updated_at__date__range=query_range(range))
            archived_cblines = archived_cblines.filter(updated_at__date__range=query_range(range))
        else:
            if start_date and end_date:
                open_cblines = open_cblines.filter(updated_at__date__range=[start_date, end_date])
                archived_cblines = archived_cblines.filter(updated_at__date__range=[start_date, end_date])

        cblines = list(chain(open_cblines, archived_cblines))

        time1 = datetime.datetime.now()

        # needed for the manual report (company name, from db) and pass it to the structure as a static value
        try:
            company_name = Company.objects.get(database=db_ctx.get()).name
        except:
            company_name = ''

        # Structure
        structure = get_manual_report_structure(company_name)

        # Export to excel or csv
        if export_to == 'excel':
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_manual_report.xlsx"
            response = export_report_to_excel(cblines, filename, structure)
        else:
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_manual_report.csv"
            response = export_report_to_csv(cblines, filename, structure)

        time2 = datetime.datetime.now()
        delta = (time2 - time1).total_seconds()
        print(f"Delta Time Export: {delta} sec")

        # response = export_manual_report_to_excel(cblines, company=data['company'], customer_name=None)
        return response

    except Exception as ex:
        print(ex.__str__())
