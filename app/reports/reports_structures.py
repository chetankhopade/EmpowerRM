"""
    Structures for every Report to be exported to excel or csv dynamically
"""


def get_exceptions_header_report_structure():
    """
    JSON Structute for Exceptions Header Report (header columns names and field names for data)
    :return:
    """
    return [
        # {
        #     'header': 'Distributor',
        #     'field': 'distributor',
        #     'type': '',
        #     'value': ''
        # },
        {
            'header': 'SubContractNo',
            'field': 'submitted_contract_no',
            'type': '',
            'value': ''
        },
        {
            'header': 'ContractNo',
            'field': 'contract_no',
            'type': '',
            'value': ''
        },
        {
            'header': 'NDC',
            'field': 'item_ndc',
            'type': '',
            'value': ''
        },
        {
            'header': 'WAC Sub',
            'field': 'wac_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'WAC Sys',
            'field': 'wac_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'CP Sub',
            'field': 'cp_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'CP Sys',
            'field': 'cp_system',
            'type': '',
            'value': ''
        },
        # EA-1468 - HOTFIX: Exception Page & Slider File Export Missing Columns
        # add two additional columns “minimum_invoice_date“ & “maximum_invoice_date” that show the earliest invoice date and most recent invoice date in each group
        {
            'header': 'minimum_invoice_date',
            'field': 'min_invoice_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'maximum_invoice_date',
            'field': 'max_invoice_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Errors Count',
            'field': 'errors_count',
            'type': '',
            'value': ''
        },
        {
            'header': 'Disputes Notes',
            'field': 'cb_dispute_notes',
            'type': '',
            'value': ''
        },
    ]


def get_exceptions_details_report_structure():
    """
    JSON Structute for Exceptions Details Report (header columns names and field names for data)
    :return:
    """
    return [
        {
            'header': 'CBID',
            'field': 'chargeback_ref__cbid',
            'type': '',
            'value': ''
        },
        {
            'header': 'CBLNID',
            'field': 'cblnid',
            'type': '',
            'value': ''
        },
        {
            'header': 'Customer',
            'field': 'chargeback_ref__customer_ref__name',
            'type': '',
            'value': ''
        },
        {
            'header': 'DC',
            'field': 'chargeback_ref__distribution_center_ref__name',
            'type': '',
            'value': ''
        },
        {
            'header': 'CBNumber',
            'field': 'chargeback_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'SubContractNo',
            'field': 'submitted_contract_no',
            'type': '',
            'value': ''
        },
        {
            'header': 'ContractNo',
            'field': 'contract_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'LocNo',
            'field': 'indirect_customer_ref__location_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'indirect_customer_name',
            'field': 'indirect_customer_ref__company_name',
            'type': '',
            'value': ''
        },
        {
            'header': 'indirect_customer_address1',
            'field': 'indirect_customer_ref__address1',
            'type': '',
            'value': ''
        },
        {
            'header': 'indirect_customer_address2',
            'field': 'indirect_customer_ref__address2',
            'type': '',
            'value': ''
        },
        {
            'header': 'indirect_customer_city',
            'field': 'indirect_customer_ref__city',
            'type': '',
            'value': ''
        },
        {
            'header': 'indirect_customer_state',
            'field': 'indirect_customer_ref__state',
            'type': '',
            'value': ''
        },
        {
            'header': 'indirect_customer_zipcode',
            'field': 'indirect_customer_ref__zip_code',
            'type': '',
            'value': ''
        },
        {
            'header': 'NDC',
            'field': 'item_ref__ndc',
            'type': '',
            'value': ''
        },
        {
            'header': 'Item Description',
            'field': 'item_ref__description',
            'type': '',
            'value': ''
        },
        {
            'header': 'InvDate',
            'field': 'invoice_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'InvNo',
            'field': 'invoice_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'WAC Sub',
            'field': 'wac_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'WAC Sys',
            'field': 'wac_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'CP Sub',
            'field': 'contract_price_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'CP Sys',
            'field': 'contract_price_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'Claim amount submitted',
            'field': 'claim_amount_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'Claim amount system',
            'field': 'claim_amount_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'Claim amount adjustment',
            'field': 'claim_amount_adjusment',
            'type': '',
            'value': ''
        },
        {
            'header': 'Disputes Codes',
            'field': 'disputes_codes',
            'type': '',
            'value': ''
        },
        # EA-1468 - HOTFIX: Exception Page & Slider File Export Missing Columns
        {
            'header': 'Disputes Notes',
            'field': 'disputes_notes',
            'type': '',
            'value': ''
        },
        {
            'header': 'Error Count',
            'field': 'error_count',
            'type': '',
            'value': ''
        }
    ]


def get_contracts_report_structure():
    """
        JSON Structute for Contracts Report (header columns names and field names for data)
        :return:
    """
    return [
        {
            'header': 'Contract Name',
            'field': 'contract__description',
            'type': '',
            'value': ''
        },
        {
            'header': 'Contract Number',
            'field': 'contract__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Contract Type',
            'field': 'contract__type',  # choicefield
            'type': 'choice',
            'value': 'CONTRACT_TYPES'
        },
        {
            'header': 'Contract Start',
            'field': 'contract__start_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Contract End',
            'field': 'contract__end_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Product ID',
            'field': 'item__ndc',
            'type': '',
            'value': ''
        },
        {
            'header': 'Product Type',
            'field': 'created_by',
            'type': 'static',
            'value': 'NDC'
        },
        {
            'header': 'Product Name',
            'field': 'item__description',
            'type': '',
            'value': ''
        },
        {
            'header': 'Unit Measure',
            'field': 'updated_by',
            'type': 'static',
            'value': 'EA'
        },
        {
            'header': 'Unit Contract Price',
            'field': 'price',
            'type': '',
            'value': ''
        },
        {
            'header': 'Product Start',
            'field': 'start_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Product End',
            'field': 'end_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Status',
            'field': 'status',   # choicefield
            'type': 'choice',
            'value': 'STATUSES'
        }
    ]


def get_chargebackslines_history_report_structure():
    """
    JSON Structute for Chargebacks Report (header columns names and field names for data)
    :return:
    """
    return [
        {
            'header': 'CBType',
            'field': 'chargeback_ref__type',
            'type': '',
            'value': ''
        },
        {
            'header': 'Credit Memo Number',
            'field': 'chargeback_ref__accounting_credit_memo_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Credit Memo Date',
            'field': 'chargeback_ref__accounting_credit_memo_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Parent Wholesaler',
            'field': 'chargeback_ref__customer_ref__name',
            'type': '',
            'value': ''
        },
        {
            'header': 'Wholesaler Name',
            'field': 'chargeback_ref__distribution_center_ref__name',
            'type': '',
            'value': ''
        },
        {
            'header': 'Wholesaler ID',
            'field': 'chargeback_ref__distribution_center_ref__dea_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Wholesaler ID Type',
            'field': 'chargeback_ref__distribution_center_ref__pk',
            'type': 'static',
            'value': 'DEA'
        },
        {
            'header': 'Wholesaler Address',
            'field': 'chargeback_ref__distribution_center_ref__address1',
            'type': '',
            'value': ''
        },
        {
            'header': 'Wholesaler City',
            'field': 'chargeback_ref__distribution_center_ref__city',
            'type': '',
            'value': ''
        },
        {
            'header': 'Wholesaler State',
            'field': 'chargeback_ref__distribution_center_ref__state',
            'type': '',
            'value': ''
        },
        {
            'header': 'Wholesaler Zip Code',
            'field': 'chargeback_ref__distribution_center_ref__zip_code',
            'type': '',
            'value': ''
        },
        {
            'header': 'Contract Name',
            'field': 'contract_ref__description',
            'type': '',
            'value': ''
        },
        {
            'header': 'Contract Tier No.',
            'field': 'contract_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Invoice No.',
            'field': 'invoice_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Invoice Date',
            'field': 'invoice_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Customer Name',
            'field': 'indirect_customer_ref__company_name',
            'type': '',
            'value': ''
        },
        {
            'header': 'Customer Location No.',
            'field': 'indirect_customer_ref__location_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Customer ID Type',
            'field': 'indirect_customer_ref__pk',
            'type': 'static',
            'value': 'DEA'
        },
        {
            'header': 'Customer COT',
            'field': 'contract_ref__cots',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship Address 1',
            'field': 'indirect_customer_ref__address1',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship Address 2',
            'field': 'indirect_customer_ref__address2',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship City',
            'field': 'indirect_customer_ref__city',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship State',
            'field': 'indirect_customer_ref__state',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship ZipCode',
            'field': 'indirect_customer_ref__zip_code',
            'type': '',
            'value': ''
        },
        {
            'header': 'NDC',
            'field': 'item_ref__ndc',
            'type': '',
            'value': ''
        },
        {
            'header': 'Brand Name',
            'field': 'item_ref__brand',
            'type': '',
            'value': ''
        },
        {
            'header': 'Product Name',
            'field': 'item_ref__description',
            'type': '',
            'value': ''
        },
        {
            'header': 'UOM',
            'field': 'item_uom',
            'type': '',
            'value': ''
        },
        {
            'header': 'QTY',
            'field': 'item_qty',
            'type': '',
            'value': ''
        },
        {
            'header': 'WAC System',
            'field': 'wac_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'WAC Submitted',
            'field': 'wac_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'Contract Price System',
            'field': 'contract_price_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'Contract Price Submitted',
            'field': 'contract_price_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'Total Chargeback',
            'field': 'claim_amount_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'Credit Amount Submitted',
            'field': 'claim_amount_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'Extended Wholesaler Sales',
            'field': 'contract_ref__pk',        # whatever field doesnt matter but need a valid field
            'type': 'static',
            'value': ''
        },
        {
            'header': 'Extended Contract Sales',
            'field': 'import_844_ref__pk',  # whatever field doesnt matter but need a valid field
            'type': 'calculated',
            'value': 'contract_price_system*item_qty'
        },
        {
            'header': 'DM Number',
            'field': 'chargeback_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'DM Date',
            'field': 'chargeback_ref__date',
            'type': '',
            'value': ''
        },
        {
            'header': 'System Line ID',
            'field': 'cblnid',
            'type': '',
            'value': ''
        },
    ]


def get_cb_details_report_structure():
    """
    JSON Structute for CB Detail Report (header columns names and field names for data)
    :return:
    """
    return [
        {
            'header': 'CusName',
            'field': 'chargeback_ref__customer_ref__name',
            'type': '',
            'value': ''
        },
        {
            'header': 'DistAddressName',
            'field': 'chargeback_ref__distribution_center_ref__name',
            'type': '',
            'value': ''
        },
        {
            'header': 'DistAddress1',
            'field': 'chargeback_ref__distribution_center_ref__address1',
            'type': '',
            'value': ''
        },
        {
            'header': 'DistAddress2',
            'field': 'chargeback_ref__distribution_center_ref__address2',
            'type': '',
            'value': ''
        },
        {
            'header': 'DistCity',
            'field': 'chargeback_ref__distribution_center_ref__city',
            'type': '',
            'value': ''
        },
        {
            'header': 'DistState',
            'field': 'chargeback_ref__distribution_center_ref__state',
            'type': '',
            'value': ''
        },
        {
            'header': 'DistZipCode',
            'field': 'chargeback_ref__distribution_center_ref__zip_code',
            'type': '',
            'value': ''
        },
        {
            'header': 'ProcessDate',
            'field': 'chargeback_ref__processed_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'CBNumber',
            'field': 'chargeback_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'InvoiceDate',
            'field': 'invoice_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'InvoiceNo',
            'field': 'invoice_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'ContractNo',
            'field': 'contract_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'ContractDesc',
            'field': 'contract_ref__description',
            'type': '',
            'value': ''
        },
        {
            'header': 'STCompanyName',
            'field': 'indirect_customer_ref__company_name',
            'type': '',
            'value': ''
        },
        {
            'header': 'STAddress1',
            'field': 'indirect_customer_ref__address1',
            'type': '',
            'value': ''
        },
        {
            'header': 'STAddress2',
            'field': 'indirect_customer_ref__address2',
            'type': '',
            'value': ''
        },
        {
            'header': 'STCity',
            'field': 'indirect_customer_ref__city',
            'type': '',
            'value': ''
        },
        {
            'header': 'STState',
            'field': 'indirect_customer_ref__state',
            'type': '',
            'value': ''
        },
        {
            'header': 'STZipCode',
            'field': 'indirect_customer_ref__zip_code',
            'type': '',
            'value': ''
        },
        {
            'header': 'TradeDesc',
            'field': 'indirect_customer_ref__cot__trade_class',
            'type': '',
            'value': ''
        },
        {
            'header': 'NDC',
            'field': 'item_ref__ndc',
            'type': '',
            'value': ''
        },
        {
            'header': 'ItemDesc',
            'field': 'item_ref__description',
            'type': '',
            'value': ''
        },
        {
            'header': 'ContractPriceSys',
            'field': 'contract_price_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'WACSys',
            'field': 'wac_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'ItemQty',
            'field': 'item_qty',
            'type': '',
            'value': ''
        },
        {
            'header': 'IndirectSalesAmt',
            'field': 'import_844_ref__pk',
            'type': 'calculated',
            'value': 'contract_price_system*item_qty'
        },
        {
            'header': 'ClaimAmtIssue',
            'field': 'claim_amount_issue',
            'type': '',
            'value': ''
        },
        {
            'header': 'UnitChargebackAmt',
            'field': 'chargeback_ref__pk',
            'type': 'calculated',
            'value': 'claim_amount_issue/item_qty'

        },
        {
            'header': 'WACSalesAmt',
            'field': 'contract_ref__pk',
            'type': 'calculated',
            'value': 'wac_system*item_qty'
        },
    ]


def get_amp_report_structure():
    """
    JSON Structute for AMP Report (header columns names and field names for data)
    :return:
    """
    return [
        {
            'header': 'GPO Name',
            'field': 'contract_ref__description',
            'type': '',
            'value': ''
        },
        {
            'header': 'Wholesaler ID',
            # ticket EA-1350 shows the direct customer’s account number
            'field': 'chargeback_ref__customer_ref__account_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Wholesaler Name',
            # ticket EA-1350 shows the direct customer’s name
            'field': 'chargeback_ref__customer_ref__name',
            'type': '',
            'value': ''
        },
        {
            'header': 'Contract No',
            'field': 'contract_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship To Name',
            'field': 'indirect_customer_ref__company_name',
            'type': '',
            'value': ''
        },
        {
            'header': 'DEA No',
            'field': 'indirect_customer_ref__location_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'HIN No',
            'field': 'indirect_customer_ref__pk',
            'type': 'static',
            'value': ''
        },
        {
            'header': 'Ship To Address 1',
            'field': 'indirect_customer_ref__address1',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship To Address 2',
            'field': 'indirect_customer_ref__address2',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship To City',
            'field': 'indirect_customer_ref__city',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship To State',
            'field': 'indirect_customer_ref__state',
            'type': '',
            'value': ''
        },
        {
            'header': 'Ship To Zip',
            'field': 'indirect_customer_ref__zip_code',
            'type': '',
            'value': ''
        },
        {
            'header': 'Debit Memo No',
            'field': 'chargeback_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Debit Memo Date',
            'field': 'chargeback_ref__date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Received Date',
            'field': 'created_at',
            'type': 'static',
            'value': ''
        },
        {
            'header': 'Invoice No',
            'field': 'invoice_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Invoice Date',
            'field': 'invoice_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'NDC No',
            'field': 'item_ref__ndc',
            'type': '',
            'value': ''
        },
        {
            'header': 'Product Description',
            'field': 'item_ref__description',
            'type': '',
            'value': ''
        },
        {
            'header': 'Qty Sold Of Product',
            'field': 'item_qty',
            'type': '',
            'value': ''
        },
        {
            'header': 'WAC Price',
            'field': 'wac_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'Submitted WAC Price',
            'field': 'wac_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'Contract Price',
            'field': 'contract_price_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'Submitted Contract Price',
            'field': 'contract_price_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'Credit Amount',
            'field': 'claim_amount_issue',
            'type': '',
            'value': ''
        },
        {
            'header': 'Submitted Credit Amount',
            'field': 'claim_amount_submitted',
            'type': '',
            'value': ''
        },
        {
            'header': 'WAC Sales',
            'field': 'contract_ref__pk',
            'type': 'calculated',
            'value': 'wac_system*item_qty'
        },
        {
            'header': 'Contract Sales',
            'field': 'import_844_ref__pk',  # whatever field doesnt matter but need a valid field
            'type': 'calculated',
            'value': 'contract_price_system*item_qty'
        },
        {
            'header': 'Cbk Type',
            'field': 'chargeback_ref__is_received_edi',
            'type': 'boolean',
            'value': 'EDI/MANUAL',
            'condition_for_true': ''
        },
        {
            'header': 'Credit Memo No',
            'field': 'chargeback_ref__accounting_credit_memo_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Credit Memo Date',
            'field': 'chargeback_ref__accounting_credit_memo_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Class of Trade Desc',
            'field': 'indirect_customer_ref__cot__trade_class',
            'type': '',
            'value': ''
        },
        {
            'header': 'Resubmit Flag',
            'field': 'chargeback_ref__type',
            'type': 'boolean',
            'value': 'Y/N',
            'condition_for_true': '15'
        },
        # ticket EA-1350 In between “Resubmit Flag” and “Status“ add column “Cbk Claim Info ID” which show cblnid
        {
            'header': 'Cbk Claim Info ID',
            'field': 'cblnid',
            'type': '',
            'value': ''
        },
        {
            'header': 'Status',
            'field': 'item_ref__pk',
            'type': 'static',
            'value': 'Paid'
        }
    ]


def get_manual_report_structure(company_name):
    """
    JSON Structute for MANUAL Report (header columns names and field names for data)
    :return:
    """
    return [
        {
            'header': 'Manufacturer Name',
            'field': 'item_ref__pk',
            'type': 'static',
            'value': f'{company_name}'
        },
        {
            'header': 'Wholesaler Name',
            'field': 'chargeback_ref__distribution_center_ref__name',
            'type': '',
            'value': ''
        },
        {
            'header': 'Line ID',
            'field': 'cblnid',
            'type': '',
            'value': ''
        },
        {
            'header': 'Debit Memo Number',
            'field': 'chargeback_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Debit Memo Date',
            'field': 'chargeback_ref__date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Debit Memo Amount',
            'field': 'chargeback_ref__claim_subtotal',
            'type': '',
            'value': ''
        },
        {
            'header': 'EDI Line Type',
            'field': 'chargeback_ref__distribution_center_ref__pk',
            'type': 'static',
            'value': 'RA'
        },
        {
            'header': 'Credit Memo Number',
            'field': 'chargeback_ref__accounting_credit_memo_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Credit Memo Date',
            'field': 'chargeback_ref__accounting_credit_memo_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Credit Memo Amount',
            'field': 'chargeback_ref__accounting_credit_memo_amount',
            'type': '',
            'value': ''
        },
        {
            'header': 'Accepted Status',
            'field': 'chargeback_ref__claim_issue',
            'type': 'boolean',
            'value': 'Y/N',
            'condition_for_true': ''
        },
        {
            'header': 'Corrected Indicator',
            'field': 'chargeback_ref__customer_ref__pk',
            'type': 'static',
            'value': 'Y'
        },
        {
            'header': 'Rejection Reason Codes',
            'field': 'disputes_codes',
            'type': '',
            'value': ''
        },
        {
            'header': 'Submitted Contract ID',
            'field': 'submitted_contract_no',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Contract ID',
            'field': 'contract_ref__number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Customer ID',
            'field': 'indirect_customer_ref__location_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Customer ID Qualifier',
            'field': 'indirect_customer_ref__pk',
            'type': 'static',
            'value': '11'
        },
        {
            'header': 'Corrected Product ID',
            'field': 'item_ref__ndc',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Product ID Qualifier',
            'field': 'item_ref__pk',
            'type': 'static',
            'value': 'NDC'
        },
        {
            'header': 'Corrected Wholesaler Cost',
            'field': 'wac_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Contract Price',
            'field': 'contract_price_system',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Quantity',
            'field': 'item_qty',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Unit of Measure',
            'field': 'item_uom',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Chargeback Amount',
            'field': 'contract_ref__pk',
            'type': 'calculated',
            'value': 'wac_system-contract_price_system'
        },
        {
            'header': 'Corrected Extended Chargeback Amount',
            'field': 'claim_amount_issue',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Invoice Number',
            'field': 'invoice_number',
            'type': '',
            'value': ''
        },
        {
            'header': 'Corrected Invoice Date',
            'field': 'invoice_date',
            'type': '',
            'value': ''
        },
        {
            'header': 'Notes',
            'field': 'disputes_notes',
            'type': '',
            'value': ''
        },
        {
            'header': 'Customer Ship To Name',
            'field': 'indirect_customer_ref__company_name',
            'type': '',
            'value': '',
        },
        {
            'header': 'Customer Ship To Address',
            'field': 'indirect_customer_ref__address1',
            'type': '',
            'value': ''
        },
        {
            'header': 'Customer Ship To City',
            'field': 'indirect_customer_ref__city',
            'type': '',
            'value': ''
        },
        {
            'header': 'Customer Ship To State',
            'field': 'indirect_customer_ref__state',
            'type': '',
            'value': ''
        },
        {
            'header': 'Customer Ship To Zip',
            'field': 'indirect_customer_ref__zip_code',
            'type': '',
            'value': ''
        },
        {
            'header': 'Customer Ship To Country',
            'field': 'chargeback_ref__pk',
            'type': 'static',
            'value': 'USA'
        }
    ]
