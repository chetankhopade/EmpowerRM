# import debug_toolbar

from django.conf.urls.static import static
from django.urls import path, include
from django.apps import apps
from django.contrib import admin

from app.sales_and_inventory import data_852, data_867
from empowerb.settings import DEBUG, MEDIA_URL, MEDIA_ROOT, DATABASES, STATIC_URL, STATIC_ROOT, \
    USE_EXTERNAL_IMPORT_SERVICE

from ermm import views as common_views
from ermm.admin import MASTER_MODELS_ADMIN
from erms.admin import COMPANIES_MODELS_ADMIN

from app import (search, users, direct_customers, profile, help, products,
                 companies, indirect_customers, dashboard, file_manager, notifications, test_async, dashboard_async)
from app.settings import company_settings, srecipients, scontracts, schargebacks, suploads, sedi
from app.contracts import (tab_active_contract, contract_view, tab_price_change, tab_assign_products,
                           tab_manage_servers, tab_manage_membership, contract_cots, contract_aliases, contract_audit_trails)
from app.reports import (report_view, report_contracts, report_chargebacks, report_manual,
                         report_amp, report_cb_detail, report_builder, report_operations)

from app.edi_module import edi_dashboard
from app.administration import service_status, help_desk
from app.administration.edi_mapping import step1, step2, step3

from app.chargebacks import (cb_view, cb_exceptions, cb_archive, cb_import_from_quickbooks, cb_generate_849,
                             cb_import_844, cb_manual, cb_post_to_accounting, cb_purge, cb_revalidate, cb_search,
                             cb_import)

urlpatterns = [

    # Homepage
    path('', common_views.index, name='index'),

    # APIs
    path('api/v1/', include('api.v1.urls'), name='apis_v1'),

    # Login
    path('login', common_views.login_user, name='login'),

    # Logout
    path('logout', common_views.logout_user, name='logout'),

    # Forgot password
    path('forgot_password', common_views.forgot_password, name='forgot_password'),

    # Signup
    path('signup', common_views.signup, name='signup'),

    # Check User Activity API
    path('check_user_activity', common_views.check_user_activity, name='check_user_activity'),
    path('reset_user_activity', common_views.reset_user_activity, name='reset_user_activity'),

    # TESTING ASYNC DJjango 3.1
    path("api/", test_async.api),
    path("api/aggregated/async/", test_async.api_aggregated_async),
    path("api/aggregated/sync/", test_async.api_aggregated_sync),

    # Check API Status
    # path('check_api_status', views.check_api_status, name='check_api_status'),

]

# URLs for Master

master_site_id = admin.AdminSite('default')
for model_obj in apps.get_app_config('ermm').get_models():
    model_admin = MASTER_MODELS_ADMIN.get(model_obj.__name__, '')
    if model_admin:
        master_site_id.register(model_obj, model_admin)

urlpatterns += [

    # Django Admin #

    # Models
    path(f'default/admin/', master_site_id.urls, name='default_admin'),

    # Users and Groups
    path(f'default/admin/users/', admin.site.urls, name='default_admin_users'),

    # Views #

    # User Companies
    path(f'default/companies/', companies.views, name='companies'),

    # User Profile
    path('default/profile', profile.view, name='profile'),
    path('default/profile/edit', profile.edit, name='profile_edit'),
    path('default/profile/avatar', profile.avatar, name='profile_avatar'),
    path('default/profile/feedback', profile.feedback, name='profile_feedback'),
    path('default/profile/load_audit_trail_data', profile.load_audit_trail_data, name='profile_load_audit_trail_data'),
    path('default/profile/change_password', profile.change_password, name='profile_change_password'),

    # Users
    path('default/users', users.view, name='users'),
    path('default/users/activation', users.activation, name='users_activation'),

    # Administration

    # Service Status
    path(f'default/administration/service_status', service_status.view, name=f'administration_service_status'),
    path(f'default/administration/service_status/get_count_of_open_cbs_by_partner', service_status.get_count_of_open_cbs_by_partner, name=f'administration_get_count_of_open_cbs_by_partner'),
    path(f'default/administration/service_status/get_last_inbound_transaction_from_edi_api', service_status.get_last_inbound_transaction_from_edi_api, name=f'administration_service_status_get_last_inbound_transaction_from_edi_api'),
    path(f'default/administration/service_status/get_last_outbound_transaction_from_edi_api', service_status.get_last_outbound_transaction_from_edi_api, name=f'administration_service_status_get_last_outbound_transaction_from_edi_api'),
    path(f'default/administration/service_status/get_parser_activity_from_edi_api', service_status.get_parser_activity_from_edi_api, name=f'administration_service_status_get_parser_activity_from_edi_api'),

    # EDI Mapping
    # step 1
    path(f'default/administration/edi_mapping/s1', step1.view, name=f'administration_edi_mapping_step1'),
    path(f'default/administration/edi_mapping/s1/upload_file', step1.upload_edi_file, name=f'administration_edi_mapping_step1_upload_edi_file'),
    path(f'default/administration/edi_mapping/s1/delete_file', step1.delete_edi_file, name=f'administration_edi_mapping_step1_delete_edi_file'),
    # step 2
    path(f'default/administration/edi_mapping/s2', step2.view, name=f'administration_edi_mapping_step2'),
    path(f'default/administration/edi_mapping/s2/mapping_details', step2.mapping_details, name=f'administration_edi_mapping_step2_mapping_details'),
    path(f'default/administration/edi_mapping/s2/save_template', step2.save_template, name=f'administration_edi_mapping_step2_save_template'),
    # step 3
    path(f'default/administration/edi_mapping/s3', step3.view, name=f'administration_edi_mapping_step3'),
    path(f'default/administration/edi_mapping/s3/<str:map_id>/update_status/<int:status_id>', step3.update_mapping_status, name=f'administration_edi_mapping_step3_update_mapping_status'),
    path(f'default/administration/edi_mapping/s3/source_data', step3.source_data, name=f'administration_edi_mapping_step3_source_data'),
    path(f'default/administration/edi_mapping/s3/destination_data', step3.destination_data, name=f'administration_edi_mapping_step3_destination_data'),
    path(f'default/administration/edi_mapping/s3/destination_data/<str:filename>/view', step3.destination_data_view, name=f'administration_edi_mapping_step3_destination_data_view'),
    path(f'default/administration/edi_mapping/s3/destination_data/<str:filename>/download', step3.destination_data_download, name=f'administration_edi_mapping_step3_destination_data_download'),

    # EDI
    path(f'default/edi/dashboard', edi_dashboard.view, name=f'edi_module_dashboard'),
    path(f'default/edi/dashboard/charts/activity_by_trading_partner', edi_dashboard.chart_activity_by_trading_partner, name='edi_module_dashboard_chart_activity_by_trading_partner'),
    path(f'default/edi/dashboard/charts/processing_totals_by_doctype', edi_dashboard.chart_processing_totals_by_doctype, name='edi_module_dashboard_chart_processing_totals_by_doctype'),
    path(f'default/edi/dashboard/charts/current_mtd_throughput', edi_dashboard.chart_current_mtd_throughput, name='edi_module_dashboard_chart_current_mtd_throughput'),
    path(f'default/edi/dashboard/charts/forecasted_mtd_throughput', edi_dashboard.chart_forecasted_mtd_throughput, name='edi_module_dashboard_chart_forecasted_mtd_throughput'),

    # Help Desk
    path(f'default/administration/helpdesk', help_desk.view, name=f'administration_help_desk'),
    path(f'default/administration/helpdesk/tickets', help_desk.tickets, name=f'administration_help_desk_tickets'),
    path(f'default/administration/helpdesk/tickets/<str:ticket_id>/comments', help_desk.add_comment_to_ticket, name=f'administration_help_desk_add_comment_to_ticket'),
    path(f'default/administration/helpdesk/tickets/<str:ticket_id>/close', help_desk.close_ticket, name=f'administration_help_desk_close_ticket'),

]

# URLs for companies
for company in [k for k in DATABASES.keys() if k != 'default']:

    # django admin register
    company_site_id = admin.AdminSite(company)
    for model_obj in apps.get_app_config('erms').get_models():
        model_admin = COMPANIES_MODELS_ADMIN.get(model_obj.__name__, '')
        if model_admin:
            company_site_id.register(model_obj, model_admin)

    # URLs

    urlpatterns += [

        # Django admin
        path(f'{company}/admin/', company_site_id.urls, name=f'{company}_admin'),
        # Dashboard async
        path(f'{company}/async_dashboard', dashboard_async.views, name=f'{company}_dashboard_async'),
        path(f'{company}/async_dashboard/get_my_net_income_chart_data',
             dashboard_async.async_get_my_net_income_chart_data,
             name=f'{company}_async_dashboard_get_my_net_income_chart_data'),
        path(f'{company}/async_dashboard/get_my_chargeback_chart_data',
             dashboard_async.async_get_my_chargeback_chart_data,
             name=f'{company}_async_dashboard_get_my_chargeback_chart_data'),
        path(f'{company}/async_dashboard/get_sales_distribution_chart_data',
             dashboard_async.get_sales_distribution_chart_data,
             name=f'{company}_async_dashboard_get_sales_distribution_chart_data'),
        path(f'{company}/async_dashboard/get_growth', dashboard_async.get_growth,
             name=f'{company}_async_dashboard_get_growth'),
        path(f'{company}/async_dashboard/get_common_sales_by_categories', dashboard_async.get_common_sales_by_categories,
             name=f'{company}_async_dashboard_get_common_sales_by_categories'),
        path(f'{company}/async_dashboard/get_dates_by_selected_range', dashboard_async.get_dates_by_selected_range,
             name=f'{company}_async_dashboard_get_dates_by_selected_range'),
        # Dashboard
        path(f'{company}/dashboard', dashboard.views, name=f'{company}_dashboard'),

        # Dashboard Charts
        path(f'{company}/dashboard/get_sales_distribution_chart_data', dashboard.get_sales_distribution_chart_data, name=f'{company}_dashboard_get_sales_distribution_chart_data'),
        path(f'{company}/dashboard/get_overall_sales_revenue_chart_data', dashboard.get_overall_sales_revenue_chart_data,
             name=f'{company}_dashboard_get_overall_sales_revenue_chart_data'),
        path(f'{company}/dashboard/get_my_net_income_chart_data',
             dashboard.get_my_net_income_chart_data,
             name=f'{company}_dashboard_get_my_net_income_chart_data'),
        path(f'{company}/dashboard/get_my_chargeback_chart_data',
             dashboard.get_my_chargeback_chart_data,
             name=f'{company}_dashboard_get_my_chargeback_chart_data'),
        path(f'{company}/dashboard/get_cb_count_drill_down_chart',
             dashboard.get_cb_count_drill_down_chart,
             name=f'{company}_dashboard_get_cb_count_drill_down_chart'),
        path(f'{company}/dashboard/get_sales_distribution_by_other_category', dashboard.get_sales_distribution_by_other_category, name=f'{company}_dashboard_get_sales_distribution_by_other_category'),
        path(f'{company}/dashboard/get_cb_sales_by_other_categories', dashboard.get_cb_sales_by_other_categories, name=f'{company}_dashboard_get_cb_sales_by_other_categories'),
        path(f'{company}/dashboard/get_common_sales_by_categories', dashboard.get_common_sales_by_categories,
             name=f'{company}_dashboard_get_common_sales_by_categories'),
        # Dashboard calculations
        path(f'{company}/dashboard/get_wac_sales', dashboard.get_wac_sales, name=f'{company}_dashboard_get_wac_sales'),
        path(f'{company}/dashboard/get_contract_sales', dashboard.get_contract_sales, name=f'{company}_dashboard_get_contract_sales'),
        path(f'{company}/dashboard/get_units_sold', dashboard.get_units_sold, name=f'{company}_dashboard_get_units_sold'),
        path(f'{company}/dashboard/get_cb_credits_requested', dashboard.get_cb_credits_requested,
             name=f'{company}_dashboard_get_cb_credits_requested'),
        path(f'{company}/dashboard/get_cb_credits_issued', dashboard.get_cb_credits_issued,
             name=f'{company}_dashboard_get_cb_credits_issued'),
        path(f'{company}/dashboard/get_cb_credits_adjusted', dashboard.get_cb_credits_adjusted,
             name=f'{company}_dashboard_get_cb_credits_adjusted'),
        path(f'{company}/dashboard/get_projected_indirect_sales', dashboard.get_projected_indirect_sales,
             name=f'{company}_dashboard_get_projected_indirect_sales'),
        path(f'{company}/dashboard/get_new_indirect_customers', dashboard.get_new_indirect_customers,
             name=f'{company}_dashboard_get_new_indirect_customers'),
        path(f'{company}/dashboard/get_growth', dashboard.get_growth, name=f'{company}_dashboard_get_growth'),

        path(f'{company}/dashboard/dashboard_handler', dashboard.dashboard_handler, name=f'{company}_dashboard_dashboard_handler'),
        path(f'{company}/dashboard/get_dates_by_selected_range', dashboard.get_dates_by_selected_range, name=f'{company}_dashboard_get_dates_by_selected_range'),
        path(f'{company}/dashboard/export_grid_data', dashboard.export_grid_data, name=f'{company}_dashboard_export_grid_data'),

        # Chargebacks
        path(f'{company}/chargebacks', cb_view.view, name=f'{company}_chargebacks'),
        path(f'{company}/chargebacks/view/load_data', cb_view.load_data, name=f'{company}_chargebacks_load_data'),
        path(f'{company}/chargebacks/view/load_cbs_counters_data', cb_view.load_cbs_counters_data, name=f'{company}_chargebacks_load_cbs_counters_data'),
        path(f'{company}/chargebacks/<uuid:chargeback_id>/details', cb_view.chargeback_details, name=f'{company}_chargeback_details'),
        path(f'{company}/chargebacks/<uuid:chargeback_id>/details/load_data_cblines', cb_view.load_data_cblines, name=f'{company}_chargeback_details_load_data_cblines'),
        path(f'{company}/chargebacks/<uuid:chargeback_id>/details/modal', cb_view.chargeback_modal_details, name=f'{company}chargeback_modal_details'),
        path(f'{company}/chargebacks/<uuid:chargebackline_id>/line_details/', cb_view.chargeback_line_details, name=f'{company}_chargeback_line_details'),
        path(f'{company}/chargebacks/<uuid:chargebackline_id>/line_details/modal', cb_view.chargeback_line_modal_details, name=f'{company}_chargeback_line_details_modal'),
        path(f'{company}/chargebacks/<uuid:chargeback_id>/details/load_data_cbhistory', cb_view.load_data_cbhistory,name=f'{company}_chargeback_details_load_data_cbhistory'),
        # exceptions / actions
        path(f'{company}/chargebacks/exceptions', cb_exceptions.view, name=f'{company}_chargebacks_exceptions'),
        path(f'{company}/chargebacks/exceptions/load_data_duplicates_header', cb_exceptions.load_data_duplicates_header, name=f'{company}_chargebacks_exceptions_load_data_duplicates_header'),
        path(f'{company}/chargebacks/exceptions/load_data_duplicates_details', cb_exceptions.load_data_duplicates_details, name=f'{company}_chargebacks_exceptions_load_data_duplicates_details'),
        path(f'{company}/chargebacks/exceptions/dispute_cb', cb_exceptions.dispute_cb, name=f'{company}_chargebacks_exceptions_dispute_cb'),
        path(f'{company}/chargebacks/exceptions/autocorrect_price', cb_exceptions.autocorrect_price, name=f'{company}_chargebacks_exceptions_autocorrect_price'),
        path(f'{company}/chargebacks/exceptions/override', cb_exceptions.override, name=f'{company}_chargebacks_exceptions_override'),
        path(f'{company}/chargebacks/exceptions/allow_member', cb_exceptions.allow_member, name=f'{company}_chargebacks_exceptions_allow_member'),
        path(f'{company}/chargebacks/exceptions/assign_cot', cb_exceptions.assign_cot, name=f'{company}_chargebacks_exceptions_assign_cot'),
        path(f'{company}/chargebacks/exceptions/rerun_validations', cb_exceptions.rerun_validations, name=f'{company}_chargebacks_exceptions_rerun_validations'),
        path(f'{company}/chargebacks/exceptions/alter_contract_no', cb_exceptions.alter_contract_no, name=f'{company}_chargebacks_exceptions_alter_contract_no'),
        path(f'{company}/chargebacks/exceptions/update_dispute_code_container', cb_exceptions.update_dispute_code_container, name=f'{company}_chargebacks_exceptions_update_dispute_code_container'),
        path(f'{company}/chargebacks/exceptions/allow_member/get_contract_members', cb_exceptions.get_contract_members, name=f'{company}_chargebacks_exceptions_allow_member_get_contract_members'),
        path(f'{company}/chargebacks/exceptions/allow_member_update', cb_exceptions.allow_member_update, name=f'{company}_chargebacks_exceptions_allow_member_update'),
        path(f'{company}/chargebacks/exceptions/add_indirect_customer/get_indirect_customer', cb_exceptions.get_indirect_customer,
             name=f'{company}_chargebacks_exceptions_add_indirect_customer_get_indirect_customer'),
        path(f'{company}/chargebacks/exceptions/add_indirect_customer', cb_exceptions.add_indirect_customer,name=f'{company}_chargebacks_exceptions_add_indirect_customer'),
        # cb buttons
        path(f'{company}/chargebacks/revalidate', cb_revalidate.view, name=f'{company}_chargebacks_revalidate'),
        path(f'{company}/chargebacks/purge', cb_purge.view, name=f'{company}_chargebacks_purge'),
        # cb search
        path(f'{company}/chargebacks/search', cb_search.view, name=f'{company}_chargebacks_search'),
        path(f'{company}/chargebacks/search/load_data', cb_search.load_data, name=f'{company}_chargebacks_load_data'),
        # import 844
        # EA-1755 - Redirect ERM 2.0 Import to point back to ERM App instead of Import Service
        path(f'{company}/chargebacks/import_844_files', cb_import.view_api, name=f'{company}_import_844_files') if USE_EXTERNAL_IMPORT_SERVICE else path(f'{company}/chargebacks/import_844_files', cb_import.view, name=f'{company}_import_844_files'),

        path(f'{company}/chargebacks/files/upload', cb_import.upload_844_files, name=f'{company}_upload_844_files'),
        path(f'{company}/chargebacks/files/list', cb_import.get_844_files_list, name=f'{company}_get_844_files_list'),
        path(f'{company}/chargebacks/files/delete', cb_import_844.delete_844_files, name=f'{company}_delete_844_files'),
        # import from quickbooks
        path(f'{company}/chargebacks/import_file_from_quickbooks/process', cb_import_from_quickbooks.process_quickbooks_file, name=f'{company}_process_quickbooks_file'),
        # post to accounting
        path(f'{company}/chargebacks/post_to_accounting/none', cb_post_to_accounting.none_handler, name=f'{company}_chargebacks_post_to_accounting_none'),
        path(f'{company}/chargebacks/post_to_accounting/manual', cb_post_to_accounting.manual_handler, name=f'{company}_chargebacks_post_to_accounting_manual'),
        path(f'{company}/chargebacks/post_to_accounting/quickbooks', cb_post_to_accounting.quickbooks_handler, name=f'{company}_chargebacks_post_to_quickbooks'),
        path(f'{company}/chargebacks/post_to_accounting/acumatica/connection', cb_post_to_accounting.acumatica_connection, name=f'{company}_chargebacks_post_to_accounting_acumatica_connection'),
        path(f'{company}/chargebacks/post_to_accounting/acumatica/validations', cb_post_to_accounting.acumatica_validations, name=f'{company}_chargebacks_post_to_accounting_acumatica_validations'),
        path(f'{company}/chargebacks/post_to_accounting/acumatica/sending', cb_post_to_accounting.acumatica_sending, name=f'{company}_chargebacks_post_to_accounting_acumatica_sending'),
        path(f'{company}/chargebacks/post_to_accounting/acumatica/updating', cb_post_to_accounting.acumatica_updating, name=f'{company}_chargebacks_post_to_accounting_acumatica_updating'),
        path(f'{company}/chargebacks/post_to_accounting/dynamics365/connection', cb_post_to_accounting.dynamics365_connection, name=f'{company}_chargebacks_post_to_accounting_dynamics365_connection'),
        path(f'{company}/chargebacks/post_to_accounting/dynamics365/validations', cb_post_to_accounting.dynamics365_validations, name=f'{company}_chargebacks_post_to_accounting_dynamics365_validations'),
        path(f'{company}/chargebacks/post_to_accounting/dynamics365/sending_and_updating', cb_post_to_accounting.dynamics365_sending_and_updating, name=f'{company}_chargebacks_post_to_accounting_dynamics365_sending_and_updating'),
        # generate 849
        path(f'{company}/chargebacks/generate_849', cb_generate_849.view, name=f'{company}_chargebacks_generate_849'),
        path(f'{company}/chargebacks/generate_849/<str:filename>/download', cb_generate_849.download_849_file, name=f'{company}_download_849_file'),
        # archive
        path(f'{company}/chargebacks/archive', cb_archive.view, name=f'{company}_chargebacks_archive'),
        # manual
        path(f'{company}/chargebacks/manual/<int:cbid>/update', cb_manual.cb_update, name=f'{company}_chargeback_manual_update'),
        path(f'{company}/chargebacks/manual/<int:cbid>/delete', cb_manual.cb_delete, name=f'{company}_chargeback_manual_delete'),
        path(f'{company}/chargebacks/manual/<int:cbid>/run_validations', cb_manual.run_validations, name=f'{company}_chargeback_manual_rerun_validations'),
        path(f'{company}/chargebacks/manual/<int:cbid>/lines/<int:cblnid>/delete', cb_manual.cbline_delete, name=f'{company}_chargeback_manual_cbline_delete'),
        path(f'{company}/chargebacks/manual/<int:cbid>/lines/create', cb_manual.cbline_create, name=f'{company}_chargeback_manual_create_line'),
        path(f'{company}/chargebacks/manual/<int:cbid>/lines/<int:cblnid>/update', cb_manual.cbline_update, name=f'{company}_chargeback_manual_update_line'),
        path(f'{company}/chargebacks/manual/create', cb_manual.cb_create, name=f'{company}_chargeback_manual_create'),
        path(f'{company}/chargebacks/manual/purchaser_data', cb_manual.get_json_for_purchaser, name=f'{company}_chargeback_manual_purchaser_data'),

        # Contracts
        path(f'{company}/contracts/', contract_view.view, name=f'{company}_contracts'),
        path(f'{company}/contracts/load_data', contract_view.load_data, name=f'{company}_contracts_load_data'),
        path(f'{company}/contracts/load_expiring_data', contract_view.load_expiring_data, name=f'{company}_contracts_load_expiring_data'),
        path(f'{company}/contracts/create', contract_view.create, name=f'{company}_contract_create'),
        path(f'{company}/contracts/upload_update', contract_view.upload_update, name=f'{company}_contract_upload_update'),
        path(f'{company}/contracts/<uuid:contract_id>/edit', contract_view.edit, name=f'{company}_contract_edit'),
        path(f'{company}/contracts/<uuid:contract_id>/details', contract_view.details, name=f'{company}_contract_details'),
        path(f'{company}/contracts/<uuid:contract_id>/load_contract_lines_data', contract_view.load_contract_lines_data, name=f'{company}_load_contract_lines_data'),
        path(f'{company}/contracts/<uuid:contract_id>/details/products', contract_view.products_on_contracts, name=f'{company}_products_on_contracts'),
        path(f'{company}/contracts/<uuid:contract_id>/details/servers', contract_view.servers_on_contracts, name=f'{company}_servers_on_contracts'),
        path(f'{company}/contracts/<uuid:contract_id>/details/members', contract_view.members_on_contracts, name=f'{company}_servers_on_cmembers'),
        path(f'{company}/contracts/<uuid:contract_id>/details/history', contract_view.history, name=f'{company}_contracts_history'),
        path(f'{company}/contracts/<uuid:contract_id>/contract_audit_trails/load_data', contract_audit_trails.load_data, name=f'{company}_contracts_history_load_data'),
        path(f'{company}/contracts/charts/performance', contract_view.chart_contract_performance, name=f'{company}_chart_contract_performance'),
        path(f'{company}/contracts/contracts_performance_information', contract_view.contracts_performance_information, name=f'{company}_contracts_performance_information'),
        path(f'{company}/contracts/contract_lines_load_data', contract_view.contract_lines_load_data, name=f'{company}_contract_lines_load_data'),
        path(f'{company}/contracts/contract_servers_load_data', contract_view.contract_servers_load_data, name=f'{company}_contract_servers_load_data'),
        path(f'{company}/contracts/<uuid:contract_id>/contract_lines/<uuid:contract_line_id>/delete', contract_view.delete_contract_line, name=f'{company}_contract_delete_contract_line'),

        # Download contract upload update
        path(f'{company}/contracts/download_sample_upload', contract_view.download_sample_upload, name=f'{company}_contract_download_sample_upload'),
        path(f'{company}/contract_upload/update/<str:filename>/download', contract_view.download_contract_upload, name=f'{company}_download_contract_upload'),
        # Delete contract uploaded file
        path(f'{company}/contract_upload/<str:filename>/delete', contract_view.contract_upload_file_delete, name=f'{company}_contract_upload_file_delete'),
        # Contracts CoTs
        path(f'{company}/contracts/<uuid:contract_id>/cots/load_active_cots', contract_cots.load_active_cots, name=f'{company}_contract_load_active_cots'),
        path(f'{company}/contracts/<uuid:contract_id>/cots/add_new_cots', contract_cots.add_new_cots, name=f'{company}_contract_add_new_cots'),
        path(f'{company}/contracts/<uuid:contract_id>/cots/save', contract_cots.save, name=f'{company}_contract_cots_save'),
        path(f'{company}/contracts/<uuid:contract_id>/cots/<uuid:cot_id>/remove', contract_cots.remove, name=f'{company}_contract_cot_remove'),

        # Contract Alias
        path(f'{company}/contracts/<uuid:contract_id>/contract_aliases/load_aliases', contract_aliases.load_aliases, name=f'{company}_contract_aliases'),
        path(f'{company}/contracts/<uuid:contract_id>/contract_aliases/add_new_aliases', contract_aliases.add_new_aliases, name=f'{company}_contract_aliases_add_new_aliases'),
        path(f'{company}/contracts/<uuid:contract_id>/contract_aliases/save', contract_aliases.save, name=f'{company}_contract_aliases_save'),
        path(f'{company}/contracts/<uuid:contract_id>/contract_aliases/<uuid:contract_alias_id>/remove', contract_aliases.remove, name=f'{company}_contract_alias_remove'),


        # Contract tabs options
        # tab active_contract
        path(f'{company}/contracts/<uuid:contract_id>/tab_active_contract/load_data', tab_active_contract.load_data, name=f'{company}_contract_tab_active_contract_load_data'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_active_contract/load_contract_line_items', tab_active_contract.load_contract_line_items, name=f'{company}_contract_tab_active_contract_load_contract_line_items'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_active_contract/update_lines_changes', tab_active_contract.update_lines_changes, name=f'{company}_contract_update_lines_changes'),
        # tab price_change
        path(f'{company}/contracts/<uuid:contract_id>/tab_price_change/load_data', tab_price_change.load_data, name=f'{company}_contract_tab_price_change_load_data'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_price_change/update_lines_changes', tab_price_change.update_lines_changes, name=f'{company}_contract_tab_price_change_update_lines_changes'),
        # tab assign_products
        path(f'{company}/contracts/<uuid:contract_id>/tab_assign_products/load_data', tab_assign_products.load_data, name=f'{company}_contract_tab_assign_products_load_data'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_assign_products/add_items_to_contract', tab_assign_products.add_items_to_contract, name=f'{company}_contract_tab_assign_products_add_items_to_contract'),
        # tab manage_server
        path(f'{company}/contracts/<uuid:contract_id>/tab_manage_servers/load_data', tab_manage_servers.load_data, name=f'{company}_contract_tab_manage_servers_load_data'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_manage_servers/get_servers_list', tab_manage_servers.get_servers_list, name=f'{company}_contract_tab_manage_servers_get_servers_list'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_manage_servers/update_servers_list', tab_manage_servers.update_servers_list, name=f'{company}_contract_tab_manage_servers_update_servers_list'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_manage_servers/active_server_load_data', tab_manage_servers.active_server_load_data,name=f'{company}_contract_active_server_load_data'),
        # tab manage_membership
        path(f'{company}/contracts/<uuid:contract_id>/tab_manage_membership/load_data', tab_manage_membership.load_data,name=f'{company}_contract_tab_manage_memebrship_load_data'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_manage_membership/update_membership_list', tab_manage_membership.update_membership_list, name=f'{company}_contract_tab_manage_membership_update_servers_list'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_manage_membership/update_membership_lines_changes', tab_manage_membership.update_membership_lines_changes, name=f'{company}_contract_update_membership_lines_changes'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_manage_membership/customersrs', tab_manage_membership.autofix_all_membership_errors, name=f'{company}_contract_tab_manage_membership_autofix_all_membership_errors'),
        path(f'{company}/contracts/<uuid:contract_id>/tab_manage_membership/active_membership_load_data', tab_manage_membership.active_membership_load_data,
             name=f'{company}_contract_active_membership_load_data'),
        # Products
        path(f'{company}/products/', products.view, name=f'{company}_products'),
        path(f'{company}/products/load_data', products.load_data, name=f'{company}_products_load_data'),
        path(f'{company}/products/contracts_lines_load_data', products.contracts_lines_load_data, name=f'{company}_products_contracts_lines_load_data'),
        path(f'{company}/products/create', products.create, name=f'{company}_product_create'),
        path(f'{company}/products/<uuid:item_id>/edit', products.edit, name=f'{company}_product_edit'),
        path(f'{company}/products/<uuid:item_id>/details', products.details, name=f'{company}_product_details'),
        path(f'{company}/products/charts/performance', products.chart_product_performance, name=f'{company}_contract_chart_product_performance'),

        # Direct Customers and Distributors
        path(f'{company}/customers/direct/', direct_customers.views, name=f'{company}_direct_customers'),
        path(f'{company}/customers/direct/load_data', direct_customers.load_data, name=f'{company}_direct_customers_load_data'),
        path(f'{company}/customers/direct/serialized_list', direct_customers.serialized_list, name=f'{company}_direct_customers_serialized_list'),
        path(f'{company}/customers/direct/create', direct_customers.create, name=f'{company}_direct_customers_create'),
        path(f'{company}/customers/direct/add', direct_customers.add, name=f'{company}_direct_customers_add'),
        path(f'{company}/customers/direct/add/existing', direct_customers.add_existing, name=f'{company}_direct_customers_add_existing'),
        path(f'{company}/customers/direct/<uuid:customer_id>/edit', direct_customers.edit, name=f'{company}_customer_edit'),
        path(f'{company}/customers/direct/<uuid:customer_id>/metadata', direct_customers.metadata, name=f'{company}_customer_metadata'),
        path(f'{company}/customers/direct/<uuid:customer_id>/metadata/<str:key>/remove', direct_customers.remove_metadata, name=f'{company}_customer_remove_metadata'),
        path(f'{company}/customers/direct/<uuid:customer_id>/data', direct_customers.get_direct_customer_data, name=f'{company}_customer_data'),
        path(f'{company}/customers/direct/<uuid:customer_id>/distribution_centers/create', direct_customers.create_distribution_center, name=f'{company}_distribution_centers_create'),
        path(f'{company}/customers/direct/<uuid:customer_id>/distribution_centers/load_data', direct_customers.load_distribution_centers_data, name=f'{company}_customer_details_load_distribution_centers_data'),
        path(f'{company}/customers/direct/<uuid:customer_id>/distribution_centers/json', direct_customers.get_distribution_center_json, name=f'{company}_customer_details_get_distribution_center_json'),
        path(f'{company}/customers/direct/<uuid:customer_id>/distribution_centers/<uuid:distribution_center_id>/edit', direct_customers.edit_distribution_center, name=f'{company}_distribution_centers_create'),

        # Direct Customers Details
        path(f'{company}/customers/direct/<uuid:customer_id>/details/info', direct_customers.details_info, name=f'{company}_customer_details_info'),
        path(f'{company}/customers/direct/<uuid:customer_id>/details/contracts', direct_customers.details_contracts, name=f'{company}_customer_details_contracts'),
        path(f'{company}/customers/direct/<uuid:customer_id>/details/contracts/load_data', direct_customers.load_contracts_data, name=f'{company}_customer_load_contracts_data'),
        path(f'{company}/customers/direct/<uuid:customer_id>/details/products', direct_customers.details_products, name=f'{company}_customer_details_products'),
        path(f'{company}/customers/direct/<uuid:customer_id>/details/products/load_data', direct_customers.load_products_data, name=f'{company}_customer_load_products_data'),
        path(f'{company}/customers/direct/<uuid:customer_id>/details/contacts', direct_customers.details_contacts, name=f'{company}_customer_details_contacts'),
        path(f'{company}/customers/direct/<uuid:customer_id>/details/contacts/load_data', direct_customers.load_contacts_data, name=f'{company}_customer_load_contacts_data'),
        path(f'{company}/customers/direct/<uuid:customer_id>/details/contacts/<uuid:contact_id>/delete', direct_customers.delete_contact, name=f'{company}_customer_delete_contact'),
        path(f'{company}/customers/direct/<uuid:customer_id>/details/distributors', direct_customers.details_distributors, name=f'{company}_customer_details_distributors'),
        path(f'{company}/customers/direct/<uuid:customer_id>/details/duplicate_distributors',
             direct_customers.duplicate_distributors, name=f'{company}_customer_duplicate_distributors'),

        # Indirect Customers
        path(f'{company}/customers/indirect/', indirect_customers.views, name=f'{company}_indirect_customers'),
        path(f'{company}/customers/indirect/load_data', indirect_customers.load_data, name=f'{company}_indirect_customers_load_data'),
        path(f'{company}/customers/indirect/create', indirect_customers.create, name=f'{company}_indirect_customer_create'),
        path(f'{company}/customers/indirect/<uuid:indirect_customer_id>/edit', indirect_customers.edit, name=f'{company}_indirect_customer_edit'),
        path(f'{company}/customers/indirect/<uuid:indirect_customer_id>/edit_details', indirect_customers.edit_details, name=f'{company}_indirect_customer_edit_details'),
        path(f'{company}/customers/indirect/<uuid:indirect_customer_id>/details/info', indirect_customers.details_info, name=f'{company}_indirect_customer_details_info'),
        path(f'{company}/customers/indirect/<uuid:indirect_customer_id>/details/contracts', indirect_customers.details_contracts, name=f'{company}_indirect_customer_details_contracts'),
        path(f'{company}/customers/indirect/<uuid:indirect_customer_id>/details/products', indirect_customers.details_products, name=f'{company}_indirect_customer_details_products'),
        path(f'{company}/customers/indirect/load_contracts_data', indirect_customers.load_contracts_data, name=f'{company}_indirect_customer_load_contracts_data'),
        path(f'{company}/customers/indirect/load_products_data', indirect_customers.load_products_data, name=f'{company}_indirect_customer_load_products_data'),

        # Help Center
        path(f'{company}/help/', help.views, name=f'{company}_help'),

        # Settings
        path(f'{company}/settings', company_settings.views, name=f'{company}_settings'),
        # settings - chargebacks section
        path(f'{company}/settings/update_integration_system', schargebacks.update_integration_system, name=f'{company}_settings_update_integration_system'),
        # settings - contracts section
        path(f'{company}/settings/cots/copy_from_master', scontracts.copy_from_master, name=f'{company}_cots_copy_from_master'),
        path(f'{company}/settings/cots/save', scontracts.save, name=f'{company}_cots_save'),
        path(f'{company}/settings/cots/add_new_cots', scontracts.add_new_cots, name=f'{company}_cots_add_new_cots'),
        path(f'{company}/settings/cots/<uuid:cot_id>/remove', scontracts.remove, name=f'{company}_cot_remove'),
        path(f'{company}/settings/cots/load_data', scontracts.load_data, name=f'{company}_cot_load_data'),
        # settings - chargebacks section
        path(f'{company}/settings/uploads/company_data', suploads.upload_company_data, name=f'{company}_upload_company_data'),
        path(f'{company}/settings/uploads/company_cbhistory', suploads.upload_company_cbhistory, name=f'{company}_upload_company_cbhistory'),
        # settings - contract manage membership
        # path(f'{company}/settings/uploads/membership_data', suploads.upload_membership_data, name=f'{company}_upload_membership_data'),
        path(f'{company}/settings/uploads/membership_data', suploads.contract_upload_membership, name=f'{company}_contract_upload_membership'),
        # Delete contract membership uploaded file
        path(f'{company}/contract_members_upload/<str:filename>/delete', suploads.contract_members_upload_delete, name=f'{company}_contract_members_upload_delete'),
        path(f'{company}/settings/download_cm_list', suploads.download_cm_list, name=f'{company}_download_cm_list'),

        # settings - recipients section
        path(f'{company}/settings/recipients', srecipients.list, name=f'{company}_recipients_list'),
        path(f'{company}/settings/recipients/add', srecipients.add, name=f'{company}_settings_add_recipient'),
        path(f'{company}/settings/recipients/<uuid:recipient_id>/remove', srecipients.remove, name=f'{company}_settings_remove_recipient'),
        # settings - edi section
        path(f'{company}/settings/update_edi_option', sedi.update_edi_option, name=f'{company}_settings_update_edi_option'),
        path(f'{company}/settings/all_outbound_folder', sedi.all_outbound_folder, name=f'{company}_settings_all_outbound_folder'),

        # Search
        path(f'{company}/search/', search.views, name=f'{company}_search'),

        # Notifications
        path(f'{company}/notifications/load_data', notifications.load_data, name=f'{company}_notifications_load_data'),

        # Reports
        path(f'{company}/reports/', report_view.views, name=f'{company}_reports'),
        path(f'{company}/reports/standard/', report_view.standard, name=f'{company}_standard_reports'),
        path(f'{company}/reports/scheduled/', report_view.scheduled, name=f'{company}_scheduled_reports'),
        path(f'{company}/reports/<uuid:report_id>/update_schedule_report', report_view.update_schedule_report, name=f'{company}_reports_update_schedule_report'),
        path(f'{company}/reports/<uuid:report_id>/execute_report', report_view.execute_report, name=f'{company}_reports_update_execute_report'),
        path(f'{company}/reports/contracts', report_contracts.view, name=f'{company}_report_contracts'),
        path(f'{company}/reports/contracts/load_data', report_contracts.load_data, name=f'{company}_report_contracts_load_data'),
        path(f'{company}/reports/contracts/export', report_contracts.export, name=f'{company}_report_contracts_export'),
        path(f'{company}/reports/chargebacks', report_chargebacks.view, name=f'{company}_report_chargebacks'),
        path(f'{company}/reports/chargebacks/load_data', report_chargebacks.load_data, name=f'{company}_report_chargebacks_load_data'),
        path(f'{company}/reports/chargebacks/export', report_chargebacks.export, name=f'{company}_report_chargebacks_export'),
        path(f'{company}/reports/manual', report_manual.view, name=f'{company}_report_manual'),
        path(f'{company}/reports/manual/load_data', report_manual.load_data, name=f'{company}_report_manual_load_data'),
        path(f'{company}/reports/manual/export', report_manual.export, name=f'{company}_report_manual_export'),
        path(f'{company}/reports/add_report_schedule', report_view.add_report_schedule, name=f'{company}_reports_add_schedule_report'),
        path(f'{company}/reports/load_schedule_reports', report_view.load_schedule_reports, name=f'{company}_reports_load_schedule_reports'),
        path(f'{company}/reports/update_schedule', report_view.update_schedule, name=f'{company}_reports_update_schedule'),
        path(f'{company}/reports/schedule/<uuid:schedule_id>/remove', report_view.remove_schedule, name=f'{company}_reports_remove_schedule'),
        path(f'{company}/reports/<uuid:report_id>/remove', report_view.remove_report, name=f'{company}_reports_remove'),
        path(f'{company}/reports/send_scheduled_report/<uuid:schedule_id>', report_view.send_scheduled_report, name=f'{company}_reports_send_scheduled_report'),
        path(f'{company}/reports/schedule/<uuid:schedule_id>/load_recipients', report_view.load_recipients, name=f'{company}_reports_schedule_load_recipients'),
        path(f'{company}/reports/schedule/<uuid:schedule_id>/add_new_recipients', report_view.add_new_recipients, name=f'{company}_reports_add_new_recipients'),
        path(f'{company}/reports/schedule/recipient/<uuid:schedule_recipient_id>/remove', report_view.remove_schedule_recipient, name=f'{company}_reports_remove_schedule'),
        path(f'{company}/reports/schedule/<uuid:schedule_id>/save', report_view.save_recipients, name=f'{company}_reports_save_recipients'),
        path(f'{company}/reports/get_all', report_view.get_all_reports, name=f'{company}_report_get_all'),
        path(f'{company}/reports/update_schedule_is_enabled', report_view.update_schedule_is_enabled, name=f'{company}_reports_update_schedule_update_schedule_is_enabled'),
        # Report Operations
        path(f'{company}/report/operation/clone', report_operations.clone, name=f'{company}_report_operation_clone'),
        # AMP Report
        path(f'{company}/reports/amp', report_amp.view, name=f'{company}_report_amp'),
        path(f'{company}/reports/amp/load_data', report_amp.load_data, name=f'{company}_report_amp_load_data'),
        path(f'{company}/reports/amp/export', report_amp.export, name=f'{company}_report_amp_export'),
        # CB Detail Report
        path(f'{company}/reports/cb_detail', report_cb_detail.view, name=f'{company}_report_cb_detail'),
        path(f'{company}/reports/cb_detail/load_data', report_cb_detail.load_data, name=f'{company}_report_cb_detail_load_data'),
        path(f'{company}/reports/cb_detail/export', report_cb_detail.export, name=f'{company}_report_cb_detail_export'),
        path(f'{company}/reports/cb_detail/get_direct_customer_by_name', report_cb_detail.get_direct_customer_by_name, name=f'{company}_report_cb_detail_get_direct_customer_by_name'),
        path(f'{company}/reports/cb_detail/get_indirect_customer_by_name', report_cb_detail.get_indirect_customer_by_name, name=f'{company}_report_cb_detail_get_indirect_customer_by_name'),

        # File Manager
        path(f'{company}/files', file_manager.view, name=f'{company}_files'),
        path(f'{company}/files/<str:dirname>/<str:filename>/view', file_manager.file_view, name=f'{company}_file_view'),
        path(f'{company}/files/<str:dirname>/<str:filename>/download', file_manager.file_download, name=f'{company}_file_download'),
        path(f'{company}/files/<str:dirname>/<str:filename>/delete', file_manager.file_delete, name=f'{company}_file_delete'),

        # Report Builder
        path(f'{company}/report_builder', report_builder.view, name=f'{company}_report_builder'),
        path(f'{company}/report_builder/load_reports', report_builder.load_reports, name=f'{company}_report_builder_load_reports'),
        path(f'{company}/report_builder/create', report_builder.create, name=f'{company}_report_builder_load_reports'),
        path(f'{company}/report_builder/<uuid:report_id>/update_report', report_builder.update_report, name=f'{company}_report_builder_update_report'),
        path(f'{company}/report_builder/<uuid:report_id>/update_report_distinct', report_builder.update_report_distinct,
             name=f'{company}_report_builder_update_report_distinct'),
        # Report Builder - Edit and Fields
        path(f'{company}/report_builder/edit/<uuid:report_id>', report_builder.edit, name=f'{company}_report_builder_edit'),
        path(f'{company}/report_builder/get_model_related_fields', report_builder.get_model_related_fields, name=f'{company}_report_builder_get_model_related_fields'),
        path(f'{company}/report_builder/get_model_fields', report_builder.get_model_fields, name=f'{company}_report_builder_get_model_fields'),
        path(f'{company}/report_builder/<uuid:report_id>/load_report_fields', report_builder.load_report_fields, name=f'{company}_report_builder_report_fields'),
        path(f'{company}/report_builder/<uuid:report_id>/add_field_to_report', report_builder.add_field_to_report, name=f'{company}_report_builder_report_add_field_to_report'),
        path(f'{company}/report_builder/<uuid:report_id>/change_field_order', report_builder.change_field_order, name=f'{company}_report_builder_change_field_order'),
        path(f'{company}/report_builder/save_field_changes', report_builder.save_field_changes, name=f'{company}_report_builder_save_field_changes'),
        path(f'{company}/report_builder/remove_report_field', report_builder.remove_report_field, name=f'{company}_report_builder_remove_report_field'),
        # Report Builder - Preview and Download
        path(f'{company}/report_builder/edit/<uuid:report_id>/preview', report_builder.preview_report, name=f'{company}_report_builder_preview_report'),
        path(f'{company}/report_builder/<uuid:report_id>/run', report_builder.run_report, name=f'{company}_report_builder_run_report'),
        path(f'{company}/report_builder/<uuid:report_id>/run/run_report_load_data', report_builder.run_report_load_data, name=f'{company}_report_builder_run_report_load_data'),
        # Report Builder - Filter
        path(f'{company}/report_builder/edit/<uuid:report_id>/filterfields', report_builder.filter_fields, name=f'{company}_report_builder_filter_fields'),
        path(f'{company}/report_builder/<uuid:report_id>/load_report_filter_fields', report_builder.load_report_filter_fields, name=f'{company}_report_builder_load_report_filter_fields'),
        path(f'{company}/report_builder/<uuid:report_id>/add_filter_to_report', report_builder.add_filter_to_report, name=f'{company}_report_builder_report_add_filter_to_report'),
        path(f'{company}/report_builder/save_filter_changes', report_builder.save_filter_changes, name=f'{company}_report_builder_save_filter_changes'),
        path(f'{company}/report_builder/remove_report_filter_field', report_builder.remove_report_filter_field, name=f'{company}_report_builder_remove_report_filter_field'),
        # Report Builder - Run Parameters
        path(f'{company}/report_builder/is_preveiw_data/<uuid:report_id>', report_builder.is_preveiw_data,
             name=f'{company}_report_builder_is_preveiw_data'),
        path(f'{company}/report_builder/edit/<uuid:report_id>/run_parameters', report_builder.run_parameters, name=f'{company}_report_builder_run_parameters'),
        path(f'{company}/report_builder/<uuid:report_id>/load_report_run_parameters', report_builder.load_report_run_parameters, name=f'{company}_report_builder_load_report_run_parameters'),
        path(f'{company}/report_builder/save_run_parameters', report_builder.save_run_parameters, name=f'{company}_report_builder_save_run_parameters'),
        # Report Builder - Custom Field
        path(f'{company}/report_builder/<uuid:report_id>/add_custom_field_to_report', report_builder.add_custom_field_to_report, name=f'{company}_report_builder_report_add_custom_field_to_report'),
        path(f'{company}/report_builder/<uuid:report_id>/add_calculated_field_to_report', report_builder.add_calculated_field_to_report, name=f'{company}_report_builder_add_calculated_field_to_report'),
        path(f'{company}/report_builder/<uuid:report_id>/add_percent_field_to_report', report_builder.add_percent_field_to_report, name=f'{company}_report_builder_add_percent_field_to_report'),
        path(f'{company}/report_builder/<uuid:report_id>/add_case_field_to_report', report_builder.add_case_field_to_report, name=f'{company}_report_builder_add_case_field_to_report'),
        path(f'{company}/report_builder/get_fields_for_calculations', report_builder.get_fields_for_calculations, name=f'{company}_report_builder_get_calculation_fields'),
        path(f'{company}/report_builder/<uuid:report_id>/run_erm_report_api', report_builder.run_erm_report_api,name=f'{company}_run_erm_report_api'),

        # Sales and Inventory
        path(f'{company}/sales_and_inventory/search_852', data_852.view, name=f'{company}_sales_and_inventory_search_852'),
        path(f'{company}/sales_and_inventory/search_867', data_867.view, name=f'{company}_sales_and_inventory_search_867'),

        path(f'{company}/sales_and_inventory/data852/load_data', data_852.load_data, name=f'{company}_sales_and_inventory_search_852_load_data'),
        path(f'{company}/sales_and_inventory/data867/load_data', data_867.load_data, name=f'{company}_sales_and_inventory_search_867_load_data'),

        path(f'{company}/sales_and_inventory/data_852/export', data_852.export, name=f'{company}_sales_and_inventory_data_852_export'),
        path(f'{company}/sales_and_inventory/data_867/export', data_867.export, name=f'{company}_sales_and_inventory_data_867_export'),
    ]


if DEBUG:
    urlpatterns += [
        path('404', common_views.error_404_view, name='404_page'),
        path('500', common_views.error_500_view, name='500_page'),
        # path("__debug__/", include(debug_toolbar.urls))
    ]

# Static and Media
urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
