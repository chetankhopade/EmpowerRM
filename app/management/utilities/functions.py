import calendar
import datetime
import json
import os
import random
import re
import shutil
import string
import uuid
from decimal import Decimal
from datetime import timezone

import dateutil.parser
from dateutil.relativedelta import relativedelta
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Q, QuerySet
from django.forms import model_to_dict
from django.http import HttpResponse
from django.template.loader import render_to_string

from app.management.utilities.constants import (STAGE_TYPE_IMPORTED, SUBSTAGE_TYPE_RESUBMISSIONS,
                                                SUBSTAGE_TYPE_DUPLICATES, SUBSTAGE_TYPE_INVALID,
                                                SUBSTAGE_TYPE_ERRORS, STAGE_TYPE_VALIDATED, SUBSTAGE_TYPE_NO_ERRORS,
                                                STAGE_TYPE_POSTED, STAGE_TYPE_PROCESSED, COLORS_LIST,
                                                REPORT_TYPE_CONTRACT, REPORT_TYPE_CHARGEBACK, REPORT_TYPE_MANUAL,
                                                SUBSTAGE_TYPE_WAITING_FOR_RESPONSE, CONTRACT_TYPES, STATUSES,
                                                SUBSTAGES_TYPES, STAGES_TYPES, STATUS_PENDING, STATUS_INACTIVE,
                                                STATUS_ACTIVE)
from empowerb.settings import (DIR_NAME_844_ERM_ERROR, FOLDERS_STRUCTURE, DIR_NAME_844_ERM_INTAKE,
                               DIR_NAME_849_ERM_OUT, DIR_NAME_FILES_STORAGE, DIR_NAME_849_ERM_HISTORY,
                               CLIENTS_DIRECTORY, EMAIL_HOST_USER)



def bad_json(message=None, error=None, extradata=None):
    data = {'result': 'bad'}
    if message:
        data.update({'message': message})
    if message and "NoneType" in message: #EA-1689 Bad JSON handler causes http error message
        data.update({'message': "Attribute Type Error"})
    if extradata:
        data.update({'extradata': extradata})
    if error:
        if error == 0:
            data.update({"mensaje": "Bad Request"})
        elif error == 1:
            data.update({"mensaje": "Error saving data"})
        elif error == 2:
            data.update({"mensaje": "Error updating data"})
        elif error == 3:
            data.update({"mensaje": "Error deleting data"})
        elif error == 4:
            data.update({"mensaje": "Permission Denied"})
        elif error == 5:
            data.update({"mensaje": "Error generating information"})
        else:
            data.update({"mensaje": "Server Error"})
    return HttpResponse(json.dumps(data), content_type="application/json")


def ok_json(data=None):
    if data:
        if 'result' not in data.keys():
            data.update({"result": "ok"})
    else:
        data = {"result": "ok"}
    return HttpResponse(json.dumps(data), content_type="application/json")


def convert_string_to_date(s):
    """
    :param s: string date with format MM/DD/YYYY
    :return: string date with format YYYY-MM-DD
    """
    try:
        return datetime.datetime(int(s[-4:]), int(s[:2]), int(s[3:5])).date()
    except Exception:
        return datetime.datetime.now().date()


def convert_string_to_date_cb(s):
    """
    :param s: string date with format: "YYYYMMDD"
    :return:
    """
    try:
        return datetime.datetime(int(s[:4]), int(s[4:6]), int(s[-2:])).date()
    except Exception:
        return None


def convert_string_to_date_imports(s):
    """
    :param s: string date with format: "YYYY-MM-DD"
    :return:
    """
    try:
        # EA-1686 :- HOTFIX: Unable to use Bulk Contract Upload - Error Index out of range
        # return datetime.datetime(int(s[:4]), int(s[5:7]), int(s[-2:])).date()
        return datetime.datetime(int(s[-4:]), int(s[:2]), int(s[3:5])).date()
    except Exception:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()


def convert_timestamp_to_datetime(s):
    """
    :param s: timestamp with format: "YYYY-MM-DDThh:mm:ss:ms"
    :return:
    """
    try:
        return dateutil.parser.parse(s)
    except Exception:
        return None


def get_string_from_timestamp(_timestamp, is_without_date_format=False):
    if is_without_date_format:
        return datetime.datetime.fromtimestamp(_timestamp)
    return datetime.datetime.fromtimestamp(_timestamp).strftime("%m/%d/%Y, %H:%M:%S")


def serialize_string_date(s):
    """
    :param s: string date with format: "YYYY-MM-DD"
    :return: string with cb format "MM/DD/YYYY"
    """
    try:
        return f'{s[5:7]}/{s[-2:]}/{s[:4]}'
    except Exception:
        return None


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_valid_date(s):
    """
    Python format   |           Possible formats in the file
    %d/%m/%Y        |       dd/MM/yyyy, d/MM/yyyy, d/M/yyyy, dd/M/yyyy
    %m/%d/%Y        |       MM/dd/yyyy, MM/d/yyyy, M/d/yyyy, M/dd/yyyy
    %Y/%m/%d        |       yyyy/MM/dd, yyyy/MM/d, yyyy/M/d, yyyy/M/dd)
    
    %d-%m-%Y        |       dd-MM-yyyy, d-MM-yyyy, d-M-yyyy, dd-M-yyyy
    %m-%d-%Y        |       MM-dd-yyyy, MM-d-yyyy, M-d-yyyy, M-dd-yyyy
    %Y-%m-%d        |       yyyy-MM-dd, yyyy-MM-d, yyyy-M-d, yyyy-M-dd)
    
    %d.%m.%Y        |       dd.MM.yyyy, d.MM.yyyy, d.M.yyyy, dd.M.yyyy
    %m.%d.%Y        |       MM.dd.yyyy, MM.d.yyyy, M.d.yyyy, M.dd.yyyy
    %Y.%m.%d        |       yyyy.MM.dd, yyyy.MM.d, yyyy.M.d, yyyy.M.dd)
    
    %d%m%Y          |       ddMMyyy
    %m%d%Y          |       MMddyyyy
    %Y%m%d          |       yyyyMMdd

    :param s: string
    :return: datetime
    """
    POSSIBLE_FORMATS = [
        '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
        '%m-%d-%Y', '%d-%m-%Y', '%Y-%m-%d',
        '%m.%d.%Y', '%d.%m.%Y', '%Y.%m.%d',
        '%m%d%Y', '%d%m%Y', '%Y%m%d'
    ]
    parsed_date = None
    for fmt in POSSIBLE_FORMATS:
        try:
            parsed_date = datetime.datetime.strptime(s, fmt).date()
            break
        except ValueError:
            pass
    return parsed_date


def get_ip_address(request):
    """
    Get the ip address
    :param request: map
    :return:
    """
    try:
        # external server
        ip_address = request.META['HTTP_X_FORWARDED_FOR']
    except Exception:
        # localhost o 127.0.0.1
        ip_address = request.META['REMOTE_ADDR']

    return ip_address


def audit_trail(**kwargs):
    """
     Audit Trail function
    fields:
        {
            [required fields]
            username: str
            ip_address: str
            action: str
            entity1_name: str
            entity1_id: str
            entity1_reference: str

            [optional fields]
            entity2_name: str
            entity2_id: str
            entity2_reference: str
            history: map
            filename: str
            db: str
        }
    :return:
    """
    from erms.models import AuditTrail

    try:
        username = kwargs['username']
        action = kwargs['action']
        ip_address = kwargs['ip_address']
        history = kwargs.get('history', None)
        filename = kwargs.get('filename', None)
        db = kwargs.get('db', None)

        # entity 1
        entity1_name = kwargs['entity1_name']
        entity1_id = kwargs['entity1_id']
        entity1_reference = kwargs['entity1_reference']

        # entity 2 (optional)
        entity2_name = kwargs.get('entity2_name', '')
        entity2_id = kwargs.get('entity2_id', '')
        entity2_reference = kwargs.get('entity2_reference', '')

        audit = AuditTrail(username=username,
                           ip_address=ip_address,
                           action=action,
                           entity=entity1_name,
                           reference=entity1_reference,
                           # entity 1 (req)
                           entity1_name=entity1_name,
                           entity1_id=entity1_id,
                           entity1_reference=entity1_reference,
                           # entity 2 (opt)
                           entity2_name=entity2_name,
                           entity2_id=entity2_id,
                           entity2_reference=entity2_reference,
                           # filename (for 849 for now, ticket 1090)
                           filename=filename,
                           # history (opt)
                           history=history)
        # for scripts (which dont have context)
        # if db:
        #     audit.save(using=db)
        # else:
        #     audit.save()

    except Exception as ex:
        print(ex.__str__())


def generate_token():
    """
    Function to generate a random token to associate it with User thru UserProfile model
    :return: string
    """
    from ermm.models import UserProfile
    code = ''
    for e in range(50):
        code += random.choice('0123456789abcdefghijklmnopqrstuvwxyz')

    # check that there is any UserProfile with that token, if so then call function recursively
    if UserProfile.objects.filter(token=code).exists():
        generate_token()

    return code


def get_list_from_txt(targetfile, delimiter="|"):
    # using generators (better than lists)
    lines = (row for row in open(targetfile))

    i = 1
    results = []
    columns = []
    for line in lines:
        line = line.strip()
        if line:
            if i == 1:
                columns = [item.strip() for item in line.split(delimiter)]
                i += 1
            else:
                # dictionary to store file data (each line)
                d = {}
                data = [item.strip() for item in line.split(delimiter)]
                for index, elem in enumerate(data):
                    d[columns[index]] = data[index]

                # append dictionary to list
                results.append(d)

    # results
    return results


# Move file to Bad folder if file is not valid (Ticket 270)
def move_file_to_bad_folder(src_path):
    try:
        txt_file = os.path.basename(src_path)
        parent_directory = os.path.dirname(src_path)
        company_directory = os.path.dirname(parent_directory)
        shutil.move(src_path, ''.join(os.path.join(company_directory, DIR_NAME_844_ERM_ERROR, txt_file)))

    except Exception as ex:
        print(ex.__str__())


def random_string(num):
    a_z = string.ascii_letters
    word = ""
    for _ in range(num):
        word += random.choice(a_z)
    return word


def random_company():
    return random.choice(['company1', 'company2', 'company3'])


def strip_special_characters_and_spaces(str):
    return re.sub('[^A-Za-z0-9]+', ' ', str).strip()


def random_number(num):
    num_str = ""
    for _ in range(num):
        num_str += str(round(random.randint(0, 11)))
    return num_str


def get_next_cbid(database):
    """
    Function to get next cb number id
    :return:
    """
    from erms.models import ChargeBack, ChargeBackHistory
    value = 1000

    # open CB
    last_cb_open_cbid = 0
    try:
        last_cb_open_cbid = ChargeBack.objects.using(database).latest('cbid').cbid
        value = last_cb_open_cbid + 1
    except Exception:
        pass

    # history CB
    try:
        last_cb_history_cbid = ChargeBackHistory.objects.using(database).latest('cbid').cbid
        if last_cb_history_cbid > last_cb_open_cbid:
            value = last_cb_history_cbid + 1
    except Exception:
        pass

    return value


def get_next_cblnid(database):
    """
    Function to get next cbline number id
    :return:
    """
    from erms.models import ChargeBackLine, ChargeBackLineHistory
    value = 1000

    # open CBLine
    last_cbline_open_cbid = 0
    try:
        last_cbline_open_cbid = ChargeBackLine.objects.using(database).latest('cblnid').cblnid
        value = last_cbline_open_cbid + 1
    except Exception:
        pass

    # history CBLine
    try:
        last_cbline_history_cbid = ChargeBackLineHistory.objects.latest('cblnid').cblnid
        if last_cbline_history_cbid > last_cbline_open_cbid:
            value = last_cbline_history_cbid + 1
    except Exception:
        pass

    return value


def get_chargeback_object(chargeback_id):
    """
    Function to get the cb object, either from CB or CBHistory table
    :param chargeback_id: str
    :return:
    """
    from erms.models import ChargeBack, ChargeBackHistory

    try:
        cb = ChargeBack.objects.get(id=chargeback_id)
    except:
        cb = None

    if not cb:
        try:
            cb = ChargeBackHistory.objects.get(id=chargeback_id)
        except:
            cb = None

    return cb


def get_chargebackline_object(chargebackline_id):
    """
    Function to get the cbline object, either from CBLine or CBLineHistory table
    :param chargebackline_id: str
    :return:
    """
    from erms.models import ChargeBackLine, ChargeBackLineHistory

    cbline = ChargeBackLine.objects.filter(id=chargebackline_id)
    if cbline.exists():
        return cbline[0]

    cbline = ChargeBackLineHistory.objects.filter(chargeback_line_id=chargebackline_id)
    if cbline.exists():
        return cbline[0]

    return None


def model_to_dict_safe(m, exclude=None):
    if not exclude:
        exclude = []
    d = model_to_dict(m, exclude=exclude)
    if 'id' not in d.keys():
        d['id'] = m.id
    for x, y in d.items():
        if type(y) == Decimal:
            d[x] = float(y)
        if type(y) == datetime.date or type(y) == datetime.datetime:
            d[x] = serialize_string_date(str(y))
        if type(y) == uuid.UUID:
            d[x] = str(y)
    return d


def valid_range(start_date, end_date):
    """
    This function test it the start date and end date, are a valid range start before end date.
    :param start_date:
    :param end_date:
    :return bool:
    """
    return True if start_date < end_date else False


def get_849_file_header_structure():
    """
    manual header for 849 document
    :return:
    """
    # H_DocType|H_TotalCONCount|H_AcctNo|H_CBType|H_CMDate|H_CMNo|H_CBNumber|H_ResubNo|H_DistName|H_DistIDType|H_DistID|H_SuppName|H_SuppIDType|H_SuppID|H_SubClaimAmt|H_NetClaimAmt|H_AdjClaimAmt|L_ContractNo|L_ContractRejCode|L_CorContractNo|L_ShipToIDType|L_ShipToID|L_ShipToName|L_ShipToAddress|L_ShipToCity|L_ShipToState|L_ShipToZipCode|L_PAD01|L_InvoiceLineNo|L_ItemNDCNo|L_ItemUPCNo|L_LineRejCode|L_SubContAmt|L_ContAmt|L_SubWHAmt|L_WHAmt|L_ItemQtySubSold|L_ItemQtySold|L_ItemQtySubRet|L_ItemQtyRet|L_ItemSubClaimAmt|L_ItemAdjClaimAmt|L_InvoiceNo|L_DisputeNote|L_InvoiceDate|
    return 'H_DocType' \
           '|H_TotalCONCount' \
           '|H_AcctNo' \
           '|H_CBType' \
           '|H_CMDate' \
           '|H_CMNo' \
           '|H_CBNumber' \
           '|H_ResubNo' \
           '|H_DistName' \
           '|H_DistIDType' \
           '|H_DistID' \
           '|H_SuppName' \
           '|H_SuppIDType' \
           '|H_SuppID' \
           '|H_SubClaimAmt' \
           '|H_NetClaimAmt' \
           '|H_AdjClaimAmt' \
           '|L_ContractNo' \
           '|L_ContractRejCode' \
           '|L_CorContractNo' \
           '|L_ShipToIDType' \
           '|L_ShipToID' \
           '|L_ShipToName' \
           '|L_ShipToAddress' \
           '|L_ShipToCity' \
           '|L_ShipToState' \
           '|L_ShipToZipCode' \
           '|L_PAD01' \
           '|L_InvoiceLineNo' \
           '|L_ItemNDCNo' \
           '|L_ItemUPCNo' \
           '|L_LineRejCode' \
           '|L_SubContAmt' \
           '|L_ContAmt' \
           '|L_SubWHAmt' \
           '|L_WHAmt' \
           '|L_ItemQtySubSold' \
           '|L_ItemQtySold' \
           '|L_ItemQtySubRet' \
           '|L_ItemQtyRet' \
           '|L_ItemSubClaimAmt' \
           '|L_ItemAdjClaimAmt' \
           '|L_InvoiceNo' \
           '|L_DisputeNote' \
           '|L_InvoiceDate'


def move_import844_to_import844_history_table(db, import844s):
    from erms.models import Import844History
    try:
        with transaction.atomic():

            import844s_history_instances = [
                Import844History(id=x.id, header=x.header, line=x.line, file_name=x.file_name) for x in import844s
            ]
            # create Import844 history records
            Import844History.objects.using(db).bulk_create(import844s_history_instances, batch_size=100)
            # delete open import 844s
            import844s.delete()

    except Exception as ex:
        print(ex.__str__())


def move_chargeback_to_chargeback_history_table(chargeback):
    from erms.models import ChargeBackHistory
    try:
        with transaction.atomic():

            chargeback_history, _ = ChargeBackHistory.objects.get_or_create(id=chargeback.id)

            chargeback_history.chargeback_id = chargeback.id
            chargeback_history.cbid = chargeback.cbid
            chargeback_history.customer_id = chargeback.customer_id
            chargeback_history.distribution_center_id = chargeback.distribution_center_id
            chargeback_history.import844_id = chargeback.import844_id
            # new fk fields
            chargeback_history.customer_ref = chargeback.customer_ref
            chargeback_history.distribution_center_ref = chargeback.distribution_center_ref
            chargeback_history.import_844_ref = chargeback.import_844_ref
            # EA-1626 Chargeback Detail shows GUID in Original CBID field
            chargeback_history.original_chargeback_id = chargeback.original_chargeback_id
            chargeback_history.document_type = chargeback.document_type
            chargeback_history.date = chargeback.date
            chargeback_history.type = chargeback.type
            chargeback_history.number = chargeback.number
            chargeback_history.resubmit_number = chargeback.resubmit_number
            chargeback_history.resubmit_description = chargeback.resubmit_description

            chargeback_history.claim_subtotal = chargeback.claim_subtotal
            chargeback_history.claim_calculate = chargeback.claim_calculate
            chargeback_history.claim_issue = chargeback.claim_issue
            chargeback_history.claim_adjustment = chargeback.claim_adjustment
            chargeback_history.total_line_count = chargeback.total_line_count

            chargeback_history.is_received_edi = chargeback.is_received_edi
            chargeback_history.accounting_credit_memo_number = chargeback.accounting_credit_memo_number
            chargeback_history.accounting_credit_memo_date = chargeback.accounting_credit_memo_date
            chargeback_history.accounting_credit_memo_amount = chargeback.accounting_credit_memo_amount

            chargeback_history.is_export_849 = chargeback.is_export_849
            chargeback_history.export_849_date = chargeback.export_849_date

            chargeback_history.is_received_edi = chargeback.is_received_edi
            chargeback_history.stage = chargeback.stage
            chargeback_history.substage = chargeback.substage
            chargeback_history.created_at = chargeback.created_at
            chargeback_history.updated_at = chargeback.updated_at

            # ticket EA-1035 When a chargeback is archived this field should be filled in with the current date/time
            chargeback_history.processed_date = datetime.datetime.now()

            chargeback_history.save()

    except Exception as ex:
        print(ex.__str__())


def move_chargebacklines_to_chargebackline_history_table(chargeback_lines):
    from erms.models import ChargeBackLineHistory
    try:
        with transaction.atomic():

            for chargeback_line in chargeback_lines:
                chargebackline_history, _ = ChargeBackLineHistory.objects.get_or_create(id=chargeback_line.id)

                chargebackline_history.cblnid = chargeback_line.cblnid
                chargebackline_history.chargeback_id = chargeback_line.chargeback_id
                chargebackline_history.chargeback_ref_id = chargeback_line.chargeback_ref_id
                chargebackline_history.chargeback_line_id = chargeback_line.get_id_str()  # maybe remove later

                chargebackline_history.submitted_contract_no = chargeback_line.submitted_contract_no
                chargebackline_history.contract_id = chargeback_line.contract_id
                chargebackline_history.indirect_customer_id = chargeback_line.indirect_customer_id
                chargebackline_history.item_id = chargeback_line.item_id
                chargebackline_history.import844_id = chargeback_line.import844_id

                # new fk fields
                chargebackline_history.contract_ref = chargeback_line.contract_ref
                chargebackline_history.indirect_customer_ref = chargeback_line.indirect_customer_ref
                chargebackline_history.item_ref = chargeback_line.item_ref
                chargebackline_history.import_844_ref = chargeback_line.import_844_ref

                chargebackline_history.invoice_number = chargeback_line.invoice_number
                chargebackline_history.invoice_date = chargeback_line.invoice_date
                chargebackline_history.invoice_line_no = chargeback_line.invoice_line_no
                chargebackline_history.invoice_note = chargeback_line.invoice_note

                chargebackline_history.item_qty = chargeback_line.item_qty
                chargebackline_history.item_uom = chargeback_line.item_uom

                chargebackline_history.wac_submitted = chargeback_line.wac_submitted
                chargebackline_history.contract_price_submitted = chargeback_line.contract_price_submitted
                chargebackline_history.wac_system = chargeback_line.wac_system
                chargebackline_history.contract_price_system = chargeback_line.contract_price_system

                chargebackline_history.claim_amount_submitted = chargeback_line.claim_amount_submitted
                chargebackline_history.claim_amount_system = chargeback_line.claim_amount_system
                chargebackline_history.claim_amount_issue = chargeback_line.claim_amount_issue
                chargebackline_history.claim_amount_adjusment = chargeback_line.claim_amount_adjusment

                chargebackline_history.line_status = chargeback_line.line_status
                chargebackline_history.approved_reason_id = chargeback_line.approved_reason_id

                chargebackline_history.user_dispute_note = chargeback_line.user_dispute_note
                chargebackline_history.action_taken = chargeback_line.action_taken
                chargebackline_history.received_with_errors = chargeback_line.received_with_errors

                chargebackline_history.disputes_codes = chargeback_line.disputes_codes
                chargebackline_history.disputes_notes = chargeback_line.disputes_notes

                # EA-1427 and EA-1418 new 6 calculated fields
                chargebackline_history.contract_price_issued = chargeback_line.contract_price_issued
                chargebackline_history.wac_price_issued = chargeback_line.wac_price_issued
                chargebackline_history.submitted_wac_extended_amount = chargeback_line.submitted_wac_extended_amount
                chargebackline_history.submitted_contract_price_extended_amount = chargeback_line.submitted_contract_price_extended_amount
                chargebackline_history.system_wac_extended_amount = chargeback_line.system_wac_extended_amount
                chargebackline_history.system_contract_price_extended_amount = chargeback_line.system_contract_price_extended_amount

                chargebackline_history.save()

    except Exception as ex:
        print(ex.__str__())


def move_chargebackdisputes_to_chargebackdispute_history_table(disputes, db):
    from erms.models import ChargeBackDisputeHistory
    try:
        with transaction.atomic():

            for dispute in disputes:
                chargebackdispute_history, _ = ChargeBackDisputeHistory.objects.using(db).get_or_create(id=dispute.id)

                chargebackdispute_history.chargeback_id = dispute.chargeback_id
                chargebackdispute_history.chargebackline_id = dispute.chargebackline_id

                # check cb_ref and cbline_ref based on ids
                if dispute.chargeback_id and not dispute.chargeback_ref_id:
                    chargebackdispute_history.chargeback_ref_id = dispute.chargeback_id
                else:
                    chargebackdispute_history.chargeback_ref_id = dispute.chargeback_ref_id if dispute.chargeback_ref_id else None

                if dispute.chargebackline_id and not dispute.chargebackline_ref_id:
                    chargebackdispute_history.chargebackline_ref_id = dispute.chargebackline_id
                else:
                    chargebackdispute_history.chargebackline_ref_id = dispute.chargebackline_ref_id if dispute.chargebackline_ref_id else None

                chargebackdispute_history.dispute_code = dispute.dispute_code
                chargebackdispute_history.dispute_note = dispute.dispute_note
                chargebackdispute_history.field_name = dispute.field_name
                chargebackdispute_history.field_value = dispute.field_value
                chargebackdispute_history.is_active = dispute.is_active
                chargebackdispute_history.save(using=db)
                # delete dispute
                dispute.delete(using=db)

                print(f"Moved CBDispute to CBHistoryDispute (ID: {chargebackdispute_history.id})")
    except Exception as ex:
        print(ex.__str__())


def get_random_color_for_charts():
    return random.choice(COLORS_LIST)


def strip_all_none_number_in_string(ndc_num):
    """
    :param ndc_num: string type
    :return: it remove everything that is not a number from the string and return
    """
    return re.sub(r'[^0-9]+', '', ndc_num)


def strip_segment_name_which_contains_digits(s):
    r = re.compile("([a-zA-Z]+)([0-9]+)")
    m = r.match(s)

    elem_name = m.group(1)
    elem_index = m.group(2)

    # for EDI Segments with letters and numbers like N1, N2, N3, N4, N9, AK1, AK2, AK3) handle those specific cases
    if elem_name == 'N':
        elem_name = f'N{elem_index[0]}'
        elem_index = elem_index[1:]

    if elem_name == 'AK':
        elem_name = f'AK{elem_index[0]}'
        elem_index = elem_index[1:]

    return elem_name, int(elem_index)  # string, number


def generate_filename_for_reports(obj_name, ext='xlsx'):
    return f"{obj_name}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}.{ext}"


def validate_844_header(src_path):
    with open(src_path, 'r') as f:
        header = f.readline().split('|')
    if header:
        return True if header[0] == 'H_DocType' and len(header) == 39 else False
    return False


def scan_dir(root, children, ui_reference, params):
    for entry in os.scandir(root):
        if entry.is_dir():
            if params["stage"] == entry.name or params["stage"] == "":
                fileInfo = {
                    "name": entry.name,
                    "ui_reference": FOLDERS_STRUCTURE[entry.name] if entry.name in FOLDERS_STRUCTURE.keys() else "",
                    "type": "directory",
                    "modified_time": get_string_from_timestamp(entry.stat().st_mtime),
                    "created_time": get_string_from_timestamp(entry.stat().st_ctime)
                }

                children.append(fileInfo)
                fileInfo["children"] = []
                scan_dir(entry, fileInfo["children"], fileInfo["ui_reference"], params)

        if entry.is_file():
            _type = root.name[:3]

            file_created_time = entry.stat().st_ctime
            file_modified_time = entry.stat().st_mtime
            if params["create_date"] <= file_created_time <= params["end_date"]:
                if _type == "fil":
                    _type = "User Gen"

                fileInfo = {
                    "name": entry.name,
                    "ext": entry.name.split('.')[1],
                    "root": root.name,
                    "ui_reference": ui_reference,
                    "path": entry.path,
                    "type": _type if _type is 849 or _type is 844 or _type or _type == "User Gen" else "",
                    "modified_time": get_string_from_timestamp(file_modified_time),
                    "created_time": get_string_from_timestamp(file_created_time),
                    "created_time_for_ordering_table": get_string_from_timestamp(file_created_time, True),
                    "extension": os.path.splitext(entry.name)[1]
                }
                children.append(fileInfo)


def create_client_dir(company_id):
    base_dirs_from_settings = (DIR_NAME_844_ERM_ERROR,
                               DIR_NAME_844_ERM_INTAKE,
                               DIR_NAME_849_ERM_OUT,
                               DIR_NAME_FILES_STORAGE,
                               DIR_NAME_849_ERM_HISTORY)
    for dir in base_dirs_from_settings:
        base_dir = os.path.join(CLIENTS_DIRECTORY, company_id, dir)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
    return True


# Function to handle in a dynamic way the DataTables server side processing
def datatable_handler(**kwargs):
    from erms.models import (ChargeBackLine, Contract, ChargeBackDispute, ChargeBack, ContractMember, ContractCustomer,
                             ContractLine, ChargeBackLineHistory, ChargeBackHistory, Item, Data852)

    # params
    request = kwargs['request']
    queryset = kwargs['queryset']
    is_export = kwargs.get('is_export', '0')
    search_fields = kwargs['search_fields']
    is_summary = kwargs.get('is_summary', True)
    contract_id = kwargs.get('contract_id', None)  # for CoTs in Contract view
    indirect_customer_id = kwargs.get('indirect_customer_id', None)  # For Products and Contracts indirect customer
    indirect_customer_option = kwargs.get('indirect_customer_option', None)  # To identify dict
    # dynamic queryset from model object
    total = queryset.count() if isinstance(queryset, QuerySet) else len(queryset)
    total_filtered = total
    is_list = False

    # searching
    search = request.POST.get('search[value]', '')
    if search:
        q_objects = Q()  # Create an empty Q object to start with
        for field_name in search_fields:
            # for ChargebackLine
            if isinstance(queryset[0], ChargeBackLine) or isinstance(queryset[0], ChargeBackLineHistory):
                # To-Do :- Remove list part once list_datatable_handler runs smoothly
                if isinstance(queryset, list):
                    is_list = True
                    if field_name == 'cblnid' or field_name == 'cbnumber':
                        queryset = [x for x in queryset if x.cblnid.__str__().__contains__(
                            search) or x.chargeback_ref.number.__str__().__contains__(search)]
                else:
                    if field_name == 'cbid':
                        q_objects |= Q(**{'chargeback_ref__cbid__icontains': search})
                    elif field_name == 'contract_id':
                        q_objects |= Q(**{'contract_ref__number__icontains': search})
                    elif field_name == 'contract_id':
                        q_objects |= Q(**{'contract_ref__number__icontains': search})
                    elif field_name == 'cbtype':
                        q_objects |= Q(**{'chargeback_ref__type__icontains': search})
                    elif field_name == 'cbnumber':
                        q_objects |= Q(**{'chargeback_ref__number__icontains': search})
                    elif field_name == 'cb_cm_number':
                        q_objects |= Q(**{'chargeback_ref__accounting_credit_memo_number__icontains': search})
                    elif field_name == 'cb_cm_date':
                        q_objects |= Q(**{'chargeback_ref__accounting_credit_memo_date__icontains': search})
                    elif field_name == 'distributor_id':
                        q_objects |= Q(**{'chargeback_ref__distributor_ref__distributor__icontains': search})
                    elif field_name == 'customer':
                        q_objects |= Q(**{'chargeback_ref__customer_ref__name__icontains': search})
                    elif field_name == 'distributor':
                        q_objects |= Q(**{'chargeback_ref__distribution_center_ref__name__icontains': search})
                    elif field_name == 'distributor_city':
                        q_objects |= Q(**{'chargeback_ref__distribution_center_ref__city__icontains': search})
                    elif field_name == 'distributor_state':
                        q_objects |= Q(**{'chargeback_ref__distribution_center_ref__state__icontains': search})
                    elif field_name == 'distributor_zipcode':
                        q_objects |= Q(**{'chargeback_ref__distribution_center_ref__zip_code__icontains': search})
                    elif field_name == 'contract_name':
                        q_objects |= Q(**{'contract_ref__description__icontains': search})
                    elif field_name == 'contract_cots':
                        q_objects |= Q(**{'contract_ref__cots__icontains': search})
                    elif field_name == 'contract_no':
                        q_objects |= Q(**{'contract_ref__number__icontains': search})
                    elif field_name == 'invoice_no':
                        q_objects |= Q(**{'invoice_number__icontains': search})
                    elif field_name == 'indirect_customer_name':
                        q_objects |= Q(**{'indirect_customer_ref__company_name__icontains': search})
                    elif field_name == 'indirect_customer_location_no':
                        q_objects |= Q(**{'indirect_customer_ref__location_number__icontains': search})
                    elif field_name == 'indirect_customer_address1':
                        q_objects |= Q(**{'indirect_customer_ref__address1__icontains': search})
                    elif field_name == 'indirect_customer_address2':
                        q_objects |= Q(**{'indirect_customer_ref__address2__icontains': search})
                    elif field_name == 'indirect_customer_city':
                        q_objects |= Q(**{'indirect_customer_ref__city__icontains': search})
                    elif field_name == 'indirect_customer_state':
                        q_objects |= Q(**{'indirect_customer_ref__state__icontains': search})
                    elif field_name == 'indirect_customer_zipcode':
                        q_objects |= Q(**{'indirect_customer_ref__zip_code__icontains': search})
                    elif field_name == 'item_ndc':
                        q_objects |= Q(**{'item_ref__ndc__icontains': search})
                    elif field_name == 'item_brand':
                        q_objects |= Q(**{'item_ref__brand__icontains': search})
                    elif field_name == 'item_description':
                        q_objects |= Q(**{'item_ref__description__icontains': search})
                    elif field_name == 'dispute_codes':
                        cblines_ids_from_disputes = [x.chargebackline_ref_id for x in
                                                     ChargeBackDispute.objects.filter(is_active=True,
                                                                                      chargebackline_ref__isnull=False,
                                                                                      dispute_code__contains=search)]
                        q_objects |= Q(**{'id__in': cblines_ids_from_disputes})
                    else:
                        q_objects |= Q(**{f'{field_name}__icontains': search})

            # for Contracts
            elif isinstance(queryset[0], Contract):
                if field_name == 'type':
                    types_ids = [x[0] for x in CONTRACT_TYPES if x[1].__contains__(search)]
                    q_objects |= Q(**{'type__in': types_ids})
                elif field_name == 'status_name':
                    status_ids = [x[0] for x in STATUSES if x[1].__contains__(search)]
                    q_objects |= Q(**{'status__in': status_ids})
                elif field_name == 'customer_name':
                    q_objects |= Q(**{'customer__name__icontains': search})
                else:
                    q_objects |= Q(**{f'{field_name}__icontains': search})

            # for ChargeBacks
            elif isinstance(queryset[0], ChargeBack):
                if field_name == 'stage':
                    stage_ids = [x[0] for x in STAGES_TYPES if x[1].__contains__(search)]
                    q_objects |= Q(**{'stage__in': stage_ids})
                elif field_name == 'substage':
                    substage_ids = [x[0] for x in SUBSTAGES_TYPES if x[1].__contains__(search)]
                    q_objects |= Q(**{'substage__in': substage_ids})
                elif field_name == 'customer':
                    q_objects |= Q(**{'customer_ref__name__icontains': search})
                elif field_name == 'distributor':
                    q_objects |= Q(**{'distribution_center_ref__name__icontains': search})
                else:
                    q_objects |= Q(**{f'{field_name}__icontains': search})

            # for ContractLine
            elif isinstance(queryset[0], ContractLine):
                if field_name == 'number':
                    q_objects |= Q(**{'contract__number__icontains': search})
                elif field_name == 'item__ndc__formatted':
                    q_objects |= Q(**{'item__ndc__icontains': search})
                else:
                    q_objects |= Q(**{f'{field_name}__icontains': search})

            # for ContractMember
            elif isinstance(queryset[0], ContractMember):
                if field_name == 'number':
                    q_objects |= Q(**{'contract__number__icontains': search})
                elif field_name == 'company_name':
                    q_objects |= Q(**{'indirect_customer__company_name__icontains': search})
                elif field_name == 'location_number':
                    q_objects |= Q(**{'indirect_customer__location_number__icontains': search})
                elif field_name == 'bid_340':
                    q_objects |= Q(**{'indirect_customer__bid_340__icontains': search})
                else:
                    q_objects |= Q(**{f'{field_name}__icontains': search})

            else:
                q_objects |= Q(**{f'{field_name}__icontains': search})

        # If it is a list we can not use filter we have queryset defined already
        if not is_list:
            queryset = queryset.filter(q_objects)
        total_filtered = queryset.count() if isinstance(queryset, QuerySet) else len(queryset)

    # ordering
    if request.POST and request.POST['order[0][column]']:
        ord_index = int(request.POST['order[0][column]'])
        ord_asc = False if request.POST['order[0][dir]'] == 'asc' else True
        ord_column = request.POST[f'columns[{ord_index}][data]']
        custom_column_sort = False

        if queryset:
            # for CBLines sorting (keep this until we moved to FK fields)
            if isinstance(queryset[0], ChargeBackLine) or isinstance(queryset[0], ChargeBackLineHistory):
                if ord_column == 'cbid':
                    queryset = sorted(queryset, key=lambda t: t.get_my_cbid(), reverse=ord_asc)
                elif ord_column == 'disputes_codes':
                    queryset = sorted(queryset, key=lambda t: t.disputes_codes, reverse=ord_asc)
                elif ord_column == 'distributor_address':
                    queryset = sorted(queryset, key=lambda t: t.get_my_distribution_center_name(), reverse=ord_asc)
                else:
                    if ord_column == 'cbtype':
                        ord_column = 'chargeback_ref__type'
                    elif ord_column == 'cbnumber':
                        ord_column = 'chargeback_ref__number'
                    elif ord_column == 'cbdate':
                        ord_column = 'chargeback_ref__date'
                    elif ord_column == 'cb_cm_number':
                        ord_column = 'chargeback_ref__accounting_credit_memo_number'
                    elif ord_column == 'cb_cm_date':
                        ord_column = 'chargeback_ref__accounting_credit_memo_date'
                    elif ord_column == 'distributor_id':
                        ord_column = 'distributor_ref__distributor'
                    elif ord_column == 'customer':
                        ord_column = "chargeback_ref__customer_ref__name"
                    elif ord_column == 'distributor':
                        ord_column = "chargeback_ref__distribution_center_ref__name"
                    elif ord_column == 'distributor_city':
                        ord_column = "chargeback_ref__distribution_center_ref__city"
                    elif ord_column == 'distributor_state':
                        ord_column = "chargeback_ref__distribution_center_ref__state"
                    elif ord_column == 'distributor_zipcode':
                        ord_column = "chargeback_ref__distribution_center_ref__zip_code"
                    # EA-1679 ERM: CB Detail report cannot sort or export
                    elif ord_column == 'distributor_address1':
                        ord_column = "chargeback_ref__distribution_center_ref__address1"
                    elif ord_column == 'distributor_address2':
                        ord_column = "chargeback_ref__distribution_center_ref__address2"
                    elif ord_column == 'cb_processed_date':
                        ord_column = "chargeback_ref__processed_date"
                    elif ord_column == 'extended_wholesaler_sales':
                        ord_column = "wac_system"
                    elif ord_column == 'extended_contract_sales':
                        ord_column = "contract_price_system"
                    # EA-1679 end here 
                    elif ord_column == 'contract_name':
                        ord_column = "contract_ref__description"
                    elif ord_column == 'contract_cots':
                        ord_column = "contract_ref__cots"
                    elif ord_column == 'contract_no':
                        ord_column = "contract_ref__number"
                    elif ord_column == 'invoice_no':
                        ord_column = "invoice_number"
                    elif ord_column == 'indirect_customer_name':
                        ord_column = "indirect_customer_ref__company_name"
                    elif ord_column == 'indirect_customer_location_no':
                        ord_column = "indirect_customer_ref__location_number"
                    elif ord_column == 'indirect_customer_address1':
                        ord_column = "indirect_customer_ref__address1"
                    elif ord_column == 'indirect_customer_address2':
                        ord_column = "indirect_customer_ref__address2"
                    elif ord_column == 'indirect_customer_city':
                        ord_column = "indirect_customer_ref__city"
                    elif ord_column == 'indirect_customer_state':
                        ord_column = "indirect_customer_ref__state"
                    elif ord_column == 'indirect_customer_zipcode':
                        ord_column = "indirect_customer_ref__zip_code"
                    elif ord_column == 'item_ndc':
                        ord_column = "item_ref__ndc"
                    elif ord_column == 'item_brand':
                        ord_column = "item_ref__brand"
                    elif ord_column == 'item_description':
                        ord_column = "item_ref__description"
                    elif ord_column == "cp_system":
                        ord_column = "contract_price_system"
                    elif ord_column == "cp_submitted":
                        ord_column = "contract_price_submitted"
                    elif ord_column == "cline_claim_amount_issue":
                        ord_column = "claim_amount_issue"
                    elif ord_column == "indirect_customer_cot":
                        ord_column = "indirect_customer_ref__cot__trade_class"
                    else:
                        ord_column = ord_column
                    # To-Do :- Remove list part once list_datatable_handler runs smoothly
                    if isinstance(queryset, list):
                        # For foreign key tables we need to get or create a function to call in python sort
                        # As order_by doesn't work on list
                        if ord_column == 'chargeback_ref__distribution_center_ref__name':
                            queryset = sorted(queryset, key=lambda t: t.get_my_distribution_center_name(),
                                              reverse=ord_asc)
                        elif ord_column == 'chargeback_ref__number':
                            queryset = sorted(queryset, key=lambda t: t.get_my_cb().number, reverse=ord_asc)
                        elif ord_column == 'chargeback_ref__date':
                            queryset = sorted(queryset, key=lambda t: t.get_my_cb().date, reverse=ord_asc)
                        elif ord_column == 'cb_claim_subtotal':
                            queryset = sorted(queryset, key=lambda t: t.get_my_cb().claim_subtotal, reverse=ord_asc)
                        elif ord_column == 'chargeback_ref__accounting_credit_memo_number':
                            queryset = sorted(queryset, key=lambda t: t.get_my_cb().accounting_credit_memo_number,
                                              reverse=ord_asc)
                        elif ord_column == 'chargeback_ref__accounting_credit_memo_date':
                            queryset = sorted(queryset, key=lambda t: t.get_my_cb().accounting_credit_memo_date,
                                              reverse=ord_asc)
                        elif ord_column == 'cb_cm_amount':
                            queryset = sorted(queryset, key=lambda t: t.get_my_cb().accounting_credit_memo_amount,
                                              reverse=ord_asc)
                        elif ord_column == 'contract_ref__number':
                            queryset = sorted(queryset, key=lambda t: t.get_my_contract().number, reverse=ord_asc)
                        elif ord_column == 'indirect_customer_ref__location_number':
                            queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer().location_number,
                                              reverse=ord_asc)
                        elif ord_column == 'item_ref__ndc':
                            queryset = sorted(queryset, key=lambda t: t.get_my_item().ndc, reverse=ord_asc)
                        elif ord_column == 'cline_corrected_chargeback_amount':
                            queryset = sorted(queryset, key=lambda t: t.get_corrected_chargeback_amount(),
                                              reverse=ord_asc)
                        elif ord_column == 'disputes_notes':
                            queryset = sorted(queryset, key=lambda t: t.disputes_notes, reverse=ord_asc)
                        elif ord_column == 'indirect_customer_ref__company_name':
                            queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer().company_name,
                                              reverse=ord_asc)
                        elif ord_column == 'indirect_customer_complete_address':
                            queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer().address1,
                                              reverse=ord_asc)
                        elif ord_column == 'indirect_customer_ref__city':
                            queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer().city,
                                              reverse=ord_asc)
                        elif ord_column == 'indirect_customer_ref__state':
                            queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer().state,
                                              reverse=ord_asc)
                        elif ord_column == 'indirect_customer_ref__zip_code':
                            queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer().zip_code,
                                              reverse=ord_asc)
                        # This else part will only work for the fields belongs to model
                        else:
                            queryset = sorted(queryset, key=lambda t: getattr(t, ord_column), reverse=ord_asc)
                    else:
                        if not ord_asc:
                            ord_column = f"-{ord_column}"
                        queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset,
                                                                                            QuerySet) else queryset

            # for Contract sorting (keep this until we moved to FK fields)
            elif isinstance(queryset[0], Contract):
                if ord_column == 'status_name':
                    queryset = sorted(queryset, key=lambda t: t.status, reverse=ord_asc)
                elif ord_column == 'customer_name':
                    queryset = sorted(queryset, key=lambda t: t.customer.name, reverse=ord_asc)
                elif ord_column == 'total_amount':
                    queryset = sorted(queryset, key=lambda t: t.get_my_revenue_by_mtd(), reverse=ord_asc)
                elif ord_column == 'units_sold':
                    queryset = sorted(queryset, key=lambda t: t.get_my_units_sold_by_mtd(), reverse=ord_asc)
                elif ord_column == 'indirect_purchasers':
                    queryset = sorted(queryset, key=lambda t: t.get_my_indirect_purchasers_by_mtd(), reverse=ord_asc)
                else:
                    if not ord_asc:
                        ord_column = f"-{ord_column}"
                    queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset,
                                                                                        QuerySet) else queryset

            # for Products sorting
            elif isinstance(queryset[0], Item):
                if ord_column == 'ndc_formatted':
                    ord_column = 'ndc'
                elif ord_column == 'units_sold':
                    queryset = sorted(queryset,
                                      key=lambda t: t.get_my_items_sold_by_cblines_history(query_range('MTD')),
                                      reverse=ord_asc)
                elif ord_column == 'total_amount':
                    queryset = sorted(queryset, key=lambda t: t.get_my_revenue_by_cblines_history(query_range('MTD')),
                                      reverse=ord_asc)
                elif ord_column == 'total_sale':
                    queryset = sorted(queryset, key=lambda t: t.get_my_revenue_by_cblines_history(), reverse=ord_asc)
                else:
                    if not ord_asc:
                        ord_column = f"-{ord_column}"
                    queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset,
                                                                                        QuerySet) else queryset
            # for Chargeback Processing view
            elif isinstance(queryset[0], ChargeBack) or isinstance(queryset[0], ChargeBackHistory):
                if ord_column == 'customer':
                    ord_column = "customer_ref__name"
                elif ord_column == 'distributor':
                    ord_column = "distribution_center_ref__name"
                elif ord_column == 'cbnumber':
                    ord_column = 'number'
                elif ord_column == 'request':
                    ord_column = 'claim_subtotal'
                elif ord_column == 'issued':
                    ord_column = 'claim_issue'
                elif ord_column == 'imported':
                    ord_column = 'created_at'
                else:
                    ord_column = ord_column
                # EA-1103 - Add the ability to sort all columns on the Search page and add paging
                # For CB Search the querysets are chained so it's a list and not a queryset
                # To-Do :- Remove list part once list_datatable_handler runs smoothly
                if isinstance(queryset, list):
                    # For foreign key tables we need to get or create a function to call in python sort
                    # As order_by doesn't work on list
                    if ord_column == 'customer_ref__name':
                        queryset = sorted(queryset, key=lambda t: t.get_my_customer_name(), reverse=ord_asc)
                    elif ord_column == 'distribution_center_ref__name':
                        queryset = sorted(queryset, key=lambda t: t.get_my_distribution_center_name(), reverse=ord_asc)
                    # This else part will only work for the fields belongs to model
                    else:
                        queryset = sorted(queryset, key=lambda t: getattr(t, ord_column), reverse=ord_asc)
                else:
                    if not ord_asc:
                        ord_column = f"-{ord_column}"
                    queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset,
                                                                                        QuerySet) else queryset

            # for ContractMember
            elif isinstance(queryset[0], ContractMember):
                if ord_column == 'location_number':
                    ord_column = "indirect_customer__location_number"
                elif ord_column == 'bid_340':
                    ord_column = "indirect_customer__bid_340"
                elif ord_column == 'company_name':
                    ord_column = 'indirect_customer__company_name'

                if not ord_asc:
                    ord_column = f"-{ord_column}"
                queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset, QuerySet) else queryset

            # For Contract Manage Server
            elif isinstance(queryset[0], ContractCustomer):
                if ord_column == 'name':
                    ord_column = "customer__name"
                elif ord_column == 'address':
                    ord_column = "customer__address1"
                elif ord_column == 'city':
                    ord_column = 'customer__city'
                elif ord_column == 'state':
                    ord_column = 'customer__state'
                elif ord_column == 'zip_code':
                    ord_column = 'customer__zip_code'
                elif ord_column == 'cb_amount':
                    queryset = sorted(queryset, key=lambda t: t.contract.get_contract_cb_count_by_server(t.customer), reverse=ord_asc)
                    custom_column_sort = True
                elif ord_column == 'cb_lines':
                    queryset = sorted(queryset, key=lambda t: t.contract.get_contract_cbline_count_by_server(t.customer), reverse=ord_asc)
                    custom_column_sort = True
                elif ord_column == 'units_sold':
                    queryset = sorted(queryset, key=lambda t: t.contract.get_contract_units_sold_by_server(t.customer), reverse=ord_asc)
                    custom_column_sort = True

                if not ord_asc:
                    ord_column = f"-{ord_column}"
                if not custom_column_sort:
                    queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset, QuerySet) else queryset

            # For Contract Lines
            elif isinstance(queryset[0], ContractLine):
                if ord_column == 'name':
                    ord_column = "contract__description"
                if ord_column == 'number':
                    ord_column = "contract__number"
                if ord_column == 'item__ndc__formatted':
                    ord_column = "item__ndc"
                if ord_column == 'ctype':
                    ord_column = "contract__type"
                if not ord_asc:
                    ord_column = f"-{ord_column}"
                queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset, QuerySet) else queryset

            elif isinstance(queryset[0], Data852):
                if ord_column == 'L_item_id_description':
                    queryset = sorted(queryset, key=lambda t: t.get_my_item_description(), reverse=ord_asc)
                if not ord_asc:
                    ord_column = f"-{ord_column}"
                queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset, QuerySet) else queryset
            else:
                if ord_column == 'ndc_formatted':
                    ord_column = 'ndc'
                if not ord_asc:
                    ord_column = f"-{ord_column}"
                queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset, QuerySet) else queryset

    # pagination
    start = int(request.POST.get('start', 0))
    length = int(request.POST.get('length', -1))
    if length > 0:
        queryset = queryset[start:start + length]

    # for exports (excel, csv)
    if is_export == '1':
        return queryset

    # for ui datatables
    else:
        # specific for CoT / Alias in Contracts
        if contract_id:
            data = [elem.dict_for_datatable_in_contracts(contract_id) for elem in queryset]
        # specific for Indirect Customers - Products and Contracts
        elif indirect_customer_id and indirect_customer_option:
            if indirect_customer_option == "item":
                data = [elem.dict_for_datatable_items_in_indc(indirect_customer_id) for elem in queryset]
            # indirect_customer_option ins not item then it should be contract
            else:
                data = [elem.dict_for_datatable_contracts_in_indc(indirect_customer_id) for elem in queryset]
        # all others queries
        else:
            data = [elem.dict_for_datatable(is_summary) for elem in queryset]

        # response
        return {
            'data': data,
            'recordsTotal': total,
            'recordsFiltered': total_filtered,
        }


# Function to handle in a dynamic way the DataTables server side processing where queryset is list chained
def list_datatable_handler(**kwargs):
    from erms.models import ChargeBackLine, ChargeBack, ChargeBackLineHistory, ChargeBackHistory

    # params
    request = kwargs['request']
    queryset = kwargs['queryset']
    search_fields = kwargs['search_fields']
    is_summary = kwargs.get('is_summary', True)

    total = queryset.count() if isinstance(queryset, QuerySet) else len(queryset)
    total_filtered = total

    # This is strictly for list chained querysets, pass search_fields list carefully from controller
    # searching
    search = request.POST.get('search[value]', '')
    if search and search_fields:
        if isinstance(queryset[0], ChargeBackLine) or isinstance(queryset[0], ChargeBackLineHistory):
            if isinstance(queryset, list):
                queryset = [x for x in queryset if
                            x.cblnid.__str__().__contains__(search) or x.chargeback_ref.number.__str__().__contains__(
                                search) or x.chargeback_ref.distribution_center_ref.__str__().__contains__(
                                search) or x.contract_ref.__str__().__contains__(
                                search) or x.indirect_customer_ref.__str__().__contains__(
                                search) or x.indirect_customer_ref.company_name.__str__().__contains__(
                                search) or x.item_ref.__str__().__contains__(search)]

        total_filtered = queryset.count() if isinstance(queryset, QuerySet) else len(queryset)

    # ordering
    if request.POST and request.POST['order[0][column]']:
        ord_index = int(request.POST['order[0][column]'])
        ord_asc = False if request.POST['order[0][dir]'] == 'asc' else True
        ord_column = request.POST[f'columns[{ord_index}][data]']

        if queryset:
            if isinstance(queryset[0], ChargeBackLine) or isinstance(queryset[0], ChargeBackLineHistory):
                # For foreign key tables we need to get or create a function to call in python sort
                # As order_by doesn't work on list
                if ord_column == 'cbid':
                    queryset = sorted(queryset, key=lambda t: t.get_my_cbid(), reverse=ord_asc)
                elif ord_column == 'disputes_codes':
                    queryset = sorted(queryset, key=lambda t: t.disputes_codes, reverse=ord_asc)
                elif ord_column == 'distributor_address':
                    queryset = sorted(queryset, key=lambda t: t.get_my_distribution_center_address(), reverse=ord_asc)
                elif ord_column == 'distributor':
                    queryset = sorted(queryset, key=lambda t: t.get_my_distribution_center_name(), reverse=ord_asc)
                elif ord_column == 'cbnumber':
                    queryset = sorted(queryset, key=lambda t: t.get_my_cb_number(), reverse=ord_asc)
                elif ord_column == 'cbdate':
                    queryset = sorted(queryset, key=lambda t: t.get_my_cb_date(), reverse=ord_asc)
                elif ord_column == 'cb_claim_subtotal':
                    queryset = sorted(queryset, key=lambda t: t.get_my_cb_claim_subtotal(), reverse=ord_asc)
                elif ord_column == 'cb_cm_number':
                    queryset = sorted(queryset, key=lambda t: t.get_my_accounting_credit_memo_number(), reverse=ord_asc)
                elif ord_column == 'cb_cm_date':
                    queryset = sorted(queryset, key=lambda t: t.get_my_accounting_credit_memo_date(), reverse=ord_asc)
                elif ord_column == 'cb_cm_amount':
                    queryset = sorted(queryset, key=lambda t: t.get_my_accounting_credit_memo_amount(), reverse=ord_asc)
                elif ord_column == 'accepted_status':
                    queryset = sorted(queryset, key=lambda t: t.get_my_accepted_status(), reverse=ord_asc)
                elif ord_column == 'contract_no':
                    queryset = sorted(queryset, key=lambda t: t.get_my_contract_number(), reverse=ord_asc)
                elif ord_column == 'indirect_customer_location_no':
                    queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer_location_no(), reverse=ord_asc)
                elif ord_column == 'item_ndc':
                    queryset = sorted(queryset, key=lambda t: t.get_my_item_ndc(), reverse=ord_asc)
                elif ord_column == 'cline_corrected_chargeback_amount':
                    queryset = sorted(queryset, key=lambda t: t.get_corrected_chargeback_amount(), reverse=ord_asc)
                elif ord_column == 'disputes_notes':
                    queryset = sorted(queryset, key=lambda t: t.disputes_notes, reverse=ord_asc)
                elif ord_column == 'indirect_customer_name':
                    queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer_name(), reverse=ord_asc)
                elif ord_column == 'indirect_customer_complete_address':
                    queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer_address1(), reverse=ord_asc)
                elif ord_column == 'indirect_customer_city':
                    queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer_city(), reverse=ord_asc)
                elif ord_column == 'indirect_customer_state':
                    queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer_state(), reverse=ord_asc)
                elif ord_column == 'indirect_customer_zipcode':
                    queryset = sorted(queryset, key=lambda t: t.get_my_indirect_customer_zipcode(), reverse=ord_asc)
                elif ord_column == 'wac_system':
                    queryset = sorted(queryset, key=lambda t: t.get_my_wac_system(), reverse=ord_asc)
                elif ord_column == 'cp_system':
                    queryset = sorted(queryset, key=lambda t: t.get_my_cp_system(), reverse=ord_asc)
                elif ord_column == 'cline_claim_amount_issue':
                    queryset = sorted(queryset, key=lambda t: t.get_my_claim_amount_issue(), reverse=ord_asc)
                elif ord_column == 'invoice_no':
                    queryset = sorted(queryset, key=lambda t: t.get_my_invoice_number(), reverse=ord_asc)
                else:
                    queryset = sorted(queryset, key=lambda t: getattr(t, ord_column), reverse=ord_asc)

            # for Chargeback Processing view
            elif isinstance(queryset[0], ChargeBack) or isinstance(queryset[0], ChargeBackHistory):
                if ord_column == 'customer':
                    ord_column = "customer_ref__name"
                elif ord_column == 'distributor':
                    ord_column = "distribution_center_ref__name"
                elif ord_column == 'cbnumber':
                    ord_column = 'number'
                elif ord_column == 'request':
                    ord_column = 'claim_subtotal'
                elif ord_column == 'issued':
                    ord_column = 'claim_issue'
                elif ord_column == 'imported':
                    ord_column = 'created_at'
                else:
                    ord_column = ord_column
                # EA-1103 - Add the ability to sort all columns on the Search page and add paging
                # For CB Search the querysets are chained so it's a list and not a queryset
                if isinstance(queryset, list):
                    # For foreign key tables we need to get or create a function to call in python sort
                    # As order_by doesn't work on list
                    if ord_column == 'customer_ref__name':
                        queryset = sorted(queryset, key=lambda t: t.get_my_customer_name(), reverse=ord_asc)
                    elif ord_column == 'distribution_center_ref__name':
                        queryset = sorted(queryset, key=lambda t: t.get_my_distribution_center_name(), reverse=ord_asc)
                    # This else part will only work for the fields belongs to model
                    else:
                        queryset = sorted(queryset, key=lambda t: getattr(t, ord_column), reverse=ord_asc)
                else:
                    if not ord_asc:
                        ord_column = f"-{ord_column}"
                    queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset,
                                                                                        QuerySet) else queryset

            else:
                if ord_column == 'ndc_formatted':
                    ord_column = 'ndc'
                if not ord_asc:
                    ord_column = f"-{ord_column}"
                queryset = queryset.order_by(ord_column) if queryset and isinstance(queryset, QuerySet) else queryset

    # pagination
    start = int(request.POST.get('start', 0))
    length = int(request.POST.get('length', -1))
    if length > 0:
        queryset = queryset[start:start + length]

    data = [elem.dict_for_datatable(is_summary) for elem in queryset]

    # response
    return {
        'data': data,
        'recordsTotal': total,
        'recordsFiltered': total_filtered,
    }


def get_stage_and_substage_based_on_key(key):
    """
    return stage and substage tuple based on key to filter cbs
    :param key: str
    :return: tuple
    """
    objects = {
        "resubmissions": (STAGE_TYPE_IMPORTED, SUBSTAGE_TYPE_RESUBMISSIONS),  # Resubmissions: Stage 1 Substage 3
        "duplicates": (STAGE_TYPE_IMPORTED, SUBSTAGE_TYPE_DUPLICATES),  # Duplicate: Stage 1 substage 2
        "invalids": (STAGE_TYPE_IMPORTED, SUBSTAGE_TYPE_INVALID),  # Invalid: Stage 1 Substage 4
        "issues": (STAGE_TYPE_IMPORTED, SUBSTAGE_TYPE_ERRORS),  # Import Issues: Stage 1 Substage 1
        "failed_validations": (STAGE_TYPE_VALIDATED, SUBSTAGE_TYPE_ERRORS),  # Validation Failed: Stage 2 Substage 1
        "generate_849": (STAGE_TYPE_POSTED, SUBSTAGE_TYPE_NO_ERRORS),  # Generate 849: Stage 3 Substage 0
        "archive": (STAGE_TYPE_PROCESSED, SUBSTAGE_TYPE_NO_ERRORS),  # Archive: Stage 4 Substage 0
        "ready_to_post": (STAGE_TYPE_VALIDATED, SUBSTAGE_TYPE_NO_ERRORS,
                          STAGE_TYPE_POSTED, SUBSTAGE_TYPE_WAITING_FOR_RESPONSE,
                          STAGE_TYPE_POSTED, SUBSTAGE_TYPE_ERRORS),
        # Ready to Post: Stage 2 Substage 0 OR Stage 3 Substage 5 OR Stage 3 Substage 1

    }
    return objects[key]


def query_range(key):
    """
    return data date range list based on key range text
    :param key: data range selection
    :return: obj date range
    """
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)

    dt = datetime.date.today()

    year = today.year
    currentYear = today.year
    last_month = today.month - 1
    if not last_month:
        year = today.year - 1
        last_month = 12

    _, last_month_days = calendar.monthrange(year, last_month)

    start_this_week = today - datetime.timedelta(days=today.weekday())
    end_this_week = start_this_week + datetime.timedelta(days=6)
    start_last_week = start_this_week - datetime.timedelta(weeks=1)
    end_last_week = start_last_week + datetime.timedelta(days=6)

    # EA- 1522 - HOTFIX: Add "Quarter" filter options to the Report Builder Run Parameters
    current_quarter_start_date = datetime.date(dt.year, (dt.month - 1) // 3 * 3 + 1, 1)
    last_quarter_start_date = previous_quarter_start_date(today)
    last_quarter_end_date = previous_quarter_end_date(today)

    ranges = {
        "TD": [today.date(), today.date()],  # Today
        "YD": [yesterday.date(), yesterday.date()],  # Yesterday
        "LM": [datetime.datetime(year, last_month, 1).date(), datetime.datetime(year, last_month, last_month_days).date()],  # Last Month
        "WTD": [start_this_week.date(), today.date()],  # Week To Date
        "MTD": [datetime.datetime(currentYear, today.month, 1).date(), today.date()],  # Month To Date
        "YTD": [datetime.datetime(currentYear, 1, 1).date(), today.date()],  # Year To Date
        "TW": [start_this_week.date(), end_this_week.date()],  # This Week
        "LW": [start_last_week.date(), end_last_week.date()],  # Last Week
        "LY": [datetime.datetime(currentYear - 1, 1, 1).date(), datetime.datetime(currentYear - 1, 12, 31).date()],  # Last Year
        "LQ": [last_quarter_start_date, last_quarter_end_date],
        "QTD": [current_quarter_start_date, today.date()]
    }

    return ranges[key]


def scheduled_reports_handler(report, db, from_web):
    from erms.models import ChargeBackLineHistory
    try:

        rtype = report.report_type
        drange = report.data_range

        output = None
        filename = ''
        recipient_emails_list = []
        for recipient in report.get_my_related_processing_recipients():
            if recipient.email:
                recipient_emails_list.append(recipient.email)

        if rtype == REPORT_TYPE_CONTRACT:
            filename = generate_filename_for_reports(obj_name='contracts')

        if rtype == REPORT_TYPE_MANUAL:
            filename = generate_filename_for_reports(obj_name='manual_report')

        if rtype == REPORT_TYPE_CHARGEBACK:
            execute = False
            if from_web:
                execute = True
            else:
                # implement schedule based on (hrs, mins, monthday, month, weekday)
                now = datetime.datetime.now()

                if report.hour and report.minute:
                    # hour (0 - 23) minute (0 - 59)
                    execute = now.hour == report.hour and now.minute == report.minute

                if report.monthday:
                    # monthday (1 - 31)
                    execute = now.day == report.monthday

                if report.month:
                    # month (1 - 12)
                    execute = now.month == report.month

                if report.weekday:
                    # weekday (0 - 6) (sunday=0)
                    execute = now.today().isoweekday() == report.weekday

            if execute:
                print("Generating Chargeback Report ...")
                filename = generate_filename_for_reports(obj_name='chargebacks_report')
                cblines_history = ChargeBackLineHistory.objects.using(db).filter(
                    updated_at__date__range=query_range(drange))
                output = None
            else:
                print("No Execution based on schedule")

        if output and recipient_emails_list:
            email = EmailMessage()
            email.subject = 'Scheduled Report - EmpowerRM'
            email.body = render_to_string('emails/scheduled_reports.html', {'report': report})
            email.from_email = EMAIL_HOST_USER
            email.to = recipient_emails_list
            email.content_subtype = "html"  # html content
            email.attach(filename, output.getvalue(), 'application/vnd.ms-excel')
            email.send()
            return recipient_emails_list

        return []
    except Exception as ex:
        print(ex.__str__())
        return []


def generate_bulk_id(db):
    """
    Function to generate a bulk_id for import844 process
    :return:
    """
    from erms.models import Import844

    bulk_id = uuid.uuid4().__str__()
    # check that bulk_id does not already exist, if so then call function recursively
    if Import844.objects.using(db).filter(bulk_id=bulk_id).exists():
        generate_bulk_id(db)

    return bulk_id


def generate_import844_id(db):
    """
    Function to generate a import844 uuid for import import process
    :return:
    """
    from erms.models import Import844

    import844_id = uuid.uuid4().__str__()
    # check that chargebackid does not already exist, if so then call function recursively
    if Import844.objects.using(db).filter(id=import844_id).exists():
        generate_import844_id(db)

    return import844_id


def generate_chargeback_id(db):
    """
    Function to generate a chargeback uuid for import chargeback process
    :return:
    """
    from erms.models import ChargeBack

    chargeback_id = uuid.uuid4().__str__()
    # check that chargebackid does not already exist, if so then call function recursively
    if ChargeBack.objects.using(db).filter(id=chargeback_id).exists():
        generate_chargeback_id(db)

    return chargeback_id


def generate_chargebackline_id(db):
    """
    Function to generate a chargebackline uuid for import chargeback process
    :return:
    """
    from erms.models import ChargeBackLine

    chargebackline_id = uuid.uuid4().__str__()
    # check that chargebackid does not already exist, if so then call function recursively
    if ChargeBackLine.objects.using(db).filter(id=chargebackline_id).exists():
        generate_chargebackline_id(db)

    return chargebackline_id


def get_contract_status_from_date_ranges(start_date, end_date):
    today = datetime.datetime.now().date()
    if start_date > today:
        status = STATUS_PENDING
    elif end_date < today:
        status = STATUS_INACTIVE
    else:
        status = STATUS_ACTIVE
    return status


def get_dates_for_report_filter(start_date, end_date, source=''):
    """
    return list of start and end date
    :param start_date: start date , end_date: end_date
    :param source e.g -3d , 2d, 2w,etc.
    """
    result = [start_date, end_date]
    try:
        d = 1  # d = day
        w = 7  # w = week (7 days)
        m = 30 # m = month (30 days)

        is_negative = False

        if source:
            if source.startswith('-'):
                is_negative = True
                source = source[1:]  # removing the first characters

            constraint = source[-1] if source[-1] in ['d', 'w', 'm'] else 'd'  # default d , if it is something different
            source = int(source[:-1])  # removing last character of the string and getting middle digits

            days_to_calculate = d * source
            if constraint == 'w':
                days_to_calculate = w * source  # 2w i.e 2 * 7 = 14 days
            elif constraint == 'm':
                days_to_calculate = m * source  # 2m i.e 2 * 30 = 60 days
            day_to_adjust = datetime.timedelta(days_to_calculate)
            # Extend date range as per sign
            if is_negative:
                start_date = start_date - day_to_adjust
            else:
                end_date = end_date + day_to_adjust

            return [start_date, end_date]

        else:
            return result
    except:
        return result


def dates_exceeds_range(start_date, end_date, max_years=2):
    """
        return True or False
        :param start_date: start date , end_date: end_date (python date objects)
        :param max_years: max year difference between dates.
    """
    try:
        difference_in_years = relativedelta(end_date, start_date).years
        if difference_in_years >= max_years:
            return True
        else:
            return False
    except:
        return False


def previous_quarter_start_date(today):
    if today.month < 4:
        return datetime.date(today.year - 1, 10, 1)
    elif today.month < 7:
        return datetime.date(today.year, 1, 1)
    elif today.month < 10:
        return datetime.date(today.year, 4, 1)
    return datetime.date(today.year, 7, 1)


def previous_quarter_end_date(today):
    if today.month < 4:
        return datetime.date(today.year - 1, 12, 31)
    elif today.month < 7:
        return datetime.date(today.year, 3, 31)
    elif today.month < 10:
        return datetime.date(today.year, 6, 30)
    return datetime.date(today.year, 9, 30)


def contract_audit_trails(**kwargs):
    """
         Contract Audit Trail function
        fields:
            {
                contract: FK (Contract)
                user_email: str
                date: date
                time: time format("HH:MM")
                change_type: str(header, line, server, alias)
                field_name: str(which gets changed)
                product: FK (Item)
                change_text: str
            }
        :return:
        """
    from erms.models import ContractAuditTrail, Contract, Item
    try:
        contract_id = kwargs['contract']
        product_id = kwargs.get('product', None)
        user_email = kwargs['user_email']
        change_type = kwargs['change_type']
        field_name = kwargs['field_name']
        change_text = kwargs['change_text']
        db = kwargs.get('db', None)

        # EA-1701 - Contract History page missing data.
        if change_type == 'line' and not field_name:
            field_name = "Multiple Fields"

        try:
            if db:
                contract = Contract.objects.using(db).get(id=contract_id)
            else:
                contract = Contract.objects.get(id=contract_id)
        except:
            contract = None


        product = None
        if change_type == 'line' and product_id:
            try:
                if db:
                    product = Item.objects.using(db).get(id=product_id)
                else:
                    product = Item.objects.get(id=product_id)
            except:
                product = None

        contract_audit = ContractAuditTrail(contract=contract,
                                            product=product,
                                            user_email=user_email,
                                            change_type=change_type,
                                            field_name=field_name,
                                            change_text=change_text,
                                            date=datetime.datetime.now(timezone.utc),
                                            time=datetime.datetime.now(timezone.utc)
                                            )
        # for scripts (which dont have context)
        if db:
            contract_audit.save(using=db)
        else:
            contract_audit.save()

    except Exception as ex:
        print(ex.__str__())

def chargeback_audit_trails(**kwargs):
    """
         Chargeback Audit Trail function
        fields:
            {
                cbid: FK (Chargeback)
                cblnid: int
                user_email: str
                date: date
                time: time format("HH:MM")
                change_text: str
            }
        :return:
        """
    from erms.models import AuditChargeBack, ChargeBack
    try:
        cbid = kwargs['cbid']
        cblnid = kwargs.get('cblnid', None)
        user_email = kwargs['user_email']
        change_text = kwargs['change_text']
        db = kwargs.get('db', None)
        try:
            chargeback = ChargeBack.objects.get(id=cbid)
        except:
            chargeback = None

        chargeback_audit = AuditChargeBack( cbid=chargeback,
                                            cblnid=cblnid,
                                            user_email=user_email,
                                            change_text=change_text,
                                            date=datetime.datetime.now(timezone.utc),
                                            time=datetime.datetime.now(timezone.utc)
                                            )
        # for scripts (which dont have context)
        if db:
            chargeback_audit.save(using=db)
        else:
            chargeback_audit.save()

    except Exception as ex:
        print(ex.__str__())

def is_valid_location_number(location_number):
        is_valid_dea_number = False
        try:
            if hasDigits(location_number) == True:
                    is_valid_dea_number= True

            return is_valid_dea_number
        except:
            return False


def hasDigits(s):
     return any( 48 <= ord(char) <= 57 for char in s)