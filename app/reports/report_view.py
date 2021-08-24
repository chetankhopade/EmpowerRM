import json
import os
import time

from django.apps import apps
from django.contrib.auth.decorators import login_required
import requests
from django.core.validators import validate_email
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status

from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_USER_REPORTS_SCHEDULE, ERM_REPORT_API_TOKEN, \
    ERM_REPORT_API_URL, USE_EXTERNAL_REPORT_SERVICE
from erms.models import ScheduledReport, Report, ScheduledReportRecipient
from app.management.utilities.globals import addGlobalData
from app.management.utilities.functions import (bad_json, ok_json, scheduled_reports_handler, datatable_handler,
                                                model_to_dict_safe)
from app.management.utilities.constants import (REPORT_SCHEDULE_FREQUENCIES, MONTHS, MONTHDAYS, WEEKDAYS,
                                                REPORT_SCHEDULE_FREQUENCY_DAILY, REPORT_SCHEDULE_FREQUENCY_WEEKLY,
                                                REPORT_SCHEDULE_FREQUENCY_MONTHLY,REPORT_SCHEDULE_FREQUENCY_QUARTARLY)

ALL_MODELS = [x._meta.model.__name__ for x in apps.all_models['erms'].values()]
ALLOWED_MODELS = ['ChargeBackLineHistory', 'ChargeBackHistory', 'Data852', 'Data867', 'ContractLine']


@login_required(redirect_field_name='ret', login_url='/login')
def views(request):
    """
        User's reports
    """
    data = {'title': 'Reports', 'header_title': 'My Reports'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # For creating reports
    data['include_models'] = ALLOWED_MODELS
    # for Schedule Reports
    data['scheduled_reports'] = ScheduledReport.objects.all()

    data['report_schedule_frequencies'] = REPORT_SCHEDULE_FREQUENCIES
    data['report_schedule_frequency_daily'] = REPORT_SCHEDULE_FREQUENCY_DAILY
    data['report_schedule_frequency_weekly'] = REPORT_SCHEDULE_FREQUENCY_WEEKLY
    data['report_schedule_frequency_monthly'] = REPORT_SCHEDULE_FREQUENCY_MONTHLY
    data['report_schedule_frequency_quartarly'] = REPORT_SCHEDULE_FREQUENCY_QUARTARLY
    data['report_schedule_months'] = MONTHS
    data['report_schedule_monthdays'] = MONTHDAYS
    data['report_schedule_weekdays'] = WEEKDAYS
    data['report_schedule_hours'] = range(0, 24)
    data['report_schedule_minutes'] = range(0, 60)

    data["all_reports"] = Report.objects.all()
    data['active_tab'] = 'c'
    # active menu
    data['menu_option'] = 'menu_reports'
    return render(request, "reports/reports.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
def standard(request):
    """
        User's reports
    """
    data = {'title': 'Reports', 'header_title': 'My Reports'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # For creating reports
    data['include_models'] = ALLOWED_MODELS
    # for Schedule Reports
    data['scheduled_reports'] = ScheduledReport.objects.all()

    data['report_schedule_frequencies'] = REPORT_SCHEDULE_FREQUENCIES
    data['report_schedule_frequency_daily'] = REPORT_SCHEDULE_FREQUENCY_DAILY
    data['report_schedule_frequency_weekly'] = REPORT_SCHEDULE_FREQUENCY_WEEKLY
    data['report_schedule_frequency_monthly'] = REPORT_SCHEDULE_FREQUENCY_MONTHLY
    data['report_schedule_frequency_quartarly'] = REPORT_SCHEDULE_FREQUENCY_QUARTARLY
    data['report_schedule_months'] = MONTHS
    data['report_schedule_monthdays'] = MONTHDAYS
    data['report_schedule_weekdays'] = WEEKDAYS
    data['report_schedule_hours'] = range(0, 24)
    data['report_schedule_minutes'] = range(0, 60)

    data["all_reports"] = Report.objects.all()
    data['active_tab'] = 's'
    # active menu
    data['menu_option'] = 'menu_reports'
    return render(request, "reports/reports.html", data)

@login_required(redirect_field_name='ret', login_url='/login')
def scheduled(request):
    """
        User's reports
    """
    data = {'title': 'Reports', 'header_title': 'My Reports'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # For creating reports
    data['include_models'] = ALLOWED_MODELS
    # for Schedule Reports
    data['scheduled_reports'] = ScheduledReport.objects.all()

    data['report_schedule_frequencies'] = REPORT_SCHEDULE_FREQUENCIES
    data['report_schedule_frequency_daily'] = REPORT_SCHEDULE_FREQUENCY_DAILY
    data['report_schedule_frequency_weekly'] = REPORT_SCHEDULE_FREQUENCY_WEEKLY
    data['report_schedule_frequency_monthly'] = REPORT_SCHEDULE_FREQUENCY_MONTHLY
    data['report_schedule_frequency_quartarly'] = REPORT_SCHEDULE_FREQUENCY_QUARTARLY
    data['report_schedule_months'] = MONTHS
    data['report_schedule_monthdays'] = MONTHDAYS
    data['report_schedule_weekdays'] = WEEKDAYS
    data['report_schedule_hours'] = range(0, 24)
    data['report_schedule_minutes'] = range(0, 60)

    data["all_reports"] = Report.objects.all()
    data['active_tab'] = 'sr'
    # active menu
    data['menu_option'] = 'menu_reports'
    return render(request, "reports/reports.html", data)

@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def update_schedule_report(request, report_id):
    data = {'title': 'Enable/Disable Report'}
    addGlobalData(request, data)

    try:
        scheduled_report = ScheduledReport.objects.get(id=report_id)
        scheduled_report.is_enabled = True if int(request.POST['value']) == 1 else False
        scheduled_report.save()
        return ok_json(data={"message": f"Scheduled report updated ({'enabled' if scheduled_report.is_enabled else 'disabled'})",})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def execute_report(request, report_id):
    data = {'title': 'Execute Report'}
    addGlobalData(request, data)
    try:
        scheduled_report = ScheduledReport.objects.get(id=report_id)
        recipients = scheduled_reports_handler(report=scheduled_report, db=data['db_name'], from_web=True)
        return ok_json(data={"message": f"Report generated and email has been sent to recipients: {recipients}"})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add_report_schedule(request):
    data = {'title': 'Update Schedule'}
    addGlobalData(request, data)
    company = data['company'].get_id_str()

    report_schedule_data = json.loads(request.POST['data'])
    schedule_data = report_schedule_data[0]
    report_id = schedule_data['rsReportId']
    try:
        report = Report.objects.get(id=report_id)
    except:
        return bad_json(message="No report Found")

    rsName = schedule_data['rsName']
    rsFrequency = int(schedule_data['rsFrequency'])
    rsMinute = int(schedule_data['rsMinute'])
    rsHour = int(schedule_data['rsHour'])
    rsMonthDay = int(schedule_data['rsMonthDay'])
    rsWeekday = int(schedule_data['rsWeekday'])
    rsIsEnabled = schedule_data['rsIsEnabled']

    # Validation for all required fields
    if not rsName:
        return bad_json(message="Name is required")

    # When frequency is daily we do not need month and week day
    if rsFrequency == REPORT_SCHEDULE_FREQUENCY_DAILY:
        rsMonthDay = None
        rsWeekday = None
    elif rsFrequency == REPORT_SCHEDULE_FREQUENCY_WEEKLY:
        rsMonthDay = None
    # try:
    #     schedule_report = ScheduledReport.objects.get(report_id=report_id)
    # except:
    #     schedule_report = ScheduledReport(report_id=report_id)

    schedule_report = ScheduledReport(name=rsName, is_enabled=rsIsEnabled, minute=rsMinute,report=report,
                                      hour=rsHour, monthday=rsMonthDay, weekday=rsWeekday, frequency=rsFrequency)
    schedule_report.save()

    # Create json file for schedule
    filename = f"reports_schedule_{schedule_report.get_id_str()}.json"
    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company}", f"{DIR_NAME_USER_REPORTS_SCHEDULE}", f"{filename}")
    with open(file_path, 'w') as outfile:
        json.dump(model_to_dict_safe(schedule_report), outfile)

    return ok_json(data={'message': 'Schedule updated!','report_schedule_id': schedule_report.get_id_str()})


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_schedule_reports(request):
    queryset = ScheduledReport.objects.all()

    search_fields = ['name']
    response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
    return JsonResponse(response)


def update_schedule(request):
    data = {'title': 'Update Schedule'}
    addGlobalData(request, data)
    company = data['company'].get_id_str()

    report_schedule_data = json.loads(request.POST['data'])
    schedule_data = report_schedule_data[0]
    schedule_id = schedule_data['rsScheduleId']
    try:
        schedule_report = ScheduledReport.objects.get(id=schedule_id)
    except:
        return bad_json(message="No Schedule Found")

    rsName = schedule_data['rsName']
    rsFrequency = int(schedule_data['rsFrequency']) if schedule_data['rsFrequency'] else None
    rsMinute = int(schedule_data['rsMinute']) if schedule_data['rsMinute'] else None
    rsHour = int(schedule_data['rsHour']) if schedule_data['rsHour'] else None
    rsMonthDay = int(schedule_data['rsMonthDay']) if schedule_data['rsMonthDay'] else None
    rsWeekday = int(schedule_data['rsWeekday']) if schedule_data['rsWeekday'] else None
    rsIsEnabled = schedule_data['rsIsEnabled']
    rsReportEditId = schedule_data['rsReportEditId']

    # Validation for all required fields
    if not rsName:
        return bad_json(message="Name is required")

    # When frequency is daily we do not need month and week day
    if rsFrequency == REPORT_SCHEDULE_FREQUENCY_DAILY:
        rsMonthDay = None
        rsWeekday = None
    elif rsFrequency == REPORT_SCHEDULE_FREQUENCY_WEEKLY:
        rsMonthDay = None

    schedule_report.name = rsName
    schedule_report.is_enabled = rsIsEnabled
    schedule_report.minute = rsMinute
    schedule_report.hour = rsHour
    schedule_report.monthday = rsMonthDay
    schedule_report.weekday = rsWeekday
    schedule_report.frequency = rsFrequency
    try:
        report = Report.objects.get(id=rsReportEditId)
        schedule_report.report = report
    except:
        pass
    schedule_report.save()

    # Modify json file for schedule
    filename = f"reports_schedule_{schedule_report.get_id_str()}.json"
    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company}", f"{DIR_NAME_USER_REPORTS_SCHEDULE}", f"{filename}")
    with open(file_path, 'w') as outfile:
        json.dump(model_to_dict_safe(schedule_report), outfile)

    return ok_json(data={'message': 'Schedule updated!','report_schedule_id':schedule_report.get_id_str()})


@login_required(redirect_field_name='ret', login_url='/login')
def remove_schedule(request, schedule_id):
    """
        Remove Report Schedule Alias
    """
    data = {'title': 'Remove Schedule'}
    addGlobalData(request, data)
    company = data['company'].get_id_str()
    try:
        with transaction.atomic():
            ScheduledReport.objects.filter(id=schedule_id).delete()

            try:
                # Remove json created file
                filename = f"reports_schedule_{schedule_id}.json"
                file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company}", f"{DIR_NAME_USER_REPORTS_SCHEDULE}", f"{filename}")
                os.remove(file_path)
            except:
                pass

            return ok_json(data={'message': 'Schedule successfully removed!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def send_scheduled_report(request, schedule_id):
    data = {'title': 'Send Report'}
    addGlobalData(request, data)
    try:
        if USE_EXTERNAL_REPORT_SERVICE: # EA-1756
            company_id = data['company'].get_id_str()
            emailId = request.user.email
            response = requests.get(f"{ERM_REPORT_API_URL}/erm_send_scheduled_report",params={'token': ERM_REPORT_API_TOKEN, 'db_name': data['db_name'], 'schedule_id': schedule_id,'company_id':company_id,'emailId':emailId})
            json_data = json.loads(response.content)
            if response.status_code == status.HTTP_200_OK:
                return ok_json(data={"message": f"Report generated and saved in Reports"})
            elif response.status_code == status.HTTP_400_BAD_REQUEST:
                return bad_json(message= json_data['error'])
            else:
                return bad_json(message= json_data['error'])
        else:
            scheduled_report = ScheduledReport.objects.get(id=schedule_id)
            company_id = data['company'].get_id_str()
            scheduled_report.report_schedule_handler(db=data['db_name'], from_web=True, company_id=company_id)
            # recipients = scheduled_reports_handler(report=scheduled_report, db=data['db_name'], from_web=True)
            return ok_json(data={"message": f"Report generated and saved in Reports"})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_recipients(request, schedule_id):
    scheduled_report = ScheduledReport.objects.get(id=schedule_id)
    queryset = ScheduledReportRecipient.objects.filter(scheduled_report=scheduled_report)

    search_fields = ['name']
    response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
    return JsonResponse(response)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add_new_recipients(request, schedule_id):
    recipients = json.loads(request.POST['recipients'])
    existing_recipients = []
    invalid_emails = []
    try:
        scheduled_report = ScheduledReport.objects.get(id=schedule_id)
    except:
        return bad_json(message='Schedule Not found')
    for elem in recipients:
        elemEmail = elem['email']
        try:
            validate_email(elemEmail)
            try:
                ScheduledReportRecipient.objects.get(scheduled_report=scheduled_report, email=elemEmail)
                existing_recipients.append(elemEmail)
            except:
                ScheduledReportRecipient.objects.create(scheduled_report=scheduled_report, email=elemEmail)
        except:
            invalid_emails.append(elemEmail)

    time.sleep(0.3)
    if invalid_emails:
        return ok_json(data={
            'message': f'Following recipients has invalid email: {", ".join([x for x in invalid_emails])}',
            'error': 'y'})
    if existing_recipients:
        return ok_json(data={
            'message': f'Following recipients already exist for this Schedule: {", ".join([x for x in existing_recipients])}',
            'error': 'y'})
    return ok_json(data={'message': 'Recipients associated to Report Schedule', 'error': 'n'})


@login_required(redirect_field_name='ret', login_url='/login')
def remove_schedule_recipient(request, schedule_recipient_id):
    """
        Remove Report Schedule Alias
    """
    try:
        with transaction.atomic():
            ScheduledReportRecipient.objects.filter(id=schedule_recipient_id).delete()
            return ok_json(data={'message': 'Recipient successfully removed!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def save_recipients(request, schedule_id):
    recipients = json.loads(request.POST['recipients'])
    existing_recipients = []
    invalid_emails = []
    try:
        scheduled_report = ScheduledReport.objects.get(id=schedule_id)
    except:
        return bad_json(message='Schedule Not found')
    for elem in recipients:
        elemEmail = elem['email']
        try:
            validate_email(elemEmail)
            try:
                ScheduledReportRecipient.objects.get(scheduled_report=scheduled_report, email=elemEmail)
                existing_recipients.append(elemEmail)
            except:
                schedule_recipient = ScheduledReportRecipient.objects.get(id=elem["id"])
                schedule_recipient.email = elemEmail
                schedule_recipient.save()
        except:
            invalid_emails.append(elemEmail)

    time.sleep(0.3)
    if invalid_emails:
        return ok_json(data={
            'message': f'Following recipients has invalid email: {", ".join([x for x in invalid_emails])}',
            'error': 'y'})
    if existing_recipients:
        return ok_json(data={
            'message': f'Following recipients already exist for this Schedule: {", ".join([x for x in existing_recipients])}',
            'error': 'y'})
    return ok_json(data={'message': 'Recipients updated!', 'error': 'n'})


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_all_reports(request):
    result = []
    for elem in Report.objects.all():
        result.append({
            'id': elem.get_id_str(),
            'name': elem.name
        })

    return ok_json(data={'message': 'reports', 'reports': result})


@login_required(redirect_field_name='ret', login_url='/login')
def remove_report(request, report_id):
    """
        Remove Report
    """
    data = {'title': 'Remove Report'}
    addGlobalData(request, data)
    company = data['company'].get_id_str()
    try:
        with transaction.atomic():
            report = Report.objects.get(id=report_id)
            for elem in ScheduledReport.objects.filter(report=report):
                try:
                    # Remove json created file
                    filename = f"reports_schedule_{elem.id}.json"
                    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company}", f"{DIR_NAME_USER_REPORTS_SCHEDULE}", f"{filename}")
                    os.remove(file_path)
                    elem.delete()
                except:
                    pass
            report.delete()

            return ok_json(data={'message': 'Report is successfully removed!'})
    except Exception as ex:
        return bad_json(message=ex.__str__())


def update_schedule_is_enabled(request):
    data = {'title': 'Update Schedule is_enabled'}
    addGlobalData(request, data)
    company = data['company'].get_id_str()

    var_is_enabled = request.POST.get('is_enabled', '0')
    schedule_id = request.POST['schedule_id']

    is_enabled = True if var_is_enabled == '1' else False

    try:
        schedule_report = ScheduledReport.objects.get(id=schedule_id)
    except:
        return bad_json(message="No Schedule Found")

    schedule_report.is_enabled = is_enabled
    schedule_report.save()

    # Modify json file for schedule
    filename = f"reports_schedule_{schedule_report.get_id_str()}.json"
    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company}", f"{DIR_NAME_USER_REPORTS_SCHEDULE}", f"{filename}")
    with open(file_path, 'w') as outfile:
        json.dump(model_to_dict_safe(schedule_report), outfile)

    return ok_json(data={'message': 'Schedule updated!','report_schedule_id':schedule_report.get_id_str()})