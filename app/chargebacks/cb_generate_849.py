import datetime
import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from app.management.utilities.constants import (LINE_STATUS_DISPUTED, STAGE_TYPE_PROCESSED,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_GENERATE_849, STAGE_TYPE_ARCHIVED)
from app.management.utilities.exports import export_manual_report_to_excel
from app.management.utilities.functions import (ok_json, bad_json, get_849_file_header_structure, audit_trail,
                                                get_ip_address, chargeback_audit_trails)
from app.management.utilities.globals import addGlobalData
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_849_ERM_OUT, DIR_NAME_849_ERM_MANUAL
from erms.models import (ChargeBack, ChargeBackHistory,AuditChargeBack)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
    Generate an 849 file from selected chargebacks
    Output filename is in format: 849_Wholesalername_MMDDYYYYunixtime.txt
    :param request:
    :return:
    """
    data = {'title': 'Chargebacks - Generate 849'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:

        chargebacks_ids = request.POST.get('chargebacks_ids', '')
        if not chargebacks_ids:
            return bad_json(message='Not Chargebacks Found')

        valid_cbs_to_process = []
        invalid_cbs_to_process = []

        for cb_id in chargebacks_ids.split("|"):
            try:
                cb = ChargeBack.objects.get(id=cb_id)
            except ChargeBack.DoesNotExist:
                try:
                    cb = ChargeBackHistory.objects.get(id=cb_id)
                except:
                    cb = None

            if cb:
                # Ticket EA-398
                # check all selected CBs to make sure that there are no CBs where CM fields are null if Claim Issued is > 0
                if cb.claim_issue and (not cb.accounting_credit_memo_number or not cb.accounting_credit_memo_amount or not cb.accounting_credit_memo_date):
                    invalid_cbs_to_process.append((cb.cbid, cb.number, 'Missing CM information'))

                # Validate that CBs with lines that are still pending status, dont get added to 849 if they are selected.
                elif cb.has_chargebacks_lines_with_pending_status():
                    invalid_cbs_to_process.append((cb.cbid, cb.number, 'CBLines with status Pending'))

                else:
                    valid_cbs_to_process.append(cb)

        results = []
        if valid_cbs_to_process:

            # Ticket EA-731 849 New Generate 849
            # If the EDI toggle is enabled, Create an 849 file as we currently do
            # If the EDI toggle is disabled, Create a manual report excel export, one per customer
            # If multiple CBs are selected, there is the possibility of generating 849 files for one customer, an excel for a 2nd company and another excel for a third

            # create a list of direct customers with its cbs and attrs objects (to use later in the logic)
            customers_objects_list = []
            for chargeback in valid_cbs_to_process:
                customer = chargeback.get_my_customer()

                obj_list = [x[0] for x in customers_objects_list]
                if customer in obj_list:
                    index = obj_list.index(customer)
                    customers_objects_list[index][1].append(chargeback)
                else:
                    customers_objects_list.append((customer, [chargeback]))

            # loop over the customers and cb objects list
            for elem in customers_objects_list:
                customer, chargebacks = elem[0], elem[1]
                customer_name = customer.name if customer else ''

                chargebacks_files_list = []
                if customer and customer.enabled_849:
                    #  create a file (txt) for customers with 849_enabled
                    txt_file_path, txt_file_name = create_849_txt_file(customer, chargebacks, data['company'])
                    results.append({
                        'customer': customer_name,
                        'text': f"{len(chargebacks)} chargeback{'s' if len(chargebacks) > 1 else ''} added to 849",
                        'file': txt_file_path,
                        'filename': txt_file_name,
                        'show_download_btn': 0
                    })
                    # for audit trail
                    chargebacks_files_list.append((chargebacks, txt_file_name))
                else:
                    #  create manual report (excel) file for customers with 849_disabled
                    cblines = []
                    for cb in chargebacks:
                        cblines += cb.get_my_chargeback_lines()

                    excel_file_path, excel_file_name = export_manual_report_to_excel(cblines, data['company'], customer)
                    results.append({
                        'customer': customer_name,
                        'text': f"{len(chargebacks)} chargeback{'s' if len(chargebacks) > 1 else ''} added to manual file",
                        'file': excel_file_path,
                        'filename': excel_file_name,
                        'show_download_btn': 1
                    })
                    # for audit trail
                    chargebacks_files_list.append((chargebacks, excel_file_name))

                for cbfile_elem in chargebacks_files_list:
                    filename = cbfile_elem[1]
                    chargebacks = cbfile_elem[0]
                    for chargeback in chargebacks:
                        if chargeback.stage != STAGE_TYPE_ARCHIVED:
                            chargeback.stage = STAGE_TYPE_PROCESSED
                        chargeback.is_export_849 = True
                        chargeback.export_849_date = datetime.datetime.now()
                        chargeback.save()

                        # Audit Trail
                        # audit_trail(username=request.user.username,
                        #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_GENERATE_849,
                        #             ip_address=get_ip_address(request),
                        #             entity1_name=chargeback.__class__.__name__,
                        #             entity1_id=chargeback.get_id_str(),
                        #             entity1_reference=chargeback.cbid,
                        #             filename=filename)

                        # EA -EA-1548 New Chargeback Audit
                        change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_GENERATE_849}"
                        chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                                user_email=request.user.email,
                                                change_text=change_text
                                                )
        return ok_json(data={'invalid_cbs_to_process': invalid_cbs_to_process, 'results': results})

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


def create_849_txt_file(customer, chargebacks, company):

    try:
        # vars
        today = datetime.datetime.today()
        customer_name = customer.name.replace(' ', '')
        company_id = company.get_id_str()
        company_name = company.name
        show_only_disputed_lines = company.show_only_disputed_lines_in_849

        # create file and open it in writing mode
        file_name = f"849_{customer_name}_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}.txt"

        # ticket 1382 ALL OUTBOUND files for that company will go to that folder
        outbound_folder = customer.all_outbound_folder if customer.all_outbound_folder else f"{DIR_NAME_849_ERM_OUT}"

        # file path
        file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company_id}", f"{outbound_folder}", f"{file_name}")
        file = open(file_path, "w+")

        # get 849 Header row
        header_row = get_849_file_header_structure()
        file.write(header_row)
        file.write("\n")

        for chargeback in chargebacks:

            chargebacks_lines = chargeback.get_my_chargeback_lines()
            distribution_center = chargeback.get_my_distribution_center()
            import844_obj = chargeback.get_my_import844_obj()

            # CB Header (H_XXXXXX)
            H_DocType = '849'
            H_TotalCONCount = chargebacks_lines.count()
            H_AcctNo = customer.account_number if customer else ''
            H_CBType = chargeback.type
            H_CMDate = today.strftime('%Y%m%d')
            H_CMNo = chargeback.accounting_credit_memo_number if chargeback.accounting_credit_memo_number else ''
            H_CBNumber = chargeback.number if chargeback.number else ''
            H_ResubNo = chargeback.resubmit_number if chargeback.resubmit_number else ''
            H_DistName = distribution_center.name if distribution_center else ''
            H_DistIDType = '11'
            H_DistID = distribution_center.dea_number if distribution_center else ''
            H_SuppName = company_name
            H_SuppIDType = import844_obj.header.get('H_SuppIDType', '') if import844_obj else ''
            H_SuppID = import844_obj.header.get('H_SuppID', '') if import844_obj else ''

            H_SubClaimAmt = chargeback.claim_subtotal if chargeback.claim_subtotal else '0.00'
            # Ticket EA-780
            # H_NetClaimAmt and H_AdjClaimAmt - These are reversed.
            # Swap the mappings from db so the delta amount goes into the NetClaimAmt and the Issued Amount goes into the AdjClaimAmt
            H_NetClaimAmt = chargeback.claim_adjustment if chargeback.claim_adjustment else '0.00'
            H_AdjClaimAmt = chargeback.claim_issue if chargeback.claim_issue else '0.00'

            H_ROW = f"{H_DocType}" \
                f"|{H_TotalCONCount}" \
                f"|{H_AcctNo}" \
                f"|{H_CBType}" \
                f"|{H_CMDate}" \
                f"|{H_CMNo}" \
                f"|{H_CBNumber}" \
                f"|{H_ResubNo}" \
                f"|{H_DistName}" \
                f"|{H_DistIDType}" \
                f"|{H_DistID}" \
                f"|{H_SuppName}" \
                f"|{H_SuppIDType}" \
                f"|{H_SuppID}" \
                f"|{H_SubClaimAmt}" \
                f"|{H_NetClaimAmt}" \
                f"|{H_AdjClaimAmt}"

            # initialize L_ fields
            L_ContractNo = ''
            L_ContractRejCode = ''
            L_CorContractNo = ''
            L_ShipToIDType = ''

            L_ShipToID = ''
            L_ShipToName = ''
            L_ShipToAddress = ''
            L_ShipToCity = ''
            L_ShipToState = ''
            L_ShipToZipCode = ''

            L_PAD01 = ''
            L_InvoiceLineNo = ''
            L_ItemNDCNo = ''
            L_ItemUPCNo = ''
            L_LineRejCode = ''
            L_SubContAmt = ''
            L_ContAmt = ''
            L_SubWHAmt = ''
            L_WHAmt = ''
            L_ItemQtySubSold = ''
            L_ItemQtySold = ''
            L_ItemQtySubRet = ''
            L_ItemQtyRet = ''
            L_ItemSubClaimAmt = ''
            L_ItemAdjClaimAmt = ''
            L_InvoiceNo = ''
            L_DisputeNote = ''
            L_InvoiceDate = ''

            # show_only_disputed_lines = True and there are only approved lines, we show header + |||||| ONE Time
            if show_only_disputed_lines and chargeback.has_all_approved_lines():

                L_ROW = f"{L_ContractNo}" \
                    f"|{L_ContractRejCode}" \
                    f"|{L_CorContractNo}" \
                    f"|{L_ShipToIDType}" \
                    f"|{L_ShipToID}" \
                    f"|{L_ShipToName}" \
                    f"|{L_ShipToAddress}" \
                    f"|{L_ShipToCity}" \
                    f"|{L_ShipToState}" \
                    f"|{L_ShipToZipCode}" \
                    f"|{L_PAD01}" \
                    f"|{L_InvoiceLineNo}" \
                    f"|{L_ItemNDCNo}" \
                    f"|{L_ItemUPCNo}" \
                    f"|{L_LineRejCode}" \
                    f"|{L_SubContAmt}" \
                    f"|{L_ContAmt}" \
                    f"|{L_SubWHAmt}" \
                    f"|{L_WHAmt}" \
                    f"|{L_ItemQtySubSold}" \
                    f"|{L_ItemQtySold}" \
                    f"|{L_ItemQtySubRet}" \
                    f"|{L_ItemQtyRet}" \
                    f"|{L_ItemSubClaimAmt}" \
                    f"|{L_ItemAdjClaimAmt}" \
                    f"|{L_InvoiceNo}" \
                    f"|{L_DisputeNote}" \
                    f"|{L_InvoiceDate}"

                # write row
                file.write(f"{H_ROW}|{L_ROW}\n")

            else:
                for cbline in chargebacks_lines:

                    # show_only_disputed_lines = False -> we show full detail for both approved and disputed lines or
                    # there are disputed lines show full line detail for only disputed lines and do not show approved lines
                    if not show_only_disputed_lines or cbline.line_status == LINE_STATUS_DISPUTED:

                        item = cbline.get_my_item()
                        contract = cbline.get_my_contract()
                        indirect_customer = cbline.get_my_indirect_customer()

                        L_ContractNo = cbline.submitted_contract_no

                        if contract and contract.number != cbline.submitted_contract_no:
                            L_CorContractNo = contract.number

                        L_ContractRejCode = ''
                        L_ShipToIDType = '11'

                        # Ticket EA-780
                        if indirect_customer:
                            L_ShipToID = indirect_customer.location_number
                            L_ShipToName = indirect_customer.company_name
                            L_ShipToAddress = indirect_customer.get_complete_address()
                            L_ShipToCity = indirect_customer.city
                            L_ShipToState = indirect_customer.state
                            L_ShipToZipCode = indirect_customer.zip_code
                        else:
                            L_ShipToID = import844_obj.line.get('L_ShipToID', '') if import844_obj else ''
                            L_ShipToName = import844_obj.line.get('L_ShipToName', '') if import844_obj else ''
                            L_ShipToAddress = import844_obj.line.get('L_ShipToAddress', '') if import844_obj else ''
                            L_ShipToCity = import844_obj.line.get('L_ShipToCity', '') if import844_obj else ''
                            L_ShipToState = import844_obj.line.get('L_ShipToState', '') if import844_obj else ''
                            L_ShipToZipCode = import844_obj.line.get('L_ShipToZipCode', '') if import844_obj else ''
                        L_PAD01 = ''
                        if cbline.invoice_line_no:
                            L_InvoiceLineNo = cbline.invoice_line_no

                        try:
                            L_ItemNDCNo = item.ndc
                        except:
                            # Ticket EA-792
                            L_ItemNDCNo = import844_obj.line.get('L_ItemNDCNo', '') if import844_obj else ''

                        try:
                            L_ItemUPCNo = item.upc
                        except:
                            L_ItemUPCNo = import844_obj.line.get('L_ItemUPCNo', '') if import844_obj else ''

                        L_LineRejCode = cbline.disputes_codes

                        L_SubContAmt = cbline.contract_price_submitted if cbline.contract_price_submitted else '0.00'
                        L_ContAmt = cbline.contract_price_system if cbline.contract_price_system else '0.00'
                        L_SubWHAmt = cbline.wac_submitted if cbline.wac_submitted else '0.00'
                        L_WHAmt = cbline.wac_system if cbline.wac_system else '0.00'

                        if cbline.item_qty:
                            L_ItemQtySubSold = cbline.item_qty
                            L_ItemQtySold = cbline.item_qty
                            L_ItemQtySubRet = cbline.item_qty
                            L_ItemQtyRet = cbline.item_qty

                        L_ItemSubClaimAmt = cbline.claim_amount_submitted if cbline.claim_amount_submitted else '0.00'
                        # Ticket EA-780 This should be mapped to claim_amount_issue on line
                        L_ItemAdjClaimAmt = cbline.claim_amount_issue if cbline.claim_amount_issue else '0.00'

                        if cbline.invoice_number:
                            L_InvoiceNo = cbline.invoice_number

                        # ticket EA-1371 only contain user_dispute note. Put blank if user_dispute note is blank
                        L_DisputeNote = cbline.user_dispute_note[:80] if cbline.user_dispute_note else ''

                        L_InvoiceDate = cbline.invoice_date.strftime('%Y%m%d') if cbline.invoice_date else f'{today}'

                        L_ROW = f"{L_ContractNo}" \
                            f"|{L_ContractRejCode}" \
                            f"|{L_CorContractNo}" \
                            f"|{L_ShipToIDType}" \
                            f"|{L_ShipToID}" \
                            f"|{L_ShipToName}" \
                            f"|{L_ShipToAddress}" \
                            f"|{L_ShipToCity}" \
                            f"|{L_ShipToState}" \
                            f"|{L_ShipToZipCode}" \
                            f"|{L_PAD01}" \
                            f"|{L_InvoiceLineNo}" \
                            f"|{L_ItemNDCNo}" \
                            f"|{L_ItemUPCNo}" \
                            f"|{L_LineRejCode}" \
                            f"|{L_SubContAmt}" \
                            f"|{L_ContAmt}" \
                            f"|{L_SubWHAmt}" \
                            f"|{L_WHAmt}" \
                            f"|{L_ItemQtySubSold}" \
                            f"|{L_ItemQtySold}" \
                            f"|{L_ItemQtySubRet}" \
                            f"|{L_ItemQtyRet}" \
                            f"|{L_ItemSubClaimAmt}" \
                            f"|{L_ItemAdjClaimAmt}" \
                            f"|{L_InvoiceNo}" \
                            f"|{L_DisputeNote}" \
                            f"|{L_InvoiceDate}"

                        # write row
                        file.write(f"{H_ROW}|{L_ROW}\n")

        # close file
        file.close()

        # return path
        return file_path, file_name

    except Exception as ex:
        print(ex.__str__())
        return ''


def download_849_file(request, filename):
    data = {'title': 'Chargebacks - Download 849 file'}
    addGlobalData(request, data)

    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{data['company'].get_id_str()}", f"{DIR_NAME_849_ERM_OUT}", f"{filename}")

    actual_file_path = file_path

    if not os.path.exists(file_path):
        # For manual 849 files
        actual_file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{data['company'].get_id_str()}", f"{DIR_NAME_849_ERM_MANUAL}", f"{filename}")

    with open(actual_file_path, 'rb') as f:
        response = HttpResponse(f, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = f'attachment; filename={filename}'

    return response
