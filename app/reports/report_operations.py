import decimal
import json
import os
import re

from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Max, Q, QuerySet, F, DecimalField, Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import REPORT_FIELD_STATIC
from app.management.utilities.functions import bad_json, ok_json, model_to_dict_safe
from app.management.utilities.globals import addGlobalData
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_USER_REPORTS_SCHEDULE
from erms.models import Report, ReportField, ReportFilter, ReportDynamicStaticField, ScheduledReport, \
    ScheduledReportRecipient, ReportCaseStatementField


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def clone(request):
    data = {'title': 'Clone Report'}
    addGlobalData(request, data)
    company = data['company'].get_id_str()

    report_name = request.POST.get('name', '')
    report_description = request.POST.get('description', '')
    parent_report_id = request.POST.get('parent_report_id', '')

    if not report_name:
        return bad_json(message="Report Name is required")

    if not parent_report_id:
        return bad_json(message="Parent report is required")

    report_id = clone_report(parent_report_id, report_name, report_description, company)

    return ok_json(data={'message': 'Report cloned successfully', 'report_id': str(report_id)})


def clone_report(parent_report_id, report_name, report_description, company_id):
    # Parent Report
    parent_report = Report.objects.get(id=parent_report_id)
    parent_report_fields = parent_report.reportfield_set.all()
    parent_report_filters = parent_report.reportfilter_set.all()
    parent_report_schedules = parent_report.scheduledreport_set.all()

    # Newly created cloned report
    report = Report(name=report_name, description=report_description)
    report.root_model = parent_report.root_model
    # EA-1530 Add the ability to distinct Report Builder results
    report.distinct = parent_report.distinct
    report.save()
    report_id = report.id

    # Creating/Cloning report fields
    old_new_report_fields = []
    for rfield in parent_report_fields:
        # Old Field_id
        parent_report_field_id = rfield.id
        parent_report_case_fields = ReportCaseStatementField.objects.filter(report_field=rfield)

        rfield.pk = None
        rfield.report_id = report_id
        rfield.save()

        # New Field_id
        report_field_id = rfield.id

        # Add case fields to clone reports
        for parent_case_field in parent_report_case_fields:
            parent_case_field.pk = None
            parent_case_field.report_field_id = report_field_id
            parent_case_field.save()

        if rfield.field_type == REPORT_FIELD_STATIC:
            old_new_report_fields.append({str(parent_report_field_id): str(report_field_id)})

    # Creating/Cloning report filters
    for rfilter in parent_report_filters:
        # Get dynamic static fields for old report filter
        parent_dynamic_static_fields = ReportDynamicStaticField.objects.filter(parameter_field=rfilter)

        rfilter.pk = None
        rfilter.report_id = report_id
        rfilter.save()

        # New report_filter_id
        report_filter_id = rfilter.id

        # Create New Report dynamic fields
        for elem in parent_dynamic_static_fields:
            old_static_field_id = str(elem.static_field.id)
            if old_new_report_fields:
                for i in old_new_report_fields:
                    new_report_field_id = i.get(old_static_field_id)
                    if new_report_field_id is not None:
                        new_static_field_obj = ReportField.objects.get(id=new_report_field_id)
                        report_dynamic_static_field = ReportDynamicStaticField(static_field=new_static_field_obj, parameter_field=rfilter, parameter_attribute=elem.parameter_attribute)
                        report_dynamic_static_field.save()

    # Creating/Cloning report schedule
    for rschedule in parent_report_schedules:
        # Old Schedule_id
        parent_report_field_id = rschedule.id
        parent_report_schedule_recipients = rschedule.scheduledreportrecipient_set.all()

        rschedule.pk = None
        rschedule.report_id = report_id
        rschedule.name = f"Clone of {rschedule.name}"
        rschedule.is_enabled = False
        # EA-1603 Disabled scheduled report was still sent
        rschedule.last_sent = None
        rschedule.save()

        # New Schedule_id
        report_schedule_id = rschedule.id

        # Create json file for schedule
        filename = f"reports_schedule_{report_schedule_id}.json"
        file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company_id}", f"{DIR_NAME_USER_REPORTS_SCHEDULE}",
                                 f"{filename}")
        with open(file_path, 'w') as outfile:
            json.dump(model_to_dict_safe(rschedule), outfile)

        # Attaching Recipients to schedule
        for elem in parent_report_schedule_recipients:
            elem.pk = None
            elem.scheduled_report_id = report_schedule_id
            elem.save()

    return report.id
