import requests
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import bad_json, ok_json
from app.management.utilities.globals import addGlobalData
from empowerb.settings import IMPORT_SERVICE_URL, USE_EXTERNAL_IMPORT_SERVICE
from erms.models import (DirectCustomer, ScheduledReport, ClassOfTrade)
from app.management.utilities.constants import CB_MODULE_PAGE, CONTRACT_THRESHOLD_VALUE
from service_import844 import Import844Handler


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def views(request):
    """
        Settings
    """
    data = {'title': 'Company Settings'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # company_setting
    data['company_settings'] = company_settings = data['company'].my_company_settings()

    # Required for upload add contracts pop-up
    # print(data['company_settings'].expired_cb_threshold)
    data['my_customers'] = DirectCustomer.objects.all()
    data['cb_pages'] = CB_MODULE_PAGE
    data['contract_threshold_val'] = CONTRACT_THRESHOLD_VALUE

    if request.method == 'POST':
        try:
            if request.POST['opt'] == 'val_expired_cb_threshold' and not request.POST['expired_cb_threshold']:
                return bad_json('Expired CB threshold value is required')
            if request.POST['opt'] == 'val_expired_contract_threshold' and not request.POST['expire_notification_contract_threshold']:
                return bad_json('Expiration Notification Threshold (Days) is required.')

            with transaction.atomic():

                # enabled or disabled scheduled reports based on this option
                if request.POST['opt'] == 'auto_chargeback_reports_enable':
                    if int(request.POST['value']) == 1:
                        ScheduledReport.objects.update(is_enabled=True)
                    else:
                        ScheduledReport.objects.update(is_enabled=False)

                if request.POST['opt'] == 'generate_transaction_number':
                    data['company'].generate_transaction_number = True if int(request.POST['value']) == 1 else False
                    data['company'].save()
                elif request.POST['opt'] == 'chargeback_start_page':
                    company_settings.cb_start_page = request.POST['value']
                    company_settings.save()
                else:
                    ScheduledReport.objects.update(is_enabled=False)

            if request.POST['opt'] == 'generate_transaction_number':
                data['company'].generate_transaction_number = True if int(request.POST['value']) == 1 else False
                data['company'].save()
            else:
                if request.POST['opt'] != 'expired_contract_threshold' and request.POST['opt'] != 'val_expired_contract_threshold' and request.POST['opt'] != 'expired_cb_threshold' and request.POST['opt'] != 'val_expired_cb_threshold' and request.POST['opt'] != 'chargeback_start_page':
                        setattr(company_settings, request.POST['opt'], True if int(request.POST['value']) == 1 else False)
                        company_settings.save()

                if request.POST['opt'] == 'proactive_membership_validation' and int(request.POST['value']) == 1 and not company_settings.membership_validation_enable:
                    company_settings.membership_validation_enable = True
                    company_settings.save()
                if request.POST['opt'] == 'expired_cb_threshold' and int(request.POST['value']) == 1:
                    company_settings.enable_expired_cb_threshold = True
                    company_settings.expired_cb_threshold = request.POST['expired_cb_threshold']
                if request.POST['opt'] == 'expired_cb_threshold' and int(request.POST['value']) == 0:
                    company_settings.enable_expired_cb_threshold = False
                    company_settings.expired_cb_threshold = None
                    company_settings.save()
                if request.POST['opt'] == 'val_expired_cb_threshold' and int(request.POST['value']) == 1:
                    company_settings.enable_expired_cb_threshold = True
                    company_settings.expired_cb_threshold = request.POST['expired_cb_threshold']
                    company_settings.save()
                if request.POST['opt'] == 'expired_contract_threshold' and int(request.POST['value']) == 0:
                    company_settings.enable_contract_expiration_threshold = False
                    company_settings.contract_expiration_threshold = None
                    company_settings.save()
                if request.POST['opt'] == 'expired_contract_threshold' and int(request.POST['value']) == 1:
                    company_settings.enable_contract_expiration_threshold = True
                    if request.POST['expire_notification_contract_threshold']:
                        company_settings.contract_expiration_threshold = request.POST['expire_notification_contract_threshold']
                    company_settings.save()
                if request.POST['opt'] == 'val_expired_contract_threshold' and int(request.POST['value']) == 1:
                    company_settings.enable_contract_expiration_threshold = True
                    company_settings.contract_expiration_threshold = request.POST['expire_notification_contract_threshold']
                    company_settings.save()

            # EA-1429 - Import Microservice
            if request.POST['opt'] == 'automate_import' and int(request.POST['value']) == 1:
                # EA-1755 - Redirect ERM 2.0 Import to point back to ERM App instead of Import Service
                if USE_EXTERNAL_IMPORT_SERVICE:
                    response = requests.post(f"{IMPORT_SERVICE_URL}/auto_import/check_existing_844_files")
                else:
                    import844_handler = Import844Handler()
                    import844_handler.check_existing_files()

            return ok_json(data={'message': 'Settings Updated!'})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    data['direct_customers'] = DirectCustomer.objects.all()
    data['company_has_cot'] = 'true' if ClassOfTrade.objects.exists() else 'false'
    data['menu_option'] = 'menu_settings'
    print(data)
    return render(request, "settings/settings.html", data)
