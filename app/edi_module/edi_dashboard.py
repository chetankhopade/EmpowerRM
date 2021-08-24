import time

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import ok_json, bad_json
from app.management.utilities.globals import addGlobalData


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'EDI - Dashboard', 'header_title': 'EDI > Dashboard'}
    addGlobalData(request, data)

    data['menu_option'] = 'menu_edi_dashboard'
    return render(request, "edi_module/dashboard.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def chart_activity_by_trading_partner(request):

    try:
        # Example of response
        response = [
            ['Customer', 'Docs'],
            ['AmerisourceBergen', 4260],
            ['McKesson', 3970],
            ['Cardinal', 3453],
            ['HD Smith', 2390],
        ]
        time.sleep(1)
        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def chart_processing_totals_by_doctype(request):

    try:
        # Example of response
        response = [
            ['Year', 'Sales', 'Expenses'],
            ['2013', 1000, 400],
            ['2014', 1170, 460],
            ['2015', 660, 1120],
            ['2016', 1030, 540]
        ]
        time.sleep(1)
        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def chart_current_mtd_throughput(request):

    try:
        # Example of response
        response = [
            ['Task', 'Hours'],
            ['A', 19.2],
            ['B', 30.8],
            [None, 50.0]
        ]
        time.sleep(1)
        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def chart_forecasted_mtd_throughput(request):

    try:
        # Example of response
        response = [
            ['Task', 'Hours'],
            ['A', 5.0],
            ['B', 45.0],
            [None, 50.0]
        ]
        time.sleep(1)
        return JsonResponse(response, safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())
