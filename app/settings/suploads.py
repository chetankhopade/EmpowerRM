import json
import os
from decimal import Decimal
import datetime

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (CONTRACT_TYPE_INDIRECT, CONTRACT_TYPE_DIRECT, CONTRACT_TYPE_BOTH,
                                                STATUS_ACTIVE, STATUS_INACTIVE, STATUS_PENDING, SUBSTAGE_TYPE_NO_ERRORS,
                                                CUSTOMER_TYPE_DISTRIBUTOR, CUSTOMER_TYPE_GPO, STAGE_TYPE_ARCHIVED,
                                                CUSTOMER_TYPE_BUYING_GROUP, CUSTOMER_TYPE_PARENT, STATUS_PROPOSED)
from app.management.utilities.functions import bad_json, ok_json, convert_string_to_date_imports
from app.management.utilities.exports import (export_contract_membership_list, export_membership_upload)
from app.management.utilities.globals import addGlobalData

from app.contracts import tab_manage_membership
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_FILES_STORAGE

from erms.models import (Item, Contract, ContractLine, DirectCustomer, ChargeBackHistory, DistributionCenter,
                         ContractMember, IndirectCustomer, ClassOfTrade)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def upload_company_data(request):
    """
        Import Company Data
    """
    data = {'title': 'Import Company Data'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        # Read the file and its sheets and returns an OrderedDict of DataFrames
        df = pd.read_excel(request.FILES['file'], sheet_name=['ITEMS', 'CONTRACTS', 'CUSTOMERS'])

        # ITEM DataFrame
        for _, row in df['ITEMS'].iterrows():
            item_acctno = row.get('ACCNO', '')
            item_ndc = row.get('NDC', '')
            item_description = row.get('DESCRIPTION', '')
            item_upc = row.get('UPC', '')
            # item_wac = row['WAC']
            # item_awp = row['AWP']

            item_obj, _ = Item.objects.get_or_create(account_number=item_acctno)
            item_obj.ndc = item_ndc
            item_obj.description = item_description
            item_obj.upc = item_upc
            item_obj.save()

        # CUSTOMERS Dataframe
        for _, row in df['CUSTOMERS'].iterrows():
            cus_name = row.get('NAME', '')
            cus_accno = row.get('ACCNO', '')
            cus_type = row.get('TYPE', '')
            cus_address1 = row.get('ADDRESS1', '')
            cus_address2 = row.get('ADDRESS2', '')
            cus_city = row.get('CITY', '')
            cus_state = row.get('STATE', '')
            cus_zip_code = row.get('ZIP_CODE', '')
            cus_email = row.get('EMAIL', '')
            cus_phone = row.get('PHONE', '')
            cus_main_contact = row.get('MAIN_CONTACT', '')
            cus_fax = row.get('FAX', '')
            cus_vendor_no = row.get('VENDOR_NO', '')

            customer_type_id = None
            if cus_type == 'DISTRIBUTOR':
                customer_type_id = CUSTOMER_TYPE_DISTRIBUTOR
            if cus_type == 'GPO':
                customer_type_id = CUSTOMER_TYPE_GPO
            if cus_type == 'BUYING':
                customer_type_id = CUSTOMER_TYPE_BUYING_GROUP
            if cus_type == 'PARENT':
                customer_type_id = CUSTOMER_TYPE_PARENT

            customer_obj, _ = DirectCustomer.objects.get_or_create(account_number=cus_accno)
            customer_obj.name = cus_name
            customer_obj.type = customer_type_id
            customer_obj.address1 = cus_address1
            customer_obj.address2 = cus_address2
            customer_obj.city = cus_city
            customer_obj.state = cus_state
            customer_obj.zip_code = cus_zip_code
            customer_obj.email = cus_email
            customer_obj.phone = cus_phone
            customer_obj.save()

            # add metadata (because we dont have these fields in the model)
            customer_obj.metadata.update({
                'MAIN_CONTACT': cus_main_contact,
                'FAX': cus_fax,
                'VENDOR_NO': cus_vendor_no
            })
            customer_obj.save()

        # CONTRACTS Dataframe
        for _, row in df['CONTRACTS'].iterrows():
            c_number = row.get('C_NUMBER', '')
            c_description = row.get('C_DESCRIPTION', '')
            c_type = row.get('C_TYPE', '').upper()  # DIRECT, INDIRECT, BOTH
            c_start_date = row.get('C_START_DATE', '')  # yyyy-mm-dd
            c_end_date = row.get('C_END_DATE', '')  # yyyy-mm-dd
            c_status = row.get('ContStatusID', '').upper()  # ACTIVE, INACTIVE, PENDING

            contract_type_id = None
            if c_type == 'INDIRECT':
                contract_type_id = CONTRACT_TYPE_INDIRECT
            if c_type == 'DIRECT':
                contract_type_id = CONTRACT_TYPE_DIRECT
            if c_type == 'BOTH':
                contract_type_id = CONTRACT_TYPE_BOTH

            contract_status_id = None
            if c_status == 'ACTIVE':
                contract_status_id = STATUS_ACTIVE
            if c_status == "INACTIVE":
                contract_status_id = STATUS_INACTIVE
            if c_status == "PENDING":
                contract_status_id = STATUS_PENDING

            contract_obj, _ = Contract.objects.get_or_create(number=c_number)
            contract_obj.description = c_description
            contract_obj.type = contract_type_id
            contract_obj.start_date = convert_string_to_date_imports(c_start_date) if c_start_date else None
            contract_obj.end_date = convert_string_to_date_imports(c_end_date) if c_end_date else None
            contract_obj.status = contract_status_id
            contract_obj.save()

            # CONTRACT LINE
            cline_ndc = row['CL_NDC']
            cline_item_obj, _ = Item.objects.get_or_create(ndc=cline_ndc)

            cline_status = row.get('CL_STATUS', '')
            cline_start_date = row.get('CL_START_DATE', '')
            cline_end_date = row.get('CL_END_DATE', '')
            cline_price = Decimal(row.get('CL_PRICE', '0'))
            cline_type = row.get('CL_TYPE', 'A').upper()

            cline_type_id = None
            if cline_type == 'INDIRECT':
                cline_type_id = CONTRACT_TYPE_INDIRECT
            if cline_type == 'DIRECT':
                cline_type_id = CONTRACT_TYPE_DIRECT
            if cline_type == 'BOTH':
                cline_type_id = CONTRACT_TYPE_BOTH

            cline_status_id = None
            if cline_status == 'ACTIVE':
                cline_status_id = STATUS_ACTIVE
            if cline_status == "INACTIVE":
                cline_status_id = STATUS_INACTIVE
            if cline_status == "PENDING":
                cline_status_id = STATUS_PENDING

            contract_line_obj, _ = ContractLine.objects.get_or_create(contract=contract_obj,
                                                                      item=cline_item_obj,
                                                                      type=cline_type_id,
                                                                      start_date=convert_string_to_date_imports(
                                                                          cline_start_date) if cline_start_date else None,
                                                                      end_date=convert_string_to_date_imports(
                                                                          cline_end_date) if cline_end_date else None,
                                                                      price=cline_price if isinstance(cline_price,
                                                                                                      float) else None,
                                                                      status=cline_status_id)
            contract_line_obj.save()

        return ok_json()

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def upload_company_cbhistory(request):
    """
        Import Company CB History Data
    """
    data = {'title': 'Import Company CB History Data'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        # Read the file and its sheets and returns an OrderedDict of DataFrames
        df = pd.read_excel(request.FILES['file'], sheet_name=['CBHISTORY'])

        # ITEM DataFrame
        for _, row in df['CBHISTORY'].iterrows():
            cbid = row.get('CBID', '')
            cus_accno = row.get('ACCNO', '')
            distr_dea = row.get('DEA', '')
            doc_type = row.get('DOCTYPE', '844')
            cb_date = str(row.get('DATE', '')).split(' ')[0]
            cb_number = row.get('NUMBER', '')
            cb_type = '00' if pd.isna(row['TYPE']) or int(row['TYPE']) == 0 else '15'

            cb_resub_no = '' if pd.isna(row['RESUBNO']) else row['RESUBNO']
            cb_resub_desc = '' if pd.isna(row['RESUBDESC']) else row['RESUBDESC']
            original_cb_id = '' if pd.isna(row['ORIGCBID']) else row['ORIGCBID']

            claim_subtotal = row.get('SUBTOTAL', None)
            claim_calculate = row.get('CALCULATE', None)
            claim_issue = row.get('ISSUE', None)
            claim_adjustment = row.get('ADJUSTMENT', None)
            lines_count = row.get('LINECOUNT', 0)

            cm_number = row.get('CMNO', None)
            cm_date = str(row.get('CMDATE', '')).split(' ')[0]
            cm_amount = row.get('CMAMOUNT', None)

            if cbid:
                # get Direct Customer obj (from acc number)
                direct_customer = DirectCustomer.objects.filter(account_number=cus_accno)
                customer_id = direct_customer[0].get_id_str() if direct_customer else None

                # get Distribution Center obj (from dea number)
                distr_dea = DistributionCenter.objects.filter(dea_number=distr_dea)
                distr_dea_id = distr_dea[0].get_id_str() if distr_dea else None

                # CB History obj
                cbhistory, _ = ChargeBackHistory.objects.get_or_create(cbid=cbid)
                cbhistory.chargeback_id = None
                cbhistory.customer_id = customer_id
                cbhistory.distribution_center_id = distr_dea_id
                cbhistory.import844_id = None
                cbhistory.document_type = doc_type
                cbhistory.date = convert_string_to_date_imports(cb_date) if cb_date else None
                cbhistory.type = cb_type
                cbhistory.number = cb_number

                cbhistory.resubmit_number = cb_resub_no
                cbhistory.resubmit_description = cb_resub_desc
                cbhistory.original_chargeback_id = original_cb_id

                cbhistory.claim_subtotal = Decimal(claim_subtotal) if claim_subtotal else None
                cbhistory.claim_calculate = Decimal(claim_calculate) if claim_calculate else None
                cbhistory.claim_issue = Decimal(claim_issue) if claim_issue else None
                cbhistory.claim_adjustment = Decimal(claim_adjustment) if claim_adjustment else None
                cbhistory.total_line_count = int(lines_count) if lines_count else 0

                cbhistory.is_received_edi = False
                cbhistory.accounting_credit_memo_number = cm_number
                cbhistory.accounting_credit_memo_date = convert_string_to_date_imports(cm_date) if cm_date else None
                cbhistory.accounting_credit_memo_amount = Decimal(cm_amount) if cm_amount else None

                cbhistory.stage = STAGE_TYPE_ARCHIVED
                cbhistory.substage = SUBSTAGE_TYPE_NO_ERRORS

                cbhistory.save()

        return ok_json()

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


# To-Do - Remove this function once contract_upload_membership works fine
@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def upload_membership_data(request):
    """
        Import Contract Membership Data
    """
    data = {'title': 'Import Membership Data'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        existing_contract_members = []
        newly_added_members = []

        # Read the file and its sheets and returns an OrderedDict of DataFrames
        df = pd.read_excel(request.FILES['file'], sheet_name=['MEMBERSHIP'])
        required_headers = ['CONTRACT', 'MEMBER_LOCNO', 'Start_Date', 'End_Date']
        headers = pd.read_excel(request.FILES['file']).columns.ravel()

        for rh in required_headers:
            if rh not in headers:
                return bad_json(message='Required headers are no present. Please check the file and upload again')

        # MEMBERSHIP Dataframe
        for _, row in df['MEMBERSHIP'].iterrows():

            save_new_line = True

            today = datetime.datetime.now().date()

            contract_number = row.get('CONTRACT', '')
            member_locno = row.get('MEMBER_LOCNO', '')

            # line dates
            start_date = row.get('Start_Date', '')
            end_date = row.get('End_Date', '')

            # Get Contract
            contractObj = Contract.objects.filter(number=contract_number)
            # Get Indirect Customer number
            indirect_customer_obj = IndirectCustomer.objects.filter(location_number=member_locno)

            # EA-938 - Membership import needs to create Ind. Customers
            cot = ''
            if not indirect_customer_obj:
                # EA-961 - Membership file upload issues
                ad1 = '' if pd.isnull(row.get('ADDRESS1')) else row.get('ADDRESS1')
                ad2 = '' if pd.isnull(row.get('ADDRESS2')) else row.get('ADDRESS2')
                glnno = '' if pd.isnull(row.get('GLNNO')) else row.get('GLNNO')
                bid_340 = '' if pd.isnull(row.get('340B')) else row.get('340B')
                cot = '' if pd.isnull(row.get('COT')) else row.get('COT')

                indc_data = [{
                    "company_name": row.get('COMPANY_NAME', ''),
                    "location_number": member_locno,
                    "address1": ad1,
                    "address2": ad2,
                    "city": row.get('CITY', ''),
                    "state": row.get('STATE', ''),
                    "zip_code": row.get('ZIP_CODE', ''),
                    "cot_id": cot,
                    "gln_no": glnno,
                    "bid_340": bid_340
                }]

                indc_created = create_indirect_customer(indc_data)
                if indc_created == 1:
                    indirect_customer_obj = IndirectCustomer.objects.filter(location_number=member_locno)

            check_and_update_cot(cot, indirect_customer_obj[0].id)

            # Check if contract and indirect customer is present
            if indirect_customer_obj and contractObj:

                # Getting contract and Indirect Customer
                contract = Contract.objects.get(id=contractObj[0].id)
                indirect_customer = IndirectCustomer.objects.get(id=indirect_customer_obj[0].id)

                # Looking of contract overlap lines
                co_validation = tab_manage_membership.validate_membership_line(contractObj[0].id,
                                                                               indirect_customer_obj[0].id,
                                                                               contract.start_date, contract.end_date,
                                                                               start_date,
                                                                               end_date)

                if len(co_validation["message"]) > 0 and co_validation["contract_validation"] == 1:
                    # Contract range overlapping. So extend the contract
                    if start_date < contract.start_date:
                        contract.start_date = start_date
                    if end_date > contract.end_date:
                        contract.end_date = end_date
                    # Updating contract dates
                    contract.save()
                existing_membership_lines = ContractMember.objects.filter(contract=contract,
                                                                          indirect_customer=indirect_customer)
                existing_cm = existing_membership_lines[0] if existing_membership_lines.exists() else None

                if existing_cm:

                    existing_contract_members.append(existing_cm.id)
                    if (start_date == existing_cm.start_date and end_date == existing_cm.end_date) or (
                            start_date > existing_cm.start_date and end_date < existing_cm.end_date):
                        save_new_line = False
                    elif start_date > existing_cm.start_date and end_date >= existing_cm.end_date:
                        day_to_adjust = datetime.timedelta(1)
                        # Ending existing line one day prior new start date
                        existing_cm.end_date = start_date - day_to_adjust
                        existing_cm.status = STATUS_INACTIVE
                        # There can be multiple pending lines.
                        if today < existing_cm.start_date:
                            existing_cm.status = STATUS_PENDING
                        existing_cm.save()

                    elif start_date <= existing_cm.start_date and end_date < existing_cm.end_date:
                        day_to_adjust = datetime.timedelta(1)
                        # Moving existing start date to day after new end date
                        existing_cm.start_date = end_date + day_to_adjust
                        # There can be multiple pending lines.
                        if today < existing_cm.start_date:
                            existing_cm.status = STATUS_PENDING
                        elif today > existing_cm.end_date:
                            existing_cm.status = STATUS_INACTIVE

                        existing_cm.save()
                    # for complete inner overlap i.e. do not take any action
                    elif start_date < existing_cm.start_date and end_date > existing_cm.end_date:
                        # Extend the existing line
                        existing_cm.start_date = start_date
                        existing_cm.end_date = end_date
                        if today < existing_cm.start_date:
                            existing_cm.status = STATUS_PENDING
                        elif today > existing_cm.end_date:
                            existing_cm.status = STATUS_INACTIVE
                        else:
                            existing_cm.status = STATUS_ACTIVE
                        existing_cm.save()
                        save_new_line = False

                if save_new_line:
                    if today < start_date:
                        new_status = STATUS_PENDING
                    elif today > end_date:
                        new_status = STATUS_INACTIVE
                    else:
                        new_status = STATUS_ACTIVE

                    # create ManageMembership instance
                    manage_membership = ContractMember(contract=contract,
                                                       indirect_customer_id=indirect_customer_obj[0].id,
                                                       start_date=start_date,
                                                       end_date=end_date,
                                                       status=new_status)
                    manage_membership.save()
                    newly_added_members.append(manage_membership.id)
            else:
                return ok_json(data={'message': 'Contract or Indirect Customer is not available!'})

        # # EA-1115 - Upload Member Spreadsheet - When uploading , do not delete or update members not present in the spreadsheet
        # # Change status to Inactive for those active lines which were not uploaded
        # if active_contract_members and existing_contract_members:
        #     for acm in active_contract_members:
        #         if acm.id not in existing_contract_members and acm.id not in newly_added_members:
        #             # Deleting future line if it is not uploaded
        #             if acm.status == STATUS_PENDING:
        #                 acm.delete()
        #             else:
        #                 # If Existing line is not uploaded then set it's end date to Today and status to Inactive
        #                 acm.end_date = today
        #                 acm.status = STATUS_INACTIVE
        #                 acm.save()

        return ok_json(data={'message': 'Membership has been successfully updated to the Contract!'})
    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def download_cm_list(request):
    data = {'title': 'Download Contract Membership List'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # EA-1115 - Upload Member Spreadsheet - Download empty file
    response = export_contract_membership_list()
    return response


# EA-938 - Membership import needs to create Ind. Customers
def create_indirect_customer(indc_data):
    cot = None
    if indc_data[0]['cot_id']:
        cot_line = ClassOfTrade.objects.filter(trade_class=indc_data[0]['cot_id'])
        cot = cot_line[0].id if cot_line.exists() else None
    # create indirect customer
    indirect_customer = IndirectCustomer(company_name=indc_data[0]['company_name'],
                                         location_number=indc_data[0]['location_number'],
                                         address1=indc_data[0]['address1'],
                                         address2=indc_data[0]['address2'],
                                         city=indc_data[0]['city'],
                                         state=indc_data[0]['state'],
                                         zip_code=indc_data[0]['zip_code'],
                                         cot_id=cot,
                                         gln_no=indc_data[0]['gln_no'],
                                         bid_340=indc_data[0]['bid_340'])
    indirect_customer.save()
    created_record = 1

    return created_record


def check_and_update_cot(cot, indc_id):

    if cot:
        # get cot
        cot_line = ClassOfTrade.objects.filter(trade_class=cot)
        cot_id = cot_line[0].id if cot_line.exists() else None

        indirect_customer = IndirectCustomer.objects.get(id=indc_id)

        if cot_id:
            indirect_customer.cot_id = cot_id
            indirect_customer.save()
        else:
            # EA-961 - Creating CoT if it is not there in system
            cotObj = ClassOfTrade.objects.create(trade_class=cot, description="")
            indirect_customer.cot_id = cotObj.id
            indirect_customer.save()

# EA-1225 - Membership Uploads Improvements
@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def contract_upload_membership(request):
    """
        Import Contract Membership Data
    """
    data = {'title': 'Import Contract Membership Data'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:

        check_missing = request.POST.get('check_missing', '0')
        confirm_upload = request.POST.get('confirm_upload', '0')

        required_headers = ['CONTRACT', 'MEMBER_LOCNO', 'COMPANY_NAME', 'ADDRESS1', 'ADDRESS2', 'CITY', 'STATE', 'ZIP_CODE', '340B', 'GLNNO', 'COT', 'Start_Date', 'End_Date', 'Change_Indicator']
        if check_missing == "1":

            missing_contract_list = json.loads(request.POST['missing_contract_list'])

            for mcl in missing_contract_list:
                try:
                    Contract.objects.get(number=mcl["entity"])
                except:
                    return bad_json(message="Please add all contracts to continue!")

            # Pick file from file_storage
            filename = request.POST['filename']
            file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE, filename)
            file_to_processed = file_path
        elif confirm_upload == "1":
             filename = request.POST['filename']
             file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE, filename)

             file_to_processed = file_path
        else:
            file_to_processed = request.FILES['file']

        df = pd.read_excel(file_to_processed, usecols=required_headers)
        # 1.b Confirm that the file has the correct headers
        headers = pd.read_excel(file_to_processed).columns.ravel()

        for rh in required_headers:
            if rh not in headers:
                return bad_json(message='Required headers are no present. Please check the file and upload again')

        # 1.c. Confirm that each row has a contract number and member location number filled in. Both of these fields are required to upload membership.
        # 1.d Confirm that each row in the file has one of the following Change Indicators , A, U, D
        primary_validation_errors = []
        empty_contract_id_df = df.loc[df["CONTRACT"].isnull()]
        empty_indirect_customer_df = df.loc[df["MEMBER_LOCNO"].isnull()]
        change_Indicator = df.loc[~df["Change_Indicator"].isin(['A', 'D', 'U'])]
        empty_start_date_df = df.loc[df["Start_Date"].isnull()]
        empty_end_date_df = df.loc[df["End_Date"].isnull()]

        if len(empty_contract_id_df) > 0:
            primary_validation_errors.append("CONTRACT ID column missing values.")
        if len(empty_indirect_customer_df) > 0:
            primary_validation_errors.append("MEMBER_LOCNO column missing values.")
        if len(change_Indicator) > 0:
            primary_validation_errors.append("Change_Indicator column should contain values only from A, U, D.")
        if len(empty_start_date_df) > 0:
            primary_validation_errors.append("Start_Date column missing values.")
        if len(empty_end_date_df) > 0:
            primary_validation_errors.append("End_Date column missing values.")

        if primary_validation_errors:
            return ok_json(data={'error': 'y',
                                 'error_type': 'primary_validations',
                                 'message': 'We could not processed the file due to following errors!',
                                 'errors': primary_validation_errors})

        # If Primary validations is empty go ahead
        # For EA-1436 below changes start
        if not primary_validation_errors and confirm_upload == '0':
            file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE)
            file = file_to_processed
            fs = FileSystemStorage(location=file_path)
            basename, extension = os.path.splitext(file.name)
            filename = f"c_membership_upload_{basename}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}{extension}"
            fs.save(filename, file)
            contract_list = df.groupby(['CONTRACT']).size().to_dict()
            # grpd = df.groupby(['CONTRACT ID']).size().to_frame('ctlist').to_json()
            return ok_json(data={'error': 'y',
                                     'error_type': 'confirm_validations',
                                     'message': 'Contract Unique List count',
                                     'contract_list': contract_list,
                                     'filename': filename})
        # For EA-1436 below changes end
        missing_contracts = []
        if check_missing == "0":
            # Get unique values from contracts to check if they exists in the system or not
            unique_contracts = df["CONTRACT"].unique()
            # collect those contracts which are not in the system
            for uc in unique_contracts:
                try:
                    contract_obj = Contract.objects.get(number=uc)
                except:
                    contract_obj = None
                    missing_contracts.append({
                        'type': 'Contract',
                        'entity': uc,
                    })

            # If there are missing items send that information to user and save the file to directory to process it later
            if missing_contracts:
                # file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE)
                # file = file_to_processed
                # fs = FileSystemStorage(location=file_path)
                # basename, extension = os.path.splitext(file.name)
                # filename = f"c_membership_upload_{basename}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}{extension}"
                # fs.save(filename, file)
                return ok_json(data={'error': 'y',
                                     'error_type': 'missing_error',
                                     'message': 'We could not process the file due to following missing contracts',
                                     'errors_missing_contracts': missing_contracts,
                                     'filename': filename})

        # If check_missing = 1 means user clicked on continue so process the file

        processing_errors = []
        processed_contracts = []
        processed_records = []
        for _, row in df.iterrows():
            today = datetime.datetime.now().date()

            contract_number = row.get('CONTRACT', '')
            indc_loc_number = row.get('MEMBER_LOCNO', '')
            change_Indicator = row.get('Change_Indicator', '')
            company_name = '' if pd.isnull(row.get('COMPANY_NAME')) else row.get('COMPANY_NAME')
            address1 = '' if pd.isnull(row.get('ADDRESS1')) else row.get('ADDRESS1', '')
            address2 = '' if pd.isnull(row.get('ADDRESS2')) else row.get('ADDRESS2', '')
            city = '' if pd.isnull(row.get('CITY')) else row.get('CITY', '')
            state = '' if pd.isnull(row.get('STATE')) else row.get('STATE', '')
            zip_code = '' if pd.isnull(row.get('ZIP_CODE')) else row.get('ZIP_CODE', '')
            b340 = '' if pd.isnull(row.get('340B')) else row.get('340B', '')
            glnno = '' if pd.isnull(row.get('GLNNO')) else row.get('GLNNO', '')
            cot = '' if pd.isnull(row.get('COT')) else row.get('COT', '')
            s_date = str(row.get('Start_Date', ''))
            head, sep, tail = s_date.partition(' ')
            line_start_date = head
            start_date_obj = convert_string_to_date_imports(line_start_date)
            e_date = str(row.get('End_Date', ''))
            head, sep, tail = e_date.partition(' ')
            line_end_date = head
            end_date_obj = convert_string_to_date_imports(line_end_date)

            if not cot:
                cot_id = None
            else:
                try:
                    cot_id_obj = ClassOfTrade.objects.get(trade_class=cot)
                except:
                    cot_id_obj = ClassOfTrade.objects.create(trade_class=cot)
                cot_id = cot_id_obj.id

            # check submitted dates - start date should not be > than end date
            if start_date_obj > end_date_obj:
                e_messages = []
                e_messages.append(f'Submitted Line start date is greater than end date {start_date_obj.strftime("%m/%d/%Y")}-{end_date_obj.strftime("%m/%d/%Y")}')
                processing_errors.append({
                    'type': 'invalid_dates',
                    'type_text': 'Invalid Dates',
                    'message': e_messages,
                    'contract': contract_number,
                    'indc_loc_number': indc_loc_number,
                    'company_name': company_name,
                    'address1': address1,
                    'address2': address2,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code,
                    'b340': b340,
                    'glnno': glnno,
                    'cot': cot,
                    'change_indicator': change_Indicator,
                    'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                    'submitted_end_date': end_date_obj.strftime("%m/%d/%Y"),
                })
                # Go to next line
                continue

            # Contract Validation
            try:
                contract = Contract.objects.get(number=contract_number)
            except:
                contract = None
                e_messages = ['Contract does not exists']
                processing_errors.append({
                    'type': 'contract',
                    'type_text': 'Contract Not Found',
                    'message': e_messages,
                    'contract': contract_number,
                    'indc_loc_number': indc_loc_number,
                    'company_name': company_name,
                    'address1': address1,
                    'address2': address2,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code,
                    'b340': b340,
                    'glnno': glnno,
                    'cot': cot,
                    'change_indicator': change_Indicator,
                    'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                    'submitted_end_date': end_date_obj.strftime("%m/%d/%Y")
                })
                # Go to next line
                continue

            try:
                indc_obj = IndirectCustomer.objects.get(location_number=indc_loc_number)
            except:
                indc_obj = IndirectCustomer.objects.create(location_number=indc_loc_number,
                                                           company_name=company_name,
                                                           address1=address1,
                                                           address2=address2,
                                                           city=city,
                                                           state=state,
                                                           zip_code=zip_code,
                                                           gln_no=glnno,
                                                           bid_340=b340)

            # EA-1420 - When uploading a membership file with an indirect customer that already exist the COT is not getting updated
            if cot_id:
                indc_obj.cot_id = cot_id
                indc_obj.save()


            # Overlapping Validation
            # Get overlapping lines with non active lines
            contract_member_lines_other = ContractMember.objects.filter(Q(contract=contract), Q(status__in=[STATUS_INACTIVE, STATUS_PENDING, STATUS_PROPOSED]), Q(indirect_customer=indc_obj), Q(start_date__range=[line_start_date, line_end_date]) | Q(end_date__range=[line_start_date, line_end_date]))
            contract_member_line_other = contract_member_lines_other if contract_member_lines_other.exists() else None
            if contract_member_line_other:
                e_messages = []
                for clo in contract_member_line_other:
                    e_messages.append(f'Submitted Line conflicts with existing {clo.get_status_display()} line: location : {indc_loc_number} with range {clo.start_date.strftime("%m/%d/%Y")}-{clo.end_date.strftime("%m/%d/%Y")}')

                processing_errors.append({
                    'type': 'overlapping_ranges',
                    'type_text': 'Range Conflict',
                    'message': e_messages,
                    'contract': contract_number,
                    'indc_loc_number': indc_loc_number,
                    'company_name': company_name,
                    'address1': address1,
                    'address2': address2,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code,
                    'b340': b340,
                    'glnno': glnno,
                    'cot': cot,
                    'change_indicator': change_Indicator,
                    'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                    'submitted_end_date': end_date_obj.strftime("%m/%d/%Y")
                })
                # Go to next line
                continue

            if change_Indicator == 'D':
                contract_member_lines_active = ContractMember.objects.filter(contract=contract, indirect_customer=indc_obj, status=STATUS_ACTIVE)
                contract_member_line_active = contract_member_lines_active[0] if contract_member_lines_active.exists() else None
                if contract_member_line_active:
                    if contract_member_line_active.start_date <= end_date_obj:
                        contract_member_line_active.end_date = end_date_obj

                        if today < contract_member_line_active.start_date:
                            contract_member_line_active.status = STATUS_PENDING
                        elif today > end_date_obj:
                            contract_member_line_active.status = STATUS_INACTIVE
                        else:
                            contract_member_line_active.status = STATUS_ACTIVE
                        contract_member_line_active.save()
                    else:
                        e_messages = ['Existing membership line start date greater than submitted end date']
                        processing_errors.append({
                            'type': 'membership',
                            'type_text': 'Range Conflict',
                            'message': e_messages,
                            'contract': contract_number,
                            'indc_loc_number': indc_loc_number,
                            'company_name': company_name,
                            'address1': address1,
                            'address2': address2,
                            'city': city,
                            'state': state,
                            'zip_code': zip_code,
                            'b340': b340,
                            'glnno': glnno,
                            'cot': cot,
                            'change_indicator': change_Indicator,
                            'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                            'submitted_end_date': end_date_obj.strftime("%m/%d/%Y")
                        })
                        # Go to next line
                        continue
                else:
                    e_messages = ['Could not delete because membership line does not exist']
                    processing_errors.append({
                        'type': 'membership',
                        'type_text': 'Line does not exist',
                        'message': e_messages,
                        'contract': contract_number,
                        'indc_loc_number': indc_loc_number,
                        'company_name': company_name,
                        'address1': address1,
                        'address2': address2,
                        'city': city,
                        'state': state,
                        'zip_code': zip_code,
                        'b340': b340,
                        'glnno': glnno,
                        'cot': cot,
                        'change_indicator': change_Indicator,
                        'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                        'submitted_end_date': end_date_obj.strftime("%m/%d/%Y")
                    })
                    # Go to next line
                    continue
            else:
                contract_member_lines_active = ContractMember.objects.filter(Q(contract=contract), Q(status__in=[STATUS_ACTIVE]), Q(indirect_customer=indc_obj), Q(start_date__range=[line_start_date, line_end_date]) | Q(end_date__range=[line_start_date, line_end_date]))
                contract_member_line_active = contract_member_lines_active if contract_member_lines_active.exists() else None
                if contract_member_line_active:
                    if len(contract_member_line_active) > 1:  # Means overlapping with more than 1 Active line , which is not correct
                        e_messages = []
                        for cla in contract_member_line_active:
                            e_messages.append(f'Submitted Line conflicts with existing {cla.get_status_display()} line: location : {indc_loc_number} with range {cla.start_date.strftime("%m/%d/%Y")}-{cla.end_date.strftime("%m/%d/%Y")}')

                        processing_errors.append({
                            'type': 'overlapping_ranges',
                            'type_text': 'Range Conflict',
                            'message': e_messages,
                            'contract': contract_number,
                            'indc_loc_number': indc_loc_number,
                            'company_name': company_name,
                            'address1': address1,
                            'address2': address2,
                            'city': city,
                            'state': state,
                            'zip_code': zip_code,
                            'b340': b340,
                            'glnno': glnno,
                            'cot': cot,
                            'change_indicator': change_Indicator,
                            'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                            'submitted_end_date': end_date_obj.strftime("%m/%d/%Y")
                        })
                        # Go to next line
                        continue
                    else:
                        existing_cline = contract_member_line_active[0]
                        start_date = convert_string_to_date_imports(line_start_date)
                        end_date = convert_string_to_date_imports(line_end_date)

                        if start_date > existing_cline.start_date and end_date >= existing_cline.end_date:
                            day_to_adjust = datetime.timedelta(1)
                            # Ending existing line one day prior new start date
                            existing_cline.end_date = start_date - day_to_adjust
                            existing_cline.status = STATUS_INACTIVE
                            # If new submitted line is in Pending and existing line still in active range , just change dates not status
                            if existing_cline.start_date <= today <= existing_cline.end_date:
                                existing_cline.status = STATUS_ACTIVE
                            if today < existing_cline.start_date:
                                existing_cline.status = STATUS_PENDING
                            existing_cline.save()
                        else:
                            e_messages = [f'Submitted Line conflicts with existing {existing_cline.get_status_display()} line: location : {indc_loc_number} with range {existing_cline.start_date.strftime("%m/%d/%Y")}-{existing_cline.end_date.strftime("%m/%d/%Y")}']
                            processing_errors.append({
                                'type': 'overlapping_ranges',
                                'type_text': 'Range Conflict',
                                'message': e_messages,
                                'contract': contract_number,
                                'indc_loc_number': indc_loc_number,
                                'company_name': company_name,
                                'address1': address1,
                                'address2': address2,
                                'city': city,
                                'state': state,
                                'zip_code': zip_code,
                                'b340': b340,
                                'glnno': glnno,
                                'cot': cot,
                                'change_indicator': change_Indicator,
                                'submitted_start_date': start_date_obj.strftime("%m/%d/%Y"),
                                'submitted_end_date': end_date_obj.strftime("%m/%d/%Y")
                            })
                            # Go to next line
                            continue

            if change_Indicator in ['A', 'U']:
                if today < start_date_obj:
                    new_status = STATUS_PENDING
                elif today > end_date_obj:
                    new_status = STATUS_INACTIVE
                else:
                    new_status = STATUS_ACTIVE

                # Create or Update membership line
                manage_membership = ContractMember(contract=contract, indirect_customer=indc_obj, start_date=start_date_obj, end_date=end_date_obj, status=new_status)
                manage_membership.save()

            processed_contracts.append(contract_number)

        if processed_contracts:
            exclude_to_count = []
            for pc in processed_contracts:
                if pc not in exclude_to_count:
                    processed_records.append({'contract': pc, 'processed_successfully': processed_contracts.count(pc)})
                    exclude_to_count.append(pc)

        # Remove file which was processed after clicking continue
        if check_missing == "1":
            file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE, filename)
            os.remove(file_path)

        excel_file_name = ''
        if processing_errors:
            excel_file_path, excel_file_name = export_membership_upload(data=processing_errors, company=data['company'])

        # Everything went well so return success message
        return ok_json(data={'error': 'n', 'message': 'Membership lines processed successfully!', 'processed_records': processed_records, 'processing_errors': processing_errors, 'filename': excel_file_name})

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


def contract_members_upload_delete(request, filename):
    data = {'title': 'Contract Membership upload file delete'}
    addGlobalData(request, data)

    try:
        file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_FILES_STORAGE, filename)
        os.remove(file_path)
        return ok_json()

    except Exception as ex:
        return bad_json(message=ex.__str__())