import json
import uuid
import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (STAGE_TYPE_IMPORTED, SUBSTAGE_TYPE_NO_ERRORS, LINE_STATUS_PENDING,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_CREATE_MANUAL_CB,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_UPDATE_MANUAL_CB,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_RERUN_VALIDATION)
from app.management.utilities.functions import (ok_json, bad_json, is_valid_date, get_next_cbid, get_next_cblnid,
                                                model_to_dict_safe, audit_trail, get_ip_address,chargeback_audit_trails)
from app.management.utilities.globals import addGlobalData
from app.tasks import import_validations_function

from erms.models import (ChargeBack, ChargeBackLine, IndirectCustomer, Import844History, DirectCustomer, Item,
                         DistributionCenter, Contract)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def cb_create(request):
    """
        Company's Chargeback - Manual Creation
    """
    data = {'title': 'Chargeback - Manual Creation'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # activate menu option
    data['menu_option_chargebacks'] = True

    try:
        with transaction.atomic():

            # Get json data from ajax call for CB and CBLine
            obj = json.loads(request.POST['payload'])

            # chargeback number (needed by import844 and then in main query in import validations)
            cb_number = obj['cb_number']

            # company cbid counter
            cbid = data['company'].cbid_counter if data['company'].cbid_counter else get_next_cbid(data['db_name'])

            # Ticket 1208 create a import844 to associate with CB
            bulk_id = uuid.uuid4().__str__()
            file_name = f"Manual_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}"
            import_844h = Import844History.objects.create(bulk_id=bulk_id, file_name=file_name)

            # update import844 obj to avoid future errors in validations process
            try:
                distribution_center = DistributionCenter.objects.get(id=obj['cb_distributor_id'])
                dea_number = distribution_center.dea_number
            except:
                distribution_center = None
                dea_number = ''

            try:
                direct_customer = DirectCustomer.objects.get(id=obj['cb_customer_id'])
                account_number = direct_customer.account_number
            except:
                direct_customer = None
                account_number = ''

            # EA-1450 - 1.8 Unable to edit a manual chargeback because comma in submitted amount
            obj['cb_claim_subtotal'] = obj['cb_claim_subtotal'].replace(",", "") if obj['cb_claim_subtotal'] else None
            claim_subtotal = Decimal(obj['cb_claim_subtotal']) if obj['cb_claim_subtotal'] else None

            # needed for import validations function
            import_844h.header['H_CBNumber'] = cb_number
            import_844h.header['H_DocType'] = '844'
            import_844h.header['H_CBDate'] = obj['cb_date']
            import_844h.header['H_AcctNo'] = account_number
            import_844h.header['H_DistID'] = dea_number
            import_844h.header['H_CBType'] = obj['cb_type']
            import_844h.header['H_SubClaimAmt'] = float(claim_subtotal) if claim_subtotal else ''
            import_844h.save()

            # create Chargeback object
            new_chargeback = ChargeBack(cbid=cbid,
                                        import844_id=import_844h.id,
                                        import_844_ref=import_844h,
                                        document_type=import_844h.header['H_DocType'],
                                        date=is_valid_date(import_844h.header['H_CBDate']) if import_844h.header['H_CBDate'] else None,
                                        type=import_844h.header['H_CBType'],
                                        number=cb_number,
                                        customer_id=direct_customer.id if direct_customer else None,
                                        distribution_center_id=distribution_center.id if distribution_center else None,
                                        # new fk fields
                                        customer_ref=direct_customer,
                                        distribution_center_ref=distribution_center,
                                        resubmit_number=obj['cb_resub_number'] if obj['cb_resub_number'] else None,
                                        resubmit_description=obj['cb_resub_description'] if obj['cb_resub_description'] else None,
                                        original_chargeback_id=obj['cb_original_chargeback_id'] if obj['cb_original_chargeback_id'] else None,
                                        total_line_count=int(obj['cb_total_line_count']) if obj['cb_total_line_count'] else None,
                                        claim_subtotal=claim_subtotal,
                                        # these fields are disabled in the UI
                                        claim_calculate=None,
                                        claim_adjustment=None,
                                        claim_issue=None,
                                        accounting_credit_memo_number=None,
                                        accounting_credit_memo_date=None,
                                        accounting_credit_memo_amount=None,
                                        is_received_edi=False,
                                        stage=STAGE_TYPE_IMPORTED,
                                        substage=SUBSTAGE_TYPE_NO_ERRORS)
            new_chargeback.save()

            # update cbid counter in company
            data['company'].cbid_counter = cbid + 1
            data['company'].save()

            # Audit Trail
            # audit_trail(username=request.user.username,
            #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_CREATE_MANUAL_CB,
            #             ip_address=get_ip_address(request),
            #             entity1_name=new_chargeback.__class__.__name__,
            #             entity1_id=new_chargeback.get_id_str(),
            #             entity1_reference=new_chargeback.cbid)
            # EA -EA-1548 New Chargeback Audit
            change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_CREATE_MANUAL_CB}"
            chargeback_audit_trails(cbid=new_chargeback.get_id_str(),
                                    user_mail=request.user.email,
                                    change_text=change_text,
                                    )
            return ok_json(data={
                'chargeback': model_to_dict_safe(new_chargeback),
                'chargeback_id': new_chargeback.get_id_str()
            })

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def cb_update(request, cbid):
    """
        Company's Chargeback - Manual Creation Update
    """
    data = {'title': 'Chargeback - Manual Update'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # activate menu option
    data['menu_option_chargebacks'] = True

    chargeback = ChargeBack.objects.get(cbid=cbid)

    try:
        with transaction.atomic():

            # Get json data from ajax call for CB
            obj = json.loads(request.POST['payload'])

            # chargeback number (needed by import844 and then in main query in import validations)
            cb_number = obj['cb_number']

            # update import 844 header in case cbnumber has changed
            import_844h = chargeback.import_844_ref

            # update import844 obj to avoid future errors in validations process
            try:
                distribution_center = DistributionCenter.objects.get(id=obj['cb_distributor_id'])
                dea_number = distribution_center.dea_number
            except:
                distribution_center = None
                dea_number = ''

            try:
                direct_customer = DirectCustomer.objects.get(id=obj['cb_customer_id'])
                account_number = direct_customer.account_number
            except:
                direct_customer = None
                account_number = ''

            # EA-1450 - 1.8 Unable to edit a manual chargeback because comma in submitted amount
            obj['cb_claim_subtotal'] = obj['cb_claim_subtotal'].replace(",", "") if obj['cb_claim_subtotal'] else None
            claim_subtotal = Decimal(obj['cb_claim_subtotal']) if obj['cb_claim_subtotal'] else None

            # needed for import validations function
            import_844h.header['H_CBNumber'] = cb_number
            import_844h.header['H_DocType'] = '844'
            import_844h.header['H_CBDate'] = obj['cb_date']
            import_844h.header['H_AcctNo'] = account_number
            import_844h.header['H_DistID'] = dea_number
            import_844h.header['H_CBType'] = obj['cb_type']
            import_844h.header['H_SubClaimAmt'] = float(claim_subtotal) if claim_subtotal else ''
            import_844h.save()

            chargeback.date = is_valid_date(import_844h.header['H_CBDate']) if import_844h.header['H_CBDate'] else None
            chargeback.type = import_844h.header['H_CBType']
            chargeback.number = import_844h.header['H_CBNumber']
            chargeback.customer_id = direct_customer.id if direct_customer else None
            chargeback.distribution_center_id = distribution_center.id if distribution_center else None
            # new fk fields
            chargeback.customer_ref = direct_customer
            chargeback.distribution_center_ref = distribution_center
            # end new fk fields
            chargeback.resubmit_number = obj['cb_resub_number'] if obj['cb_resub_number'] else None
            chargeback.resubmit_description = obj['cb_resub_description'] if obj['cb_resub_description'] else None
            chargeback.original_chargeback_id = obj['cb_original_chargeback_id'] if obj['cb_original_chargeback_id'] else None
            chargeback.total_line_count = int(obj['cb_total_line_count']) if obj['cb_total_line_count'] else None
            chargeback.claim_subtotal = claim_subtotal
            chargeback.save()

            # Audit Trail
            # audit_trail(username=request.user.username,
            #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_UPDATE_MANUAL_CB,
            #             ip_address=get_ip_address(request),
            #             entity1_name=chargeback.__class__.__name__,
            #             entity1_id=chargeback.get_id_str(),
            #             entity1_reference=chargeback.cbid)

            # EA -EA-1548 New Chargeback Audit
            change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_UPDATE_MANUAL_CB}"
            chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                    user_email=request.user.email,
                                    change_text=change_text,
                                    )

            return ok_json(data={'chargeback': model_to_dict_safe(chargeback)})

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def cb_delete(request, cbid):
    data = {'title': 'Chargeback - Manual Delete'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():
            chargeback = ChargeBack.objects.get(cbid=cbid)
            chargeback.get_my_chargeback_lines().delete()
            chargeback.delete()
            return ok_json(data={"message": "Manual ChargeBack has been deleted",
                                 "redirect_url": f"/{data['db_name']}/chargebacks"})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def cbline_create(request, cbid):
    """
        Company's Chargeback Manual - Add Line
    """
    data = {'title': 'Chargeback - Manual Add Line'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # activate menu option
    data['menu_option_chargebacks'] = True

    try:
        with transaction.atomic():

            # Get json data from ajax call for CBLine
            obj = json.loads(request.POST['payload'])

            chargeback = ChargeBack.objects.get(cbid=cbid)
            import_844h = chargeback.import_844_ref

            if not chargeback.has_chargebacks_lines_with_pending_status():
                # first line then get the same import_844h object in order to complete the line information
                import_844 = import_844h
            else:
                # is not the first line then create a new import844 obj cloning the info and header from import_844h
                import_844 = Import844History(bulk_id=import_844h.bulk_id,
                                              file_name=import_844h.file_name,
                                              header=import_844h.header)
                import_844.save()

            # company cblnid counter
            cblnid = data['company'].cblnid_counter if data['company'].cblnid_counter else get_next_cblnid(data['db_name'])

            # amounts (needed for validation functions)
            wac_submitted = Decimal(obj['cbline_wac_submitted']) if obj['cbline_wac_submitted'] else None
            cp_submitted = Decimal(obj['cbline_contract_price_submitted']) if obj['cbline_contract_price_submitted'] else None
            claim_amount_submitted = Decimal(obj['cbline_claim_submitted']) if obj['cbline_claim_submitted'] else None

            import_844.line['L_ItemWAC'] = float(wac_submitted) if wac_submitted else ''
            import_844.line['L_ItemContractPrice'] = float(cp_submitted) if cp_submitted else ''
            import_844.line['L_ItemCreditAmt'] = float(claim_amount_submitted) if claim_amount_submitted else ''
            import_844.line['L_ItemQty'] = obj['cbline_item_qty'] if obj['cbline_item_qty'] else ''
            import_844.line['L_ShipToID'] = obj['cbline_purchaser_dea_number']
            import_844.line['L_ShipToName'] = obj['cbline_purchaser_name']
            import_844.line['L_ShipToAddress'] = obj['cbline_purchaser_address1']
            import_844.line['L_ShipToCity'] = obj['cbline_purchaser_city']
            import_844.line['L_ShipToState'] = obj['cbline_purchaser_state']
            import_844.line['L_ShipToZipCode'] = obj['cbline_purchaser_zip']
            import_844.line['L_ShipToGLN'] = ''
            import_844.line['L_ShipTo340BID'] = ''
            import_844.line['L_InvoiceDate'] = obj['cbline_invoice_date']

            try:
                item = Item.objects.get(id=obj['cbline_item_id'])
                item_ndc = item.ndc
                import_844.line['L_ItemNDCNo'] = item_ndc
            except:
                item = None
                item_ndc = ''

            try:
                contract = Contract.objects.get(id=obj['cbline_contract_id'])
                contract_number = contract.number
                import_844.line['L_ContractNo'] = contract_number
            except:
                contract = None
                contract_number = ''

            import_844.line['L_ItemNDCNo'] = item_ndc
            import_844.line['L_ContractNo'] = contract_number

            import_844.save()

            # Add New CBLine
            # EA-1427
            # - submitted_wac_extended_amount(wac_submitted * item_qty)
            # - submitted_contract_price_extended_amount(contract_price_submitted * item_qty)
            # - system_wac_extended_amount(wac_system * item_qty)
            # - system_contract_price_extended_amount(contract_price_system * item_qty)

            item_qty = int(import_844.line['L_ItemQty']) if import_844.line['L_ItemQty'] else None

            submitted_wac_extended_amount = None
            submitted_contract_price_extended_amount = None

            if item_qty and wac_submitted:
                submitted_wac_extended_amount = Decimal(item_qty * wac_submitted).quantize(Decimal(10) ** -2)

            if item_qty and cp_submitted:
                submitted_contract_price_extended_amount = Decimal(item_qty * cp_submitted).quantize(Decimal(10) ** -2)

            cbline = ChargeBackLine(cblnid=cblnid,
                                    submitted_contract_no=contract_number,
                                    chargeback_id=chargeback.id,
                                    contract_id=contract.id if contract else None,
                                    import844_id=import_844.id,
                                    # new fk fields
                                    chargeback_ref=chargeback,
                                    import_844_ref=import_844,
                                    contract_ref=contract,
                                    wac_submitted=wac_submitted,
                                    contract_price_submitted=cp_submitted,
                                    submitted_wac_extended_amount=submitted_wac_extended_amount,
                                    submitted_contract_price_extended_amount=submitted_contract_price_extended_amount,
                                    claim_amount_submitted=claim_amount_submitted,
                                    invoice_number=obj['cbline_invoice_number'],
                                    invoice_date=is_valid_date(import_844.line['L_InvoiceDate']) if import_844.line['L_InvoiceDate'] else None,
                                    invoice_line_no=obj['cbline_invoice_line_number'],
                                    invoice_note=obj['cbline_invoice_notes'],
                                    item_qty=int(import_844.line['L_ItemQty']) if import_844.line['L_ItemQty'] else None,
                                    item_uom=obj['cbline_item_uom'])
            cbline.save()

            # Purchaser (IndirectCustomer???)
            indirect_customer, _ = IndirectCustomer.objects.get_or_create(location_number=import_844.line['L_ShipToID'])
            indirect_customer.company_name = import_844.line['L_ShipToName']
            indirect_customer.address1 = import_844.line['L_ShipToAddress']
            indirect_customer.address2 = obj['cbline_purchaser_address2']
            indirect_customer.city = import_844.line['L_ShipToCity']
            indirect_customer.state = import_844.line['L_ShipToState']
            indirect_customer.zip_code = import_844.line['L_ShipToZipCode']
            indirect_customer.save()

            # assign Item_id and Purchaser_id in cbline
            cbline.indirect_customer_id = indirect_customer.id
            cbline.item_id = item.id if item else None
            # new fk fields
            cbline.indirect_customer_ref = indirect_customer
            cbline.item_ref = item
            cbline.line_status = LINE_STATUS_PENDING
            cbline.save()

            # update cbid counter in company
            data['company'].cblnid_counter = cblnid + 1
            data['company'].save()

            return ok_json(data={
                'cb': model_to_dict_safe(chargeback),
                'cblines': [x.get_my_dict_representation() for x in chargeback.get_my_chargeback_lines()]
            })

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def cbline_update(request, cbid, cblnid):
    """
        Company's Chargeback Manual - Add Line
    """
    data = {'title': 'Chargeback - Manual Add Line'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # activate menu option
    data['menu_option_chargebacks'] = True

    try:
        with transaction.atomic():

            # Get json data from ajax call for CBLine
            obj = json.loads(request.POST['payload'])

            chargeback = ChargeBack.objects.get(cbid=cbid)
            cbline = ChargeBackLine.objects.get(chargeback_ref=chargeback, cblnid=cblnid)
            import_844 = cbline.import_844_ref

            # amounts (needed for validation functions)
            wac_submitted = Decimal(obj['cbline_wac_submitted']) if obj['cbline_wac_submitted'] else None
            cp_submitted = Decimal(obj['cbline_contract_price_submitted']) if obj['cbline_contract_price_submitted'] else None
            claim_amount_submitted = Decimal(obj['cbline_claim_submitted']) if obj['cbline_claim_submitted'] else None

            import_844.line['L_ItemWAC'] = float(wac_submitted) if wac_submitted else ''
            import_844.line['L_ItemContractPrice'] = float(cp_submitted) if cp_submitted else ''
            import_844.line['L_ItemCreditAmt'] = float(claim_amount_submitted) if claim_amount_submitted else ''
            import_844.line['L_ItemQty'] = obj['cbline_item_qty'] if obj['cbline_item_qty'] else ''
            import_844.line['L_ShipToID'] = obj['cbline_purchaser_dea_number']
            import_844.line['L_ShipToName'] = obj['cbline_purchaser_name']
            import_844.line['L_ShipToAddress'] = obj['cbline_purchaser_address1']
            import_844.line['L_ShipToCity'] = obj['cbline_purchaser_city']
            import_844.line['L_ShipToState'] = obj['cbline_purchaser_state']
            import_844.line['L_ShipToZipCode'] = obj['cbline_purchaser_zip']
            import_844.line['L_ShipToGLN'] = ''
            import_844.line['L_ShipTo340BID'] = ''
            import_844.line['L_InvoiceDate'] = obj['cbline_invoice_date']

            try:
                item = Item.objects.get(id=obj['cbline_item_id'])
                item_ndc = item.ndc
            except:
                item = None
                item_ndc = ''

            try:
                contract = Contract.objects.get(id=obj['cbline_contract_id'])
                contract_number = contract.number
                contract_id = contract.id
            except:
                contract = None
                contract_number = ''
                contract_id = ''

            import_844.line['L_ItemNDCNo'] = item_ndc
            import_844.line['L_ContractNo'] = contract_number

            import_844.save()

            # Add New CBLine
            cbline.submitted_contract_no = contract_number
            cbline.contract_id = contract_id
            cbline.contract_ref = contract
            cbline.wac_submitted = wac_submitted
            cbline.contract_price_submitted = cp_submitted
            cbline.claim_amount_submitted = claim_amount_submitted
            cbline.invoice_number = obj['cbline_invoice_number']
            cbline.invoice_date = is_valid_date(import_844.line['L_InvoiceDate']) if import_844.line['L_InvoiceDate'] else None
            cbline.invoice_line_no = obj['cbline_invoice_line_number']
            cbline.invoice_note = obj['cbline_invoice_notes']
            cbline.item_qty = int(import_844.line['L_ItemQty']) if import_844.line['L_ItemQty'] else None
            cbline.item_uom = obj['cbline_item_uom']
            cbline.save()

            # Purchaser (IndirectCustomer???)
            indirect_customer, _ = IndirectCustomer.objects.get_or_create(location_number=import_844.line['L_ShipToID'])
            indirect_customer.company_name = import_844.line['L_ShipToName']
            indirect_customer.address1 = import_844.line['L_ShipToAddress']
            indirect_customer.address2 = obj['cbline_purchaser_address2']
            indirect_customer.city = import_844.line['L_ShipToCity']
            indirect_customer.state = import_844.line['L_ShipToState']
            indirect_customer.zip_code = import_844.line['L_ShipToZipCode']
            indirect_customer.save()

            # assign Item_id and Purchaser_id in cbline
            cbline.indirect_customer_id = indirect_customer.id
            cbline.item_id = item.id if item else None
            # new fk fields
            cbline.indirect_customer_ref = indirect_customer
            cbline.item_ref = item
            cbline.line_status = LINE_STATUS_PENDING
            cbline.save()

            return ok_json(data={
                'cb': model_to_dict_safe(chargeback),
                'cblines': [x.get_my_dict_representation() for x in chargeback.get_my_chargeback_lines()],
                'redirect_url': f'/{data["db_name"]}/chargebacks'
            })

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def cbline_delete(request, cbid, cblnid):
    """
        Company's Chargeback - Manual CB Delete Line
    """
    data = {'title': 'Manual Chargeback - Delete Line'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # activate menu option
    data['menu_option_chargebacks'] = True

    try:
        with transaction.atomic():

            cbline = ChargeBackLine.objects.get(cblnid=cblnid)
            cb = ChargeBack.objects.get(cbid=cbid)
            cbline.delete()
            return ok_json(data={
                'cb': model_to_dict_safe(cb),
                'cblines': [x.get_my_dict_representation() for x in cb.get_my_chargeback_lines()]
            })

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def get_json_for_purchaser(request):
    try:
        with transaction.atomic():
            elements = IndirectCustomer.objects.filter(location_number__icontains=request.POST['query'])
            data = {
                "results": [{
                    "id": x.get_id_str(),
                    "name": x.location_number,
                    "company_name": x.company_name,
                    "address1": x.address1,
                    "address2": x.address2,
                    "city": x.city,
                    "state": x.state,
                    "zip_code": x.zip_code,
                } for x in elements]
            }
            return ok_json(data=data)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def run_validations(request, cbid):
    """
        Company's Chargeback - Manual CB Run Validations
    """
    data = {'title': 'Manual Chargeback - Run Validations'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # activate menu option
    data['menu_option_chargebacks'] = True

    try:
        with transaction.atomic():

            chargeback = ChargeBack.objects.using(data['db_name']).get(cbid=cbid)
            import_validations_function(data['company'].id, data['db_name'], [chargeback],request)

            source = request.POST.get('source', 'cb_view')
            if source == 'cb_view':
                redirect_url = f"/{data['db_name']}/chargebacks"
            else:
                redirect_url = f"/{data['db_name']}/chargebacks/{chargeback.id}/details"

            # Audit Trail
            # audit_trail(username=request.user.username,
            #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_RERUN_VALIDATION,
            #             ip_address=get_ip_address(request),
            #             entity1_name=chargeback.__class__.__name__,
            #             entity1_id=chargeback.get_id_str(),
            #             entity1_reference=chargeback.cbid)

            # EA -EA-1548 New Chargeback Audit
            change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_RERUN_VALIDATION}"
            chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                    user_email=request.user.email,
                                    change_text=change_text,
                                    )
            return ok_json(data={"message": "Manual ChargeBack successfully processed",
                                 "redirect_url": redirect_url})

    except Exception as ex:
        return bad_json(message=ex.__str__())
