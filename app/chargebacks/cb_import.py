import datetime
import fnmatch
import os
import shutil
import uuid
from decimal import Decimal
from pathlib import Path

import requests
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.tasks import import_validations_function
from app.management.utilities.constants import (STAGE_TYPE_IN_PROCESS, SUBSTAGE_TYPE_NO_ERRORS, LINE_STATUS_PENDING,
                                                PROCESSING_OPTION_ORIGINAL_ID)
from app.management.utilities.functions import (ok_json, bad_json, move_file_to_bad_folder, validate_844_header,
                                                get_next_cbid, get_next_cblnid, is_valid_date)
from app.management.utilities.globals import addGlobalData
from empowerb.settings import (CLIENTS_DIRECTORY, DIR_NAME_844_ERM_INTAKE, DIR_NAME_844_PROCESSED, IMPORT_SERVICE_URL)
from erms.models import Import844, ChargeBack, ChargeBackLine, Import844History


def process_import844(row, file_name, bulk_id):
    import844 = Import844(
            id=uuid.uuid4().__str__(),
            bulk_id=bulk_id,
            file_name=file_name,
            header={
                "H_DocType": row[0],
                "H_ControlNo": row[1],
                "H_AcctNo": row[2],
                "H_CBType": row[3],
                "H_CBDate": row[4],
                "H_CBNumber": row[5],
                "H_ResubNo": row[6],
                "H_ResubDesc": row[7],
                "H_SuppName": row[8],
                "H_SuppIDType": row[9],
                "H_SuppID": row[10],
                "H_DistName": row[11],
                "H_DistIDType": row[12],
                "H_DistID": row[13],
                "H_SubClaimAmt": row[14],
                "H_TotalCONCount": row[15]
            },
            line={
                "L_ContractNo": row[16],
                "L_ContractStatus": row[17],
                "L_ShipToIDType": row[18],
                "L_ShipToID": row[19],
                "L_ShipToName": row[20],
                "L_ShipToAddress": row[21],
                "L_ShipToCity": row[22],
                "L_ShipToState": row[23],
                "L_ShipToZipCode": row[24],
                "L_ShipToHIN": row[25],
                "L_InvoiceNo": row[26],
                "L_InvoiceDate": row[27],
                "L_InvoiceLineNo": row[28],
                "L_InvoiceNote": row[29],
                "L_ItemNDCNo": row[30],
                "L_ItemUPCNo": row[31],
                "L_ItemQty": row[32],
                "L_ItemUOM": row[33],
                "L_ItemWAC": row[34],
                "L_ItemContractPrice": row[35],
                "L_ItemCreditAmt": row[36],
                "L_ShipTo340BID": row[37],
                "L_ShipToGLN": row[38],
            }
        )

    return import844


def process_chargeback(obj, chargeback_id, cbid_counter):
    chargeback = ChargeBack(id=chargeback_id,
                            cbid=cbid_counter,
                            import844_id=obj.id,
                            # new FK fields
                            import_844_ref_id=obj.id,
                            # end new FK fields
                            distribution_center_id=None,
                            customer_id=None,
                            document_type=obj.header.get("H_DocType", "844"),
                            type=obj.header.get("H_CBType", "00"),
                            date=is_valid_date(obj.header["H_CBDate"]),
                            number=obj.header["H_CBNumber"],
                            resubmit_number=obj.header["H_ResubNo"],
                            resubmit_description=obj.header["H_ResubDesc"],
                            claim_subtotal=Decimal(obj.header["H_SubClaimAmt"]),
                            claim_calculate=Decimal('0.00'),
                            claim_issue=Decimal('0.00'),
                            claim_adjustment=Decimal('0.00'),
                            total_line_count=int(obj.header["H_TotalCONCount"]) if obj.header["H_TotalCONCount"] else None,
                            is_received_edi=True,
                            accounting_credit_memo_number='',
                            accounting_credit_memo_date=None,
                            accounting_credit_memo_amount=None,
                            is_export_849=False,
                            export_849_date=None,
                            original_chargeback_id=None,
                            stage=STAGE_TYPE_IN_PROCESS,
                            substage=SUBSTAGE_TYPE_NO_ERRORS)

    return chargeback


def process_chargebackline(obj, chargebackline_id, chargeback_id, cblnid_counter):
    # EA-1427
    # - submitted_wac_extended_amount(wac_submitted * item_qty)
    # - submitted_contract_price_extended_amount(contract_price_submitted * item_qty)
    # - system_wac_extended_amount(wac_system * item_qty)
    # - system_contract_price_extended_amount(contract_price_system * item_qty)

    item_qty = int(obj.line["L_ItemQty"]) if obj.line["L_ItemQty"] else None
    wac_submitted = Decimal(obj.line["L_ItemWAC"]) if obj.line["L_ItemWAC"] else None
    contract_price_submitted = Decimal(obj.line["L_ItemContractPrice"]) if obj.line["L_ItemContractPrice"] else None

    submitted_wac_extended_amount = None
    submitted_contract_price_extended_amount = None

    if item_qty and wac_submitted:
        submitted_wac_extended_amount = Decimal(item_qty * wac_submitted).quantize(Decimal(10) ** -2)

    if item_qty and contract_price_submitted:
        submitted_contract_price_extended_amount = Decimal(item_qty * contract_price_submitted).quantize(Decimal(10) ** -2)

    chargeback_line = ChargeBackLine(id=chargebackline_id,
                                     cblnid=cblnid_counter,
                                     chargeback_id=chargeback_id,
                                     contract_id=None,
                                     submitted_contract_no=obj.line["L_ContractNo"],
                                     indirect_customer_id=None,
                                     item_id=None,
                                     import844_id=obj.id,
                                     # new FK fields
                                     chargeback_ref_id=chargeback_id,
                                     contract_ref=None,
                                     indirect_customer_ref=None,
                                     item_ref=None,
                                     import_844_ref_id=obj.id,
                                     # end new FK fields
                                     invoice_number=obj.line["L_InvoiceNo"],
                                     invoice_date=is_valid_date(obj.line["L_InvoiceDate"]),
                                     invoice_line_no=obj.line["L_InvoiceLineNo"],
                                     invoice_note=obj.line["L_InvoiceNote"],
                                     item_qty=int(obj.line["L_ItemQty"]) if obj.line["L_ItemQty"] else None,
                                     item_uom=obj.line["L_ItemUOM"],
                                     wac_submitted=Decimal(obj.line["L_ItemWAC"]),
                                     contract_price_submitted=Decimal(obj.line["L_ItemContractPrice"]),
                                     claim_amount_submitted=Decimal(obj.line["L_ItemCreditAmt"]),
                                     wac_system=None,
                                     contract_price_system=None,
                                     system_wac_extended_amount=None,
                                     system_contract_price_extended_amount=None,
                                     submitted_wac_extended_amount=submitted_wac_extended_amount,
                                     submitted_contract_price_extended_amount=submitted_contract_price_extended_amount,
                                     claim_amount_system=None,
                                     claim_amount_issue=None,
                                     claim_amount_adjusment=None,
                                     line_status=LINE_STATUS_PENDING,
                                     received_with_errors=0)
    return chargeback_line


class ImportProcess:

    def __init__(self, company, src_path):

        self.company = company
        self.database = self.company.database
        self.src_path = src_path
        self.file_name = os.path.basename(self.src_path)
        self.import844_objects = []

    def save_import844(self):

        bulk_id = uuid.uuid4().__str__()    # important for reference to each bulk of import844s (avoid duplicates)
        with open(self.src_path) as infile:
            next(infile)
            for index, line in enumerate(infile):
                if len(line.strip()):
                    row = line.split('|')
                    obj = process_import844(row, self.file_name, bulk_id)
                    self.import844_objects.append(obj)

        Import844.objects.using(self.database).bulk_create(self.import844_objects, batch_size=100)

    def save_chargebacks(self, return_cbs_created=False):

        cbid_counter = self.company.cbid_counter if self.company.cbid_counter else get_next_cbid(self.database)
        cblnid_counter = self.company.cblnid_counter if self.company.cblnid_counter else get_next_cblnid(self.database)

        cbs_numbers = {}

        chargebacks_objects = []
        chargebacklines_objects = []

        for obj in self.import844_objects:

            # Chargeback
            current_cb_number = obj.header['H_CBNumber']
            if current_cb_number not in cbs_numbers.keys():
                chargeback_id = uuid.uuid4().__str__()
                cbs_numbers.update({
                    current_cb_number: chargeback_id
                })
                cb = process_chargeback(obj, chargeback_id, cbid_counter)
                chargebacks_objects.append(cb)
                cbid_counter += 1

            # Chargeback Line
            chargeback_id = cbs_numbers[current_cb_number]
            chargebackline_id = uuid.uuid4().__str__()
            cbline = process_chargebackline(obj, chargebackline_id, chargeback_id, cblnid_counter)
            chargebacklines_objects.append(cbline)
            cblnid_counter += 1

        # Bulk inserts
        Import844History.objects.using(self.database).bulk_create(self.import844_objects, batch_size=1000)
        cbs_created = ChargeBack.objects.using(self.database).bulk_create(chargebacks_objects, batch_size=1000)
        ChargeBackLine.objects.using(self.database).bulk_create(chargebacklines_objects, batch_size=1000)
        Import844.objects.using(self.database).filter(id__in=[x.id for x in self.import844_objects]).delete()

        # update company cbid and cblnid counters
        self.company.cbid_counter = cbid_counter
        self.company.cblnid_counter = cblnid_counter
        self.company.save()

        if return_cbs_created:
            return cbs_created


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def view(request):
    data = {'title': 'Chargebacks - Import 844 Files'}
    addGlobalData(request, data)
    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))
    try:
        files_844 = request.POST.get('844_files', '')
        if not files_844:
            return bad_json(message='Not 844 files to process')

        company = data['company']
        invalid_files = []
        valid_files = []
        for file_844 in files_844.split("|"):
            company_directory = os.path.join(CLIENTS_DIRECTORY, company.get_id_str())
            src_path = os.path.join(company_directory, DIR_NAME_844_ERM_INTAKE, file_844)
            parent_directory_name = os.path.basename(os.path.normpath(os.path.dirname(src_path)))

            # Is Valid 844 File
            if not validate_844_header(src_path):
                move_file_to_bad_folder(src_path)
                invalid_files.append(file_844.rsplit('.', 1)[0])

            # Wrong parent directory
            elif parent_directory_name != DIR_NAME_844_ERM_INTAKE:
                invalid_files.append(file_844.rsplit('.', 1)[0])
                # return bad_json(message=f"{file_844} is not in a valid 844 directory")

            else:

                valid_files.append(file_844.rsplit('.', 1)[0])
                # ImportProcess instance
                import_process = ImportProcess(company, src_path)

                # Import844 (read file and store data in the Import844 table)
                time1 = datetime.datetime.now()
                import_process.save_import844()
                time2 = datetime.datetime.now()
                delta = (time2 - time1).total_seconds()
                print(f"\nSave Import844 Process: {delta} sec")

                # Save Chargebacks, CBLines and Move844 to history
                time1 = datetime.datetime.now()
                import_process.save_chargebacks()
                time2 = datetime.datetime.now()
                delta = (time2 - time1).total_seconds()
                print(f"\nSave CB/CBL/Imp844H Process: {delta} sec")

                # Validations
                company_id = company.get_id_str()
                company_db = company.database
                # TODO: uncomment this out when test background tasks with django-q
                # if company.processing_option == PROCESSING_OPTION_ORIGINAL_ID:
                import_validations_function(company_id, company_db, [],request)

                # Move it to "DIR_NAME_844_PROCESSED" folder
                shutil.move(src_path, os.path.join(Path(''.join(os.path.join(company_directory, DIR_NAME_844_PROCESSED))), os.path.basename(src_path)))

        if len(invalid_files):
            invalid_files_name = ", ".join(invalid_files)
            return bad_json(message=f"{invalid_files_name} is not a valid 844 file",extradata={'invalid_files':invalid_files,'valid_files':valid_files})
        return ok_json(data={"message": "844 Files have been succesfully processed"})

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def view_api(request):
    data = {'title': 'Chargebacks - Import 844 Files'}
    addGlobalData(request, data)
    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))
    try:
        files_844 = request.POST.get('844_files', '')
        if not files_844:
            return bad_json(message='Not 844 files to process')

        company = data['company']

        cbid_counter = company.cbid_counter if company.cbid_counter else get_next_cbid(data['db_name'])
        cblnid_counter = company.cblnid_counter if company.cblnid_counter else get_next_cblnid(data['db_name'])

        company_id_str = company.get_id_str()
        request_data = {
            'files_844': files_844,
            'company_id_str': company_id_str,
            'db_name': data['db_name'],
            'cbid_counter': cbid_counter,
            'cblnid_counter': cblnid_counter,
            'user_email': data['user'].email
        }

        response = requests.get(
            f"{IMPORT_SERVICE_URL}/api/import_844/",
            data=request_data
        )


        # for file_844 in files_844.split("|"):
        #     company_directory = os.path.join(CLIENTS_DIRECTORY, company.get_id_str())
        #     src_path = os.path.join(company_directory, DIR_NAME_844_ERM_INTAKE, file_844)
        #     parent_directory_name = os.path.basename(os.path.normpath(os.path.dirname(src_path)))
        #
        #     # Is Valid 844 File
        #     if not validate_844_header(src_path):
        #         move_file_to_bad_folder(src_path)
        #         return bad_json(message=f"{file_844} is not a valid 844 file")
        #
        #     # Wrong parent directory
        #     if parent_directory_name != DIR_NAME_844_ERM_INTAKE:
        #         return bad_json(message=f"{file_844} is not in a valid 844 directory")
        #
        #     # ImportProcess instance
        #     import_process = ImportProcess(company, src_path)
        #
        #     # Import844 (read file and store data in the Import844 table)
        #     time1 = datetime.datetime.now()
        #     import_process.save_import844()
        #     time2 = datetime.datetime.now()
        #     delta = (time2 - time1).total_seconds()
        #     print(f"\nSave Import844 Process: {delta} sec")
        #
        #     # Save Chargebacks, CBLines and Move844 to history
        #     time1 = datetime.datetime.now()
        #     import_process.save_chargebacks()
        #     time2 = datetime.datetime.now()
        #     delta = (time2 - time1).total_seconds()
        #     print(f"\nSave CB/CBL/Imp844H Process: {delta} sec")
        #
        #     # Validations
        #     company_id = company.get_id_str()
        #     company_db = company.database
        #     # TODO: uncomment this out when test background tasks with django-q
        #     # if company.processing_option == PROCESSING_OPTION_ORIGINAL_ID:
        #     import_validations_function(company_id, company_db, [])
        #
        #     # Move it to "DIR_NAME_844_PROCESSED" folder
        #     shutil.move(src_path, os.path.join(Path(''.join(os.path.join(company_directory, DIR_NAME_844_PROCESSED))), os.path.basename(src_path)))

        return ok_json(data={"message": "844 Files have been succesfully processed"})

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())

@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_844_files_list(request):
    data = {}
    addGlobalData(request, data)
    try:
        company_844_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_844_ERM_INTAKE)
        results = []
        for filename in [x for x in os.listdir(company_844_path) if fnmatch.fnmatch(x, '*.txt')]:
            file_path = os.path.join(company_844_path, filename)
            file_id = filename.rsplit('.', 1)[0]
            datetime_stamp = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%m/%d/%Y %H:%m')

            # read file
            with open(file_path, 'r') as f:
                file_content = f.read().split('\n')

            # remove empty elem in list
            file_content = list(filter(None, file_content))

            cbnumbers = []
            for cbnumber in [x.split('|')[5] for x in file_content[1:] if len(x.strip())]:
                if cbnumber not in cbnumbers:
                    cbnumbers.append(cbnumber)

            results.append({
                'filename': filename,
                'file_id': file_id,
                'cb_count': len(cbnumbers),
                'cbline_count': len(file_content[1:]),
                'datetime_stamp': datetime_stamp
            })

        data['results'] = results
        data['844_total_files'] = len(results)
        return render(request, "chargebacks/includes/844_files_list.html", data)
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def upload_844_files(request):
    data = {}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    company_844_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_844_ERM_INTAKE)
    try:
        if request.FILES:
            for index in range(len(request.FILES)):
                new_844_file = request.FILES[f'file[{index}]']
                if new_844_file.name.split('.')[-1] == 'txt':
                    fs = FileSystemStorage(location=company_844_path)
                    fs.save(new_844_file.name, new_844_file)
            return ok_json()

        return bad_json(message='Not files found')
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def delete_844_files(request):
    data = {}
    addGlobalData(request, data)
    try:
        dirpath = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_844_ERM_INTAKE)

        import844_filename = request.POST.get('file', '')
        if import844_filename:
            os.remove(os.path.join(dirpath, import844_filename))
            return ok_json(data={'message': 'File removed'})
        else:
            for filename in os.listdir(dirpath):
                os.remove(os.path.join(dirpath, filename))
            return ok_json(data={'message': 'All Files removed'})

    except Exception as ex:
        return bad_json(message=ex.__str__())
