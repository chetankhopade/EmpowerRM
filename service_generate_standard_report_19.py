import os
import sys

import django

from app.management.utilities.constants import REPORT_FIELD_CASE_STATEMENT

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from empowerb.settings import DATABASES
from erms.models import Report, ReportField, ReportFilter, ReportDynamicStaticField, REPORT_FIELD_STATIC, \
    REPORT_FIELD_SYSTEM, REPORT_FIELD_PERCENT, REPORT_FIELD_CALCULATED, ReportCaseStatementField


def generate_contract_report(db):
    print(f"\n<<< Generating Contract Report - Company: {db} >>>")
    try:
        report = Report(name="Contract Report", description="EmpowerRM Standard Report", root_model="ContractLine")
        report.save(using=db)

        ReportField.objects.using(db).bulk_create(
            [
                ReportField(order=0, ref_path='contract__', field='description', name='Contract Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=1, ref_path='contract__', field='number', name='Contract Number', report=report, field_type=REPORT_FIELD_SYSTEM),
                # ReportField(order=2, ref_path='contract__', field='type', name='Contract Type', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=3, ref_path='contract__', field='start_date', name='Contract Start', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=4, ref_path='contract__', field='end_date', name='Contract End', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=5, ref_path='item__', field='ndc', name='Product ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=6, ref_path='', field='product_type_static', custom_value='NDC', name='Product Type', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=7, ref_path='item__', field='description', name='Product Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=8, ref_path='', field='unit_measure_static', custom_value='EA', name='Unit Measure', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=9, ref_path='', field='price', name='Unit Contract Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=10, ref_path='', field='start_date', name='Product Start', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=11, ref_path='', field='end_date', name='Product End', report=report, field_type=REPORT_FIELD_SYSTEM),
                # ReportField(order=12, ref_path='', field='status', name='Status', report=report, field_type=REPORT_FIELD_SYSTEM),

            ]
        )

        # Case Statements fields
        report_field_ctype = ReportField(order=2, ref_path='', field='contract_type_case', name='Contract Type', report=report, field_type=REPORT_FIELD_CASE_STATEMENT, case_default_value="", case_is_custom_default=True)
        report_field_ctype.save(using=db)

        report_field_status = ReportField(order=12, ref_path='', field='status_case', name='Status', report=report, field_type=REPORT_FIELD_CASE_STATEMENT, case_default_value="", case_is_custom_default=True)
        report_field_status.save(using=db)

        ReportCaseStatementField.objects.using(db).bulk_create(
            [
                ReportCaseStatementField(report_field=report_field_ctype, case_field_name='contract__type', action='exact', case_when_value='1', case_then_value='DIRECT'),
                ReportCaseStatementField(report_field=report_field_ctype, case_field_name='contract__type', action='exact', case_when_value='2', case_then_value='INDIRECT'),
                ReportCaseStatementField(report_field=report_field_status, case_field_name='status', action='exact', case_when_value='1', case_then_value='Active'),
                ReportCaseStatementField(report_field=report_field_status, case_field_name='status', action='exact', case_when_value='2', case_then_value='Inactive'),
                ReportCaseStatementField(report_field=report_field_status, case_field_name='status', action='exact', case_when_value='3', case_then_value='Pending'),
                ReportCaseStatementField(report_field=report_field_status, case_field_name='status', action='exact', case_when_value='4', case_then_value='Proposed')
            ]
        )

        print(f"\n<<< Contract Report generated successfully for - Company: {db} >>>")
    except Exception as ex:
        print(ex.__str__())


def generate_chargeback_report(db):
    print(f"\n<<< Generating Chargeback Report - Company: {db} >>>")
    try:
        report = Report(name="Chargeback Report", description="EmpowerRM Standard Report", root_model="ChargeBackLineHistory")
        report.save(using=db)

        ReportField.objects.using(db).bulk_create(
            [
                ReportField(order=0, ref_path='chargeback_ref__', field='type', name='CBType', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=1, ref_path='chargeback_ref__', field='accounting_credit_memo_number', name='Credit Memo Number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=2, ref_path='chargeback_ref__', field='accounting_credit_memo_date', name='Credit Memo Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=3, ref_path='chargeback_ref__customer_ref__', field='name', name='Parent Wholesaler', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=4, ref_path='chargeback_ref__distribution_center_ref__', field='name', name='Wholesaler Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=5, ref_path='chargeback_ref__distribution_center_ref__', field='dea_number', name='Wholesaler ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=6, ref_path='', field='wholesaler_id_type_static', custom_value='DEA', name='Wholesaler ID Type', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=7, ref_path='chargeback_ref__distribution_center_ref__', field='address1', name='Wholesaler Address', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=8, ref_path='chargeback_ref__distribution_center_ref__', field='city', name='Wholesaler City', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=9, ref_path='chargeback_ref__distribution_center_ref__', field='state', name='Wholesaler State', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=10, ref_path='chargeback_ref__distribution_center_ref__', field='zip_code', name='Wholesaler Zip Code', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=11, ref_path='contract_ref__', field='description', name='Contract Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=12, ref_path='contract_ref__', field='number', name='Contract Tier No.', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=13, ref_path='', field='invoice_number', name='Invoice No.', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=14, ref_path='', field='invoice_date', name='Invoice Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=15, ref_path='indirect_customer_ref__', field='company_name', name='Customer Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=16, ref_path='indirect_customer_ref__', field='location_number', name='Customer Location No.', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=17, ref_path='indirect_customer_ref__', custom_value="DEA", field='customer_id_type_static', name='Customer ID Type', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=18, ref_path='contract_ref__', field='cots', name='Customer COT', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=19, ref_path='indirect_customer_ref__', field='address1', name='Ship Address 1', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=20, ref_path='indirect_customer_ref__', field='address2', name='Ship Address 2', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=21, ref_path='indirect_customer_ref__', field='city', name='Ship City', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=22, ref_path='indirect_customer_ref__', field='state', name='Ship State', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=23, ref_path='indirect_customer_ref__', field='zip_code', name='Ship ZipCode', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=24, ref_path='item_ref__', field='ndc', name='NDC', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=25, ref_path='item_ref__', field='brand', name='Brand Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=26, ref_path='item_ref__', field='description', name='Product Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=27, ref_path='', field='item_uom', name='UOM', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=28, ref_path='', field='item_qty', name='QTY', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=29, ref_path='', field='wac_system', name='WAC System', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=30, ref_path='', field='wac_submitted', name='WAC Submitted', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=31, ref_path='', field='contract_price_system', name='Contract Price System', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=32, ref_path='', field='contract_price_submitted', name='Contract Price Submitted', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=33, ref_path='', field='claim_amount_system', name='Total Chargeback', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=34, ref_path='', field='claim_amount_submitted', name='Credit Amount Submitted', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=35, ref_path='', field='extended_wholesaler_sale_calculated', custom_value='wac_system@@@*@@@item_qty', name='Extended Wholesaler Sales', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=36, ref_path='', field='extended_contract_sales_calculated', custom_value='contract_price_system@@@*@@@item_qty', name='Extended Contract Sales', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=37, ref_path='chargeback_ref__', field='number', name='DM Number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=38, ref_path='chargeback_ref__', field='date', name='DM Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=39, ref_path='', field='cblnid', name='System Line ID', report=report, field_type=REPORT_FIELD_SYSTEM),

            ]
        )
        print(f"\n<<< Chargeback Report generated successfully for - Company: {db} >>>")
    except Exception as ex:
        print(ex.__str__())


def generate_manual_report(db):
    print(f"\n<<< Generating Manual Report - Company: {db} >>>")
    try:
        report = Report(name="Manual Report", description="EmpowerRM Standard Report", root_model="ChargeBackLineHistory")
        report.save(using=db)

        ReportField.objects.using(db).bulk_create(
            [
                ReportField(order=0, ref_path='', field='manufacturer_name_static', custom_value=db, name='Manufacturer Name', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=1, ref_path='chargeback_ref__distribution_center_ref__', field='name', name='Wholesaler Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=2, ref_path='', field='cblnid', name='Line ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=3, ref_path='chargeback_ref__', field='number', name='Debit Memo Number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=4, ref_path='chargeback_ref__', field='date', name='Debit Memo Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=5, ref_path='chargeback_ref__', field='claim_subtotal', name='Debit Memo Amount', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=6, ref_path='', field='edi_line_type_static', custom_value="RA", name='EDI Line Type', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=7, ref_path='chargeback_ref__', field='accounting_credit_memo_number', name='Credit Memo Number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=8, ref_path='chargeback_ref__', field='accounting_credit_memo_date', name='Credit Memo Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=9, ref_path='chargeback_ref__', field='accounting_credit_memo_amount', name='Credit Memo Amount', report=report, field_type=REPORT_FIELD_SYSTEM),
                # ReportField(order=10, ref_path='', field='accepted_status_static', custom_value="Y", name='Accepted Status', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=11, ref_path='', field='corrected_indicator_static', custom_value="Y", name='Corrected Indicator', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=12, ref_path='', field='disputes_codes', name='Rejection Reason Codes', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=13, ref_path='', field='submitted_contract_no', name='Submitted Contract ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=14, ref_path='contract_ref__', field='number', name='Corrected Contract ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=15, ref_path='indirect_customer_ref__', field='location_number', name='Corrected Customer ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=16, ref_path='', field='corrected_customer_id_qualifier_static', custom_value="11", name='Corrected Customer ID Qualifier', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=17, ref_path='item_ref__', field='ndc', name='Corrected Product Id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=18, ref_path='', field='corrected_product_id_qualifier_static', custom_value="NDC", name='Corrected Product ID Qualifier', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=19, ref_path='', field='wac_system', name='Corrected Wholesaler Cost', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=20, ref_path='', field='contract_price_system', name='Corrected Contract Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=21, ref_path='', field='item_qty', name='Corrected Quantity', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=22, ref_path='', field='corrected_unit_of_measure_static', custom_value="EA", name='Corrected Unit of Measure', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=23, ref_path='', field='corrected_chargeback_amount_calculated', custom_value="wac_system@@@-@@@contract_price_system", name='Corrected Chargeback Amount', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=24, ref_path='', field='claim_amount_issue', name='Corrected Extended Chargeback Amount', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=25, ref_path='', field='invoice_number', name='Corrected Invoice Number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=26, ref_path='', field='invoice_date', name='Corrected Invoice Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=27, ref_path='', field='disputes_notes', name='Notes', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=28, ref_path='indirect_customer_ref__', field='company_name', name='Customer Ship To Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=29, ref_path='indirect_customer_ref__', field='address1', name='Customer Ship To Address', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=30, ref_path='indirect_customer_ref__', field='city', name='Customer Ship To City', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=31, ref_path='indirect_customer_ref__', field='state', name='Customer Ship To State', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=32, ref_path='indirect_customer_ref__', field='zip_code', name='Customer Ship To Zip', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=33, ref_path='', field='customer_ship_to_country_static', custom_value="USA", name='Customer Ship To Country', report=report, field_type=REPORT_FIELD_STATIC),
            ]
        )

        # Case Statements fields
        report_field_accepted_status = ReportField(order=10, ref_path='', field='accepted_status_case', name='Accepted Status', report=report, field_type=REPORT_FIELD_CASE_STATEMENT, case_default_value="N", case_is_custom_default=True)
        report_field_accepted_status.save(using=db)

        case_field = ReportCaseStatementField(report_field=report_field_accepted_status, case_field_name='chargeback_ref__claim_issue', action='gt', case_when_value='0', case_then_value='Y')
        case_field.save(using=db)

        print(f"\n<<< Manual Report generated successfully for - Company: {db} >>>")
    except Exception as ex:
        print(ex.__str__())


def generate_cb_detail_report(db):
    print(f"\n<<< Generating CB Detail Report - Company: {db} >>>")
    try:
        report = Report(name="CB Detail Report", description="EmpowerRM Standard Report", root_model="ChargeBackLineHistory")
        report.save(using=db)

        ReportField.objects.using(db).bulk_create(
            [
                ReportField(order=0, ref_path='chargeback_ref__customer_ref__', field='name', name='CusName', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=1, ref_path='chargeback_ref__distribution_center_ref__', field='name', name='DistAddressName', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=2, ref_path='chargeback_ref__distribution_center_ref__', field='address1', name='DistAddress1', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=3, ref_path='chargeback_ref__distribution_center_ref__', field='address2', name='DistAddress2', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=4, ref_path='chargeback_ref__distribution_center_ref__', field='city', name='DistCity', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=5, ref_path='chargeback_ref__distribution_center_ref__', field='state', name='DistState', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=6, ref_path='chargeback_ref__distribution_center_ref__', field='zip_code', name='DistZipCode', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=7, ref_path='chargeback_ref__', field='processed_date', name='ProcessDate', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=8, ref_path='chargeback_ref__', field='number', name='CBNumber', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=9, ref_path='', field='invoice_date', name='InvoiceDate', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=10, ref_path='', field='invoice_number', name='InvoiceNo', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=11, ref_path='', field='submitted_contract_no', name='ContractNo', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=12, ref_path='contract_ref__', field='description', name='ContractDesc', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=13, ref_path='indirect_customer_ref__', field='company_name', name='STCompanyName', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=14, ref_path='indirect_customer_ref__', field='address1', name='STAddress1', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=15, ref_path='indirect_customer_ref__', field='address2', name='STAddress2', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=16, ref_path='indirect_customer_ref__', field='city', name='STCity', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=17, ref_path='indirect_customer_ref__', field='state', name='STState', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=18, ref_path='indirect_customer_ref__', field='zip_code', name='STZipCode', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=19, ref_path='indirect_customer_ref__cot__', field='trade_class', name='TradeDesc', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=20, ref_path='item_ref__', field='ndc', name='NDC', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=21, ref_path='item_ref__', field='description', name='ItemDesc', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=22, ref_path='', field='contract_price_system', name='ContractPriceSys', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=23, ref_path='', field='wac_system', name='WACSys', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=24, ref_path='', field='item_qty', name='ItemQty', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=25, ref_path='', field='indirectsalesamt_calculated', custom_value="contract_price_system@@@*@@@item_qty", name='IndirectSalesAmt', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=26, ref_path='', field='claim_amount_issue', name='ClaimAmtIssue', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=27, ref_path='', field='unitchargebackamt_calculated', custom_value="claim_amount_issue@@@/@@@item_qty", name='UnitChargebackAmt', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=28, ref_path='', field='wacsalesamt_calculated', custom_value="wac_system@@@*@@@item_qty", name='WACSalesAmt', report=report, field_type=REPORT_FIELD_CALCULATED),
            ]
        )

        print(f"\n<<< CB Detail Report generated successfully for - Company: {db} >>>")
    except Exception as ex:
        print(ex.__str__())


def generate_weekly_processing_report(db):
    print(f"\n<<< Generating Weekly Processing Report - Company: {db} >>>")
    try:
        report = Report(name="Weekly Processing Report", description="EmpowerRM Standard Report", root_model="ChargeBackLineHistory")
        report.save(using=db)

        ReportField.objects.using(db).bulk_create(
            [
                ReportField(order=0, ref_path='chargeback_ref__', field='accounting_credit_memo_number', name='Credit Memo Nbr', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=1, ref_path='chargeback_ref__', field='accounting_credit_memo_date', name='Credit Memo Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=2, ref_path='chargeback_ref__customer_ref__', field='name', name='Parent Wholesaler', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=3, ref_path='chargeback_ref__distribution_center_ref__', field='name', name='Wholesaler Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=4, ref_path='chargeback_ref__distribution_center_ref__', field='dea_number', name='Wholesaler ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=5, ref_path='', field='wholesaler_id_type_static', custom_value='DEA', name='WholeSaler ID Type', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=6, ref_path='chargeback_ref__distribution_center_ref__', field='address1', name='Wholesaler Address', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=7, ref_path='chargeback_ref__distribution_center_ref__', field='city', name='Wholesaler City', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=8, ref_path='chargeback_ref__distribution_center_ref__', field='state', name='Wholesaler State', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=9, ref_path='chargeback_ref__distribution_center_ref__', field='zip_code', name='Wholesaler ZIP', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=10, ref_path='contract_ref__', field='description', name='Contract Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=11, ref_path='contract_ref__', field='number', name='Contract Tier Nbr', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=12, ref_path='', field='invoice_number', name='Invoice Nbr', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=13, ref_path='', field='invoice_date', name='Invoice Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=14, ref_path='indirect_customer_ref__', field='company_name', name='Customer Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=15, ref_path='indirect_customer_ref__', field='location_number', name='Customer ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=16, ref_path='', custom_value="DEA", field='customer_id_type_static', name='Customer ID Type', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=17, ref_path='', field='customer_cot_static', custom_value="", name='Customer COT', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=18, ref_path='indirect_customer_ref__', field='address1', name='Ship to Address 1', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=19, ref_path='indirect_customer_ref__', field='address2', name='Ship to Address 2', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=20, ref_path='indirect_customer_ref__', field='city', name='Ship to City', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=21, ref_path='indirect_customer_ref__', field='state', name='Ship to State', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=22, ref_path='indirect_customer_ref__', field='zip_code', name='Ship to ZIP', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=23, ref_path='item_ref__', field='ndc', name='NDC', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=24, ref_path='item_ref__', field='brand', name='Brand Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=25, ref_path='item_ref__', field='description', name='Product Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=26, ref_path='', field='item_uom', name='UOM', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=27, ref_path='', field='wac_system', name='Wholesaler Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=28, ref_path='', field='contract_price_system', name='Contract Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=29, ref_path='', field='item_qty', name='Quantity', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=30, ref_path='', field='claim_amount_issue', name='Total Chargeback', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=31, ref_path='', field='extended_wholesaler_sale_calculated', custom_value='wac_system@@@*@@@item_qty', name='Extended Wholesaler Sales', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=32, ref_path='', field='extended_contract_sales_calculated', custom_value='contract_price_system@@@*@@@item_qty', name='Extended Contract Sales', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=33, ref_path='chargeback_ref__', field='number', name='Debit Memo Nbr', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=34, ref_path='chargeback_ref__', field='date', name='Debit Memo Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=35, ref_path='', field='cblnid', name='System Line ID', report=report, field_type=REPORT_FIELD_SYSTEM),
            ]
        )

        report_filter = ReportFilter(report=report, ref_path='chargeback_ref__', field='processed_date', field_type='DateTimeField', action='range', value1='', value2='0d', date_range='LW', is_run_parameter=True)
        report_filter.save()

        print(f"\n<<< Weekly Processing Report generated successfully for - Company: {db} >>>")
    except Exception as ex:
        print(ex.__str__())


def generate_monthly_processing_report(db):
    print(f"\n<<< Generating Monthly Processing Report - Company: {db} >>>")
    try:
        report = Report(name="Monthly Processing Report", description="EmpowerRM Standard Report", root_model="ChargeBackLineHistory")
        report.save(using=db)

        ReportField.objects.using(db).bulk_create(
            [
                ReportField(order=0, ref_path='chargeback_ref__', field='accounting_credit_memo_number', name='Credit Memo Nbr', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=1, ref_path='chargeback_ref__', field='accounting_credit_memo_date', name='Credit Memo Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=2, ref_path='chargeback_ref__customer_ref__', field='name', name='Parent Wholesaler', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=3, ref_path='chargeback_ref__distribution_center_ref__', field='name', name='Wholesaler Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=4, ref_path='chargeback_ref__distribution_center_ref__', field='dea_number', name='Wholesaler ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=5, ref_path='', field='wholesaler_id_type_static', custom_value='DEA', name='WholeSaler ID Type', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=6, ref_path='chargeback_ref__distribution_center_ref__', field='address1', name='Wholesaler Address', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=7, ref_path='chargeback_ref__distribution_center_ref__', field='city', name='Wholesaler City', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=8, ref_path='chargeback_ref__distribution_center_ref__', field='state', name='Wholesaler State', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=9, ref_path='chargeback_ref__distribution_center_ref__', field='zip_code', name='Wholesaler ZIP', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=10, ref_path='contract_ref__', field='description', name='Contract Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=11, ref_path='contract_ref__', field='number', name='Contract Tier Nbr', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=12, ref_path='', field='invoice_number', name='Invoice Nbr', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=13, ref_path='', field='invoice_date', name='Invoice Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=14, ref_path='indirect_customer_ref__', field='company_name', name='Customer Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=15, ref_path='indirect_customer_ref__', field='location_number', name='Customer ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=16, ref_path='', custom_value="DEA", field='customer_id_type_static', name='Customer ID Type', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=17, ref_path='', field='customer_cot_static', custom_value="", name='Customer COT', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=18, ref_path='indirect_customer_ref__', field='address1', name='Ship to Address 1', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=19, ref_path='indirect_customer_ref__', field='address2', name='Ship to Address 2', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=20, ref_path='indirect_customer_ref__', field='city', name='Ship to City', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=21, ref_path='indirect_customer_ref__', field='state', name='Ship to State', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=22, ref_path='indirect_customer_ref__', field='zip_code', name='Ship to ZIP', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=23, ref_path='item_ref__', field='ndc', name='NDC', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=24, ref_path='item_ref__', field='brand', name='Brand Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=25, ref_path='item_ref__', field='description', name='Product Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=26, ref_path='', field='item_uom', name='UOM', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=27, ref_path='', field='wac_system', name='Wholesaler Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=28, ref_path='', field='contract_price_system', name='Contract Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=29, ref_path='', field='item_qty', name='Quantity', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=30, ref_path='', field='claim_amount_issue', name='Total Chargeback', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=31, ref_path='', field='extended_wholesaler_sale_calculated', custom_value='wac_system@@@*@@@item_qty', name='Extended Wholesaler Sales', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=32, ref_path='', field='extended_contract_sales_calculated', custom_value='contract_price_system@@@*@@@item_qty', name='Extended Contract Sales', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=33, ref_path='chargeback_ref__', field='number', name='Debit Memo Nbr', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=34, ref_path='chargeback_ref__', field='date', name='Debit Memo Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=35, ref_path='', field='cblnid', name='System Line Id', report=report, field_type=REPORT_FIELD_SYSTEM),
            ]
        )

        report_filter = ReportFilter(report=report, ref_path='chargeback_ref__', field='processed_date', field_type='DateTimeField', action='range', value1='', value2='0d', date_range='LM', is_run_parameter=True)
        report_filter.save()

        print(f"\n<<< Monthly Processing Report generated successfully for - Company: {db} >>>")
    except Exception as ex:
        print(ex.__str__())


def generate_amp_data_report(db):
    print(f"\n<<< Generating AMP DATA Report - Company: {db} >>>")
    try:
        report = Report(name="AMP DATA Report", description="EmpowerRM Standard Report", root_model="ChargeBackLineHistory")
        report.save(using=db)

        ReportField.objects.using(db).bulk_create(
            [
                ReportField(order=0, ref_path='contract_ref__', field='description', name='GPO Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=1, ref_path='chargeback_ref__customer_ref__', field='account_number', name='Wholesaler ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=2, ref_path='chargeback_ref__customer_ref__', field='name', name='Wholesaler Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=3, ref_path='contract_ref__', field='number', name='Contract No', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=4, ref_path='indirect_customer_ref__', field='company_name', name='Ship To Name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=5, ref_path='indirect_customer_ref__', field='location_number', name='DEA No', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=6, ref_path='', field='hin_no_static', custom_value="", name='HIN No', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=7, ref_path='indirect_customer_ref__', field='address1', name='Ship To Address 1', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=8, ref_path='indirect_customer_ref__', field='address2', name='Ship To Address 2', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=9, ref_path='indirect_customer_ref__', field='city', name='Ship To City', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=10, ref_path='indirect_customer_ref__', field='state', name='Ship To State', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=11, ref_path='indirect_customer_ref__', field='zip_code', name='Ship To Zip', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=12, ref_path='chargeback_ref__', field='number', name='Debit Memo No', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=13, ref_path='chargeback_ref__', field='date', name='Debit Memo Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=14, ref_path='', field='received_date_static', custom_value="", name='Received Date', report=report, field_type=REPORT_FIELD_STATIC),
                ReportField(order=15, ref_path='', field='invoice_number', name='Invoice No', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=16, ref_path='', field='invoice_date', name='Invoice Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=17, ref_path='item_ref__', field='ndc', name='NDC No', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=18, ref_path='item_ref__', field='description', name='Product Description', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=19, ref_path='', field='item_qty', name='Qty Sold of Product', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=20, ref_path='', field='wac_system', name='WAC Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=21, ref_path='', field='wac_submitted', name='Submitted WAC Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=22, ref_path='', field='contract_price_system', name='Contract Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=23, ref_path='', field='contract_price_submitted', name='Submitted Contract Price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=24, ref_path='', field='claim_amount_system', name='Credit Amount', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=25, ref_path='', field='claim_amount_submitted', name='Submitted Credit Amount', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=26, ref_path='', field='wac_sales_calculated', custom_value="wac_system@@@*@@@item_qty", name='WAC Sales', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=27, ref_path='', field='contract_sales_calculated', custom_value="contract_price_system@@@*@@@item_qty", name='Contract Sales', report=report, field_type=REPORT_FIELD_CALCULATED),
                ReportField(order=29, ref_path='chargeback_ref__', field='accounting_credit_memo_number', name='Credit Memo No', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=30, ref_path='chargeback_ref__', field='accounting_credit_memo_date', name='Credit Memo Date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=31, ref_path='indirect_customer_ref__cot__', field='trade_class', name='Class of Trade Desc', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=33, ref_path='', field='cblnid', name='Cbk Claim Info ID', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=34, ref_path='', field='status_static', custom_value="Paid", name='Status', report=report, field_type=REPORT_FIELD_STATIC),
            ]
        )

        # Case Statements fields
        report_field_resubmit_flag = ReportField(order=32, ref_path='', field='resubmit_flag_case', name='Resubmit Flag', report=report, field_type=REPORT_FIELD_CASE_STATEMENT, case_default_value="N", case_is_custom_default=True)
        report_field_resubmit_flag.save(using=db)

        case_field = ReportCaseStatementField(report_field=report_field_resubmit_flag, case_field_name='chargeback_ref__type', action='exact', case_when_value='15', case_then_value='Y')
        case_field.save(using=db)

        report_field_cbk_type = ReportField(order=28, ref_path='', field='cbk_type_case', name='Cbk Type', report=report, field_type=REPORT_FIELD_CASE_STATEMENT, case_default_value="Manual", case_is_custom_default=True)
        report_field_cbk_type.save(using=db)

        case_field2 = ReportCaseStatementField(report_field=report_field_cbk_type, case_field_name='chargeback_ref__is_received_edi', action='exact', case_when_value='1', case_then_value='EDI')
        case_field2.save(using=db)

        report_filter = ReportFilter(report=report, ref_path='', field='claim_amount_issue', field_type='DecimalField', action='exclude', value1='0', value2='')
        report_filter.save()

        print(f"\n<<< AMP DATA Report generated successfully for - Company: {db} >>>")
    except Exception as ex:
        print(ex.__str__())


def generate_data_852_report(db):
    print(f"\n<<< Generating Data 852 Report - Company: {db} >>>")
    try:
        report = Report(name="Data 852 Report", description="EmpowerRM Standard Report", root_model="Data852")
        report.save(using=db)

        ReportField.objects.using(db).bulk_create(
            [
                ReportField(order=0, ref_path='', field='customer_name', name='customer_name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=1, ref_path='', field='wholesaler_name', name='wholesaler_name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=2, ref_path='H_distributor_id__', field='name', name='dc', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=3, ref_path='H_distributor_id__', field='state', name='dc_state', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=4, ref_path='', field='id', name='id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=5, ref_path='', field='document', name='document', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=6, ref_path='', field='sender', name='sender', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=7, ref_path='', field='receiver', name='receiver', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=8, ref_path='', field='H_thc', name='H_thc', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=9, ref_path='', field='H_start_date', name='H_start_date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=10, ref_path='', field='H_end_date', name='H_end_date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=11, ref_path='', field='H_po_number', name='H_po_number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=12, ref_path='', field='H_id_qualifier', name='H_id_qualifier', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=13, ref_path='', field='H_ship_to_id_type', name='H_ship_to_id_type', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=14, ref_path='', field='H_ship_to_id', name='H_ship_to_id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=15, ref_path='', field='H_distributor_id_type', name='H_ship_to_id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=16, ref_path='H_distributor_id__', field='dea_number', name='H_distributor_id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=17, ref_path='', field='H_reporting_location_id_type', name='H_reporting_location_id_type', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=18, ref_path='', field='H_reporting_location_id', name='H_reporting_location_id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=19, ref_path='', field='L_line_item_identification', name='L_line_item_identification', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=20, ref_path='', field='L_item_id_qualifier', name='L_item_id_qualifier', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=21, ref_path='', field='L_item_id', name='L_item_id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=22, ref_path='', field='L_BS', name='L_BS', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=23, ref_path='', field='L_TS', name='L_TS', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=24, ref_path='', field='L_QA', name='L_QA', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=25, ref_path='', field='L_QP', name='L_QP', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=26, ref_path='', field='L_QS', name='L_QS', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=27, ref_path='', field='L_QO', name='L_QO', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=28, ref_path='', field='L_QC', name='L_QC', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=29, ref_path='', field='L_QT', name='L_QT', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=30, ref_path='', field='L_QD', name='L_QD', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=31, ref_path='', field='L_QB', name='L_QB', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=32, ref_path='', field='L_Q1', name='L_Q1', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=33, ref_path='', field='L_QW', name='L_QW', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=34, ref_path='', field='L_QR', name='L_QR', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=35, ref_path='', field='L_QI', name='L_QI', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=36, ref_path='', field='L_QZ', name='L_QZ', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=37, ref_path='', field='L_QU', name='L_QU', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=38, ref_path='', field='L_WQ', name='L_WQ', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=39, ref_path='', field='L_QE', name='L_QE', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=40, ref_path='', field='created_at', name='created_at', report=report, field_type=REPORT_FIELD_SYSTEM),
            ]
        )

        print(f"\n<<< Data 852 Report generated successfully for - Company: {db} >>>")

    except Exception as ex:
        print(ex.__str__())


def generate_data_867_report(db):
    print(f"\n<<< Generating Data 867 Report - Company: {db} >>>")
    try:
        report = Report(name="Data 867 Report", description="EmpowerRM Standard Report", root_model="Data867")
        report.save(using=db)

        ReportField.objects.using(db).bulk_create(
            [
                ReportField(order=0, ref_path='', field='customer_name', name='customer_name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=1, ref_path='', field='wholesaler_name', name='wholesaler_name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=2, ref_path='', field='id', name='id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=3, ref_path='', field='document', name='document', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=4, ref_path='', field='sender', name='sender', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=5, ref_path='', field='receiver', name='receiver', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=6, ref_path='', field='transaction_spc', name='transaction_spc', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=7, ref_path='', field='reference_id', name='reference_id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=8, ref_path='', field='report_run_date', name='report_run_date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=9, ref_path='', field='report_type', name='report_type', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=10, ref_path='', field='report_start_date', name='report_start_date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=11, ref_path='', field='report_end_date', name='report_end_date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=12, ref_path='', field='dist_name', name='dist_name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=13, ref_path='', field='dist_dea_number', name='dist_dea_number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=14, ref_path='', field='supplier_name', name='supplier_name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=15, ref_path='', field='supplier_dea_number', name='supplier_dea_number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=16, ref_path='', field='transfer_type', name='transfer_type', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=17, ref_path='', field='transfer_type_desc', name='transfer_type_desc', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=18, ref_path='', field='invoice_no', name='invoice_no', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=19, ref_path='', field='invoice_date', name='invoice_date', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=20, ref_path='', field='contract_number', name='contract_number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=21, ref_path='', field='ship_to_name', name='ship_to_name', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=22, ref_path='', field='ship_to_dea_number', name='ship_to_dea_number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=23, ref_path='', field='ship_to_hin_number', name='ship_to_hin_number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=24, ref_path='', field='ship_to_address1', name='ship_to_address1', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=25, ref_path='', field='ship_to_address2', name='ship_to_address2', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=26, ref_path='', field='ship_to_city', name='ship_to_city', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=27, ref_path='', field='ship_to_state', name='ship_to_state', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=28, ref_path='', field='ship_to_zip', name='ship_to_zip', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=29, ref_path='', field='quantity_type', name='quantity_type', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=30, ref_path='', field='quantity', name='quantity', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=31, ref_path='', field='quantity_uom', name='quantity_uom', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=32, ref_path='', field='product_ndc', name='product_ndc', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=33, ref_path='', field='purchaser_item_code', name='purchaser_item_code', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=34, ref_path='', field='mfg_part_number', name='mfg_part_number', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=35, ref_path='', field='unit_price', name='unit_price', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=36, ref_path='', field='unit_price_code', name='unit_price_code', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=37, ref_path='', field='extended_amount', name='extended_amount', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=38, ref_path='', field='product_description', name='product_description', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=39, ref_path='', field='created_at', name='created_at', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=40, ref_path='', field='configuration_id', name='configuration_id', report=report, field_type=REPORT_FIELD_SYSTEM),
                ReportField(order=41, ref_path='', field='transaction_id', name='transaction_id', report=report, field_type=REPORT_FIELD_SYSTEM),

            ]
        )

        print(f"\n<<< Data 867 Report generated successfully for - Company: {db} >>>")

    except Exception as ex:
        print(ex.__str__())


if __name__ == '__main__':

    print(f'Running script to generate standard reports: {sys.argv[0]}')  # prints the name of the Python script

    try:
        dbs = [sys.argv[1]]
    except:
        dbs = [x for x in DATABASES.keys() if x != 'default']

    for db in dbs:
        print(f"\n<<< PROCESS START - Company: {db} >>>")

        # Generating Contract Report
        generate_contract_report(db)

        # Generating Chargeback Report
        generate_chargeback_report(db)

        # Generating Manual Report
        generate_manual_report(db)

        # Generating CB Detail Report
        generate_cb_detail_report(db)

        # Generating Weekly Processing report
        generate_weekly_processing_report(db)

        # Generating Monthly Processing Report
        generate_monthly_processing_report(db)

        # Generating AMP DATA report
        generate_amp_data_report(db)

        # Generating data 852 report
        generate_data_852_report(db)

        # Generating data 867 report
        generate_data_867_report(db)

    print(f"\n<<< PROCESS COMPLETED - Company: {db} >>>")