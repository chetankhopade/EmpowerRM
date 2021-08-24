import datetime
import decimal
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.exports import (export_report_to_excel, export_report_to_csv)
from app.management.utilities.functions import convert_string_to_date, datatable_handler, bad_json, dates_exceeds_range, \
    get_chargebackline_object
from app.management.utilities.functions import query_range
from app.management.utilities.globals import addGlobalData
from app.reports.reports_structures import get_chargebackslines_history_report_structure
from erms.models import (ChargeBackLineHistory)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
        User's Chargebacks Report
    """
    data = {'title': 'Chargeback Report', 'header_title': 'Chargeback Report'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # activate menu option
    data['menu_option'] = 'menu_reports'
    return render(request, "reports/chargebacks.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:
        start_date_str = request.POST.get('start_date', '')
        end_date_str = request.POST.get('end_date', '')
        range = request.POST.get('range', '')

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

        if range:
            queryset = ChargeBackLineHistory.objects.filter(updated_at__date__range=query_range(range))
        else:
            if start_date and end_date:
                queryset = ChargeBackLineHistory.objects.filter(updated_at__date__range=[start_date, end_date])

        if not queryset:
            return JsonResponse({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
            })

        search_fields = ['cbtype', 'cb_cm_number', 'customer', 'distributor', 'distributor_city', 'distributor_state', 'distributor_zipcode', 'contract_name', 'contract_no', 'invoice_no', 'indirect_customer_name', 'indirect_customer_location_no', 'indirect_customer_address1', 'indirect_customer_address2', 'indirect_customer_city', 'indirect_customer_state', 'indirect_customer_zipcode', 'item_ndc', 'item_brand', 'item_description', 'item_uom', 'item_qty', 'wac_system', 'wac_submitted', 'claim_amount_system', 'claim_amount_submitted', 'cbnumber']
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
        range = request.GET.get('rg', '')

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
        if range:
            cblines_history = ChargeBackLineHistory.objects.filter(updated_at__date__range=query_range(range))
        else:
            if start_date and end_date:
                cblines_history = ChargeBackLineHistory.objects.filter(updated_at__date__range=[start_date, end_date])

        time1 = datetime.datetime.now()

        # Structure
        structure = get_chargebackslines_history_report_structure()
        # EA -1653 Add handling if Ind Cust DEA is invalid
        results = []
        for elem in cblines_history:
            chargebackline_id = elem.chargeback_line_id
            chargebackline = get_chargebackline_object(chargebackline_id)
            my_indirect_customer = chargebackline.get_my_indirect_customer()
            import844_obj = chargebackline.get_my_import844_obj()
            if not my_indirect_customer:
                indirect_customer_company_name = import844_obj.line.get('L_ShipToName', '') if import844_obj else ''
                indirect_customer_address1 = import844_obj.line.get('L_ShipToAddress', '') if import844_obj else ''
                indirect_customer_address2 = ''
                indirect_customer_city = import844_obj.line.get('L_ShipToCity', '') if import844_obj else ''
                indirect_customer_state = import844_obj.line.get('L_ShipToState', '') if import844_obj else ''
                indirect_customer_zip_code = import844_obj.line.get('L_ShipToZipCode', '') if import844_obj else ''
                indirect_customer_location_number = import844_obj.line.get('L_ShipToID', '') if import844_obj else ''
            else:
                indirect_customer_location_number = my_indirect_customer.location_number
                indirect_customer_company_name = my_indirect_customer.company_name
                indirect_customer_address1 = my_indirect_customer.address1
                indirect_customer_address2 = my_indirect_customer.address2
                indirect_customer_city = my_indirect_customer.city
                indirect_customer_state = my_indirect_customer.state
                indirect_customer_zip_code = my_indirect_customer.zip_code
            try:
                extended_wholesaler_sales = float(chargebackline.get_extended_wholesaler_sales())
            except:
                extended_wholesaler_sales = ''

            try:
                extended_contract_sales = float(chargebackline.get_extended_contract_sales())
            except:
                extended_contract_sales = ''
            results.append({
                'chargeback_ref__type': elem.chargeback_ref.type,
                'chargeback_ref__accounting_credit_memo_number': elem.chargeback_ref.accounting_credit_memo_number,
                'chargeback_ref__accounting_credit_memo_date':  elem.chargeback_ref.accounting_credit_memo_date,
                'chargeback_ref__customer_ref__name': elem.chargeback_ref.customer_ref.name,
                'chargeback_ref__distribution_center_ref__name': elem.chargeback_ref.distribution_center_ref.name,
                'chargeback_ref__distribution_center_ref__dea_number': elem.chargeback_ref.distribution_center_ref.dea_number,
                'chargeback_ref__distribution_center_ref__pk': 'DEA',
                'chargeback_ref__distribution_center_ref__address1': elem.chargeback_ref.distribution_center_ref.address1,
                'chargeback_ref__distribution_center_ref__city': elem.chargeback_ref.distribution_center_ref.city,
                'chargeback_ref__distribution_center_ref__state': elem.chargeback_ref.distribution_center_ref.state,
                'chargeback_ref__distribution_center_ref__zip_code': elem.chargeback_ref.distribution_center_ref.zip_code,
                'contract_ref__description': elem.contract_ref.description,
                'contract_ref__number': elem.contract_ref.number,
                'invoice_number': elem.invoice_number,
                'invoice_date': elem.invoice_date,
                'indirect_customer_ref__company_name': indirect_customer_company_name,
                'indirect_customer_ref__location_number': indirect_customer_location_number,
                 'indirect_customer_ref__pk': 'DEA',
                'contract_ref__cots': elem.contract_ref.cots,
                'indirect_customer_ref__address1': indirect_customer_address1,
                'indirect_customer_ref__address2': indirect_customer_address2,
                'indirect_customer_ref__city': indirect_customer_city,
                'indirect_customer_ref__state': indirect_customer_state,
                'indirect_customer_ref__zip_code': indirect_customer_zip_code,
                'item_ref__ndc': elem.item_ref.ndc,
                'item_ref__brand': elem.item_ref.brand,
                'item_ref__description': elem.item_ref.description,
                'item_uom': elem.item_uom,
                'item_qty': elem.item_qty,
                'wac_system': elem.wac_system,
                'wac_submitted': elem.wac_submitted,
                'contract_price_system': elem.contract_price_system,
                'contract_price_submitted':elem.contract_price_submitted,
                'claim_amount_system': elem.claim_amount_system,
                'claim_amount_submitted': elem.claim_amount_submitted,
                'contract_ref__pk': extended_wholesaler_sales,
                'import_844_ref__pk': extended_contract_sales,
                'chargeback_ref__number':elem.chargeback_ref.number,
                'chargeback_ref__date':elem.chargeback_ref.date,
                'cblnid':elem.cblnid
            })

        # # Export to excel or csv
        if export_to == 'excel':
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_chargebacks_report.xlsx"
            response = export_report_to_excel(results, filename, structure)
        else:
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_chargebacks_report.csv"
            response = export_report_to_csv(results, filename, structure)

        time2 = datetime.datetime.now()
        delta = (time2 - time1).total_seconds()
        print(f"Delta Time Export: {delta} sec")

        return response

    except Exception as ex:
        print(ex.__str__())
