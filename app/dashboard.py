import random
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, DecimalField
from django.shortcuts import render
from django.urls import reverse
import datetime
import calendar

from calendar import monthrange
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, JsonResponse

from app.management.utilities.exports import export_dashboard_grid_data_excel, export_dashboard_grid_data_csv
from app.management.utilities.functions import (query_range, convert_string_to_date, bad_json)
from app.management.utilities.globals import addGlobalData
from empowerb.middleware import db_ctx

from erms.models import (ChargeBackLineHistory, IndirectCustomer, ChargeBackLine, DirectCustomer, ChargeBackHistory)

@login_required(redirect_field_name='ret', login_url='/login')
def views(request):
    """
        Dashboard
    """
    data = {'title': 'Dashboard'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # custom dates filters
    start_date = None
    if 's' in request.GET and request.GET['s']:
        data['start_date'] = start_date = convert_string_to_date(request.GET['s'])

    end_date = None
    if 'e' in request.GET and request.GET['e']:
        data['end_date'] = end_date = convert_string_to_date(request.GET['e'])

    # Filter by Custom Dates or Range Filters
    if start_date and end_date:
        query_filter = 'Custom'
    else:
        query_filter = request.GET.get('range', 'YD')
        query = query_range(query_filter)
        data['start_date'] = query[0]
        data['end_date'] = query[1]

    data['query_filter'] = query_filter

    data['current_year'] = current_year = data['today'].year
    data['current_month'] = data['today'].strftime("%B")
    data['last_month'] = calendar.month_name[data['today'].month - 1]
    data['past_years'] = [current_year, current_year - 1, current_year - 2, current_year - 3, current_year - 4,current_year - 5]

    data['header_title'] = f"Overview > {data['company'].name}"
    data['menu_option'] = 'menu_dashboard'
    return render(request, "dashboard/dashboard.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_sales_distribution_chart_data(request):
    try:
        query_filter = request.POST.get('range', 'YD')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)

        direct_customers = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'chargeback_ref__customer_ref').annotate(
            revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField()),
            units=Sum(F('item_qty'))).order_by('-revenue')
        direct_customer_revenue_list = []
        colors = []
        for dc in direct_customers:
            try:
                direct_customer = DirectCustomer.objects.get(id=dc["chargeback_ref__customer_ref"])
            except:
                direct_customer = None

            if dc["revenue"]:
                random_color = get_random_color(colors)
                colors.append(random_color)
                direct_customer_revenue_list.append({
                    'color': random_color,
                    'name': direct_customer.name if direct_customer else '',
                    'dc_id': direct_customer.id if direct_customer else '',
                    'revenue': dc["revenue"],
                    'units': dc["units"]
                })

        if not direct_customer_revenue_list:
            response = {
                'labels': ["No Data Available"],
                'units': ["No Data Available"],
                'dc_ids':[0],
                'datasets': [{
                    'data': [-1],
                    'backgroundColor': ["grey"],
                }]
            }
        else:
            response = {
                'labels': [dc['name'] for dc in direct_customer_revenue_list],
                'units': [dc['units'] for dc in direct_customer_revenue_list],
                'dc_ids': [dc['dc_id'] for dc in direct_customer_revenue_list],
                'datasets': [{
                    'data': [dc['revenue'] for dc in direct_customer_revenue_list],
                    'backgroundColor': [dc['color'] for dc in direct_customer_revenue_list],
                }]
            }

        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_overall_sales_revenue_chart_data(request):
    try:
        query_filter = request.POST.get('range', 'YD')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)

        direct_customers = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'chargeback_ref__customer_ref').annotate(
            revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField()),
            units=Sum(F('item_qty'))).order_by('-revenue')
        direct_customer_revenue_list = []
        response = []

        for dc in direct_customers:
            try:
                direct_customer = DirectCustomer.objects.get(id=dc["chargeback_ref__customer_ref"])
            except:
                direct_customer = None
            direct_customer_revenue_list.append({
                'color': get_random_color(),
                'name': direct_customer.name if direct_customer else '',
                'revenue': dc["revenue"],
                'units': dc["units"]
            })

        if not direct_customer_revenue_list:
            response.append({
                'label': "No distributors found",
                'units': "No units found",
                'data': [0],
                'backgroundColor': "grey"
            })
        else:
            for dcr in direct_customer_revenue_list:
                response.append({
                    'label': dcr['name'],
                    'units': dcr['units'],
                    'data': [dcr['revenue']],
                    'backgroundColor': dcr['color']
                })

        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_my_net_income_chart_data(request):
    today = datetime.datetime.now()
    try:
        selected_year = request.POST.get('selected_year')

        if not selected_year:
            selected_year = today.year

        months = range(1, 13)
        my_net_income_chart = []
        for month in months:
            contract_price_system = ChargeBackLineHistory.objects.filter(updated_at__date__month=month,
                                                                         updated_at__date__year=selected_year).aggregate(
                sum=Sum('contract_price_system'))['sum']
            contract_price_system = Decimal(contract_price_system).quantize(
                Decimal(10) ** -2) if contract_price_system else Decimal('0.00')

            claim_amount_issue = ChargeBackLineHistory.objects.filter(updated_at__date__month=month,
                                                                      updated_at__date__year=selected_year).aggregate(
                sum=Sum('claim_amount_issue'))['sum']
            claim_amount_issue = Decimal(claim_amount_issue).quantize(
                Decimal(10) ** -2) if claim_amount_issue else Decimal('0.00')

            my_net_income_chart.append({
                'contract_price_system': contract_price_system,
                'claim_amount_issue': claim_amount_issue * -1
            })

        response = []
        if my_net_income_chart:
            response.append(
                {"data": [x["contract_price_system"] for x in my_net_income_chart], "backgroundColor": 'lightgreen'})
            response.append(
                {"data": [x["claim_amount_issue"] for x in my_net_income_chart], "backgroundColor": 'red'}, )
        else:
            response.append({"data": [0], "backgroundColor": 'lightgreen'})
            response.append({"data": [0], "backgroundColor": 'red'})
        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_my_chargeback_chart_data(request):
    try:
        query_filter = request.POST.get('range', 'YD')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)
        all_cblines = ChargeBackLine.objects.all()
        filtered_cblines_history = ChargeBackLineHistory.objects.filter(updated_at__date__range=query)
        # Open Chargebacks ( claim_amount_submitted )
        open_claim_amount_submitted_amnt = all_cblines.aggregate(sum=Sum('claim_amount_submitted'))['sum']
        open_claim_amount_submitted = Decimal(
            open_claim_amount_submitted_amnt) if open_claim_amount_submitted_amnt else Decimal('0.00')

        # Chargeback Credits Issued ( claim_amount_issue )
        total_claim_amount_issue_amnt = filtered_cblines_history.aggregate(sum=Sum('claim_amount_issue'))['sum']
        total_claim_amount_issue = Decimal(total_claim_amount_issue_amnt) if total_claim_amount_issue_amnt else Decimal(
            '0.00')

        # EA-1079 - Dashboard: Add Chargeback Lines metric to Chargeback graph
        cb_lines_count = all_cblines.count() + filtered_cblines_history.count()

        totalClaimlable = "No Data available"
        totalClaimdata = -1
        totalClaimbgColor = "grey"

        totalOpenlable = "No Data available"
        totalOpendata = -1
        totalOpenbgColor = "grey"

        if total_claim_amount_issue and total_claim_amount_issue != 0.00:
            totalClaimlable = "Processed"
            totalClaimdata = total_claim_amount_issue
            totalClaimbgColor = "lightgreen"

        if open_claim_amount_submitted and open_claim_amount_submitted != 0.00:
            totalOpenlable = "Open"
            totalOpendata = open_claim_amount_submitted
            totalOpenbgColor = "red"

        response = {
            'labels': [totalClaimlable, totalOpenlable],
            'cb_lines_count': cb_lines_count,
            'datasets': [{
                'data': [totalClaimdata, totalOpendata],
                'backgroundColor': [totalClaimbgColor, totalOpenbgColor],
            }]
        }

        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_cb_sales_by_other_categories(request):
    try:
        query_filter = request.POST.get('range', 'YD')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)

        label = request.POST.get('label', 'Open')
        category = request.POST.get('category', 'product')
        barColor = request.POST.get('barColor', 'red')
        all_results = request.POST.get('all_results', '0')

        if label == 'Processed':
            if category == 'contract':
                queryset = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(contract_number=F('contract_ref__number'), claim_amount_issue=Sum('claim_amount_issue', output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-claim_amount_issue').all()
            elif category == 'distributor':
                queryset = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(customer_name=F('chargeback_ref__customer_ref__name'), claim_amount_issue=Sum('claim_amount_issue', output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-claim_amount_issue').all()
            else:
                queryset = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc').annotate(ndc=F('item_ref__ndc'), claim_amount_issue=Sum('claim_amount_issue',  output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-claim_amount_issue').all()

            if all_results == '0':
                queryset = queryset[:10]

            labels = []
            data = []
            units = []
            backgroundColors = []
            if queryset:
                for elem in queryset:
                    if category == 'contract':
                        label_elem = elem['contract_ref__number'] if elem['contract_ref__number'] else ''
                    elif category == 'distributor':
                        label_elem = elem['chargeback_ref__customer_ref__name'] if elem['chargeback_ref__customer_ref__name'] else ''
                    else:
                        label_elem = elem['item_ref__ndc'] if elem['item_ref__ndc'] else ''

                    labels.append(label_elem)
                    data.append(elem['claim_amount_issue'])
                    units.append(elem['units'])
                    backgroundColors.append(barColor)

                response = {
                    'labels': labels,
                    'units': units,
                    'datasets': [{
                        'data': data,
                        'backgroundColor': backgroundColors
                    }]
                }
            else:
                response = {
                    'label': "No distributors found",
                    'units': "No units found",
                    'data': [0],
                    'backgroundColor': "grey"
                }
        else:
            if category == 'contract':
                queryset = ChargeBackLine.objects.values('contract_ref__number').annotate(contract_number=F('contract_ref__number'), claim_amount_submitted=Sum('claim_amount_submitted', output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-claim_amount_submitted').all()
            elif category == 'distributor':
                queryset = ChargeBackLine.objects.values('chargeback_ref__customer_ref__name').annotate(customer_name=F('chargeback_ref__customer_ref__name'), claim_amount_submitted=Sum('claim_amount_submitted', output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-claim_amount_submitted').all()
            else:
                queryset = ChargeBackLine.objects.values('item_ref__ndc').annotate(ndc=F('item_ref__ndc'), claim_amount_submitted=Sum('claim_amount_submitted', output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-claim_amount_submitted').all()

            if all_results == '0':
                queryset = queryset[:10]

            labels = []
            data = []
            units = []
            backgroundColors = []
            if queryset:
                for elem in queryset:
                    if category == 'contract':
                        label_elem = elem['contract_ref__number'] if elem['contract_ref__number'] else ''
                    elif category == 'distributor':
                        label_elem = elem['chargeback_ref__customer_ref__name'] if elem['chargeback_ref__customer_ref__name'] else ''
                    else:
                        label_elem = elem['item_ref__ndc'] if elem['item_ref__ndc'] else ''

                    labels.append(label_elem)
                    data.append(elem['claim_amount_submitted'])
                    units.append(elem['units'])
                    backgroundColors.append(barColor)

                response = {
                    'labels': labels,
                    'units': units,
                    'datasets': [{
                        'data': data,
                        'backgroundColor': backgroundColors
                    }]
                }
            else:
                response = {
                    'label': "No distributors found",
                    'units': "No units found",
                    'data': [0],
                    'backgroundColor': "grey"
                }

        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_sales_distribution_by_other_category(request):
    try:
        dc_id = request.POST.get('dc_id')
        category = request.POST.get('category', 'product')
        bgColor = request.POST.get('bgColor', 'orange')
        all_results = request.POST.get('all_results', '0')
        query_filter = request.POST.get('range', 'YD')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)
        dc = DirectCustomer.objects.get(id=dc_id)
        if category == "contract":
            category_data = ChargeBackLineHistory.objects.filter(chargeback_ref__customer_ref=dc, updated_at__date__range=query).values('contract_ref__number').annotate(ndc=F('contract_ref__number'), revenue=Sum(F('contract_price_system') * F('item_qty'),output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-revenue')
            if all_results == '0':
                category_data = ChargeBackLineHistory.objects.filter(chargeback_ref__customer_ref=dc, updated_at__date__range=query).values('contract_ref__number').annotate(ndc=F('contract_ref__number'), revenue=Sum(F('contract_price_system') * F('item_qty'),output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-revenue')[:10]

            labels = []
            data = []
            units = []
            backgroundColors = []
            if category_data:
                for elem in category_data:
                    labels.append(elem['contract_ref__number'] if elem['contract_ref__number'] else '')
                    data.append(elem['revenue'])
                    units.append(elem['units'])
                    backgroundColors.append(bgColor)

                response = {
                    'labels': labels,
                    'units': units,
                    'datasets': [{
                        'data': data,
                        'backgroundColor': backgroundColors
                    }]
                }
            else:
                response = {
                    'label': "No distributors found",
                    'units': "No units found",
                    'data': [0],
                    'backgroundColor': "grey"
                }
        elif category == "distribution_center":
            category_data = ChargeBackLineHistory.objects.filter(chargeback_ref__customer_ref=dc, updated_at__date__range=query, ).values('chargeback_ref__distribution_center_ref__name').annotate(dc_name=F('chargeback_ref__distribution_center_ref__name'), revenue=Sum(F('contract_price_system') * F('item_qty'),output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-revenue')
            if all_results == '0':
                category_data = ChargeBackLineHistory.objects.filter(chargeback_ref__customer_ref=dc, updated_at__date__range=query, ).values('chargeback_ref__distribution_center_ref__name').annotate(dc_name=F('chargeback_ref__distribution_center_ref__name'), revenue=Sum(F('contract_price_system') * F('item_qty'),output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-revenue')[:10]
            labels = []
            data = []
            units = []
            backgroundColors = []
            if category_data:
                for elem in category_data:
                    labels.append(elem['chargeback_ref__distribution_center_ref__name'] if elem['chargeback_ref__distribution_center_ref__name'] else '')
                    data.append(elem['revenue'])
                    units.append(elem['units'])
                    backgroundColors.append(bgColor)

                response = {
                    'labels': labels,
                    'units': units,
                    'datasets': [{
                        'data': data,
                        'backgroundColor': backgroundColors
                    }]
                }
            else:
                response = {
                    'label': "No distributors found",
                    'units': "No units found",
                    'data': [0],
                    'backgroundColor': "grey"
                }
        else:
            category_data = ChargeBackLineHistory.objects.filter(chargeback_ref__customer_ref=dc, updated_at__date__range=query, ).values('item_ref__ndc').annotate(ndc=F('item_ref__ndc'),revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-revenue')
            if all_results == '0':
                category_data = ChargeBackLineHistory.objects.filter(chargeback_ref__customer_ref=dc, updated_at__date__range=query, ).values('item_ref__ndc').annotate(ndc=F('item_ref__ndc'),revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField()), units=Sum(F('item_qty'))).order_by('-revenue')[:10]
            labels = []
            data = []
            units = []
            backgroundColors = []
            if category_data:
                for elem in category_data:
                    labels.append(elem['item_ref__ndc'])
                    data.append(elem['revenue'])
                    units.append(elem['units'])
                    backgroundColors.append(bgColor)

                response = {
                    'labels': labels,
                    'units': units,
                    'datasets': [{
                        'data': data,
                        'backgroundColor': backgroundColors
                    }]
                }
            else:
                response = {
                    'label': "No distributors found",
                    'units': "No units found",
                    'data': [0],
                    'backgroundColor': "grey"
                }
        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


def get_wac_sales(cblines_history):
    try:
        # Formula Revenue = ( wac_system * item_qty )
        value = \
            cblines_history.annotate(
                wac_sale=Sum(F('wac_system') * F('item_qty'), output_field=DecimalField())).aggregate(
                sum=Sum('wac_sale'))['sum']
        wac_sales = '${:,.2f}'.format(value) if value else '$ 0.00'
        return wac_sales
    except Exception as ex:
        return bad_json(message=ex.__str__())


def get_contract_sales(cblines_history):
    try:

        # Formula Contract Sales = ( contract_price_system * item_qty )
        value = cblines_history.annotate(
            contract_sales=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(
            sum=Sum('contract_sales'))['sum']
        contract_sales = '${:,.2f}'.format(value) if value else '$ 0.00'
        return contract_sales

    except Exception as ex:
        return bad_json(message=ex.__str__())


def get_units_sold(cblines_history):
    try:

        # Total items sold
        units_sold = cblines_history.aggregate(sum=Sum('item_qty'))['sum']
        return int(units_sold) if units_sold else 0

    except Exception as ex:
        return bad_json(message=ex.__str__())


def get_cblines_count(cblines_history):
    try:
        # Total cb lines in a range
        cblines_count = cblines_history.count()
        return int(cblines_count) if cblines_count else 0

    except Exception as ex:
        return bad_json(message=ex.__str__())


def get_cb_credits_requested(cblines_history):
    try:
        # Chargeback Credits Requested ( claim_amount_submitted )
        value = cblines_history.aggregate(sum=Sum('claim_amount_submitted'))['sum']
        cb_credits_requested = '${:,.2f}'.format(value) if value else '$ 0.00'
        return cb_credits_requested

    except Exception as ex:
        return bad_json(message=ex.__str__())


def get_cb_credits_issued(cblines_history):
    try:

        # Chargeback Credits Issued ( claim_amount_issue )
        value = cblines_history.aggregate(sum=Sum('claim_amount_issue'))['sum']
        cb_credits_issued = '${:,.2f}'.format(value) if value else '$ 0.00'
        return cb_credits_issued

    except Exception as ex:
        return bad_json(message=ex.__str__())


def get_cb_credits_adjusted(cblines_history):
    try:
        # Chargeback Credits Adjusted ( claim_amount_adjusment )
        value = cblines_history.aggregate(sum=Sum('claim_amount_adjusment'))['sum']
        cb_credits_adjusted = '${:,.2f}'.format(value) if value else '$ 0.00'
        return cb_credits_adjusted

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_projected_indirect_sales(request):
    try:
        today = datetime.datetime.now()

        # EA-1047 - Dashboard: Projected Indirect Sales is incorrect
        cblines_history = ChargeBackLineHistory.objects.filter(updated_at__date__month=today.month,
                                                               updated_at__date__year=today.year).only(
            'contract_price_system', 'item_qty')

        value = cblines_history.annotate(
            contract_sales=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(
            sum=Sum('contract_sales'))['sum']
        projected_contract_sales = value if value else 0

        month_num_days = 0
        if projected_contract_sales:
            projected_contract_sales = projected_contract_sales / today.day
            month_num_days = monthrange(today.year, today.month)[1]

        value = projected_contract_sales * month_num_days
        projected_indirect_sales = '${:,.2f}'.format(value) if value else '$ 0.00'

        return JsonResponse(projected_indirect_sales, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_new_indirect_customers(request):
    try:
        today = datetime.datetime.now()
        # New Indirect Customers this month
        new_indirect_customer = IndirectCustomer.objects.filter(created_at__month=today.month).count()

        return JsonResponse(new_indirect_customer, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_growth(request):
    try:
        query_filter = request.POST.get('range', 'YD')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)
        claim_amount = 0
        itemqty = 0
        growth = 0
        all_cblines_history = ChargeBackLineHistory.objects.filter(chargeback_ref__type="00", claim_amount_issue__gt=0,
                                                                   updated_at__date__range=query).only(
            'claim_amount_issue', 'item_qty','updated_at')
        claim_amount = all_cblines_history.annotate(
            claim_amount_p=Sum(F('claim_amount_issue'), output_field=DecimalField())).aggregate(
            sum=Sum('claim_amount_p'))['sum']

        itemqty = all_cblines_history.annotate(
            itm_qty=Sum(F('item_qty'), output_field=DecimalField())).aggregate(
            sum=Sum('itm_qty'))['sum']

        if claim_amount and itemqty:
            growth = claim_amount/itemqty
            growth = Decimal(growth).quantize(Decimal(10) ** -2) if growth else 0
        response = {
            'growth': growth,
            'class_to_apply': 'text-success' if growth > 0 else 'text-danger'
        }
        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def dashboard_handler(request):
    try:
        action = request.POST.get('action', '')
        if not action:
            bad_json(message="No action provided")

        query_filter = request.POST.get('range', 'YD')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)

        # ChargebackLine and ChargebackLineHistory querysets (all and filtered by range)
        cblines_history = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).only('wac_system',
                                                                                                   'item_qty',
                                                                                                   'contract_price_system')

        # time1 = datetime.datetime.now()
        counter = globals()[action](cblines_history)
        # time2 = datetime.datetime.now()
        # delta = (time2 - time1).total_seconds()
        # print(f"\nTime required for action {action}: {delta} sec")

        return JsonResponse(counter, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_cb_count_drill_down_chart(request):
    try:
        query_filter = request.POST.get('range', 'MTD')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)
        all_cblines_count = ChargeBackLine.objects.all().count()
        filtered_cblines_history_with_dc = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'chargeback_ref__customer_ref').order_by('chargeback_ref__customer_ref').annotate(
            count=Count("id")).distinct()
        direct_customer_cb_line_count_list = []
        for dc in filtered_cblines_history_with_dc:
            direct_customer_obj = DirectCustomer.objects.filter(id=dc["chargeback_ref__customer_ref"])
            if direct_customer_obj:
                direct_customer_cb_line_count_list.append({
                    'color': direct_customer_obj[0].get_random_hex_colour(),
                    'name': direct_customer_obj[0].name,
                    'cb_line_count': dc["count"],
                })
        if not direct_customer_cb_line_count_list:
            response = {
                'labels': ["No Data Available"],
                'units': ["No Data Available"],
                'ids': ["No Data Available"],
                'datasets': [{
                    'data': [-1],
                    'backgroundColor': ["grey"],
                }]
            }
        else:
            response = {
                'labels': [dc['name'] for dc in direct_customer_cb_line_count_list],
                'datasets': [{
                    'data': [dc['cb_line_count'] for dc in direct_customer_cb_line_count_list],
                    'backgroundColor': [dc['color'] for dc in direct_customer_cb_line_count_list],
                }]
            }

        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_dates_by_selected_range(request):
    query_filter = request.POST.get('range', 'YD')
    query = query_range(query_filter)
    start_date = query[0].strftime('%m/%d/%Y')
    end_date = query[1].strftime('%m/%d/%Y')

    response = {
        "start_date": start_date,
        "end_date": end_date,
    }

    return JsonResponse(response, safe=False)


def get_random_color(exclude_colors=[]):
    # return random.choice(COLORS_LIST)
    hex_number = '#{:06x}'.format(random.randint(0, 256**3))
    if hex_number not in exclude_colors:
        return hex_number
    else:
        get_random_color(exclude_colors)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_common_sales_by_categories(request):
    try:
        query_filter = request.POST.get('range', 'YD')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)
        action = request.POST['action']
        category = request.POST.get('category', 'product')
        barColor = request.POST.get('barColor', 'orange')
        limit = int(request.POST.get('limit', 10))

        all_results = request.POST.get('all_results', '0')
        is_grid_data = request.POST.get('is_grid_data', '0')
        is_export = request.POST.get('is_export', '1')

        labels = []
        data = []
        backgroundColors = []
        attribute1 = []

        grid_data = []

        if action == 'cb_credits_requested':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'),val=Sum(F('claim_amount_submitted'),output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),val=Sum(F('claim_amount_submitted'),output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'),val=Sum(F('claim_amount_submitted'),output_field=DecimalField())).order_by('-val')

        elif action == 'cb_lines':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'),val=Count(F('id'),output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),val=Count(F('id'),output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'),val=Count(F('id'),output_field=DecimalField())).order_by('-val')

        elif action == 'wac_sales':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'),val=Sum(F('wac_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),val=Sum(F('wac_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('wac_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')

        elif action == 'contract_sales':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'),val=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),val=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')

        elif action == 'cb_credit_issued':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'),val=Sum(F('claim_amount_issue'),output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),val=Sum(F('claim_amount_issue'),output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('claim_amount_issue'),output_field=DecimalField())).order_by('-val')

        elif action == 'avg_cb_amount':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query, chargeback_ref__type="00", claim_amount_issue__gt=0).values('contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('claim_amount_issue'), output_field=DecimalField()) / Sum(F('item_qty'), output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query, chargeback_ref__type="00", claim_amount_issue__gt=0).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'), val=Sum(F('claim_amount_issue'), output_field=DecimalField()) / Sum(F('item_qty'), output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query, chargeback_ref__type="00", claim_amount_issue__gt=0).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('claim_amount_issue'), output_field=DecimalField()) / Sum(F('item_qty'), output_field=DecimalField())).order_by('-val')

        else:
            # cb_credit_adjusted
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'),val=Sum(F('claim_amount_adjusment'),output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),val=Sum(F('claim_amount_adjusment'),output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('claim_amount_adjusment'),output_field=DecimalField())).order_by('-val')

        if not query_set:
            if is_grid_data == "1":
                response = {
                    'data': grid_data,
                    'recordsTotal': len(grid_data),
                    'recordsFiltered': len(grid_data),
                }
            else:
                response = {
                    'labels': [],
                    'attribute1': attribute1,
                    'datasets': [{
                        'data': data,
                        'backgroundColor': backgroundColors
                    }]
                }

        else:
            if all_results != '1':
                query_set = query_set[:limit]
            for elem in query_set:
                label_elem = elem['entity'] if elem['entity'] else ''

                if category == "product" and label_elem:
                    label_elem = get_formatted_ndc_for_graph(label_elem)
                    attribute1.append(elem['item_ref__description'] if elem['item_ref__description'] else '')

                if is_grid_data == "1" and (label_elem or elem['val']):
                    grid_data.append({
                        'entity': label_elem,
                        'value': elem['val']
                    })

                else:
                    labels.append(label_elem)
                    data.append(elem['val'])
                    backgroundColors.append(barColor)

            if is_grid_data == "1":
                response = {
                    'data': grid_data,
                    'recordsTotal': len(grid_data),
                    'recordsFiltered': len(grid_data),
                }

                return JsonResponse(response)
            response = {
                'labels': labels,
                'attribute1': attribute1,
                'datasets': [{
                    'data': data,
                    'backgroundColor': backgroundColors
                }]
            }
        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


def get_formatted_ndc_for_graph(ndc):
    return f'{ndc[:5]}-{ndc[5:9]}-{ndc[-2:]}'


@login_required(redirect_field_name='ret', login_url='/login')
def export_grid_data(request):
    try:
        query_filter = request.GET.get('range', 'YD')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)
        action = request.GET['action']
        category = request.GET.get('category', 'product')
        export_to = request.GET.get('export_to', 'excel')

        if action == 'cb_credits_requested':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('claim_amount_submitted'), output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'), val=Sum(F('claim_amount_submitted'), output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('claim_amount_submitted'), output_field=DecimalField())).order_by('-val')

        elif action == 'cb_lines':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'), val=Count(F('id'), output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'), val=Count(F('id'), output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Count(F('id'), output_field=DecimalField())).order_by('-val')

        elif action == 'wac_sales':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('wac_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'), val=Sum(F('wac_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('wac_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')

        elif action == 'contract_sales':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'), val=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')

        elif action == 'cb_credit_issued':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('claim_amount_issue'), output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),val=Sum(F('claim_amount_issue'),output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('claim_amount_issue'), output_field=DecimalField())).order_by('-val')

        elif action == 'avg_cb_amount':
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query, chargeback_ref__type="00", claim_amount_issue__gt=0).values('contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('claim_amount_issue'), output_field=DecimalField()) / Sum(F('item_qty'), output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query, chargeback_ref__type="00", claim_amount_issue__gt=0).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'), val=Sum(F('claim_amount_issue'), output_field=DecimalField()) / Sum(F('item_qty'), output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query, chargeback_ref__type="00", claim_amount_issue__gt=0).values('item_ref__ndc', 'item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('claim_amount_issue'), output_field=DecimalField()) / Sum(F('item_qty'), output_field=DecimalField())).order_by('-val')

        else:
            # cb_credit_adjusted
            if category == 'contract':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('claim_amount_adjusment'),output_field=DecimalField())).order_by('-val')
            elif category == 'distributor':
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),val=Sum(F('claim_amount_adjusment'),output_field=DecimalField())).order_by('-val')
            else:
                query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc','item_ref__description').annotate(entity=F('item_ref__ndc'), val=Sum(F('claim_amount_adjusment'), output_field=DecimalField())).order_by('-val')

        db_name = db_ctx.get()

        if export_to == "csv":
            filename = f"{db_name}_{action}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}.csv"
            response = export_dashboard_grid_data_csv(query_set, filename)
        else:
            filename = f"{db_name}_{action}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}.xlsx"
            response = export_dashboard_grid_data_excel(query_set, filename)

        return response

    except Exception as ex:
        print(ex.__str__())