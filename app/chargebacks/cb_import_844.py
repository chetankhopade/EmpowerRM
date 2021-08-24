import datetime
import fnmatch
import glob
import os
import shutil
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import SUBSTAGE_TYPE_NO_ERRORS, SUBSTAGE_TYPE_ERRORS
from app.management.utilities.functions import (ok_json, bad_json, move_file_to_bad_folder, validate_844_header,
                                                move_import844_to_import844_history_table,
                                                generate_bulk_id, get_next_cbid, get_next_cblnid)
from app.management.utilities.globals import addGlobalData
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_844_ERM_INTAKE, DIR_NAME_844_PROCESSED
from erms.models import (Import844, ChargeBack, ChargeBackDispute, ChargeBackLine, DistributionCenter,
                         DirectCustomer, ChargeBackHistory, Contract, Item)


# Preprocess handler class
class DataHandler:

    #  class to create lists of objects to optimize validations processes
    def __init__(self, company):
        db = company.database
        self.i844s_open = None

        # for header
        self.dcenters = DistributionCenter.objects.using(db).values('id', 'dea_number', 'customer__account_number')
        self.dcustomers = DirectCustomer.objects.using(db).values('id', 'account_number')
        self.cbs_open = ChargeBack.objects.using(db).filter(type='00').values('number')
        self.cbs_history = ChargeBackHistory.objects.using(db).filter(type='00').values('number', 'chargeback_id')

        # for lines
        self.contracts = Contract.objects.using(db).values('id', 'number')
        self.items = Item.objects.using(db).values('id', 'ndc')


# Import Process (read file and create Import844 records)
def import_844_process(company, src):

    # local vars
    db = company.database
    import844_instances = []
    bulk_id = generate_bulk_id(db)
    file_name = os.path.basename(src)

    time1 = datetime.datetime.now()
    with open(src) as infile:
        next(infile)
        for index, line in enumerate(infile):
            if len(line.strip()):
                row = line.split('|')
                obj = Import844(
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
                import844_instances.append(obj)

        Import844.objects.using(db).bulk_create(import844_instances, batch_size=100)
        time2 = datetime.datetime.now()
        delta = (time2 - time1).total_seconds()
        print(f"Import844 Process: {delta} sec\n")
        return bulk_id


# Chargeback Process (headervalidations and create cb records)
def import_chargebacks_process(company, import844_bulk_id):

    # PreProcess (load some data to be processed in validations in next step)
    data_handler = DataHandler(company)

    db = company.database
    chargebacks_instances = []
    chargebacks_lines_instances = []
    chargebacks_disputes_instances = []
    try:
        import844s = Import844.objects.using(db).filter(bulk_id=import844_bulk_id)
        data_handler.i844s_open = import844s.values('bulk_id', 'header__H_CBNumber', 'line__L_ItemCreditAmt')
        cbnumbers = import844s.values_list('header__H_CBNumber', flat=True).order_by().annotate(total=Count('id'))

        # initialize counters from company counters
        cbid_counter = company.cbid_counter if company.cbid_counter else get_next_cbid(db)
        cblnid_counter = company.cblnid_counter if company.cblnid_counter else get_next_cblnid(db)

        # update company cbid and cblnid counters
        company.cbid_counter = cbid_counter + cbnumbers.count()
        company.cblnid_counter = cblnid_counter + import844s.count()
        company.save()

        time1 = datetime.datetime.now()
        for cbnumber in cbnumbers:
            import_844_objects = import844s.filter(header__H_CBNumber=cbnumber)
            import844 = import_844_objects[0]

            # Header Validations
            # time4a = datetime.datetime.now()
            header_validations = import844.header_import_validations(db, data_handler)
            # time4b = datetime.datetime.now()
            # delta = (time4b - time4a).total_seconds()
            # print(f"Main ForLoop - Header Validation (#4): {delta} sec")

            # ChargeBack obj and Disputes list instances
            # time5a = datetime.datetime.now()
            cb_obj, cb_disputes_list = import844.chargeback_import_instances(db, header_validations, cbid_counter)
            chargebacks_instances.append(cb_obj)
            chargebacks_disputes_instances.extend(cb_disputes_list)
            # time5b = datetime.datetime.now()
            # delta = (time5b - time5a).total_seconds()
            # print(f"Main - CBs objects (#5): {delta} sec")

            # increase cbid counter
            cbid_counter += 1

            # Lines
            # timel1 = datetime.datetime.now()
            for import844 in import_844_objects:

                # Line Validations
                # time7a = datetime.datetime.now()
                line_validations = import844.line_import_validations(db, data_handler)
                # time7b = datetime.datetime.now()
                # delta = (time7b - time7a).total_seconds()
                # print(f"Lines ForLoop - Line Validation (#7): {delta} sec")

                # ChargeBackLine obj and CBLineDisputes list instances
                # time12a = datetime.datetime.now()
                cbline_obj, cbline_disputes_list = import844.chargebacklines_import_instances(db, line_validations, cb_obj, cblnid_counter)
                chargebacks_lines_instances.append(cbline_obj)
                chargebacks_disputes_instances.extend(cbline_disputes_list)
                # time12b = datetime.datetime.now()
                # delta = (time12b - time12a).total_seconds()
                # print(f"Lines ForLoop - CBLine and CBLineDispute objects (#12): {delta} sec")

                # increase cblnid counter
                cblnid_counter += 1

            # timel2 = datetime.datetime.now()
            # delta = (timel2 - timel1).total_seconds()
            # print(f"Lines Completed (#6): {delta} sec\n")

        time2 = datetime.datetime.now()
        delta = (time2 - time1).total_seconds()
        print(f"Main Forloop Completed (#3): {delta} sec")

        # bulk process (CB and CBDispute)
        time14a = datetime.datetime.now()
        cbs_objs = ChargeBack.objects.using(db).bulk_create(chargebacks_instances, batch_size=100)
        ChargeBackLine.objects.using(db).bulk_create(chargebacks_lines_instances, batch_size=100)
        ChargeBackDispute.objects.using(db).bulk_create(chargebacks_disputes_instances, batch_size=100)
        time14b = datetime.datetime.now()
        delta = (time14b - time14a).total_seconds()
        print(f"Bulk Completed (#14): {delta} sec")

        # ticket 854 Move Import844 to Import844History table after cb is created and delete open Import844
        time13a = datetime.datetime.now()
        move_import844_to_import844_history_table(db, import844s)
        time13b = datetime.datetime.now()
        delta = (time13b - time13a).total_seconds()
        print(f"Move844 to history (#13): {delta} sec")

        # clean (delete object from memory)
        del data_handler

        # Validations
        print('Running validations ...')
        time15a = datetime.datetime.now()
        for cb in cbs_objs:
            if cb.has_active_disputes():
                cb.get_my_chargeback_lines().update(received_with_errors=1)
            else:
                # checking lines if cb no errors until this momentum
                if cb.substage == SUBSTAGE_TYPE_NO_ERRORS and cb.has_active_disputes_lines():
                    cb.substage = SUBSTAGE_TYPE_ERRORS
                    cb.save()
                # run validations
                cb.run_validations(db)

        time15b = datetime.datetime.now()
        delta = (time15b - time15a).total_seconds()
        print(f"RunValidations (#15): {delta} sec")

    except Exception as ex:
        print(ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def view(request):
    """
    Import all selected 844 files and process it
    :param request:
    :return:
    """
    data = {'title': 'Chargebacks - Import 844 Files'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        files_844 = request.POST.get('844_files', '')
        if not files_844:
            return bad_json(message='Not 844 files to process')

        company = data['company']
        for file_844 in files_844.split("|"):
            company_directory = os.path.join(CLIENTS_DIRECTORY, company.get_id_str())
            src_path = os.path.join(company_directory, DIR_NAME_844_ERM_INTAKE, file_844)
            parent_directory_name = os.path.basename(os.path.normpath(os.path.dirname(src_path)))

            # Is Valid 844 File
            if not validate_844_header(src_path):
                move_file_to_bad_folder(src_path)
                return bad_json(message=f"{file_844} is not a valid 844 file")

            # Wrong parent directory
            if parent_directory_name != DIR_NAME_844_ERM_INTAKE:
                return bad_json(message=f"{file_844} is not in a valid 844 directory")

            # IMPORT 844 Process
            import844_bulk_id = import_844_process(company, src_path)

            # IMPORT CHARGEBACKS and LINES Process
            import_chargebacks_process(company, import844_bulk_id)

            # Move it to "DIR_NAME_844_PROCESSED" folder
            shutil.move(src_path, os.path.join(Path(''.join(os.path.join(company_directory, DIR_NAME_844_PROCESSED))), os.path.basename(src_path)))

            print('FINISH!')

        return ok_json(data={"message": "844 Files have been succesfully processed"})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_844_files_list(request):
    data = {}
    addGlobalData(request, data)
    try:
        data['844_files'] = [x for x in os.listdir(os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_844_ERM_INTAKE)) if fnmatch.fnmatch(x, '*.txt')]
        return render(request, "chargebacks/includes/844_files_list.html", data)
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


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def upload_844_files(request):
    data = {}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    company_844_path = f"{CLIENTS_DIRECTORY}/{data['company'].get_id_str()}/{DIR_NAME_844_ERM_INTAKE}/"
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
