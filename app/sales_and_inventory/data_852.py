import datetime
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.exports import export_data_852_to_excel, export_data_852_to_csv
from app.management.utilities.functions import datatable_handler, bad_json, convert_string_to_date, dates_exceeds_range
from app.management.utilities.globals import addGlobalData
from erms.models import Data852, DirectCustomer, DistributionCenter, Item


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'Data 852 - Search', 'header_title': 'Data 852 - Search'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['wholesalers'] = DirectCustomer.objects.all()
    data['distributors'] = DistributionCenter.objects.all()
    data['items'] = Item.objects.all()
    data['menu_option'] = 'menu_852_search'
    return render(request, "sales_and_inventory/search_852.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:

        wholesaler = request.POST.get('wholesaler', '')
        distributor = request.POST.get('distributor', '')
        ndc = request.POST.get('ndc', '')
        report_start_date_str = request.POST.get('report_start_date', '')
        report_end_date_str = request.POST.get('report_end_date', '')
        created_at = request.POST.get('created_at', '')

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
            kwargs['H_start_date__gte'] = report_start_date
        if report_end_date:
            kwargs['H_end_date__lte'] = report_end_date
        if wholesaler:
            kwargs['wholesaler_name'] = wholesaler
        if distributor:
            kwargs['H_distributor_id__dea_number'] = distributor
        if ndc:
            kwargs['L_item_id'] = ndc
        if created_at:
            kwargs['created_at__date'] = convert_string_to_date(created_at)

        queryset = Data852.objects.filter(**kwargs)
        # queryset = Data852.objects.all()

        if not queryset:
            return JsonResponse({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
            })

        search_fields = ['wholesaler_name', 'H_distributor_id_type', 'H_distributor_id__dea_number', 'H_distributor_id__name', 'L_item_id', 'L_BS', 'L_TS', 'L_QA', 'L_QP', 'L_QS', 'L_QO', 'L_QC', 'L_QT', 'L_QD', 'L_QB', 'L_Q1', 'L_QW', 'L_QR', 'L_QI', 'L_QZ', 'L_QH', 'L_QU', 'L_WQ', 'L_QE']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def export(request):
    try:
        wholesaler = request.GET.get('wholesaler', '')
        distributor = request.GET.get('distributor', '')
        ndc = request.GET.get('ndc', '')
        report_start_date_str = request.GET.get('report_start_date', '')
        report_end_date_str = request.GET.get('report_end_date', '')
        created_at = request.GET.get('created_at', '')
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
            kwargs['H_start_date__gte'] = report_start_date
        if report_end_date:
            kwargs['H_end_date__lte'] = report_end_date
        if wholesaler:
            kwargs['wholesaler_name'] = wholesaler
        if distributor:
            kwargs['H_distributor_id__dea_number'] = distributor
        if ndc:
            kwargs['L_item_id'] = ndc
        if created_at:
            kwargs['created_at__date'] = convert_string_to_date(created_at)

        queryset = Data852.objects.filter(**kwargs)

        # Export to excel or csv
        if export_to == 'excel':
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_data_852.xlsx"
            response = export_data_852_to_excel(queryset, filename)
        else:
            filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_data_852.csv"
            response = export_data_852_to_csv(queryset, filename)

        return response

    except Exception as ex:
        print(ex.__str__())