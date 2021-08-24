import datetime
from itertools import chain

from django.http import HttpResponseRedirect
from django.urls import reverse

from app.management.utilities.constants import (STATUS_ACTIVE, STATUS_INACTIVE, STATUS_PENDING, CONTRACT_TYPE_DIRECT,
                                                CONTRACT_TYPE_INDIRECT, CONTRACT_TYPE_BOTH, CUSTOMER_TYPES,
                                                ELIGIBILITIES, LINE_STATUS_PENDING, LINE_STATUS_APPROVED,
                                                LINE_STATUS_DISPUTED, SUBSTAGE_TYPE_NO_ERRORS, STATUSES,
                                                STAGE_TYPE_ARCHIVED, EDI_MAPPING_TYPE_DELIMITED,
                                                EDI_MAPPING_TYPE_FIXED_WIDTH, EDI_MAPPING_STATUS_BUILDING,
                                                EDI_MAPPING_STATUS_COMPLETE, EDI_MAPPING_STATUS_DISABLED,
                                                EDI_MAPPING_STATUS_ACTIVE, INTEGRATION_SYSTEMS_LIST,
                                                INTEGRATION_SYSTEM_MANUAL_ID, INTEGRATION_SYSTEM_ACUMATICA_ID,
                                                INTEGRATION_SYSTEM_QUICKBOOKS_ID, DATA_RANGES, SYSADMIN_ROLE_ID,
                                                MODULE_ADMINISTRATION_ID, INTEGRATION_SYSTEM_NONE_ID, STATUS_PROPOSED,
                                                FEEDBACK_RATING_POOR, FEEDBACK_RATING_FAIR,
                                                FEEDBACK_RATING_GOOD, FEEDBACK_RATING_EXCELLENT, LINE_STATUSES,
                                                INTEGRATION_SYSTEM_DYNAMICS365_ID, BETA_USER_ROLE_ID)
from app.management.utilities.functions import get_ip_address
from empowerb.middleware import db_ctx
from empowerb.settings import DELTA_TO_CHECK_USER_SESSION, EDI_API_URL, EDI_API_TOKEN, USE_EXTERNAL_REPORT_SERVICE

from ermm.models import UserProfile, Company, Account, Module, UserRole,Role
from erms.models import ClassOfTrade


def addGlobalData(request, data):
    data['user'] = request.user
    data['today'] = now = datetime.datetime.now()
    data['ip_address'] = get_ip_address(request)

    # delta to check user inactivity
    data['delta_to_check_user_session'] = DELTA_TO_CHECK_USER_SESSION
    request.session['last_activity'] = now.strftime('%Y-%m-%d %H:%M:%S')

    # acumatica session
    data['acumatica_request_session'] = None

    # User Profile (data extensions for User model)
    is_sysadmin = False
    is_owner = False
    if not data['user'].is_anonymous:
        data['my_profile'], _ = UserProfile.objects.get_or_create(user=data['user'])
        data['is_owner'] = is_owner = Account.objects.filter(owner=data['user']).exists()
        data['is_sysadmin'] = is_sysadmin = UserRole.objects.filter(user=data['user'], role_id=SYSADMIN_ROLE_ID).exists()
        data['is_beta_user'] = UserRole.objects.filter(user=data['user'], role_id=BETA_USER_ROLE_ID).exists()
        # EA-1614 Add read_only role to Empower
        readonlyUser = Role.objects.filter(name='read_only')
        read_only_role_id = readonlyUser[0].get_id_str() if readonlyUser else None
        data['is_read_only_user'] = False
        if read_only_role_id:
            data['is_read_only_user'] = UserRole.objects.filter(user=data['user'], role_id=read_only_role_id).exists()


    # db name from context var
    db_name = db_ctx.get()

    # Other vars for templates and views (if db_name exist)
    company = None
    if db_name != 'NoOP':

        # companies which user has access to (if is owner get it via accounts else get it thru UserCompany model)
        if is_owner:
            data['user_companies'] = Company.objects.filter(account__owner=data['user']).distinct()
        else:
            data['user_companies'] = Company.objects.filter(usercompany__user=data['user']).distinct()

        # if db is not default then get the companyh and check access to that company
        if db_name != 'default':

            try:
                company = Company.objects.get(database=db_name)
            except Exception:
                return HttpResponseRedirect(reverse('companies'))

    # database
    data['db_name'] = db_name
    # EA-1436 for fixed the alignment
    data['contract_url_path'] = '/'+db_name+'/contracts/'

    # CONSTANTS

    # Status Types
    data['status_active'] = STATUS_ACTIVE
    data['status_inactive'] = STATUS_INACTIVE
    data['status_pending'] = STATUS_PENDING
    data['status_proposed'] = STATUS_PROPOSED
    data['statuses'] = STATUSES

    # CB Lines Status
    data['line_status_pending'] = LINE_STATUS_PENDING
    data['line_status_approved'] = LINE_STATUS_APPROVED
    data['line_status_disputed'] = LINE_STATUS_DISPUTED
    data['line_statuses'] = LINE_STATUSES

    # Contract Types
    data['contract_type_direct'] = CONTRACT_TYPE_DIRECT
    data['contract_type_indirect'] = CONTRACT_TYPE_INDIRECT
    data['contract_type_both'] = CONTRACT_TYPE_BOTH

    # Customer Types
    data['customers_types'] = CUSTOMER_TYPES

    # Eligibilities
    data['eligibilities'] = ELIGIBILITIES

    # Integration Systems
    data['integration_systems_list'] = INTEGRATION_SYSTEMS_LIST[:-1]  # excluding netsuite for now
    data['integration_system_none_id'] = INTEGRATION_SYSTEM_NONE_ID
    data['integration_system_manual_id'] = INTEGRATION_SYSTEM_MANUAL_ID
    data['integration_system_acumatica_id'] = INTEGRATION_SYSTEM_ACUMATICA_ID
    data['integration_system_quickbooks_id'] = INTEGRATION_SYSTEM_QUICKBOOKS_ID
    data['integration_system_dynamics365_id'] = INTEGRATION_SYSTEM_DYNAMICS365_ID

    # CB Substage
    data['substage_type_no_errors'] = SUBSTAGE_TYPE_NO_ERRORS
    data['substage_type_no_errors_display'] = 'NO ERRORS'
    data['substage_type_errors_display'] = 'ERRORS'

    # CB Stage
    data['stage_type_archived'] = STAGE_TYPE_ARCHIVED
    data['stage_type_in_process_display'] = 'IN PROCESS'
    data['stage_type_posted_display'] = 'POSTED'

    # check user access to companies (account owner and has access to the company)
    data['has_access_to_company'] = company.user_has_access(data['user']) if company else True
    data['company'] = company

    # modules
    if company:
        modules = Module.objects.filter(companymodule__company=company, companymodule__enabled=True).exclude(id=MODULE_ADMINISTRATION_ID).distinct()
        if is_sysadmin:
            admin_module = Module.objects.filter(id=MODULE_ADMINISTRATION_ID)
            modules = list(chain(modules, admin_module))

        data['modules'] = modules

    # edi mapping types (delimited or fixed width)
    data['edi_mapping_type_delimited'] = EDI_MAPPING_TYPE_DELIMITED
    data['edi_mapping_type_fixed_width'] = EDI_MAPPING_TYPE_FIXED_WIDTH

    # edi mapping statuses
    data['edi_mapping_status_building'] = EDI_MAPPING_STATUS_BUILDING
    data['edi_mapping_status_complete'] = EDI_MAPPING_STATUS_COMPLETE
    data['edi_mapping_status_disabled'] = EDI_MAPPING_STATUS_DISABLED
    data['edi_mapping_status_active'] = EDI_MAPPING_STATUS_ACTIVE

    # data ranges for dropdown filters
    data['data_ranges'] = DATA_RANGES

    # EDI API integration
    data['edi_api_url'] = f'{EDI_API_URL}'
    data['edi_api_token'] = f'{EDI_API_TOKEN}'
    data['USE_EXTERNAL_REPORT_SERVICE'] = USE_EXTERNAL_REPORT_SERVICE

    # CoT Enables
    data['enabled_cots'] = ClassOfTrade.objects.filter(is_active=True).order_by('trade_class')

    # Feedback Types
    data['feedback_rating_poor'] = FEEDBACK_RATING_POOR
    data['feedback_rating_fair'] = FEEDBACK_RATING_FAIR
    data['feedback_rating_good'] = FEEDBACK_RATING_GOOD
    data['feedback_rating_excellent'] = FEEDBACK_RATING_EXCELLENT
    # EA-1576 Add a company setting to set the start page
    if 'user_companies' in data.keys():
            data['user_companies_list'] = [
                {
                    "name": c.name,
                    "database": c.database,
                    "total_contracts": c.total_contracts,
                    "total_products": c.total_products,
                    "total_direct_customers": c.total_direct_customers,
                    "cb_start_page": Company.objects.get(id=c.id).my_company_settings().cb_start_page
                } for c in data['user_companies']
            ]
