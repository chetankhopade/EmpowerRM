from app.management.utilities.baseadmin import MultiDBModelAdminCommon

# Admin Models
MASTER_MODELS_ADMIN = {}


class SubscriptionAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'type', 'start_date', 'end_date')
    list_filter = ('type', )


MASTER_MODELS_ADMIN.update({'Subscription': SubscriptionAdmin})


class DisputeAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'type', 'code', 'description', 'explanation')
    search_fields = ('code', 'description', 'explanation')


MASTER_MODELS_ADMIN.update({'Dispute': DisputeAdmin})


class ApprovedReasonAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'description')
    search_fields = ('description', )


MASTER_MODELS_ADMIN.update({'ApprovedReason': ApprovedReasonAdmin})


class AccountAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'owner', 'name', 'subscription')
    search_fields = ('name', 'owner__username', 'owner__first_name', 'owner__last_name')
    list_filter = ('subscription__type', )


MASTER_MODELS_ADMIN.update({'Account': AccountAdmin})


class IntegrationSystemAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'name')
    search_fields = ('name', )


MASTER_MODELS_ADMIN.update({'IntegrationSystem': IntegrationSystemAdmin})


class CompanyAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'name', 'database', 'account', 'cbid_counter', 'cblnid_counter', 'processing_option',
                    'integration_system', 'integration_config', 'address1', 'address2', 'city', 'state', 'zip_code',
                    'generate_transaction_number', 'show_only_disputed_lines_in_849')
    search_fields = ('name', 'account__user__first_name', 'account__user__last_name', 'account__user__email')
    list_filter = ('integration_system', 'generate_transaction_number', 'show_only_disputed_lines_in_849')


MASTER_MODELS_ADMIN.update({'Company': CompanyAdmin})


class CompanySettingAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'company', 'auto_contact_notifications', 'auto_chargeback_reports_enable',
                    'enable_daily_report', 'default_wac_enable', 'auto_assign_big_3_as_contract_servers',
                    'global_customer_list_updates_overrides_local_changes', 'alert_enabled',
                    'alert_sent_in_single_daily_digest', 'membership_validation_enable',
                    'proactive_membership_validation', 'auto_contract_notification_enabled',
                    'class_of_trade_validation_enabled', 'automatic_chargeback_processing', 'automate_import',
                    'quickbooks_api_integration')


MASTER_MODELS_ADMIN.update({'CompanySetting': CompanySettingAdmin})


class RecipientAdmin(MultiDBModelAdminCommon):

    list_display = ('company_setting', 'email', 'first_name', 'last_name', 'is_processing')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_processing', )


MASTER_MODELS_ADMIN.update({'Recipient': RecipientAdmin})


class QuickbooksConfigurationsAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'token', 'company', 'path', 'interval')
    search_fields = ('company__name', )
    list_filter = ('token', )
    ordering = ('token', )


MASTER_MODELS_ADMIN.update({'QuickbooksConfigurations': QuickbooksConfigurationsAdmin})


class UserCompanyAdmin(MultiDBModelAdminCommon):

    list_display = ('user', 'company')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'company__name', 'company__database')


MASTER_MODELS_ADMIN.update({'UserCompany': UserCompanyAdmin})


class UserProfileAdmin(MultiDBModelAdminCommon):

    list_display = ('user', 'phone', 'title', 'department', 'company', 'timezone')
    search_fields = ('user__username', 'title', 'token')


MASTER_MODELS_ADMIN.update({'UserProfile': UserProfileAdmin})


class UserFeedbackAdmin(MultiDBModelAdminCommon):

    list_display = ('user', 'rating', 'comments')
    search_fields = ('user__username', 'comments')
    list_filter = ('rating', )


MASTER_MODELS_ADMIN.update({'UserFeedback': UserFeedbackAdmin})


class DirectCustomerAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'name', 'type', 'address1', 'address2', 'city', 'state', 'zip_code', 'email', 'phone', )
    search_fields = ('name', 'email', 'address1', 'city', 'zip_code')
    ordering = ('name', )


MASTER_MODELS_ADMIN.update({'DirectCustomer': DirectCustomerAdmin})


class DistributionCenterAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'name', 'customer',
                    'address1', 'address2', 'city', 'state', 'zip_code', 'dea_number', 'hin_number')
    search_fields = ('customer__name', 'customer__email', 'name', 'dea_number',
                     'address1', 'city', 'state', 'zip_code')
    ordering = ('name', )


MASTER_MODELS_ADMIN.update({'DistributionCenter': DistributionCenterAdmin})


class IndirectCustomerAdmin(MultiDBModelAdminCommon):

    list_display = ('name', 'account_number', 'email', 'phone',
                    'address1', 'address2', 'city', 'state', 'zip_code')
    search_fields = ('name', 'account_number', 'email', 'address1', 'city', 'zip_code')


MASTER_MODELS_ADMIN.update({'IndirectCustomer': IndirectCustomerAdmin})


class ClassOfTradeAdmin(MultiDBModelAdminCommon):

    list_display = ('group', 'value', 'description', 'id')
    search_fields = ('value', 'description')
    list_filter = ('group', )


MASTER_MODELS_ADMIN.update({'ClassOfTrade': ClassOfTradeAdmin})


class RoleAdmin(MultiDBModelAdminCommon):

    list_display = ('id', 'name')
    search_fields = ('name', )


MASTER_MODELS_ADMIN.update({'Role': RoleAdmin})


class UserRoleAdmin(MultiDBModelAdminCommon):

    list_display = ('user', 'role')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('role', )


MASTER_MODELS_ADMIN.update({'UserRole': UserRoleAdmin})


class ModuleAdmin(MultiDBModelAdminCommon):

    list_display = ('name', 'order', 'id')
    search_fields = ('name', )
    ordering = ('order', )


MASTER_MODELS_ADMIN.update({'Module': ModuleAdmin})


class ViewAdmin(MultiDBModelAdminCommon):

    list_display = ('name', 'module', 'order', 'icon', 'link', 'option')
    search_fields = ('name', )
    list_filter = ('module', )
    ordering = ('module', 'order')


MASTER_MODELS_ADMIN.update({'View': ViewAdmin})


class CompanyModuleAdmin(MultiDBModelAdminCommon):

    list_display = ('module', 'company', 'enabled')
    search_fields = ('company__name', 'module__name')
    list_filter = ('module', 'enabled')


MASTER_MODELS_ADMIN.update({'CompanyModule': CompanyModuleAdmin})


class EDIMappingTemplateAdmin(MultiDBModelAdminCommon):

    list_display = ('name', 'document_type', 'status', 'output_format', 'mapping_type', 'delimiter', 'show_header',
                    'main_loop_segment', 'nested_loop_segment', 'end_loop_segment', 'created_at')
    search_fields = ('name', )
    list_filter = ('document_type', 'mapping_type', 'output_format', 'show_header', 'status')
    ordering = ('created_at', )


MASTER_MODELS_ADMIN.update({'EDIMappingTemplate': EDIMappingTemplateAdmin})


class EDIMappingTemplateDetailAdmin(MultiDBModelAdminCommon):

    list_display = ('emt', 'map_name', 'map_segment', 'map_descriptor', 'is_enabled',
                    'fw_row', 'fw_char', 'fw_length', 'created_at')
    search_fields = ('map_name', 'map_segment', 'map_descriptor')
    list_filter = ('is_enabled', )
    ordering = ('emt', 'created_at', )


MASTER_MODELS_ADMIN.update({'EDIMappingTemplateDetail': EDIMappingTemplateDetailAdmin})
