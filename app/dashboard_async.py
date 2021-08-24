import concurrent
import random
from decimal import Decimal

import asyncio

from asgiref.sync import sync_to_async, async_to_sync
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, DecimalField
from django.shortcuts import render
from django.urls import reverse
import datetime
import calendar

from calendar import monthrange
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse

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
    return render(request, "dashboard/dashboard_async.html", data)

@sync_to_async
def get_contact_price_system(months,selected_year):
    contract_price_result = []
    for month in months:
         contract_price_system = ChargeBackLineHistory.objects.filter(updated_at__date__month=month,updated_at__date__year=selected_year)
         contract_price_system = contract_price_system.aggregate(sum=Sum('contract_price_system'))['sum']
         contract_price_system = Decimal(contract_price_system).quantize(Decimal(10) ** -2) if contract_price_system else Decimal('0.00')
         contract_price_result.append({'contract_price_system': contract_price_system})
    return contract_price_result
@sync_to_async
def get_claim_amount_issues(months,selected_year):
    claim_amount_result = []
    for month in months:
         claim_amount_issue = ChargeBackLineHistory.objects.filter(updated_at__date__month=month,updated_at__date__year=selected_year)
         claim_amount_issue = claim_amount_issue.aggregate(sum=Sum('claim_amount_issue'))['sum']
         claim_amount_issue = Decimal(claim_amount_issue).quantize(Decimal(10) ** -2) if claim_amount_issue else Decimal('0.00')
         claim_amount_issue = claim_amount_issue * -1
         claim_amount_result.append({'claim_amount_issue':claim_amount_issue})
    return claim_amount_result


async def get_response_calculation(contract_price_system,claim_amount_issue):
    result = []
    if contract_price_system:
        result.append(
            {"data": [x['contract_price_system'] for x in contract_price_system], "backgroundColor": 'lightgreen'})
    else :
        result.append({"data": [0], "backgroundColor": 'lightgreen'})

    if claim_amount_issue:
        result.append(
            {"data": [x['claim_amount_issue'] for x in claim_amount_issue], "backgroundColor": 'red'}, )
    else:
        result.append({"data": [0], "backgroundColor": 'red'})
    return result
@sync_to_async
@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
@async_to_sync
async def async_get_my_net_income_chart_data(request):
    today = datetime.datetime.now()
    try:
        selected_year = request.POST.get('selected_year')
        if not selected_year:
            selected_year = today.year
        # time1 = datetime.datetime.now()
        months = range(1, 13)
        contract_price_system = []
        claim_amount_issue = []
        contract_price_system, claim_amount_issue = await asyncio.gather(get_contact_price_system(months, selected_year),
                                                                         get_claim_amount_issues(months, selected_year))

        response = []
        response = await asyncio.gather(get_response_calculation(contract_price_system,claim_amount_issue))

        return JsonResponse(response[0],safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@sync_to_async
@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
@async_to_sync
async def async_get_my_chargeback_chart_data(request):
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
        cbline_count= 0
        cb_history_count= 0
        open_claim_amount_submitted_result,total_claim_amount_issue_result = await asyncio.gather(getchargeback_data(), getchargebackhistory_data(query))
        # cbline_count, cb_history_count = await asyncio.gather(getchargeback_data_count(), getchargebackhistory_data_count(query))
        # EA-1079 - Dashboard: Add Chargeback Lines metric to Chargeback graph
        cb_lines_count = open_claim_amount_submitted_result[1] + total_claim_amount_issue_result[1]
        open_claim_amount_submitted = open_claim_amount_submitted_result[0]
        total_claim_amount_issue = total_claim_amount_issue_result[0]
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


@sync_to_async
def getchargeback_data():
    all_cblines = ChargeBackLine.objects.all()
    open_claim_amount_submitted_amnt = all_cblines.aggregate(sum=Sum('claim_amount_submitted'))['sum']
    open_claim_amount_submitted = Decimal(open_claim_amount_submitted_amnt) if open_claim_amount_submitted_amnt else Decimal('0.00')
    return [open_claim_amount_submitted,all_cblines.count()]

@sync_to_async
def getchargebackhistory_data(query):
    filtered_cblines_history = ChargeBackLineHistory.objects.filter(updated_at__date__range=query)
    total_claim_amount_issue_amnt = filtered_cblines_history.aggregate(sum=Sum('claim_amount_issue'))['sum']
    total_claim_amount_issue = Decimal(total_claim_amount_issue_amnt) if total_claim_amount_issue_amnt else Decimal('0.00')
    return [total_claim_amount_issue,filtered_cblines_history.count()]


@sync_to_async
@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
@async_to_sync
async def get_sales_distribution_chart_data(request):
    try:
        query_filter = request.POST.get('range', 'YD')
        # query_filter = 'LY'
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if query_filter == "custom":
            # custom dates filters
            start_date = convert_string_to_date(start_date)
            end_date = convert_string_to_date(end_date)
            query = [start_date, end_date]
        else:
            query = query_range(query_filter)
        response = []
        direct_customer_revenue_list = []
        direct_customer_revenue_list = await asyncio.gather(get_dc_customer_data(query))
        response = await asyncio.gather(get_sales_distributor_calculation(direct_customer_revenue_list[0]))

        return JsonResponse(response[0], safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())

def get_random_color(exclude_colors=[]):
    # return random.choice(COLORS_LIST)
    hex_number = '#{:06x}'.format(random.randint(0, 256**3))
    if hex_number not in exclude_colors:
        return hex_number
    else:
        get_random_color(exclude_colors)

@sync_to_async
def get_dc_customer_data(query):
    direct_customer_revenue_list = []
    colors = []
    direct_customers = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('chargeback_ref__customer_ref').annotate(
        revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField()),
        units=Sum(F('item_qty'))).order_by('-revenue')
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

    return direct_customer_revenue_list


async def get_sales_distributor_calculation(direct_customer_revenue_list):

    if not direct_customer_revenue_list:
        response = {
            'labels': ["No Data Available"],
            'units': ["No Data Available"],
            'dc_ids': [0],
            'datasets': [{
                'data': [-1],
                'backgroundColor': ["grey"],
            }]
        }
    else:

        response = {
            'labels': [dc['name'] for dc in direct_customer_revenue_list],
            'units': [dc['units'] for dc in direct_customer_revenue_list],
            'dc_ids':[dc['dc_id'] for dc in direct_customer_revenue_list] ,
            'datasets': [{
                'data': [dc['revenue'] for dc in direct_customer_revenue_list],
                'backgroundColor': [dc['color'] for dc in direct_customer_revenue_list],
            }]
        }
    return response

@sync_to_async
@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
@async_to_sync
async def get_growth(request):
    try:
        today = datetime.datetime.now()
        # GROWTH
        projected_contract_sales = await asyncio.gather(get_projected_contract_sale(today))
        contract_sales_last_month = await asyncio.gather(get_contract_sales_last_month(today))

        # EA-1150 - Calculation should be this month projected sales / last month contract sales x 100
        growth = round((projected_contract_sales[0] - contract_sales_last_month[0]) * 100 / contract_sales_last_month[0],
                       2) if contract_sales_last_month[0] else 0
        response = {
            'growth': growth,
            'class_to_apply': 'text-success' if growth > 0 else 'text-danger'
        }
        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@sync_to_async
def get_projected_contract_sale(today):

     all_cblines_history = ChargeBackLineHistory.objects.filter(updated_at__date__year=today.year).only(
            'contract_price_system', 'item_qty', 'updated_at')

     value = all_cblines_history.filter(updated_at__date__month=today.month).annotate(
            contract_sales=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(
            sum=Sum('contract_sales'))['sum']
     projected_contract_sales = value if value else 0
     month_num_days = 0
     if projected_contract_sales:
          projected_contract_sales = projected_contract_sales / today.day
          month_num_days = monthrange(today.year, today.month)[1]

     projected_contract_sales = projected_contract_sales * month_num_days

     return projected_contract_sales

@sync_to_async
def get_contract_sales_last_month(today):

    all_cblines_history = ChargeBackLineHistory.objects.filter(updated_at__date__year=today.year).only(
        'contract_price_system', 'item_qty', 'updated_at')

    value = all_cblines_history.filter(updated_at__date__month=today.month - 1).annotate(
        contract_sales=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(
        sum=Sum('contract_sales'))['sum']
    contract_sales_last_month = Decimal(value).quantize(Decimal(10) ** -2) if value else 0
    return contract_sales_last_month

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


async def async_query_range(key):
    """
    return data date range list based on key range text
    :param key: data range selection
    :return: obj date range
    """
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)

    dt = datetime.date.today()

    year = today.year
    currentYear = today.year
    last_month = today.month - 1
    if not last_month:
        year = today.year - 1
        last_month = 12

    _, last_month_days = calendar.monthrange(year, last_month)

    start_this_week = today - datetime.timedelta(days=today.weekday())
    end_this_week = start_this_week + datetime.timedelta(days=6)
    start_last_week = start_this_week - datetime.timedelta(weeks=1)
    end_last_week = start_last_week + datetime.timedelta(days=6)

    # EA- 1522 - HOTFIX: Add "Quarter" filter options to the Report Builder Run Parameters
    current_quarter_start_date = datetime.date(dt.year, (dt.month - 1) // 3 * 3 + 1, 1)
    last_quarter_start_date,last_quarter_end_date = await asyncio.gather(async_previous_quarter_start_date(today),async_previous_quarter_end_date(today))


    ranges = {
        "TD": [today.date(), today.date()],  # Today
        "YD": [yesterday.date(), yesterday.date()],  # Yesterday
        "LM": [datetime.datetime(year, last_month, 1).date(), datetime.datetime(year, last_month, last_month_days).date()],  # Last Month
        "WTD": [start_this_week.date(), today.date()],  # Week To Date
        "MTD": [datetime.datetime(currentYear, today.month, 1).date(), today.date()],  # Month To Date
        "YTD": [datetime.datetime(currentYear, 1, 1).date(), today.date()],  # Year To Date
        "TW": [start_this_week.date(), end_this_week.date()],  # This Week
        "LW": [start_last_week.date(), end_last_week.date()],  # Last Week
        "LY": [datetime.datetime(currentYear - 1, 1, 1).date(), datetime.datetime(currentYear - 1, 12, 31).date()],  # Last Year
        "LQ": [last_quarter_start_date, last_quarter_end_date],
        "QTD": [current_quarter_start_date, today.date()]
    }

    return ranges[key]

@sync_to_async
def async_previous_quarter_start_date(today):
    if today.month < 4:
        return datetime.date(today.year - 1, 10, 1)
    elif today.month < 7:
        return datetime.date(today.year, 1, 1)
    elif today.month < 10:
        return datetime.date(today.year, 4, 1)
    return datetime.date(today.year, 7, 1)

@sync_to_async
def async_previous_quarter_end_date(today):
    if today.month < 4:
        return datetime.date(today.year - 1, 12, 31)
    elif today.month < 7:
        return datetime.date(today.year, 3, 31)
    elif today.month < 10:
        return datetime.date(today.year, 6, 30)
    return datetime.date(today.year, 9, 30)

@sync_to_async
def get_cb_credits_requested_action(query,category):
    if category == 'contract':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('claim_amount_submitted'),
                                                                                       output_field=DecimalField())).order_by(
            '-val')
    elif category == 'distributor':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),
                                                           val=Sum(F('claim_amount_submitted'),
                                                                   output_field=DecimalField())).order_by('-val')
    else:
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc',
                                                                                               'item_ref__description').annotate(
            entity=F('item_ref__ndc'), val=Sum(F('claim_amount_submitted'), output_field=DecimalField())).order_by(
            '-val')


    return query_set

@sync_to_async
def get_cb_lines_action(query,category):
    if category == 'contract':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'contract_ref__number').annotate(entity=F('contract_ref__number'),
                                             val=Count(F('id'), output_field=DecimalField())).order_by('-val')
    elif category == 'distributor':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),
                                                           val=Count(F('id'), output_field=DecimalField())).order_by(
            '-val')
    else:
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc',
                                                                                               'item_ref__description').annotate(
            entity=F('item_ref__ndc'), val=Count(F('id'), output_field=DecimalField())).order_by('-val')

    return query_set
@sync_to_async
def get_wac_sales_action(query,category):
    if category == 'contract':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('wac_system') * F('item_qty'),
                                                                                       output_field=DecimalField())).order_by(
            '-val')

    elif category == 'distributor':

        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),
                                                           val=Sum(F('wac_system') * F('item_qty'),
                                                                   output_field=DecimalField())).order_by('-val')
        # print(query_set)

    else:

        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc',
                                                                                               'item_ref__description').annotate(
            entity=F('item_ref__ndc'), val=Sum(F('wac_system') * F('item_qty'), output_field=DecimalField())).order_by(
            '-val')
        # print(query_set)

    return query_set
@sync_to_async
def get_contract_sales_action(query,category):
    if category == 'contract':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'contract_ref__number').annotate(entity=F('contract_ref__number'),
                                             val=Sum(F('contract_price_system') * F('item_qty'),
                                                     output_field=DecimalField())).order_by('-val')
    elif category == 'distributor':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),
                                                           val=Sum(F('contract_price_system') * F('item_qty'),
                                                                   output_field=DecimalField())).order_by('-val')
    else:
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc',
                                                                                               'item_ref__description').annotate(
            entity=F('item_ref__ndc'),
            val=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).order_by('-val')

    return query_set

@sync_to_async
def get_cb_credit_issued_action(query,category):
    if category == 'contract':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'contract_ref__number').annotate(entity=F('contract_ref__number'),
                                             val=Sum(F('claim_amount_issue'), output_field=DecimalField())).order_by(
            '-val')
    elif category == 'distributor':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),
                                                           val=Sum(F('claim_amount_issue'),
                                                                   output_field=DecimalField())).order_by('-val')
    else:
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc',
                                                                                               'item_ref__description').annotate(
            entity=F('item_ref__ndc'), val=Sum(F('claim_amount_issue'), output_field=DecimalField())).order_by('-val')

    return query_set
@sync_to_async
def get_cb_credit_adjusted_action(query,category):
    if category == 'contract':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'contract_ref__number').annotate(entity=F('contract_ref__number'), val=Sum(F('claim_amount_adjusment'),
                                                                                       output_field=DecimalField())).order_by(
            '-val')
    elif category == 'distributor':
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values(
            'chargeback_ref__customer_ref__name').annotate(entity=F('chargeback_ref__customer_ref__name'),
                                                           val=Sum(F('claim_amount_adjusment'),
                                                                   output_field=DecimalField())).order_by('-val')
    else:
        query_set = ChargeBackLineHistory.objects.filter(updated_at__date__range=query).values('item_ref__ndc',
                                                                                               'item_ref__description').annotate(
            entity=F('item_ref__ndc'), val=Sum(F('claim_amount_adjusment'), output_field=DecimalField())).order_by(
            '-val')

    return query_set

@sync_to_async
@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
@async_to_sync
async def get_common_sales_by_categories(request):
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
            old_query = await asyncio.gather(async_query_range(query_filter))
            query = old_query[0]
            # query = query_range(query_filter)
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
            query_set = await asyncio.gather(get_cb_credits_requested_action(query,category))
        elif action == 'cb_lines':
            query_set = await asyncio.gather(get_cb_lines_action(query, category))
        elif action == 'wac_sales':
            query_set = await asyncio.gather(get_wac_sales_action(query, category))
        elif action == 'contract_sales':
            query_set = await asyncio.gather(get_contract_sales_action(query, category))
        elif action == 'cb_credit_issued':
            query_set = await asyncio.gather(get_cb_credit_issued_action(query, category))
        else:
            # cb_credit_adjusted
            query_set = await asyncio.gather(get_cb_credit_adjusted_action(query, category))

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
                # print(query_set)
            for elem in query_set[0]:
                label_elem = elem['entity'] if elem['entity'] else ''

                if category == "product" and label_elem:
                    label_elem = await get_formatted_ndc_for_graph(label_elem)
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

async def get_formatted_ndc_for_graph(ndc):
    return f'{ndc[:5]}-{ndc[5:9]}-{ndc[-2:]}'


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

