from app.management.utilities.baseadmin import MultiDBModelAdminCommon

COMPANIES_MODELS_ADMIN = {}


class DirectCustomerAdmin(MultiDBModelAdminCommon):
    list_display = ('name', 'account_number', 'email', 'phone', 'type', 'metadata',
                    'address1', 'address2', 'city', 'state', 'zip_code', 'customer_id',
                    'enabled_844', 'enabled_849', 'enabled_852', 'enabled_867', 'nocredit', 'all_outbound_folder')
    search_fields = ('name', 'phone', 'email', 'account_number', 'address1', 'city', 'zip_code')
    ordering = ('name',)
    list_filter = ('type', 'enabled_849', 'enabled_844', 'nocredit')


COMPANIES_MODELS_ADMIN.update({'DirectCustomer': DirectCustomerAdmin})


class IndirectCustomerAdmin(MultiDBModelAdminCommon):
    list_display = ('id', 'company_name', 'location_number', 'cot', 'gln_no', 'bid_340', 'customer_id',
                    'address1', 'address2', 'city', 'state', 'zip_code')
    search_fields = ('id', 'company_name', 'location_number')


COMPANIES_MODELS_ADMIN.update({'IndirectCustomer': IndirectCustomerAdmin})


class DistributionCenterAdmin(MultiDBModelAdminCommon):
    list_display = ('name', 'dea_number', 'hin_number', 'customer', 'distribution_center_id',
                    'address1', 'address2', 'city', 'state', 'zip_code')
    search_fields = ('name', 'dea_number', 'address1', 'city', 'state', 'zip_code')


COMPANIES_MODELS_ADMIN.update({'DistributionCenter': DistributionCenterAdmin})


class ContractAdmin(MultiDBModelAdminCommon):
    list_display = ('number', 'description', 'type', 'start_date', 'end_date', 'customer', 'status',
                    'cots', 'eligibility', 'member_eval', 'cot_eval')
    search_fields = ('number', 'description', 'cots')
    list_filter = ('type', 'eligibility', 'member_eval', 'cot_eval')


COMPANIES_MODELS_ADMIN.update({'Contract': ContractAdmin})


class ContractCustomerAdmin(MultiDBModelAdminCommon):
    list_display = ('contract', 'customer', 'start_date', 'end_date', 'status')
    search_fields = ('contract__number', 'customer__name')
    list_filter = ('status',)


COMPANIES_MODELS_ADMIN.update({'ContractCustomer': ContractCustomerAdmin})


class ItemAdmin(MultiDBModelAdminCommon):
    list_display = ('id', 'ndc', 'description', 'account_number', 'strength', 'size', 'brand', 'upc')
    search_fields = ('ndc', 'description', 'account_number')


COMPANIES_MODELS_ADMIN.update({'Item': ItemAdmin})


class ContractLineAdmin(MultiDBModelAdminCommon):
    list_display = ('id', 'contract', 'item', 'type', 'price', 'start_date', 'end_date', 'status')
    search_fields = ('contract__number', 'contract__description', 'item__ndc', 'item__description')
    list_filter = ('status', 'type')
    ordering = ('-created_at',)


COMPANIES_MODELS_ADMIN.update({'ContractLine': ContractLineAdmin})


class ContractPerformanceAdmin(MultiDBModelAdminCommon):
    list_display = ('id', 'contract', 'month', 'year', 'order_count', 'total_revenue')
    search_fields = ('contract__number', 'contract__description')
    list_filter = ('month', 'year')


COMPANIES_MODELS_ADMIN.update({'ContractPerformance': ContractPerformanceAdmin})


class ItemPerformancePerformanceAdmin(MultiDBModelAdminCommon):
    list_display = ('id', 'item', 'month', 'year', 'order_count')
    search_fields = ('item__ndc', 'item__description')
    list_filter = ('month', 'year')


COMPANIES_MODELS_ADMIN.update({'ItemPerformancePerformance': ItemPerformancePerformanceAdmin})


class ChargeBackAdmin(MultiDBModelAdminCommon):
    list_display = (
        'cbid', 'created_at', 'updated_at', 'customer_id', 'distribution_center_id', 'original_chargeback_id',
        'import844_id',
        'document_type', 'type', 'date', 'number', 'stage', 'substage')
    search_fields = ('number', 'cbid')
    list_filter = ('stage', 'substage', 'type')


COMPANIES_MODELS_ADMIN.update({'ChargeBack': ChargeBackAdmin})


class ChargeBackLineAdmin(MultiDBModelAdminCommon):
    list_display = ('cblnid', 'chargeback_id', 'contract_id', 'indirect_customer_id', 'item_id', 'import844_id',
                    'invoice_number', 'invoice_date', 'item_qty', 'item_uom', 'line_status',
                    'action_taken', 'received_with_errors', 'disputes_codes', 'disputes_notes')
    search_fields = ('chargeback_id', 'invoice_number')
    list_filter = ('line_status', 'action_taken', 'received_with_errors')


COMPANIES_MODELS_ADMIN.update({'ChargeBackLine': ChargeBackLineAdmin})


class ChargeBackHistoryAdmin(MultiDBModelAdminCommon):
    list_display = (
        'cbid', 'created_at', 'updated_at', 'customer_id', 'distribution_center_id', 'original_chargeback_id',
        'import844_id',
        'document_type', 'type', 'date', 'number', 'stage', 'substage')
    search_fields = ('number',)
    list_filter = ('stage', 'substage', 'type')


COMPANIES_MODELS_ADMIN.update({'ChargeBackHistory': ChargeBackHistoryAdmin})


class ChargeBackLineHistoryAdmin(MultiDBModelAdminCommon):
    list_display = ('cblnid', 'chargeback_id', 'contract_id', 'indirect_customer_id', 'item_id', 'import844_id',
                    'invoice_number', 'invoice_date', 'item_qty', 'item_uom', 'received_with_errors',
                    'action_taken', 'received_with_errors', 'disputes_codes', 'disputes_notes')
    search_fields = ('cblnid', 'chargeback_id', 'invoice_number')
    list_filter = ('line_status', 'action_taken', 'received_with_errors')


COMPANIES_MODELS_ADMIN.update({'ChargeBackLineHistory': ChargeBackLineHistoryAdmin})


class AuditTrailAdmin(MultiDBModelAdminCommon):
    list_display = ('created_at', 'username', 'action', 'ip_address',
                    'entity1_name', 'entity1_id', 'entity1_reference',
                    'entity2_name', 'entity2_id', 'entity2_reference',
                    'history', 'filename')
    search_fields = ('username', 'ip_address')
    list_filter = ('action', 'entity1_name', 'entity2_name')


COMPANIES_MODELS_ADMIN.update({'AuditTrail': AuditTrailAdmin})


class ChargeBackDisputeAdmin(MultiDBModelAdminCommon):
    list_display = ('chargeback_ref', 'chargebackline_ref', 'dispute_code', 'dispute_note',
                    'field_name', 'field_value', 'is_active')
    search_fields = ('dispute_note',)
    list_filter = ('dispute_code',)


COMPANIES_MODELS_ADMIN.update({'ChargeBackDispute': ChargeBackDisputeAdmin})


class ChargeBackDisputeHistoryAdmin(MultiDBModelAdminCommon):
    list_display = ('chargeback_ref', 'chargebackline_ref', 'dispute_code', 'dispute_note',
                    'field_name', 'field_value', 'is_active')
    search_fields = ('dispute_note',)
    list_filter = ('dispute_code',)


COMPANIES_MODELS_ADMIN.update({'ChargeBackDisputeHistory': ChargeBackDisputeHistoryAdmin})


class ChargebackActionLogAdmin(MultiDBModelAdminCommon):
    list_display = ('chargeback_id', 'process_id', 'process_outcome')
    search_fields = ('chargeback__id', 'process_outcome')
    list_filter = ('process_id',)


COMPANIES_MODELS_ADMIN.update({'ChargebackActionLog': ChargebackActionLogAdmin})


class Import844Admin(MultiDBModelAdminCommon):
    list_display = ('id', 'header', 'line', 'file_name', 'created_at')


COMPANIES_MODELS_ADMIN.update({'Import844': Import844Admin})


class Import844HistoryAdmin(MultiDBModelAdminCommon):
    list_display = ('id', 'header', 'line', 'file_name', 'created_at')


COMPANIES_MODELS_ADMIN.update({'Import844History': Import844HistoryAdmin})


class ContactsAdmin(MultiDBModelAdminCommon):
    list_display = ('first_name', 'last_name', 'job_title', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email')
    ordering = ('name',)


COMPANIES_MODELS_ADMIN.update({'Contacts': ContactsAdmin})


class DirectCustomerContactAdmin(MultiDBModelAdminCommon):
    list_display = ('direct_customer', 'contact', 'created_at')
    search_fields = ('direct_customer__name', 'direct_customer__email', 'contact__name', 'contact__email')
    ordering = ('direct_customer',)


COMPANIES_MODELS_ADMIN.update({'DirectCustomerContact': DirectCustomerContactAdmin})


class IndirectCustomerContactAdmin(MultiDBModelAdminCommon):
    list_display = ('indirect_customer', 'contact', 'created_at')
    search_fields = ('indirect_customer__name', 'indirect_customer__email', 'contact__name', 'contact__email')
    ordering = ('indirect_customer',)


COMPANIES_MODELS_ADMIN.update({'IndirectCustomerContact': IndirectCustomerContactAdmin})


class AccountingTransactionAdmin(MultiDBModelAdminCommon):
    list_display = ('id', 'status', 'cbid', 'cb_number', 'cb_amount_issue', 'customer_accno', 'post_date', 'items',
                    'cb_cm_number', 'cb_cm_date', 'cb_cm_amount', 'integration_type', 'has_error')
    search_fields = ('cbid', 'cb_number', 'customer_accno', 'company__name', 'cb_cm_number')
    list_filter = ('status', 'has_error', 'integration_type')


COMPANIES_MODELS_ADMIN.update({'AccountingTransaction': AccountingTransactionAdmin})


class AccountingErrorAdmin(MultiDBModelAdminCommon):
    list_display = ('id', 'accounting_transaction', 'cbid', 'error', 'cleared_date')
    search_fields = ('accounting_transaction__cbid', 'accounting_transaction__cb_number')


COMPANIES_MODELS_ADMIN.update({'AccountingError': AccountingErrorAdmin})


class ScheduledReportAdmin(MultiDBModelAdminCommon):
    list_display = ('name', 'report_type', 'data_range', 'last_sent', 'is_enabled',
                    'minute', 'hour', 'monthday', 'month', 'weekday', 'recurring')
    search_fields = ('name',)
    list_filter = ('is_enabled', 'recurring')


COMPANIES_MODELS_ADMIN.update({'ScheduledReport': ScheduledReportAdmin})


class ScheduledReportRecipientAdmin(MultiDBModelAdminCommon):
    list_display = ('scheduled_report', 'myrecipient')
    search_fields = ('scheduled_report__name', 'myrecipient')
    list_filter = ('scheduled_report__is_enabled', 'scheduled_report__recurring')


COMPANIES_MODELS_ADMIN.update({'ScheduledReportRecipient': ScheduledReportRecipientAdmin})


class ClassOfTradeAdmin(MultiDBModelAdminCommon):
    list_display = ('group', 'trade_class', 'description', 'is_active', 'id')
    search_fields = ('trade_class', 'description')
    list_filter = ('group', 'is_active')


COMPANIES_MODELS_ADMIN.update({'ClassOfTrade': ClassOfTradeAdmin})


class ContractMemberAdmin(MultiDBModelAdminCommon):
    list_display = ('contract', 'indirect_customer', 'start_date', 'end_date', 'status')
    search_fields = ('contract__number', 'indirect_customer__company_name')
    list_filter = ('status',)


COMPANIES_MODELS_ADMIN.update({'ContractMember': ContractMemberAdmin})


class ContractAliasAdmin(MultiDBModelAdminCommon):
    list_display = ('contract', 'alias', 'created_at')
    search_fields = ('contract__number', 'alias')


COMPANIES_MODELS_ADMIN.update({'ContractAlias': ContractAliasAdmin})


class ReportAdmin(MultiDBModelAdminCommon):
    list_display = ('name', 'description')
    search_fields = ('name',)


COMPANIES_MODELS_ADMIN.update({'Report': ReportAdmin})


class ReportFieldAdmin(MultiDBModelAdminCommon):
    list_display = ('field', 'name', 'report', 'is_sortable', 'is_ascending', 'is_total', 'is_group')
    search_fields = ('name',)
    list_filter = ('is_sortable', 'is_ascending', 'is_total', 'is_group')


COMPANIES_MODELS_ADMIN.update({'ReportField': ReportFieldAdmin})


class ReportFilterAdmin(MultiDBModelAdminCommon):
    list_display = ('field', 'report', 'is_exclude', 'action', 'value1', 'value2')
    search_fields = ('field',)


COMPANIES_MODELS_ADMIN.update({'ReportFilter': ReportFilterAdmin})


class ReportDynamicStaticFieldAdmin(MultiDBModelAdminCommon):
    list_display = ('static_field', 'parameter_field', 'parameter_attribute')
    search_fields = ('static_field__field',)


COMPANIES_MODELS_ADMIN.update({'ReportDynamicStaticField': ReportDynamicStaticFieldAdmin})


class Data852Admin(MultiDBModelAdminCommon):
    list_display = ('created_at', 'configuration_id', 'transaction_id', 'sender', 'receiver',
                    'H_thc', 'H_start_date', 'H_end_date', 'H_po_number', 'H_id_qualifier',
                    'H_ship_to_id_type', 'H_ship_to_id', 'H_distributor_id_type', 'H_distributor_id',
                    'H_reporting_location_id_type', 'H_reporting_location_id',
                    'L_line_item_identification', 'L_item_id_qualifier', 'L_item_id',
                    'L_BS', 'L_TS', 'L_QA', 'L_QP', 'L_QS', 'L_QO', 'L_QC', 'L_QT', 'L_QD',
                    'L_QB', 'L_Q1', 'L_QW', 'L_QR', 'L_QI', 'L_QZ', 'L_QH', 'L_QU', 'L_WQ', 'L_QE', 'id')
    search_fields = ('sender', 'receiver', 'H_thc', 'H_po_number', 'H_distributor_id', 'H_ship_to_id')
    ordering = ('-created_at',)


COMPANIES_MODELS_ADMIN.update({'Data852': Data852Admin})


class Data867Admin(MultiDBModelAdminCommon):
    list_display = ('created_at', 'configuration_id', 'transaction_id', 'sender', 'receiver',
                    'transaction_spc', 'reference_id', 'report_run_date', 'report_type', 'report_start_date',
                    'report_end_date', 'dist_name', 'dist_dea_number', 'supplier_name', 'supplier_dea_number',
                    'transfer_type', 'transfer_type_desc', 'invoice_no', 'invoice_date', 'contract_number',
                    'ship_to_name', 'ship_to_dea_number', 'ship_to_hin_number', 'ship_to_address1', 'ship_to_address2',
                    'ship_to_city', 'ship_to_state', 'ship_to_zip', 'quantity_type', 'quantity', 'quantity_uom',
                    'product_ndc', 'purchaser_item_code', 'mfg_part_number', 'unit_price', 'unit_price_code',
                    'extended_amount', 'product_description', 'id')
    search_fields = ('sender', 'receiver', 'transaction_spc', 'reference_id', 'dist_name', 'supplier_name')
    ordering = ('-created_at',)


COMPANIES_MODELS_ADMIN.update({'Data867': Data867Admin})


class ReportCaseStatementFieldAdmin(MultiDBModelAdminCommon):
    list_display = ('report_field', 'case_field_name', 'action', 'case_when_value', 'case_then_value')
    search_fields = ('static_field__field',)


COMPANIES_MODELS_ADMIN.update({'ReportCaseStatementField': ReportCaseStatementFieldAdmin})
