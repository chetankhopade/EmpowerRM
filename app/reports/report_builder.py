import datetime
import decimal
import json
import re

import dateutil
import requests
from rest_framework import status
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Max, Q, QuerySet, F, DecimalField, Sum, Case, When, Value, CharField
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (REPORT_FILTER_TYPES, DATA_RANGE_TD, DATA_RANGE_YD, DATA_RANGE_WTD,
                                                DATA_RANGE_YTD, DATA_RANGE_LW, DATA_RANGE_LY, DATA_RANGE_LM,
                                                DATA_RANGE_MTD, DATA_RANGE_TW,
                                                REPORT_FIELD_STATIC, REPORT_FIELD_SYSTEM, REPORT_FIELD_CALCULATED,
                                                REPORT_FIELD_PERCENT, REPORT_FIELD_CASE_STATEMENT, DATA_RANGE_LQ,
                                                DATA_RANGE_QTD, DATE_FORMAT_LIST)
from app.management.utilities.exports import export_report
from app.management.utilities.functions import (bad_json, ok_json, datatable_handler, convert_string_to_date,
                                                query_range, get_dates_for_report_filter)
from app.management.utilities.globals import addGlobalData
from erms.models import Report, ReportField, ReportFilter, ReportDynamicStaticField, ReportCaseStatementField
from empowerb.settings import ERM_REPORT_API_URL, ERM_REPORT_API_TOKEN

ALL_MODELS = [x._meta.model.__name__ for x in apps.all_models['erms'].values()]
INCLUDED_MODELS = ['ChargeBackLineHistory', 'ChargeBackHistory']


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
        User's reports
    """
    data = {'title': 'Report Builder', 'header_title': 'Report Builder'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['include_models'] = INCLUDED_MODELS

    # active menu
    data['menu_option'] = 'menu_reports'
    return render(request, "report_builder/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_reports(request):
    queryset = Report.objects.all()

    search_fields = ['name', 'description', 'root_model']
    response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
    return JsonResponse(response)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def create(request):
    report_name = request.POST.get('name', '')
    report_description = request.POST.get('description', '')
    report_root_model = request.POST.get('root_model', '')

    if not report_name:
        return bad_json(message="Report Name is required")

    if not report_root_model:
        return bad_json(message="Root Model is required")

    report = Report(name=report_name,
                    description=report_description,
                    root_model=report_root_model)
    report.save()
    data = {
        'report_id': report.id.__str__(),
        'root_model': report_root_model
    }

    return ok_json(data={'message': 'Report is created!', 'data': data})


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def edit(request, report_id):
    data = {'title': 'Edit Report', 'header_title': 'Edit Report'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Report from uuid
    data['report'] = report = Report.objects.get(id=report_id)
    if report.distinct:
        data['is_distinct'] = "checked"

    data['root_model'] = root_model = report.root_model

    data['REPORT_FIELD_SYSTEM'] = REPORT_FIELD_SYSTEM
    data['REPORT_FIELD_STATIC'] = REPORT_FIELD_STATIC
    data['REPORT_FIELD_CALCULATED'] = REPORT_FIELD_CALCULATED
    data['REPORT_FIELD_PERCENT'] = REPORT_FIELD_PERCENT
    data['REPORT_FIELD_CASE_STATEMENT'] = REPORT_FIELD_CASE_STATEMENT

    data['regular_fields'] = get_regular_fields(root_model)
    data['related_fields'] = get_related_fields(root_model)

    data['active_tab'] = 'e'

    data['menu_option'] = 'menu_reports'
    return render(request, "report_builder/edit.html", data)


def get_fields(model_name):
    model = apps.get_model(app_label='erms', model_name=model_name)
    if model:
        return model._meta.get_fields()
    return []


def get_related_fields(model_name):
    return [{'name': x.name, 'model_name': x.related_model._meta.model.__name__} for x in get_fields(model_name) if
            isinstance(x, models.ForeignKey)]

#1687:- 852/867 Report Builder Feedback
def get_regular_fields(model_name):
    if model_name == 'Data852':
        return [{'name': x.name, 'field_type': x.get_internal_type()} for x in get_fields(model_name) if not isinstance(x, models.ManyToOneRel) and x.get_internal_type() != "UUIDField"]
    else:
        return [{'name': x.name, 'field_type': x.get_internal_type()} for x in get_fields(model_name) if
            not isinstance(x, models.ForeignKey) and not isinstance(x, models.ManyToOneRel) and x.get_internal_type() != "UUIDField"]


def get_fields_for_calculations(request):
    model_name = request.POST['model_name']
    get_all_fields_var = request.POST.get('get_all_fields', '0')
    get_all_fields = True if get_all_fields_var == "1" else False
    data = []
    for x in get_fields(model_name):
        if not get_all_fields:
            if x.get_internal_type() in ['IntegerField', 'DecimalField']:
                data.append({'name':x.name})
        else:
            if not isinstance(x, models.ForeignKey) and not isinstance(x, models.ManyToOneRel) and x.get_internal_type() != "UUIDField":
                data.append({'name': x.name})
    return JsonResponse(data, safe=False)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_model_related_fields(request):
    try:
        model_name = request.POST['model_name']
        return JsonResponse(get_related_fields(model_name), safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_model_fields(request):
    try:
        model_name = request.POST['model_name']
        return JsonResponse(get_regular_fields(model_name), safe=False)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_report_fields(request, report_id):
    queryset = ReportField.objects.filter(report_id=report_id).order_by('order')

    search_fields = []
    response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
    return JsonResponse(response)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add_field_to_report(request, report_id):
    try:
        field = request.POST['field']
        field_data_type = request.POST['field_data_type']
        ref_path = request.POST['ref_path']
        report = Report.objects.get(id=report_id)

        # EA-1544 - Include the ability to add an existing field to the report.
        # if ReportField.objects.filter(report=report, field=field, ref_path=ref_path).exists():
        #     return bad_json(message=f"{field} already exists for this report!")

        max_order = ReportField.objects.filter(report=report).aggregate(Max('order'))['order__max']
        # set order to next number
        order = max_order + 1 if max_order or max_order == 0 else 0

        report_field = ReportField(report=report, field=field, field_data_type=field_data_type, name=field, order=order, ref_path=ref_path)
        report_field.save()

        return ok_json(data={'message': f'{field} is added to Report - {report.name}!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add_custom_field_to_report(request, report_id):
    try:
        display_name = request.POST['display_name']
        field_name = request.POST['field_name']
        ref_path = ""
        custom_value = request.POST['custom_value']
        report = Report.objects.get(id=report_id)

        # if ReportField.objects.filter(report=report, field=field).exists():
        #     return bad_json(message=f"{field} already exists for this report!")

        max_order = ReportField.objects.filter(report=report).aggregate(Max('order'))['order__max']
        # set order to next number
        order = max_order + 1 if max_order or max_order == 0 else 0

        report_field = ReportField(report=report, field=field_name, name=display_name, order=order, ref_path=ref_path, field_type=REPORT_FIELD_STATIC, custom_value=custom_value)
        report_field.save()
        # EA-1531 Modified Date is not getting updated for Report Builder page
        report.updated_at = datetime.datetime.now()
        report.save()
        return ok_json(data={'message': f'{display_name} is added to Report - {report.name}!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


def add_calculated_field_to_report(request, report_id):
    try:
        display_name = request.POST['display_name']
        field_name = request.POST['field_name']
        calculation_field1 = request.POST['calculation_field1']
        operand = request.POST['operand']
        operand2 = request.POST['operand2']
        calculation_field2 = request.POST['calculation_field2']
        calculation_field3 = request.POST['calculation_field3']
        ref_path = ""
        custom_value = calculation_field1 + "@@@" + operand + "@@@" + calculation_field2
        if calculation_field3 and operand2:
            custom_value = custom_value + "@@@" +operand2 + "@@@" + calculation_field3
        report = Report.objects.get(id=report_id)

        if ReportField.objects.filter(report=report, field=field_name).exists():
            return bad_json(message=f"{field_name} already exists for this report!")

        max_order = ReportField.objects.filter(report=report).aggregate(Max('order'))['order__max']
        # set order to next number
        order = max_order + 1 if max_order or max_order == 0 else 0

        report_field = ReportField(report=report,
                                   field=field_name,
                                   name=display_name,
                                   order=order,
                                   ref_path=ref_path,
                                   field_type=REPORT_FIELD_CALCULATED,
                                   custom_value=custom_value)
        report_field.save()
        # EA-1531 Modified Date is not getting updated for Report Builder page
        report.updated_at = datetime.datetime.now()
        report.save()
        return ok_json(data={'message': f'{display_name} is added to Report - {report.name}!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


def add_percent_field_to_report(request, report_id):
    try:
        display_name = request.POST['display_name']
        field_name = request.POST['field_name']
        percent_field = request.POST['percent_field']
        value = request.POST['value']
        custom_value = percent_field + '@@@' + value
        ref_path = ""

        report = Report.objects.get(id=report_id)

        if ReportField.objects.filter(report=report, field=field_name).exists():
            return bad_json(message=f"{field_name} already exists for this report!")

        max_order = ReportField.objects.filter(report=report).aggregate(Max('order'))['order__max']
        # set order to next number
        order = max_order + 1 if max_order or max_order == 0 else 0

        report_field = ReportField(report=report,
                                   field=field_name,
                                   name=display_name,
                                   order=order,
                                   ref_path=ref_path,
                                   field_type=REPORT_FIELD_PERCENT,
                                   custom_value=custom_value)
        report_field.save()
        # EA-1531 Modified Date is not getting updated for Report Builder page
        report.updated_at = datetime.datetime.now()
        report.save()

        return ok_json(data={'message': f'{display_name} is added to Report - {report.name}!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


def add_case_field_to_report(request, report_id):
    try:
        display_name = request.POST['display_name']
        report_field_name = request.POST['report_field_name']
        case_field = request.POST['case_field']
        case_is_custom_default = request.POST['case_is_custom_default']
        case_default_value = request.POST['case_custom_default_val']

        cases = request.POST.get('cases', '')
        if cases:
            cases = json.loads(request.POST['cases'])
        else:
            return bad_json(message='You need at least one case to save the case statement field!')
        ref_path = ""

        report = Report.objects.get(id=report_id)

        if ReportField.objects.filter(report=report, field=report_field_name).exists():
            return bad_json(message=f"{report_field_name} already exists for this report!")

        max_order = ReportField.objects.filter(report=report).aggregate(Max('order'))['order__max']
        # set order to next number
        order = max_order + 1 if max_order or max_order == 0 else 0

        report_field = ReportField(report=report,
                                   field=report_field_name,
                                   name=display_name,
                                   order=order,
                                   ref_path=ref_path,
                                   field_type=REPORT_FIELD_CASE_STATEMENT,
                                   case_is_custom_default=True if case_is_custom_default == "1" else False,
                                   case_default_value=case_default_value
                                   )
        report_field.save()

        for elem in cases:
            case_when_value = elem['whenVal']
            case_then_value = elem['thenVal']
            action = elem['caseAction']

            report_case_field = ReportCaseStatementField(report_field=report_field,
                                                         case_field_name=case_field,
                                                         action=action,
                                                         case_when_value=case_when_value,
                                                         case_then_value=case_then_value,
                                                         )
            report_case_field.save()
        # EA-1531 Modified Date is not getting updated for Report Builder page
        report.updated_at = datetime.datetime.now()
        report.save()

        return ok_json(data={'message': f'{display_name} is added to Report - {report.name}!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def change_field_order(request, report_id):
    try:
        field_data = json.loads(request.POST['field_data'])
        if field_data:
            for elem in field_data:
                report_field = ReportField.objects.get(id=elem['field_id'])
                report_id = report_field.report_id
                report_field.order = int(elem["order"])
                report_field.save()

            # EA-1531 Modified Date is not getting updated for Report Builder page
            report = Report.objects.get(id=report_id)
            report.updated_at = datetime.datetime.now()
            report.save()
            return ok_json(data={'message': 'Order rearranged successfully!'})

        return bad_json(message='Field data is empty')
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def save_field_changes(request):
    fields_data = json.loads(request.POST['fields_data'])

    try:
        if fields_data:
            for elem in fields_data:
                report_field_id = elem['id']
                report_field = ReportField.objects.get(id=report_field_id)
                report_id = report_field.report_id
                # EA-1591 Created a new report, but in the process of adding fields the display name is no longer getting saved
                if "display_name" in elem:
                    display_name = elem["display_name"]
                if "custom_value" in elem:
                    custom_value = elem["custom_value"]
                if "filter_data_type" in elem:
                    filter_data_type = elem["filter_data_type"]
                if "decimalformat" in elem:
                    report_field.decimalformat = elem["decimalformat"]

                is_sortable = True if elem['is_sortable'] == "1" else False
                is_ascending = True if elem['is_ascending'] == "1" else False
                is_currency = True if elem['is_currency'] == "1" else False

                if display_name:
                    report_field.name = display_name
                report_field.is_sortable = is_sortable
                report_field.is_ascending = is_ascending
                if report_field.field_type == REPORT_FIELD_STATIC:
                    report_field.custom_value = custom_value
                if report_field.field_data_type == "DateTimeField" or report_field.field_data_type == "DateField":
                    report_field.dateformat = filter_data_type
                if report_field.field_data_type == "IntegerField" or report_field.field_data_type == "DecimalField":
                    report_field.is_currency = is_currency
                report_field.save()
            # EA-1531 Modified Date is not getting updated for Report Builder page
            report = Report.objects.get(id=report_id)
            report.updated_at = datetime.datetime.now()
            report.save()
            return ok_json(data={'message': 'Fields updated successfully!'})
        return bad_json(message='There are no fields to update!')
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def remove_report_field(request):
    try:
        field_id = request.POST['field_id']
        if field_id:
            ReportField.objects.filter(id=field_id).delete()
            return ok_json(data={'message': 'Field removed successfully!'})
        return bad_json(message='There is no field to delete!')

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def preview_report(request, report_id):
    data = {'title': 'Preview Report', 'header_title': 'Preview Report', 'menu_option': 'menu_reports',
            'preview_list': ''}
    addGlobalData(request, data)

    data['report'] = report = Report.objects.get(id=report_id)
    root_model = report.root_model
    report_fields = report.reportfield_set.all().order_by('order')

    display_headers = []
    datatable_columns = []
    exclude_sort = []

    for rf in report_fields:
        display_name = rf.name if rf.name else rf.field
        field = rf.ref_path + rf.field
        display_headers.append(display_name)
        datatable_columns.append(field)
        if rf.field_type == REPORT_FIELD_STATIC:
            # Custom fields should not have sort
            exclude_sort.append(int(rf.order))

    data['display_headers'] = display_headers
    data['datatable_columns'] = datatable_columns
    data['exclude_sort'] = exclude_sort
    data['report_filter_types'] = REPORT_FILTER_TYPES

    data['active_tab'] = 'p'
    data['menu_option'] = 'menu_reports'
    # active menu
    return render(request, "report_builder/preview.html", data)


def filter_fields(request, report_id):
    data = {'title': 'Report Filter Fields', 'header_title': 'Report Filter Fields'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Report from uuid
    data['report'] = report = Report.objects.get(id=report_id)

    data['root_model'] = root_model = report.root_model

    data['regular_fields'] = get_regular_fields(root_model)
    data['related_fields'] = get_related_fields(root_model)

    data['report_filter_types'] = REPORT_FILTER_TYPES

    data['active_tab'] = 'f'

    data['menu_option'] = 'menu_reports'
    return render(request, "report_builder/filter_fields.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_report_filter_fields(request, report_id):
    queryset = ReportFilter.objects.filter(report_id=report_id)

    search_fields = []
    response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
    return JsonResponse(response)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add_filter_to_report(request, report_id):
    try:
        field = request.POST['field']
        ref_path = request.POST['ref_path']
        field_type = request.POST['field_type']

        report = Report.objects.get(id=report_id)

        # if ReportField.objects.filter(report=report, field=field).exists():
        #     return bad_json(message=f"{field} already exists for this report!")

        report_filter = ReportFilter(report=report, field=field, ref_path=ref_path, field_type=field_type)
        report_filter.save()

        return ok_json(data={'message': f'{field} is added to Report - {report.name} for filtering!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def save_filter_changes(request):
    filter_data = json.loads(request.POST['filter_data'])

    try:
        if filter_data:
            for elem in filter_data:
                filter_id = elem['id']
                report_filter = ReportFilter.objects.get(id=filter_id)

                action = elem["action"]
                value = elem['value']
                value2 = elem['value2']

                if report_filter.field_type == "DateTimeField" or report_filter.field_type == "DateField":
                    if value:
                        value = convert_string_to_date(value)
                    if value2 and action == 'range':
                        value2 = convert_string_to_date(value2)
                    else:
                        value2 = None
                report_filter.action = action
                report_filter.value1 = value
                report_filter.value2 = value2
                report_filter.save()

            return ok_json(data={'message': 'Filters updated successfully!'})
        return bad_json(message='There are no fields to update!')
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def remove_report_filter_field(request):
    try:
        field_id = request.POST['field_id']
        if field_id:
            ReportFilter.objects.filter(id=field_id).delete()
            return ok_json(data={'message': 'Filter removed successfully!'})
        return bad_json(message='There is no field to delete!')

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def update_report(request, report_id):
    try:
        report = Report.objects.get(id=report_id)
        if not report:
            return bad_json(message='Report not found!')

        report_name = request.POST['report_name']
        report_description = request.POST['report_description']

        if not report_name:
            return bad_json(message='Report Name is required!')

        report.name = report_name
        report.description = report_description
        report.save()
        return ok_json(data={'message': 'Report updated successfully'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def run_report(request, report_id):
    data = {'title': 'Run Report', 'header_title': 'Reports', 'header_target': '/reports','menu_option': 'menu_reports', 'report_data': ''}
    addGlobalData(request, data)

    data['report'] = report = Report.objects.get(id=report_id)
    report_fields = report.reportfield_set.all().order_by('order')

    data['title'] = report.name

    display_headers = []
    datatable_columns = []
    exclude_sort = []

    for rf in report_fields:
        display_name = rf.name if rf.name else rf.field
        field = rf.ref_path + rf.field
        display_headers.append(display_name)
        datatable_columns.append(field)
        if rf.field_type == REPORT_FIELD_STATIC:
            # Custom fields should not have sort
            exclude_sort.append(int(rf.order))

    data['display_headers'] = display_headers
    data['datatable_columns'] = datatable_columns
    data['exclude_sort'] = exclude_sort
    data['report_filter_types'] = REPORT_FILTER_TYPES

    # active menu
    data['breadcrumb_title1'] = f' > {report.name}'
    data['menu_option'] = 'menu_reports'
    data['ERM_REPORT_API_TOKEN'] = ERM_REPORT_API_TOKEN
    data['ERM_REPORT_API_URL'] = ERM_REPORT_API_URL
    data['Email_ID'] = request.user.email


    return render(request, "report_builder/run.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def run_report_load_data(request, report_id):
    is_preview_report = request.POST.get('is_preview_report', '0')

    results = []
    response = []

    report = Report.objects.get(id=report_id)
    root_model = report.root_model
    is_distinct = report.distinct
    report_fields = report.reportfield_set.all().order_by('order')

    fields_to_fetch = []
    display_headers = []
    order_by = []
    column_list = []
    annotate = {}
    # format_dates_indexes = []
    format_dates_indexes = {}
    format_dates_for_export = []
    is_currency_indexes = []
    field_date_formats = []
    keys_for_export = []
    headers_for_export = []
    is_decimal_indexes = []
    field_decimal_formats = []

    for rf in report_fields:
        display_name = rf.name if rf.name else rf.field
        col_field = rf.ref_path + rf.field
        headers_for_export.append(display_name)
        if col_field in keys_for_export:
            keys_for_export.append(f"{col_field}_2")
        else:
            keys_for_export.append(col_field)
        field_date_formats.append(rf.dateformat)
        field_decimal_formats.append(rf.decimalformat)


        if rf.field_data_type == "DateTimeField" or rf.field_data_type == "DateField":
            # format_dates_indexes.append(rf.order)
            format_dates_for_export.append(rf.order)
            format_dates_indexes[col_field] = rf.order

        if rf.is_currency and (rf.field_data_type == "IntegerField" or rf.field_data_type == "DecimalField"):
            is_currency_indexes.append(rf.order)

        if rf.decimalformat and (rf.field_data_type == "IntegerField" or rf.field_data_type == "DecimalField" or rf.field_type == REPORT_FIELD_CALCULATED or rf.field_type == REPORT_FIELD_PERCENT):
            is_decimal_indexes.append(rf.order)

        if rf.field_type == REPORT_FIELD_SYSTEM:
            field = rf.ref_path + rf.field
            fields_to_fetch.append(field)
            display_headers.append(display_name)
            if col_field in column_list:
                column_list.append(f"{col_field}_2")
            else:
                column_list.append(col_field)
        elif rf.field_type == REPORT_FIELD_CALCULATED:
            f3 = ''
            fieldC = rf.field
            valueList = rf.custom_value.split('@@@')
            f1 = valueList[0]
            operand = valueList[1]
            f2 = valueList[2]
            if len(valueList) > 4:
                 operand2 = valueList[3]
                 f3 = float(valueList[4])
            if operand == '/':
                    if f3:
                        if operand2 == '/':
                            annotate[fieldC] = Sum(F(f1) / F(f2) / f3, output_field=DecimalField())
                        elif operand2 == '-':
                            annotate[fieldC] = Sum(F(f1) / F(f2) - f3, output_field=DecimalField())
                        elif operand2 == '+':
                            annotate[fieldC] = Sum(F(f1) / F(f2) + f3, output_field=DecimalField())
                        else:
                            annotate[fieldC] = Sum(F(f1) / F(f2) * f3, output_field=DecimalField())
                    else:
                        annotate[fieldC] = Sum(F(f1) / F(f2), output_field=DecimalField())
            elif operand == '-':
                    if f3:
                        if operand2 == '/':
                            annotate[fieldC] = Sum(F(f1) - F(f2) / f3, output_field=DecimalField())
                        elif operand2 == '-':
                            annotate[fieldC] = Sum(F(f1) - F(f2) - f3, output_field=DecimalField())
                        elif operand2 == '+':
                            annotate[fieldC] = Sum(F(f1) - F(f2) + f3, output_field=DecimalField())
                        else:
                            annotate[fieldC] = Sum(F(f1) - F(f2) * f3, output_field=DecimalField())
                    else:
                        annotate[fieldC] = Sum(F(f1) - F(f2), output_field=DecimalField())
            elif operand == '+':
                    if f3:
                        if operand2 == '/':
                         annotate[fieldC] = Sum(F(f1) + F(f2) / f3, output_field=DecimalField())
                        elif operand2 == '-':
                         annotate[fieldC] = Sum(F(f1) + F(f2) - f3, output_field=DecimalField())
                        elif operand2 == '+':
                         annotate[fieldC] = Sum(F(f1) + F(f2) + f3, output_field=DecimalField())
                        else:
                            annotate[fieldC] = Sum(F(f1) + F(f2) * f3, output_field=DecimalField())
                    else:
                        annotate[fieldC] = Sum(F(f1) + F(f2), output_field=DecimalField())
            else:
                    if f3:
                        if operand2 == '/':
                         annotate[fieldC] = Sum(F(f1) * F(f2) / f3, output_field=DecimalField())
                        elif operand2 == '-':
                         annotate[fieldC] = Sum(F(f1) * F(f2) - f3, output_field=DecimalField())
                        elif operand2 == '+':
                         annotate[fieldC] = Sum(F(f1) * F(f2) + f3, output_field=DecimalField())
                        else:
                            annotate[fieldC] = Sum(F(f1) * F(f2) * f3, output_field=DecimalField())
                    else:
                        annotate[fieldC] = Sum(F(f1) * F(f2), output_field=DecimalField())
        elif rf.field_type == REPORT_FIELD_PERCENT:
            fieldC = rf.field
            valueList = rf.custom_value.split('@@@')
            f1 = valueList[0]
            val = float(valueList[1])
            annotate[fieldC] = Sum(F(f1)*val / 100, output_field=DecimalField())
        elif rf.field_type == REPORT_FIELD_CASE_STATEMENT:
            fieldC = rf.field
            listOfWhen = []
            varNameDict = {}

            for caseField in ReportCaseStatementField.objects.filter(report_field=rf):
                varKeyName = f"{caseField.case_field_name}__{caseField.action}"
                varNameDict[varKeyName] = caseField.case_when_value
                varVal = caseField.case_then_value
                if caseField.action == 'isnull' and varVal.startswith('1_'):
                    varVal = varVal[2:]
                    listOfWhen.append(When(**varNameDict, then=f"{varVal}"))
                else:
                    listOfWhen.append(When(**varNameDict, then=Value(varVal)))

            annotate[fieldC] = Case(*listOfWhen,
                                    default=F(rf.case_default_value) if not rf.case_is_custom_default else Value(rf.case_default_value),
                                    output_field=CharField()
                                    )


        if rf.is_sortable:
            if rf.is_ascending:
                order_by.append(field)
            else:
                order_by.append(f"-{field}")

    search_params = request.POST.get('search_params', '')
    if search_params:
        search_params = json.loads(search_params)
    else:  # This will be called from Run page to download
        search_params = request.GET.get('search_params', '')
        if search_params:
            search_params = json.loads(search_params)
    if fields_to_fetch:
        filterData = {}
        exclude = {}
        if search_params:
            for sp in search_params:
                report_filter_id = sp["id"]
                report_filter = ReportFilter.objects.get(id=report_filter_id)
                value = sp["value"]
                value2 = sp["value2"]

                if report_filter.field_type == "DateTimeField" or report_filter.field_type == "DateField":
                    value = convert_string_to_date(value)
                    if value2:
                        value2 = convert_string_to_date(value2)

                field = report_filter.ref_path + report_filter.field + "__" + sp["action"]
                if report_filter.field_type == "DateTimeField":
                    field = report_filter.ref_path + report_filter.field + "__date__" + sp["action"]
                if sp["action"] == "range":
                    value = [value, value2]
                elif sp["action"] == "in":
                    value = value.split(",")

                if sp["action"] and sp["action"] == 'exclude':
                    exclude_field = report_filter.ref_path + report_filter.field
                    exclude[exclude_field] = value
                else:
                    filterData[field] = value
        else:
            filter_fields = report.reportfilter_set.all()

            if filter_fields:
                for ff in filter_fields:
                    if ff.action:
                        field = ff.ref_path + ff.field + "__" + ff.action
                    else:
                        field = ff.ref_path + ff.field
                    if ff.field_type == "DateTimeField":
                        if ff.is_run_parameter:
                            query = query_range(ff.date_range)
                            date_range = get_dates_for_report_filter(query[0], query[1], ff.value2)
                            field = ff.ref_path + ff.field + "__date__range"
                            value = date_range
                            # field = ff.ref_path + ff.field + "__date__" + ff.action
                        else:
                            value = ff.value1
                            if ff.action:
                                if ff.action == "range":
                                    field = ff.ref_path + ff.field + "__date__" + ff.action
                                else:
                                    field = ff.ref_path + ff.field + "__" + ff.action
                            else:
                                field = ff.ref_path + ff.field
                            if ff.action == "range":
                                value = [ff.value1, ff.value2]
                    elif ff.field_type == "DateField":
                        if ff.is_run_parameter:
                            query = query_range(ff.date_range)
                            date_range = get_dates_for_report_filter(query[0], query[1], ff.value2)
                            field = ff.ref_path + ff.field + "__range"
                            value = date_range
                        else:
                            value = ff.value1
                            if ff.action == "range":
                                value = [ff.value1, ff.value2]
                    else:
                        if ff.action == "in":
                            if ff.value1:
                                value = ff.value1.split(',')
                            else:
                                value = []
                        else:
                            if ff.field_type == "IntegerField":
                                if not ff.value1:
                                    value = int(0)  # Because empty string for int datatype in mysql works like that
                                else:
                                    value = int(ff.value1)
                            else:
                                value = ff.value1

                    if ff.action and ff.action == 'exclude':
                        exclude_field = ff.ref_path + ff.field
                        exclude[exclude_field] = value
                    else:
                        filterData[field] = value

        model = apps.get_model(app_label='erms', model_name=root_model)
        # EA-1524 HOTFIX: Report Builder results are using Distinct.
        if annotate and is_distinct==0:
            Fieldname = model._meta.pk.name
            fields_to_fetch.insert(0,Fieldname)
        if filterData:
            queryset = model.objects.filter(**filterData).exclude(**exclude).values_list(*fields_to_fetch).order_by(*order_by)
        else:
            queryset = model.objects.exclude(**exclude).values_list(*fields_to_fetch).order_by(*order_by)

        if annotate:
            queryset = queryset.annotate(**annotate)
        # EA-1530 HOTFIX: Add the ability to distinct Report Builder results
        if is_distinct:
            queryset = queryset.distinct()

        total = queryset.count()
        total_filtered = total

        is_export = request.GET.get('is_export', '0')
        if is_export == "1":
            request.POST = request.POST.copy()
            request.POST['length'] = -1  # To get all the records every-time we do export
            request.POST['order[0][column]'] = ""  # So dtatable_handler doesn't throw error for ordering

        # searching
        search = request.POST.get('search[value]', '')
        if search:
            q_objects = Q()  # Create an empty Q object to start with
            for field_name in fields_to_fetch:
                q_objects |= Q(**{f'{field_name}__icontains': search})
            queryset = queryset.filter(q_objects)
            total_filtered = queryset.count()

        # ordering
        is_ordering = request.POST.get('order[0][column]', None)
        if request.POST and is_ordering:
            ord_index = int(request.POST['order[0][column]'])
            ord_asc = True if request.POST['order[0][dir]'] == 'asc' else False
            ord_column = request.POST[f'columns[{ord_index}][data]']

            if queryset:
                if not ord_asc:
                    ord_column = f"-{ord_column}"
                queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset, QuerySet) else queryset

        # pagination
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', -1))
        if length > 0:
            queryset = queryset[start:start + length]

    if is_preview_report == '1':
        queryset = queryset[:20]

    # Converting queryset into list to append custom fields
    report_data_list = list(queryset)
    for i in report_data_list:
        a = list(i)
        # Order annotate / Calulated fields as per requirement
        if annotate:
            if is_distinct == 0:
                a.pop(0) # EA-1524 HOTFIX: Report Builder results are using Distinct.
            annotateLength = len(annotate)
            # get those values from list
            calculatedValuesList = a[-annotateLength:]
            # remove those values from list as it will be at the end of the list always
            a = a[:-annotateLength]
            for index, calf in enumerate(report_fields.filter(field_type__in=[REPORT_FIELD_CALCULATED, REPORT_FIELD_PERCENT, REPORT_FIELD_CASE_STATEMENT])):
                val = calculatedValuesList[index]
                # commenting following code  as it doesn't make sense and generating error
                # if varVal == 'created_at' or varVal == 'updated_at':
                #     val = val[0:10]
                #     val = datetime.datetime.strptime(val, '%Y-%m-%d')
                #     val = datetime.datetime.strftime(val, '%m/%d/%Y')
                if calf.field_type != REPORT_FIELD_CASE_STATEMENT:
                    # val = decimal.Decimal(val).quantize(decimal.Decimal(10) ** -2) if val else decimal.Decimal('0.00')
                    # EA - 1600 - HOTFIX: Do not round amounts when using the calculated field on Report Builder.
                    val = decimal.Decimal(val) if val else decimal.Decimal('0.00')
                    # EA - 1600 - HOTFIX: Do not round amounts when using the calculated field on Report Builder.
                    if calf.decimalformat:
                        val = round(val,calf.decimalformat)
                order = int(calf.order)
                d_name = calf.name if calf.name else calf.field
                col_field = calf.ref_path + calf.field
                if d_name not in display_headers:
                    display_headers.insert(order, d_name)
                if col_field not in column_list:
                    column_list.insert(order, col_field)
                a.insert(order, val)

        for cf in report_fields.filter(field_type=REPORT_FIELD_STATIC):
            custom_field_value = cf.custom_value
            # If field is chosen for Start Date
            dynamic_static_field_obj = ReportDynamicStaticField.objects.filter(static_field=cf, parameter_attribute="SD")
            if dynamic_static_field_obj:
                dynamic_static_field = dynamic_static_field_obj[0]
                ff = ReportFilter.objects.get(id=dynamic_static_field.parameter_field_id)
                if ff:
                    if ff.is_run_parameter:
                        query = query_range(ff.date_range)
                        date_range = get_dates_for_report_filter(query[0], query[1], ff.value2)
                        custom_field_value = date_range[0].strftime(dynamic_static_field.static_dateformat)  # i.e. Start Date / SD
            # If field is chosen for End Date
            dynamic_static_field_obj = ReportDynamicStaticField.objects.filter(static_field=cf,parameter_attribute="ED")
            if dynamic_static_field_obj:
                dynamic_static_field = dynamic_static_field_obj[0]
                ff = ReportFilter.objects.get(id=dynamic_static_field.parameter_field_id)
                if ff:
                    if ff.is_run_parameter:
                        query = query_range(ff.date_range)
                        date_range = get_dates_for_report_filter(query[0], query[1], ff.value2)
                        custom_field_value = date_range[1].strftime(dynamic_static_field.static_dateformat)
            order = int(cf.order)
            d_name = cf.name if cf.name else cf.field
            col_field = cf.ref_path + cf.field
            if d_name not in display_headers:
                display_headers.insert(order, d_name)
            if col_field not in column_list:
                column_list.insert(order, col_field)
            a.insert(order, custom_field_value)
            # Convert list into returnable json dataset where columns_list is json key and a is value

        # if is_export == "0":
        #     for j in format_dates_indexes:
        #         # a[j] = a[j].strftime(field_date_formats[j])
        #         # EA-1631 Report Custom Field : Errors message on preview and run report when custom field is on position one in report.
        #         if isinstance(a[j - 1], datetime.date):
        #             a[j - 1] = a[j - 1].strftime(field_date_formats[j])
        #         else:
        #             a[j] = a[j].strftime(field_date_formats[j])
        #
        #     for k in is_currency_indexes:
        #         a[k] = '${:,.2f}'.format(a[k]) if a[k] else '$ 0.00'

        a = dict(zip(column_list, a))
        # EA-1707 - HOTFIX: Getting error in report builder when using the date format
        if is_export == "0" and format_dates_indexes:
            for elem in a.keys():
                if elem in format_dates_indexes.keys():
                    a[elem] = a[elem].strftime(field_date_formats[format_dates_indexes[elem]])
        results.append(a)

    if is_export == "1":
        response = export_report(report.name, headers_for_export, results, False, "", field_date_formats, format_dates_for_export, is_currency_indexes, keys_for_export,is_decimal_indexes,field_decimal_formats)
        return response

    response = {
        'data': results,
        'recordsTotal': total,
        'recordsFiltered': total_filtered,
    }

    return JsonResponse(response)


def run_parameters(request, report_id):
    data = {'title': 'Report Run Parameters', 'header_title': 'Report Run Parameters'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get Report from uuid
    data['report'] = report = Report.objects.get(id=report_id)

    data['report_filter_types'] = REPORT_FILTER_TYPES

    data['active_tab'] = 'r'

    static_fields = report.reportfield_set.filter(field_type=REPORT_FIELD_STATIC)
    data['static_fields'] = []
    for elem in static_fields:
        data['static_fields'].append({
            'id': elem.get_id_str(),
            'name': elem.name,
            'field': elem.field
        })

    data['menu_option'] = 'menu_reports'
    data['static_date_format_list'] = DATE_FORMAT_LIST

    return render(request, "report_builder/run_parameters.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_report_run_parameters(request, report_id):
    queryset = ReportFilter.objects.filter(report_id=report_id, field_type__in=['DateTimeField', 'DateField'])

    search_fields = []
    response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
    return JsonResponse(response)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def save_run_parameters(request):
    parameters = json.loads(request.POST['parameters'])

    try:
        if parameters:
            for elem in parameters:
                filter_id = elem['id']
                report_filter = ReportFilter.objects.get(id=filter_id)

                is_mapped_with_static_field = elem['is_mapped_with_static_field']
                parameter_attribute = elem['parameter_date_attribute']  # For SD
                static_field_id = elem['static_field']

                parameter_attribute2 = elem['parameter_date_attribute2'] # For ED
                static_field_id2 = elem['static_field2']

                date_format_static = elem['date_format_static']
                date_format_static_field2 = elem['date_format_static_field2']
                # Delete Report dynamicStatic field for run parameter if it is not checked and create new if checked
                ReportDynamicStaticField.objects.filter(parameter_field=report_filter).delete()

                if report_filter.field_type == "DateTimeField" or report_filter.field_type == "DateField":
                    is_run_parameter = elem['is_run_parameter']
                    if is_run_parameter:
                        date_range = elem['range']
                        source = elem['source']
                        date_range = date_range if date_range in [DATA_RANGE_TD, DATA_RANGE_YD, DATA_RANGE_LM, DATA_RANGE_WTD, DATA_RANGE_MTD, DATA_RANGE_YTD, DATA_RANGE_TW, DATA_RANGE_LW, DATA_RANGE_LY, DATA_RANGE_LQ, DATA_RANGE_QTD] else 'TD'  # Default to TD

                        # Regx to verify {sign}{number}{d/w}
                        x = re.search("^-?\d+(d|w|m)$", source)
                        if not x:
                            return bad_json(message='Value must be like 2d or 1w or -3d')

                        report_filter.is_run_parameter = is_run_parameter
                        report_filter.is_mapped_with_static_field = is_mapped_with_static_field
                        report_filter.date_range = date_range
                        report_filter.value2 = source
                        report_filter.save()

                        if is_mapped_with_static_field:
                            if static_field_id and parameter_attribute:
                                report_static_field = ReportField.objects.get(id=static_field_id)
                                report_dynamic_static_field = ReportDynamicStaticField(static_field=report_static_field, parameter_field=report_filter, parameter_attribute=parameter_attribute)
                                report_dynamic_static_field.static_dateformat = date_format_static
                                report_dynamic_static_field.save()
                            if static_field_id2 and parameter_attribute2:
                                report_static_field2 = ReportField.objects.get(id=static_field_id2)
                                report_dynamic_static_field2 = ReportDynamicStaticField(static_field=report_static_field2, parameter_field=report_filter, parameter_attribute=parameter_attribute2)
                                report_dynamic_static_field2.static_dateformat = date_format_static_field2
                                report_dynamic_static_field2.save()
                    else:
                        report_filter.is_run_parameter = is_run_parameter
                        report_filter.save()

            return ok_json(data={'message': 'Parameters updated successfully!'})
        return bad_json(message='There are no fields to update!')
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def run_erm_report_api(request,report_id):

    data = {'title': 'Administration - Get Parser Activity Data'}
    addGlobalData(request, data)
    try:
        search_params = request.POST.get('search_params',request.GET.get('search_params'))
        search_value = request.POST.get('search[value]','')
        zero_order_column = request.POST.get('order[0][column]','')
        start = request.POST.get('start',0)
        length = request.POST.get('length', -1)
        is_export = request.GET.get('is_export', '0')

        json_data = []
        format_dates_indexes = []
        is_currency_indexes = []
        field_date_formats = []
        keys_for_export = []
        headers_for_export = []
        is_decimal_indexes = []
        field_decimal_formats = []
        response = requests.get(f"{ERM_REPORT_API_URL}/erm_report_load_data", params={'token': ERM_REPORT_API_TOKEN,'db_name':data['db_name'],'id':report_id,'search_params':search_params,'search[value]':search_value,'order[0][column]':zero_order_column,'start':start,'length':length,'emailId':request.user.email,'action_name':'Run','is_export':is_export})
        if response.status_code == status.HTTP_200_OK:
            if is_export == "1":
                json_data = json.loads(response.content)
                start_time = dateutil.parser.parse(json_data['start_time'])
                field_date_formats = json_data['field_date_formats']
                format_dates_indexes = json_data['format_dates_indexes']
                is_currency_indexes = json_data['is_currency_indexes']
                keys_for_export = json_data['keys_for_export']
                is_decimal_indexes = json_data['is_decimal_indexes']
                field_decimal_formats = json_data['field_decimal_formats']
                exportresponse = export_report(json_data['report_name'], json_data['display_headers'],
                                               json_data['data'], False, "", field_date_formats, format_dates_indexes,
                                               is_currency_indexes, keys_for_export, is_decimal_indexes,
                                               field_decimal_formats)

                end_time = datetime.datetime.now()
                timediff = end_time - start_time # In seconds
                requests.get(f"{ERM_REPORT_API_URL}/erm_update_log_report",
                             params={'token': ERM_REPORT_API_TOKEN,
                                     'report_log_id': json_data['reportRunLogId'],
                                     'timediff':timediff.seconds,
                                     'emailId':request.user.email,
                                     'action_name':"Download"
                                     })
                return exportresponse
            return JsonResponse(response.json())
        return bad_json(message=f'Error getting parser activity data. Status Code: {response.status_code}')

    except Exception:
        return bad_json(message='ConnectionError: API is not working')


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def update_report_distinct(request, report_id):
    try:
        report = Report.objects.get(id=report_id)
        if not report:
            return bad_json(message='Report not found!')

        is_distinct = True if request.POST['is_distinct'] == "1" else False
        report.distinct = is_distinct
        report.save()
        return ok_json(data={'message': 'Report updated successfully'})

    except Exception as ex:
        return bad_json(message=ex.__str__())

@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def is_preveiw_data(request, report_id):
    try:
        report = Report.objects.get(id=report_id)
        report_fields = report.reportfield_set.all().order_by('order')
        fields_to_fetch = []
        is_flag = False
        for rf in report_fields:
            if rf.field_type == REPORT_FIELD_SYSTEM:
                field = rf.ref_path + rf.field
                fields_to_fetch.append(field)
        if fields_to_fetch:
            is_flag = True
        data = {
            'fields_to_fetch': is_flag
        }
        return ok_json(data={'message': 'Report is created!', 'data': data})
    except Exception as ex:
        return bad_json(message=ex.__str__())

