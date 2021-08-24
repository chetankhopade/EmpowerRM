import csv
import decimal
import os
import datetime
from decimal import Decimal

import xlsxwriter
import io

from django.apps import apps
from django.db.models import QuerySet, Sum, F, DecimalField
from django.http import HttpResponse
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string

from app.management.utilities.constants import CONTRACT_TYPES, STATUSES, REPORT_FIELD_SYSTEM, REPORT_FIELD_CALCULATED, REPORT_FIELD_PERCENT, REPORT_FIELD_STATIC
from app.management.utilities.functions import generate_filename_for_reports, query_range, get_dates_for_report_filter, \
    get_chargebackline_object
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_849_ERM_MANUAL, DIR_NAME_FILES_STORAGE, DIR_NAME_USER_REPORTS

# Dynamic Export to csv


def export_report_to_csv(queryset, filename, structure):
    """
    Export Exception view report to csv
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f"attachment; filename={filename}"

    writer = csv.writer(response)

    # Header
    columns_header = (x['header'] for x in structure)
    writer.writerow(columns_header)

    # statics, choices, booleans and calculated fields values
    statics_choices_booleans_calculated_fields = [(index, x) for index, x in enumerate(structure) if x['type'] != '']

    # Lists (list of dicts or list of querysets)
    if isinstance(queryset, list):

        for obj in queryset:

            if isinstance(obj, dict):
                # each obj is a dict
                column_values = []
                for k, v in obj.items():
                    if k in [x['field'] for x in structure]:
                        # add value to the column
                        column_values.append(v)
                # write row
                writer.writerow(column_values)

            else:
                # each obj is a model instance
                column_values = []
                for index, k in enumerate([x['field'] for x in structure]):

                    __splitted = k.split('__')
                    if len(__splitted) == 3:
                        ref1 = k.split('__')[0]
                        ref2 = k.split('__')[1]
                        ref3 = k.split('__')[2]
                        v = getattr(getattr(getattr(obj, ref1), ref2), ref3)
                    elif len(__splitted) == 2:
                        ref1 = k.split('__')[0]
                        ref2 = k.split('__')[1]
                        v = getattr(getattr(obj, ref1), ref2)
                    else:
                        v = getattr(obj, k)

                    if any(x[0] == index for x in statics_choices_booleans_calculated_fields):
                        elem = [x[1] for x in statics_choices_booleans_calculated_fields if x[0] == index][0]

                        if elem['type'] == 'static':
                            v = elem['value']

                        if elem['type'] == 'choice':
                            if elem['value'] == 'CONTRACT_TYPES':
                                v = CONTRACT_TYPES[v-1][1] if v else ''
                            if elem['value'] == 'STATUSES':
                                v = STATUSES[v-1][1] if v else ''

                        if elem['type'] == 'boolean':
                            condition_for_true = elem['condition_for_true'] if elem['condition_for_true'] else True
                            bool_value = elem['value'].split('/')
                            if v == condition_for_true:
                                v = bool_value[0]
                            else:
                                v = bool_value[1]

                        if elem['type'] == 'calculated':
                            if '*' in elem['value']:
                                op = elem['value'].split('*')
                                v = Decimal(getattr(obj, op[0]) * getattr(obj, op[1])).quantize(Decimal(10) ** -2) if getattr(obj, op[0]) and getattr(obj, op[1]) else Decimal('0.00')
                            if '/' in elem['value']:
                                op = elem['value'].split('/')
                                v = Decimal(getattr(obj, op[0]) / getattr(obj, op[1])).quantize(Decimal(10) ** -2) if getattr(obj, op[0]) and getattr(obj, op[1]) else Decimal('0.00')
                            if '-' in elem['value']:
                                op = elem['value'].split('-')
                                v = Decimal(getattr(obj, op[0]) - getattr(obj, op[1])).quantize(Decimal(10) ** -2) if getattr(obj, op[0]) and getattr(obj, op[1]) else Decimal('0.00')

                    # add to the column
                    column_values.append(v)
                # write row
                writer.writerow(column_values)

    # QuerySets
    if isinstance(queryset, QuerySet):
        objects = queryset.values(*(x['field'] for x in structure if x['field']))

        for obj in objects.iterator():
            column_values = []
            for index, value in enumerate(obj.values()):
                v = value
                if any(x[0] == index for x in statics_choices_booleans_calculated_fields):
                    elem = [x[1] for x in statics_choices_booleans_calculated_fields if x[0] == index][0]

                    if elem['type'] == 'static':
                        v = elem['value']

                    if elem['type'] == 'choice':
                        if elem['value'] == 'CONTRACT_TYPES':
                            v = CONTRACT_TYPES[value-1][1] if value else ''
                        if elem['value'] == 'STATUSES':
                            v = STATUSES[value-1][1] if value else ''

                    if elem['type'] == 'boolean':
                        condition_for_true = elem['condition_for_true'] if elem['condition_for_true'] else True
                        bool_value = elem['value'].split('/')
                        if value == condition_for_true:
                            v = bool_value[0]
                        else:
                            v = bool_value[1]

                    if elem['type'] == 'calculated':
                        if '*' in elem['value']:
                            op = elem['value'].split('*')
                            v = Decimal(obj[op[0]] * obj[op[1]]).quantize(Decimal(10) ** -2) if obj[op[0]] and obj[op[1]] else Decimal('0.00')
                        if '/' in elem['value']:
                            op = elem['value'].split('/')
                            v = Decimal(obj[op[0]] / obj[op[1]]).quantize(Decimal(10) ** -2) if obj[op[0]] and obj[op[1]] else Decimal('0.00')
                        if '-' in elem['value']:
                            op = elem['value'].split('/')
                            v = Decimal(obj[op[0]] - obj[op[1]]).quantize(Decimal(10) ** -2) if obj[op[0]] and obj[op[1]] else Decimal('0.00')

                # add to the column
                column_values.append(v)
            # write row
            writer.writerow(column_values)

    return response


# Dynamic Export to excel
def export_report_to_excel(queryset, filename, structure):
    time1 = datetime.datetime.now()
    # for python 3 io.BytesIO instead of StringIO.StringIO
    output = io.BytesIO()

    # Workbook
    wb = xlsxwriter.Workbook(output, {'constant_memory': True})
    ws = wb.add_worksheet()

    # Formats
    bold = wb.add_format({'bold': True})
    text_format = wb.add_format({'font_size': 10})
    date_format = wb.add_format({'font_size': 10, 'num_format': 'mm/dd/yyyy'})
    currency_format = wb.add_format({'font_size': 10, 'num_format': '#,##0.00'})

    # Draw Header (column names)
    columns_header = (x['header'] for x in structure)
    for index, value in enumerate(columns_header):
        ws.write(0, index, value, bold)

    # statics, choices, booleans and calculated fields values
    statics_choices_booleans_calculated_fields = [(index, x) for index, x in enumerate(structure) if x['type'] != '']

    # Lists (list of dicts or list of querysets)
    if isinstance(queryset, list):
        row = 1
        for obj in queryset:
            col = 0
            if isinstance(obj, dict):
                # each obj is a dict
                for k, v in obj.items():
                    if k in [x['field'] for x in structure]:
                        # format date fields
                        if isinstance(v, datetime.date):
                            cell_format = date_format
                        elif isinstance(v, decimal.Decimal) or isinstance(v, float):
                            cell_format = currency_format
                        else:
                            cell_format = text_format

                        # write row
                        ws.write(row, col, v, cell_format)
                        col += 1
            else:
                # each obj is a model instance
                for index, k in enumerate([x['field'] for x in structure]):

                    __splitted = k.split('__')
                    if len(__splitted) == 3:
                        ref1 = k.split('__')[0]
                        ref2 = k.split('__')[1]
                        ref3 = k.split('__')[2]
                        v = getattr(getattr(getattr(obj, ref1), ref2), ref3)
                    elif len(__splitted) == 2:
                        ref1 = k.split('__')[0]
                        ref2 = k.split('__')[1]
                        v = getattr(getattr(obj, ref1), ref2)
                    else:
                        v = getattr(obj, k)

                    if any(x[0] == index for x in statics_choices_booleans_calculated_fields):
                        elem = [x[1] for x in statics_choices_booleans_calculated_fields if x[0] == index][0]

                        if elem['type'] == 'static':
                            v = elem['value']

                        if elem['type'] == 'choice':
                            if elem['value'] == 'CONTRACT_TYPES':
                                v = CONTRACT_TYPES[v-1][1] if v else ''
                            if elem['value'] == 'STATUSES':
                                v = STATUSES[v-1][1] if v else ''

                        if elem['type'] == 'boolean':
                            condition_for_true = elem['condition_for_true'] if elem['condition_for_true'] else True
                            bool_value = elem['value'].split('/')
                            if v == condition_for_true:
                                v = bool_value[0]
                            else:
                                v = bool_value[1]

                        if elem['type'] == 'calculated':
                            if '*' in elem['value']:
                                op = elem['value'].split('*')
                                v = Decimal(getattr(obj, op[0]) * getattr(obj, op[1])).quantize(Decimal(10) ** -2) if getattr(obj, op[0]) and getattr(obj, op[1]) else Decimal('0.00')
                            if '/' in elem['value']:
                                op = elem['value'].split('/')
                                v = Decimal(getattr(obj, op[0]) / getattr(obj, op[1])).quantize(Decimal(10) ** -2) if getattr(obj, op[0]) and getattr(obj, op[1]) else Decimal('0.00')
                            if '-' in elem['value']:
                                op = elem['value'].split('-')
                                v = Decimal(getattr(obj, op[0]) - getattr(obj, op[1])).quantize(Decimal(10) ** -2) if getattr(obj, op[0]) and getattr(obj, op[1]) else Decimal('0.00')

                    # format date fields
                    if isinstance(v, datetime.date):
                        cell_format = date_format
                    elif isinstance(v, decimal.Decimal) or isinstance(v, float):
                        cell_format = currency_format
                    else:
                        cell_format = text_format

                    # write row
                    ws.write(row, col, v, cell_format)
                    col += 1
            row += 1

    # QuerySets
    if isinstance(queryset, QuerySet):
        objects = queryset.values(*(x['field'] for x in structure if x['field']))
        print(objects)
        row = 1
        for i, obj in enumerate(objects.iterator()):
            # print(i)
            col = 0
            for index, value in enumerate(obj.values()):
                v = value
                if any(x[0] == index for x in statics_choices_booleans_calculated_fields):
                    elem = [x[1] for x in statics_choices_booleans_calculated_fields if x[0] == index][0]

                    if elem['type'] == 'static':
                        v = elem['value']

                    if elem['type'] == 'choice':
                        if elem['value'] == 'CONTRACT_TYPES':
                            v = CONTRACT_TYPES[value-1][1] if value else ''
                        if elem['value'] == 'STATUSES':
                            v = STATUSES[value-1][1] if value else ''

                    if elem['type'] == 'boolean':
                        condition_for_true = elem['condition_for_true'] if elem['condition_for_true'] else True
                        bool_value = elem['value'].split('/')
                        if value == condition_for_true:
                            v = bool_value[0]
                        else:
                            v = bool_value[1]

                    if elem['type'] == 'calculated':
                        if '*' in elem['value']:
                            op = elem['value'].split('*')
                            v = Decimal(obj[op[0]] * obj[op[1]]).quantize(Decimal(10) ** -2) if obj[op[0]] and obj[op[1]] else Decimal('0.00')
                        if '/' in elem['value']:
                            op = elem['value'].split('/')
                            v = Decimal(obj[op[0]] / obj[op[1]]).quantize(Decimal(10) ** -2) if obj[op[0]] and obj[op[1]] else Decimal('0.00')
                        if '-' in elem['value']:
                            op = elem['value'].split('/')
                            v = Decimal(obj[op[0]] - obj[op[1]]).quantize(Decimal(10) ** -2) if obj[op[0]] and obj[op[1]] else Decimal('0.00')

                # format date fields
                if isinstance(v, datetime.date):
                    cell_format = date_format
                elif isinstance(v, decimal.Decimal) or isinstance(v, float):
                    cell_format = currency_format
                else:
                    cell_format = text_format

                # write row
                ws.write(row, col, v, cell_format)
                col += 1
            row += 1

    time2 = datetime.datetime.now()
    delta = (time2 - time1).total_seconds()
    print(f"Time required to write and export excel data: {delta} sec")

    wb.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f"attachment; filename={filename}"
    output.close()
    return response


def export_manual_report_to_excel(cb_lines, company, customer):
    # Workbook
    file_name = ''
    output = None
    if customer:
        file_name = f"849_{customer.name.replace(' ', '')}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}.xlsx"
        # ticket 759 Change Manual CB excel files to be saved in 849_manual folder
        file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company.get_id_str()}", f"{DIR_NAME_849_ERM_MANUAL}", f"{file_name}")
        wb = xlsxwriter.Workbook(file_path)
        ws = wb.add_worksheet('ManualCB Report from 849')
    else:
        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'constant_memory': True})
        ws = wb.add_worksheet('ManualCB Report')

    # Formats
    bold = wb.add_format({'bold': True})
    date_format = wb.add_format({'num_format': 'mm/dd/yy'})

    column_header = [
        'Manufacturer Name',
        'Wholesaler Name',
        'Line ID',
        'Debit Memo Number',
        'Debit Memo Date',
        'Debit Memo Amount',
        'EDI Line Type',
        'Credit Memo Number',
        'Credit Memo Date',
        'Credit Memo Amount',
        'Accepted Status',
        'Corrected Indicator',
        'Rejection Reason Codes',
        'Submitted Contract ID',
        'Corrected Contract ID',
        'Corrected Customer ID',
        'Corrected Customer ID Qualifier',
        'Corrected Product ID',
        'Corrected Product ID Qualifier',
        'Corrected Wholesaler Cost',
        'Corrected Contract Price',
        'Corrected Quantity',
        'Corrected Unit of Measure',
        'Corrected Chargeback Amount',
        'Corrected Extended Chargeback Amount',
        'Corrected Invoice Number',
        'Corrected Invoice Date',
        'Notes',
        'Customer Ship To Name',
        'Customer Ship To Address',
        'Customer Ship To City',
        'Customer Ship To State',
        'Customer Ship To Zip',
        'Customer Ship To Country'
    ]

    # Draw Header (column names)
    for index, value in enumerate(column_header):
        ws.write(0, index, value, bold)

    # Draw Detail (row values)
    row = 1
    indirect_customer_844 = {}
    for col, cb_line in enumerate(cb_lines):
        cb = cb_line.get_my_chargeback()
        item = cb_line.get_my_item()
        distribution_center = cb_line.get_my_distribution_center()
        indirect_customer = cb_line.get_my_indirect_customer()
        contract = cb_line.get_my_contract()
        chargebackline = get_chargebackline_object(cb_line.id)
        # EA-1653 Add handling if Ind Cust DEA is invalid
        import844_obj = chargebackline.get_my_import844_obj()
        if not indirect_customer:
            indirect_customer_844 = {'company_name': import844_obj.line.get('L_ShipToName', '') if import844_obj else '',
             'address1': import844_obj.line.get('L_ShipToAddress', '') if import844_obj else '',
             'address2': '',
             'city': import844_obj.line.get('L_ShipToCity', '') if import844_obj else '',
             'state': import844_obj.line.get('L_ShipToState', '') if import844_obj else '',
             'zip_code': import844_obj.line.get('L_ShipToZipCode', '') if import844_obj else '',
             'location_number': import844_obj.line.get('L_ShipToID', '') if import844_obj else ''}

        # ticket EA-1371 only contain user_dispute note. Put blank if user_dispute note is blank
        disputes_notes = cb_line.user_dispute_note[:80] if cb_line.user_dispute_note else ''

        # data
        ws.write(row, 0, company.name)
        ws.write(row, 1, distribution_center.name if distribution_center else '')
        ws.write(row, 2, cb_line.cblnid)
        ws.write(row, 3, cb.number)
        ws.write(row, 4, cb.date if cb.date else '', date_format)
        ws.write(row, 5, cb.claim_subtotal if cb.claim_subtotal else '')
        ws.write(row, 6, 'RA')
        ws.write(row, 7, cb.accounting_credit_memo_number if cb.accounting_credit_memo_number else '')
        ws.write(row, 8, cb.accounting_credit_memo_date if cb.accounting_credit_memo_date else '', date_format)
        ws.write(row, 9, cb.accounting_credit_memo_amount if cb.accounting_credit_memo_amount else '')
        ws.write(row, 10, 'Y' if cb.claim_issue else 'N')
        ws.write(row, 11, 'Y')
        ws.write(row, 12, cb_line.disputes_codes)
        ws.write(row, 13, cb_line.submitted_contract_no)
        ws.write(row, 14, contract.number if contract and contract.number else '')
        if not indirect_customer:
            ws.write(row, 15,indirect_customer_844['location_number'])
        else:
            ws.write(row, 15,indirect_customer.location_number if indirect_customer and indirect_customer.location_number else '')
        ws.write(row, 16, '11')
        ws.write(row, 17, item.ndc if item and item.ndc else '')
        ws.write(row, 18, 'NDC')
        ws.write(row, 19, cb_line.wac_system if cb_line.wac_system else '')
        ws.write(row, 20, cb_line.contract_price_system if cb_line.contract_price_system else '')
        ws.write(row, 21, cb_line.item_qty if cb_line.item_qty else '')
        ws.write(row, 22, cb_line.item_uom if cb_line.item_uom else 'EA')
        ws.write(row, 23, cb_line.get_corrected_chargeback_amount())
        ws.write(row, 24, cb_line.claim_amount_issue if cb_line.claim_amount_issue else '')
        ws.write(row, 25, cb_line.invoice_number if cb_line.invoice_number else '')
        ws.write(row, 26, cb_line.invoice_date if cb_line.invoice_date else '', date_format)
        ws.write(row, 27, disputes_notes)
        # EA-1653 Add handling if Ind Cust DEA is invalid
        if not indirect_customer:
            ws.write(row, 28, indirect_customer_844['company_name'])
            ws.write(row, 29, indirect_customer_844['address1'])
            ws.write(row, 30, indirect_customer_844['city'])
            ws.write(row, 31, indirect_customer_844['state'])
            ws.write(row, 32, indirect_customer_844['zip_code'])
        else:
            ws.write(row, 28, indirect_customer.company_name if indirect_customer else '')
            ws.write(row, 29, indirect_customer.get_complete_address() if indirect_customer else '')
            ws.write(row, 30, indirect_customer.city if indirect_customer else '')
            ws.write(row, 31, indirect_customer.state if indirect_customer else '')
            ws.write(row, 32, indirect_customer.zip_code if indirect_customer else '')
        ws.write(row, 33, 'USA')

        # increase jump (next row)
        row += 1

    # close Workbook
    wb.close()

    if customer.name:
        response = wb.filename, file_name
    else:
        # seek output
        output.seek(0)

        filename = generate_filename_for_reports(obj_name='manual_report')
        response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = f"attachment; filename={filename}"

        # close output
        output.close()

    return response


def export_contract_membership_list():
    # for python 3 io.BytesIO instead of StringIO.StringIO
    output = io.BytesIO()

    # Workbook
    wb = xlsxwriter.Workbook(output, {'constant_memory': True})
    ws = wb.add_worksheet('MEMBERSHIP')

    # Formats
    bold = wb.add_format({'bold': True})
    date_format = wb.add_format({'num_format': 'mm/dd/yy'})

    column_header = ['CONTRACT',
                     'MEMBER_LOCNO',
                     'COMPANY_NAME',
                     'ADDRESS1',
                     'ADDRESS2',
                     'CITY',
                     'STATE',
                     'ZIP_CODE',
                     '340B',
                     'GLNNO',
                     'COT',
                     'Start_Date',
                     'End_Date',
                     'Change_Indicator']

    # Draw Header (column names)
    for index, value in enumerate(column_header):
        ws.write(0, index, value, bold)

    ws.set_column(11, 11, None, date_format)
    ws.set_column(12, 12, None, date_format)

    # close Workbook
    wb.close()

    # seek output
    output.seek(0)

    filename = generate_filename_for_reports(obj_name='members')
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f"attachment; filename={filename}"

    # close output
    output.close()

    return response


def export_report(filename, headers=None, data=None, is_schedule_send=False, company="", field_date_formats=[], format_dates_indexes=[], is_currency_indexes=[], keys_for_export=[],is_decimal_indexes=[],field_decimal_formats=[]):
    time1 = datetime.datetime.now()
    # for python 3 io.BytesIO instead of StringIO.StringIO
    output = io.BytesIO()
    print(keys_for_export)
    print(">>>>>>>>>>>")
    print(field_decimal_formats)
    filename = filename + "_export"
    if is_schedule_send:
        file_name = f"{filename}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}.xlsx"
        file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company}", f"{DIR_NAME_USER_REPORTS}", f"{file_name}")
        wb = xlsxwriter.Workbook(file_path)
    # Workbook
    else:
        wb = xlsxwriter.Workbook(output, {'constant_memory': True})
    ws = wb.add_worksheet("Report Export")

    # Formats
    bold = wb.add_format({'bold': True})
    text_format = wb.add_format({'font_size': 10})
    date_format = wb.add_format({'font_size': 10, 'num_format': 'mm/dd/yyyy'})
    currency_format = wb.add_format({'font_size': 10, 'num_format': '#,##0.00'})

    column_header = headers

    # Draw Header (column names)
    for index, value in enumerate(column_header):
        ws.write(0, index, value, bold)

    row = 1
    # EA-1687 852/867 Report Builder Feedback
    data_852_quantity_column = ['L_QB', 'L_QA', 'L_QP', 'L_QI', 'L_QR', 'L_QS', 'L_QT', 'L_QU', 'L_QW', 'L_QO', 'L_QZ','L_QD', 'L_QE','L_QC','L_QH']
    for df in data:
        df_values = []
        for elem in keys_for_export:
            if elem in data_852_quantity_column:
                df[elem] = int(df[elem])          # EA-1687 852/867 Report Builder Feedback
            df_values.append(df[elem])
        col = 0
        for index, d in enumerate(df_values):
            # format date and number fields
            print(d)
            if isinstance(d, datetime.date):
                print("cvvv")
                if index in format_dates_indexes:
                    python_date_format = field_date_formats[index]
                    if python_date_format == "%m%d%Y":
                        xls_date_format = "mmddyyyy"
                    elif python_date_format == "%m-%d-%Y":
                        xls_date_format = "mm-dd-yyyy"
                    elif python_date_format == "%d/%m/%Y":
                        xls_date_format = "dd/mm/yyyy"
                    elif python_date_format == "%d-%m-%Y":
                        xls_date_format = "dd-mm-yyyy"
                    elif python_date_format == "%d%m%Y":
                        xls_date_format = "ddmmyyyy"
                    elif python_date_format == "%Y/%m/%d":
                        xls_date_format = "yyyy/mm/dd"
                    elif python_date_format == "%Y-%m-%d":
                        xls_date_format = "yyyy-mm-dd"
                    elif python_date_format == "%Y%m%d":
                        xls_date_format = "yyyymmdd"
                    elif python_date_format == "%Y%m":
                        xls_date_format = "yyyymm"
                    elif python_date_format == "%m%Y":
                        xls_date_format = "mmyyyy"
                    elif python_date_format == "%B":
                        xls_date_format = "mmmm"
                    elif python_date_format == "%Y":
                        xls_date_format = "yyyy"
                    elif python_date_format == "%B %d, %Y":
                        xls_date_format = "mmmm dd, yyyy"
                    else:
                        xls_date_format = "mm/dd/yyyy"
                else:
                    xls_date_format = "mm/dd/yyyy"

                date_format = wb.add_format({'font_size': 10, 'num_format': xls_date_format})
                cell_format = date_format
            elif isinstance(d, decimal.Decimal) or isinstance(d, float):
                if index in is_currency_indexes and index in is_decimal_indexes:
                    python_decimal_value = field_decimal_formats[index]
                    decimalformat = format(0, f'.{python_decimal_value}f')
                    python_decimal_format = f'#,$##{decimalformat}'
                    cell_format = wb.add_format({'font_size': 10, 'num_format': python_decimal_format})

                elif index in is_currency_indexes:
                    cell_format = wb.add_format({'font_size': 10, 'num_format': '#,$##0.00'})
                else:
                    python_decimal_value = field_decimal_formats[index]
                    if python_decimal_value:
                        decimalformat = format(0, f'.{python_decimal_value}f')
                        python_decimal_format = f'#,##{decimalformat}'
                        cell_format = wb.add_format({'font_size': 10, 'num_format': python_decimal_format})
                    else:
                        cell_format = currency_format
            elif isinstance(d, dict):
                d = str(d)
            else:
                cell_format = text_format
            ws.write(row, col, d, cell_format)
            col += 1
        row += 1

    time2 = datetime.datetime.now()
    delta = (time2 - time1).total_seconds()
    print(f"Time required to write and export excel data: {delta} sec")
    wb.close()

    filename = generate_filename_for_reports(obj_name=filename)

    if is_schedule_send:
        # close output
        output.close()
        response = wb.filename, filename
        return response

    # seek output
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f"attachment; filename=\"{filename}\""
    return response


def export_contract_upload(data, company):
    # Workbook
    file_name = f"contract_upload_update_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}.xlsx"
    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company.get_id_str()}", f"{DIR_NAME_FILES_STORAGE}", f"{file_name}")
    wb = xlsxwriter.Workbook(file_path)
    ws = wb.add_worksheet('Contract Upload')

    # Formats
    bold = wb.add_format({'bold': True})

    column_header = ['CONTRACT ID', 'PRODUCT ID', 'STATUS', 'START DATE', 'END DATE', 'PRICE', 'ERROR TYPE', 'ERROR DETAIL']

    # Draw Header (column names)
    for index, value in enumerate(column_header):
        ws.write(0, index, value, bold)

    # Draw Detail (row values)
    row = 1
    for record in data:
        error_messages = ' '.join(map(str, record["message"]))
        # data
        ws.write(row, 0, record["contract"])
        ws.write(row, 1, record["product"])
        ws.write(row, 2, record["status"])
        ws.write(row, 3, record["submitted_start_date"])
        ws.write(row, 4, record["submitted_end_date"])
        ws.write(row, 5, record["price"])
        ws.write(row, 6, record["type_text"])
        ws.write(row, 7, error_messages)

        # increase jump (next row)
        row += 1

    # close Workbook
    wb.close()

    response = wb.filename, file_name
    return response


def export_contract_upload_template():
    # for python 3 io.BytesIO instead of StringIO.StringIO
    output = io.BytesIO()

    # Workbook
    wb = xlsxwriter.Workbook(output, {'constant_memory': True})
    ws = wb.add_worksheet()

    # Formats
    bold = wb.add_format({'bold': True})
    date_format = wb.add_format({'num_format': 'mm/dd/yyyy'})

    column_header = ['CONTRACT ID', 'PRODUCT ID', 'STATUS', 'START DATE', 'END DATE', 'PRICE']

    # Draw Header (column names)
    for index, value in enumerate(column_header):
        ws.write(0, index, value, bold)

    ws.set_column(4, 4, None, date_format)
    ws.set_column(4, 4, None, date_format)
    # close Workbook
    wb.close()

    # seek output
    output.seek(0)

    filename = 'template_contract_upload.xlsx'
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f"attachment; filename={filename}"

    # close output
    output.close()

    return response


def export_membership_upload(data, company):
    # Workbook
    file_name = f"contract_membership_error_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}.xlsx"
    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company.get_id_str()}", f"{DIR_NAME_FILES_STORAGE}", f"{file_name}")
    wb = xlsxwriter.Workbook(file_path)
    ws = wb.add_worksheet('Contract Upload')

    # Formats
    bold = wb.add_format({'bold': True})
    date_format = wb.add_format({'num_format': 'mm/dd/yy'})

    column_header = ['CONTRACT', 'MEMBER_LOCNO', 'COMPANY_NAME', 'ADDRESS1', 'ADDRESS2', 'CITY', 'STATE', 'ZIP_CODE', '340B', 'GLNNO', 'COT', 'Start_Date', 'End_Date', 'Change_Indicator', 'Error_Type', 'Error_Details']

    # Draw Header (column names)
    for index, value in enumerate(column_header):
        ws.write(0, index, value, bold)

    ws.set_column(11, 11, None, date_format)
    ws.set_column(12, 12, None, date_format)

    # Draw Detail (row values)
    row = 1
    for record in data:
        error_messages = ' '.join(map(str, record["message"]))
        # data
        ws.write(row, 0, record["contract"])
        ws.write(row, 1, record["indc_loc_number"])
        ws.write(row, 2, record["company_name"])
        ws.write(row, 3, record["address1"])
        ws.write(row, 4, record["address2"])
        ws.write(row, 5, record["city"])
        ws.write(row, 6, record["state"])
        ws.write(row, 7, record["zip_code"])
        ws.write(row, 8, record["b340"])
        ws.write(row, 9, record["glnno"])
        ws.write(row, 10, record["cot"])
        ws.write(row, 11, record["submitted_start_date"], date_format)
        ws.write(row, 12, record["submitted_end_date"], date_format)
        ws.write(row, 13, record["change_indicator"])
        ws.write(row, 14, record["type_text"])
        ws.write(row, 15, error_messages)

        # increase jump (next row)
        row += 1

    # close Workbook
    wb.close()

    response = wb.filename, file_name
    return response


def export_dashboard_grid_data_excel(queryset, fname):
    # for python 3 io.BytesIO instead of StringIO.StringIO
    output = io.BytesIO()

    # Workbook
    wb = xlsxwriter.Workbook(output, {'constant_memory': True})
    ws = wb.add_worksheet()

    # Formats
    bold = wb.add_format({'bold': True})

    column_header = ['Entity', 'Value']

    # Draw Header (column names)
    for index, value in enumerate(column_header):
        ws.write(0, index, value, bold)

    row = 1
    for elem in queryset:
        # data

        label_elem = elem['entity'] if elem['entity'] else ''
        val = elem['val'] if elem['val'] else 0

        if label_elem and val:
            ws.write(row, 0, label_elem)
            ws.write(row, 1, val, wb.add_format({'num_format': '#,##0.00'}))

            # increase jump (next row)
            row += 1

    # close Workbook
    wb.close()

    # seek output
    output.seek(0)

    response = HttpResponse(output.read(),content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f"attachment; filename={fname}"

    # close output
    output.close()

    return response


def export_dashboard_grid_data_csv(queryset, fname):
    """
    Export Dashboard grid data to csv
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f"attachment; filename={fname}"

    writer = csv.writer(response)

    # Header
    columns_header = ('Entity', 'Value')
    writer.writerow(columns_header)

    for elem in queryset:

        label_elem = elem['entity'] if elem['entity'] else ''
        val = Decimal(elem['val']).quantize(Decimal(10) ** -2) if elem['val'] else Decimal("0.00")
        if label_elem and val:
            column_values = []
            column_values.append(label_elem)
            column_values.append(val)
            # write row
            writer.writerow(column_values)

    return response


def export_data_867_to_excel(queryset, filename):
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'constant_memory': True})
    ws = wb.add_worksheet('Data 867')

    # Formats
    bold = wb.add_format({'bold': True})
    date_format = wb.add_format({'num_format': 'mm/dd/yy'})

    column_header = [
        'Wholesaler Name',
        'Distribution Center',
        'Distribution Center DEA',
        'Report Start Date',
        'Report End Date',
        'Ship To Name',
        'Ship To DEA Number',
        'Ship_To_hin_number',
        'Ship To Address1',
        'Ship_To Address2',
        'Ship_To_City',
        'Ship_To_State',
        'RShip_To_ZipCode',
        'Transfer Type',
        'Item NDC',
        'Item Description',
        'Contract Number',
        'Invoice Number',
        'Invoice Date',
        'Quantity',
        'UOM',
        'Unite Price',
        'Extended Amount',
        'Report Run Date',
        'Created Date'
    ]

    # Draw Header (column names)
    for index, value in enumerate(column_header):
        ws.write(0, index, value, bold)

    row = 1
    for col, elem in enumerate(queryset):
        ws.write(row, 0, elem.wholesaler_name)
        ws.write(row, 1, elem.dist_name)
        ws.write(row, 2, elem.dist_dea_number)
        ws.write(row, 3, elem.report_start_date if elem.report_start_date else '', date_format)
        ws.write(row, 4, elem.report_end_date if elem.report_start_date else '', date_format)
        ws.write(row, 5, elem.ship_to_name)
        ws.write(row, 6, elem.ship_to_dea_number)
        ws.write(row, 7, elem.ship_to_hin_number)
        ws.write(row, 8, elem.ship_to_address1)
        ws.write(row, 9, elem.ship_to_address2)
        ws.write(row, 10, elem.ship_to_city)
        ws.write(row, 11, elem.ship_to_state)
        ws.write(row, 12, elem.ship_to_zip)
        ws.write(row, 13, elem.transfer_type_desc)
        ws.write(row, 14, elem.product_ndc)
        ws.write(row, 15, elem.product_description)
        ws.write(row, 16, elem.contract_number)
        ws.write(row, 17, elem.invoice_no)
        ws.write(row, 18, elem.invoice_date)
        ws.write(row, 19, elem.quantity)
        ws.write(row, 20, elem.quantity_uom)
        ws.write(row, 21, elem.unit_price)
        ws.write(row, 22, elem.extended_amount)
        ws.write(row, 23, elem.report_run_date if elem.report_run_date else '', date_format)
        ws.write(row, 24, elem.created_at if elem.created_at else '', date_format)

        # increase jump (next row)
        row += 1

    wb.close()
    # seek output
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f"attachment; filename={filename}"

    # close output
    output.close()

    return response


def export_data_867_to_csv(queryset, filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f"attachment; filename={filename}"

    writer = csv.writer(response)

    column_header = [
        'Wholesaler Name',
        'Distribution Center',
        'Distribution Center DEA',
        'Report Start Date',
        'Report End Date',
        'Ship To Name',
        'Ship To DEA Number',
        'Ship_To_hin_number',
        'Ship To Address1',
        'Ship_To Address2',
        'Ship_To_City',
        'Ship_To_State',
        'RShip_To_ZipCode',
        'Transfer Type',
        'Item NDC',
        'Item Description',
        'Contract Number',
        'Invoice Number',
        'Invoice Date',
        'Quantity',
        'UOM',
        'Unite Price',
        'Extended Amount',
        'Report Run Date',
        'Created Date'
    ]
    writer.writerow(column_header)

    for col, elem in enumerate(queryset):
        column_values = []
        column_values.append(elem.wholesaler_name)
        column_values.append(elem.dist_name)
        column_values.append(elem.dist_dea_number)
        column_values.append(elem.report_start_date if elem.report_start_date else '')
        column_values.append(elem.report_end_date if elem.report_end_date else '')
        column_values.append(elem.ship_to_name)
        column_values.append(elem.ship_to_dea_number)
        column_values.append(elem.ship_to_hin_number)
        column_values.append(elem.ship_to_address1)
        column_values.append(elem.ship_to_address2)
        column_values.append(elem.ship_to_city)
        column_values.append(elem.ship_to_state)
        column_values.append(elem.ship_to_zip)
        column_values.append(elem.transfer_type_desc)
        column_values.append(elem.product_ndc)
        column_values.append(elem.product_description)
        column_values.append(elem.contract_number)
        column_values.append(elem.invoice_no)
        column_values.append(elem.invoice_date if elem.invoice_date else '')
        column_values.append(elem.quantity)
        column_values.append(elem.quantity_uom)
        column_values.append(elem.unit_price)
        column_values.append(elem.extended_amount)
        column_values.append(elem.report_run_date if elem.report_run_date else '')
        column_values.append(elem.created_at.strftime('%Y%m%d%H%M%S%f') if elem.created_at else '')

        writer.writerow(column_values)

    return response


def export_data_852_to_excel(queryset, filename):
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'constant_memory': True})
    ws = wb.add_worksheet('Data 852')

    # Formats
    bold = wb.add_format({'bold': True})
    date_format = wb.add_format({'num_format': 'mm/dd/yy'})

    column_header = [
        'Wholesaler Name',
        'Distribution Center Name',
        'Distribution Center DEA',
        'Report Start Date',
        'Report End Date',
        'Item NDC',
        'Item Description',
        'BS',
        'TS',
        'QB',
        'QA',
        'QP',
        'QI',
        'QR',
        'QS',
        'QT',
        'QU',
        'QW',
        'QO',
        'QN',
        'QH',
        'QC',
        'QZ',
        'QD',
        'QE',
        'Created Date'
    ]

    column_comments = [
        'Wholesaler Name',
        'Distribution Center Name',
        'Distribution Center DEA',
        'Report Start Date',
        'Report End Date',
        'Item NDC',
        'Item Description',
        'Bailment Sales Quantity',
        'Total Sales Quantity',
        'Beginning Balance Quantity',
        'On Hand Quantity',
        'On Order Quantity',
        'In Transit Quantity',
        'Saleable Quantity Received',
        'Actual Sales Quantity',
        'Inventory Adjustment Quantity Positive',
        'Saleable Customer Return Quantity',
        'Quantity Withdrawn Frm Whs',
        'Quantity Out of Stock',
        'Planned Inventory Quantity',
        'Quantity Damaged Or OnHold',
        'Quantity Committed',
        'Quantity Transferred',
        'Additional Demand Quantity',
        'Ending Balance Quantity',
        'Created Date'
    ]
    print(column_comments[0])
    # Draw Header (column names)
    for index, value in enumerate(column_header):
        ws.write(0, index, value, bold)
        ws.write_comment(0, index, f"{column_comments[index]}")

    row = 1
    for col, elem in enumerate(queryset):
        item_description = elem.get_my_item_description()

        ws.write(row, 0, elem.wholesaler_name)
        ws.write(row, 1, elem.H_distributor_id.name)
        ws.write(row, 2, elem.H_distributor_id.dea_number)
        ws.write(row, 3, elem.H_start_date if elem.H_start_date else '', date_format)
        ws.write(row, 4, elem.H_end_date if elem.H_end_date else '', date_format)
        ws.write(row, 5, elem.L_item_id)
        ws.write(row, 6, item_description)
        ws.write(row, 7, elem.L_BS)
        ws.write(row, 8, elem.L_TS)
        ws.write(row, 9, elem.L_QB)
        ws.write(row, 10, elem.L_QA)
        ws.write(row, 11, elem.L_QP)
        ws.write(row, 12, elem.L_QI)
        ws.write(row, 13, elem.L_QR)
        ws.write(row, 14, elem.L_QS)
        ws.write(row, 15, elem.L_QT)
        ws.write(row, 16, elem.L_QU)
        ws.write(row, 17, elem.L_QW)
        ws.write(row, 18, elem.L_QO)
        ws.write(row, 19, '')
        ws.write(row, 20, elem.L_QH)
        ws.write(row, 21, elem.L_QC)
        ws.write(row, 22, elem.L_QZ)
        ws.write(row, 23, elem.L_QD)
        ws.write(row, 24, elem.L_QE)
        ws.write(row, 25, elem.created_at if elem.created_at else '', date_format)

        # increase jump (next row)
        row += 1

    wb.close()
    # seek output
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f"attachment; filename={filename}"

    # close output
    output.close()

    return response


def export_data_852_to_csv(queryset, filename):
    time1 = datetime.datetime.now()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f"attachment; filename={filename}"

    writer = csv.writer(response)

    column_header = [
        'Wholesaler Name',
        'Distribution Center Name',
        'Distribution Center DEA',
        'Report Start Date',
        'Report End Date',
        'Item NDC',
        'Item Description',
        'BS',
        'TS',
        'QB',
        'QA',
        'QP',
        'QI',
        'QR',
        'QS',
        'QT',
        'QU',
        'QW',
        'QO',
        'QN',
        'QH',
        'QC',
        'QZ',
        'QD',
        'QE',
        'Created Date'
    ]
    writer.writerow(column_header)

    for col, elem in enumerate(queryset):
        item_description = elem.get_my_item_description()
        column_values = []
        column_values.append(elem.wholesaler_name)
        column_values.append(elem.H_distributor_id.name)
        column_values.append(elem.H_distributor_id.dea_number)
        column_values.append(elem.H_start_date if elem.H_start_date else '')
        column_values.append(elem.H_end_date if elem.H_end_date else '')
        column_values.append(elem.L_item_id)
        column_values.append(item_description)
        column_values.append(elem.L_BS)
        column_values.append(elem.L_TS)
        column_values.append(elem.L_QB)
        column_values.append(elem.L_QA)
        column_values.append(elem.L_QP)
        column_values.append(elem.L_QI)
        column_values.append(elem.L_QR)
        column_values.append(elem.L_QS)
        column_values.append(elem.L_QT)
        column_values.append(elem.L_QU)
        column_values.append(elem.L_QW)
        column_values.append(elem.L_QO)
        column_values.append('')
        column_values.append(elem.L_QH)
        column_values.append(elem.L_QC)
        column_values.append(elem.L_QZ)
        column_values.append(elem.L_QD)
        column_values.append(elem.L_QE)
        column_values.append(elem.created_at.strftime('%Y%m%d%H%M%S%f') if elem.created_at else '')

        writer.writerow(column_values)

    time2 = datetime.datetime.now()
    delta = (time2 - time1).total_seconds()
    print(f"Time required to write and export csv data: {delta} sec")

    return response