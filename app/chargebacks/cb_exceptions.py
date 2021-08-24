import json
import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction,connections
from django.db.models import Count, Q, Min, Max
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (LINE_STATUS_PENDING, LINE_STATUS_DISPUTED, LINE_STATUS_APPROVED,
                                                EXCEPTION_ACTION_TAKEN_AUTOCORRECT, EXCEPTION_ACTION_TAKEN_DISPUTED,
                                                EXCEPTION_ACTION_TAKEN_OVERRIDE, CONTRACT_TYPE_INDIRECT,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_ALTER_CONTRACT_NUMBER,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_DISPUTE,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_AUTOCORRECT_PRICE,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_OVERRIDE,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_RERUN_VALIDATION,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_ALLOW_MEMBER, STATUS_ACTIVE,
                                                STATUS_INACTIVE, STAGE_TYPE_VALIDATED,
                                                SUBSTAGE_TYPE_NO_ERRORS, STATUS_PENDING, STATUS_PROPOSED)
from app.management.utilities.exports import export_report_to_csv, export_report_to_excel
from app.management.utilities.functions import (ok_json, bad_json, audit_trail, get_ip_address, datatable_handler,
                                                strip_special_characters_and_spaces, convert_string_to_date,
                                                chargeback_audit_trails, get_chargebackline_object)
from app.management.utilities.globals import addGlobalData
from app.reports.reports_structures import (get_exceptions_details_report_structure,
                                            get_exceptions_header_report_structure)
from app.tasks import import_validations_function
from ermm.models import ApprovedReason, Dispute
from erms.models import (ChargeBackLine, Contract, Item, ChargeBackDispute, ContractMember, ContractAlias,
                         IndirectCustomer)
from empowerb.middleware import db_ctx

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'Chargebacks Exceptions', 'header_title': 'Chargebacks > Exceptions'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['has_duplicates_header'] = ChargeBackLine.objects.filter(
        line_status=LINE_STATUS_PENDING
    ).values('id',
             'contract_ref',
             'submitted_contract_no',
             'item_id',
             'wac_submitted',
             'contract_price_submitted',
             'wac_system',
             'contract_price_system').order_by().annotate(count=Count("id")).filter(count__gt=0).exists()

    data['dispute_result'] = []
    if data['has_duplicates_header']:
        dispute_results = ChargeBackDispute.objects.filter(is_active=True, chargebackline_ref__line_status=LINE_STATUS_PENDING).exclude(dispute_code='WW').values('dispute_code').order_by().annotate(count=Count("dispute_code"))
        # EA-1155 - Correct the dispute code counts for "ALL" show that its the total number of exception lines
        data['dispute_result_total_count'] = ChargeBackLine.objects.filter(line_status=LINE_STATUS_PENDING).count()
        for dr in dispute_results:
            dispute_tooltip_obj = Dispute.objects.get(code=dr['dispute_code'])
            data['dispute_result'].append({
                'dispute_code': dr['dispute_code'],
                'count': dr['count'],
                'tooltip': dispute_tooltip_obj.description
            })

    # needed for alter contract no dropdown
    data['indirect_contracts'] = Contract.objects.filter(type=CONTRACT_TYPE_INDIRECT)
    # selected tab
    data['active_tab'] = 'e'
    data['menu_option'] = 'menu_chargebacks'
    return render(request, "chargebacks/exceptions/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data_duplicates_header(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    :param: request (required by django urls)
    """
    try:
        is_export = request.GET.get('is_export', '0')
        export_to = request.GET.get('export_to', 'excel')
        filter = request.POST.get('filter', '')  # BB, FF or '' = all

        results = []
        if filter == 'BB':
            queryset = ChargeBackLine.objects.filter(line_status=LINE_STATUS_PENDING, disputes_codes__icontains='BB').values(
                'contract_ref',
                'submitted_contract_no'
            ).order_by().annotate(count=Count("submitted_contract_no")).filter(count__gt=0)

            # EA-1204 - On the slider add search function for contract number fields , NDC
            search = request.POST.get('search[value]', '')
            if search:
                queryset = queryset.filter(Q(contract_ref__number__icontains=search) | Q(submitted_contract_no__icontains=search))

            for elem in queryset:
                contract_id = elem['contract_ref']
                contract_no = Contract.objects.get(id=contract_id).number if contract_id else ''
                submitted_contract_no = elem['submitted_contract_no']
                # append to results
                results.append({
                    'submitted_contract_no': submitted_contract_no,
                    'contract_no': contract_no,
                    'errors_count': elem['count']
                })
        else:
            queryset = ChargeBackLine.objects.filter(line_status=LINE_STATUS_PENDING).values(
                'contract_ref',
                'submitted_contract_no',
                'item_ref',
                'wac_submitted',
                'contract_price_submitted',
                'wac_system',
                'contract_price_system',
                # 'chargeback_ref__customer_ref__name'
            ).order_by().annotate(count=Count("id"), min_invoice_date=Min('invoice_date'), max_invoice_date=Max('invoice_date')).filter(count__gt=0)

            # EA-1364 - Do not include FF exceptions on the exception slider
            if filter != 'FF':
                queryset = queryset.exclude(disputes_codes__icontains='FF')
            # EA-1653 - Add handling if Ind Cust DEA is invalid
            if filter != 'JJ':
                queryset = queryset.exclude(disputes_codes__icontains='JJ')
            # EA-1204 - On the slider add search function for contract number fields , NDC
            search = request.POST.get('search[value]', '')
            if search:
                queryset = queryset.filter(Q(contract_ref__number__icontains=search) | Q(submitted_contract_no__icontains=search) | Q(item_ref__ndc__icontains=search))

            # EA-1204 - On the exception slider remove the “Distributor“ column
            results = []
            # EA-1699 Exception Page Slider non stop spinning circle when sorting grid.
            db_name = db_ctx.get()
            cursor = connections[db_name].cursor()
            for elem in queryset:
                elem['wac_system'] = elem['wac_system'] if elem['wac_system'] else 0
                elem['wac_submitted'] = elem['wac_submitted'] if elem['wac_submitted'] else 0
                elem['contract_price_submitted'] = elem['contract_price_submitted'] if elem['contract_price_submitted'] else 0
                elem['contract_price_system'] = elem['contract_price_system'] if elem['contract_price_system'] else 0

                # distributor = elem['chargeback_ref__customer_ref__name']
                contract_id = elem['contract_ref']
                contract_no = Contract.objects.get(id=contract_id).number if contract_id else ''
                submitted_contract_no = elem['submitted_contract_no']
                item_id = elem['item_ref']
                item_ndc = Item.objects.get(id=item_id).get_formatted_ndc() if item_id else ''
                wac_submitted = Decimal(elem['wac_submitted']).quantize(Decimal(10) ** -2) if elem['wac_submitted'] else None
                wac_system = Decimal(elem['wac_system']).quantize(Decimal(10) ** -2) if elem['wac_system'] else None
                contract_price_submitted = Decimal(elem['contract_price_submitted']).quantize(Decimal(10) ** -2) if elem['contract_price_submitted'] else None
                contract_price_system = Decimal(elem['contract_price_system']).quantize(Decimal(10) ** -2) if elem['contract_price_system'] else None
                min_invoice_date = elem["min_invoice_date"]
                max_invoice_date = elem["max_invoice_date"]

                # cblines = ChargeBackLine.objects.filter(
                #     line_status=LINE_STATUS_PENDING,
                #     contract_ref_id=contract_id,
                #     submitted_contract_no=submitted_contract_no,
                #     item_ref_id=item_id,
                #     wac_submitted=wac_submitted,
                #     contract_price_submitted=contract_price_submitted,
                #     wac_system=wac_system,
                #     contract_price_system=contract_price_system,
                #     # chargeback_ref__customer_ref__name=distributor
                # )
                # EA-1699 Exception Page Slider non stop spinning circle when sorting grid.
                contract_id = contract_id.__str__()
                contract_id = contract_id.replace('-', '')
                item_id = item_id.__str__()
                item_id = item_id.replace('-', '')
                query = f"SELECT  GROUP_CONCAT(distinct `chargebacks_lines`.`disputes_notes` SEPARATOR '/' ) as `disputes_notes` FROM `chargebacks_lines` WHERE (`chargebacks_lines`.`contract_price_submitted` = '{contract_price_submitted}' AND `chargebacks_lines`.`contract_price_system` = '{contract_price_system}' AND `chargebacks_lines`.`contract_ref` = '{contract_id}' AND `chargebacks_lines`.`item_ref` = '{item_id}' AND `chargebacks_lines`.`line_status` = '{LINE_STATUS_PENDING}' AND `chargebacks_lines`.`submitted_contract_no` = '{submitted_contract_no}' AND `chargebacks_lines`.`wac_submitted` = '{wac_submitted}' AND `chargebacks_lines`.`wac_system` = '{wac_system}')"
                # print(query)
                cursor.execute(query)
                row = cursor.fetchone()
                cb_dispute_notes = ''
                # As we are using raw query row comes in tuple
                if row:
                    if row[0]:
                        cb_dispute_notes = row[0]
                # Get distinct CB dispute notes
                # Ticket EA-1371 Do not use dispute_note field for anything. Only use user_dispute_note
                # cb_dispute_notes = '/'.join(list(set([x.user_dispute_note for x in cblines if x.user_dispute_note])))
                # EA-1468 - HOTFIX: Exception Page & Slider File Export Missing Columns
                # Add dispute notes from cb_dispute_notes
                # cb_dispute_notes = '/'.join(list(set([x.disputes_notes for x in cblines if x.disputes_notes])))

                # append to results
                results.append({
                    # 'distributor': distributor,
                    'contract_id': contract_id,
                    'submitted_contract_no': submitted_contract_no,
                    'contract_no': contract_no,
                    'item_id': item_id,
                    'item_ndc': item_ndc,
                    'wac_submitted': wac_submitted,
                    'wac_system': wac_system,
                    'cp_submitted': contract_price_submitted,
                    'cp_system': contract_price_system,
                    'min_invoice_date': min_invoice_date.strftime('%m/%d/%Y'),
                    'max_invoice_date': max_invoice_date.strftime('%m/%d/%Y'),
                    'errors_count': elem['count'],
                    'cb_dispute_notes': cb_dispute_notes,
                })

        # EA-1204 - On both the main exception grid and the exception slider make all columns sortable
        if request.POST and request.POST['order[0][column]']:
            ord_index = int(request.POST['order[0][column]'])
            order_asc = False if request.POST['order[0][dir]'] == 'asc' else True
            ord_column = request.POST[f'columns[{ord_index}][data]']
            results = sorted(results, key=lambda i: i[ord_column], reverse=order_asc)

        if is_export == "1":
            # Structure
            structure = get_exceptions_header_report_structure()
            # Export to excel or csv
            if export_to == 'excel':
                filename = f"Exceptions_Summary_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
                response = export_report_to_excel(results, filename, structure)
            else:
                filename = f"Exceptions_Summary_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                response = export_report_to_csv(results, filename, structure)

            return response

        else:

            # response
            response = {
                'data': results,
                'recordsTotal': len(results),
                'recordsFiltered': len(results),
            }

            return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data_duplicates_details(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:
        queryset = ChargeBackLine.objects.filter(line_status=LINE_STATUS_PENDING)

        # Export Records
        is_export = request.GET.get('is_export', '0')
        export_to = request.GET.get('export_to', 'excel')
        export_search = request.GET.get('export_search', '')
        export_dispute_code_search = request.GET.get('export_dispute_code_search', '')

        # EA-1017 - Exception Grid Changes looking if user has clicked on any active disputes
        search_dispute_code = request.POST.get('search_dispute_code', '')

        # For export apply all the filters which are applied for grid
        if is_export == "1":
            request.POST = request.POST.copy()
            request.POST['length'] = -1  # To get all the records every-time we do export
            request.POST['order[0][column]'] = ""  # So dtatable_handler doesn't throw error for ordering

            if export_search:
                request.POST['search[value]'] = export_search
            if export_dispute_code_search:
                search_dispute_code = export_dispute_code_search

        if search_dispute_code:
            queryset = queryset.filter(chargebackdispute__is_active=True, chargebackdispute__dispute_code__icontains=search_dispute_code).distinct()

        payload = request.POST.get('payload', '')
        if payload:
            payload = json.loads(payload)
            filter = payload.get('filter', '')
            if filter == 'BB':
                submitted_contract_no = payload.get('submitted_contract_no', '')
                contract_no = payload.get('contract_no', '')
                contract_ref = Contract.objects.get(number=contract_no) if contract_no else None
                queryset = queryset.filter(contract_ref=contract_ref,
                                           submitted_contract_no=submitted_contract_no,
                                           chargebackdispute__dispute_code__icontains='BB').distinct()
            else:
                submitted_contract_no = payload.get('submitted_contract_no', '')
                contract_no = payload.get('contract_no', '')
                contract_ref = Contract.objects.get(number=contract_no) if contract_no else None
                item_id = payload.get('item_id', '')
                if item_id == 'null':
                    item_id = ''
                wac_submitted = Decimal(payload['wac_submitted']) if payload['wac_submitted'] else None
                wac_system = Decimal(payload['wac_system']) if payload['wac_system'] else None
                cp_submitted = Decimal(payload['cp_submitted']) if payload['cp_submitted'] else None
                cp_system = Decimal(payload['cp_system']) if payload['cp_system'] else None

                queryset = queryset.filter(contract_ref=contract_ref,
                                           submitted_contract_no=submitted_contract_no,
                                           item_id=item_id,
                                           wac_submitted=wac_submitted,
                                           contract_price_submitted=cp_submitted,
                                           wac_system=wac_system,
                                           contract_price_system=cp_system)



        search_fields = ['cbid', 'cblnid', 'contract_id', 'dispute_codes']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_export=is_export)
        queryset = queryset.annotate(error_count=Count('chargebackdispute', filter=Q(chargebackdispute__is_active=True)))

        if is_export == "1":

            time1 = datetime.datetime.now()
            # Structure
            structure = get_exceptions_details_report_structure()
            # print(structure)
            # Export to excel or csv
            # EA -1653 Add handling if Ind Cust DEA is invalid
            results = []
            for elem in queryset:
                chargebackline_id = elem.id
                chargebackline = get_chargebackline_object(chargebackline_id)
                cb = chargebackline.get_my_chargeback()
                my_indirect_customer = chargebackline.get_my_indirect_customer()
                item = chargebackline.get_my_item()
                distribution_center = chargebackline.get_my_distribution_center()
                import844_obj = chargebackline.get_my_import844_obj()
                # EA-1688 Unable to export excel or csv from Exceptions grid
                try:
                    contract = chargebackline.get_my_contract()
                    contract_no = contract.number
                except:
                    contract_no = ''
                try:
                    distributor = chargebackline.get_my_distribution_center()
                    distributor_name = distributor.name
                except:
                    distributor_name = ''
                try:
                    customer = cb.get_my_customer()
                    customer_name = customer.name
                except:
                    customer_name = ''
                try:
                    item = chargebackline.get_my_item()
                    item_ndc = item.get_formatted_ndc()
                    item_description = item.description
                except:
                    item_ndc = ''
                    item_description = ''
                # end here ticket
                if not my_indirect_customer:
                    indirect_customer_company_name = import844_obj.line.get('L_ShipToName', '') if import844_obj else ''
                    indirect_customer_address1 = import844_obj.line.get('L_ShipToAddress', '') if import844_obj else ''
                    indirect_customer_address2 = ''
                    indirect_customer_city = import844_obj.line.get('L_ShipToCity', '') if import844_obj else ''
                    indirect_customer_state = import844_obj.line.get('L_ShipToState', '') if import844_obj else ''
                    indirect_customer_zip_code = import844_obj.line.get('L_ShipToZipCode', '') if import844_obj else ''
                    indirect_customer_location_number = import844_obj.line.get('L_ShipToID',
                                                                               '') if import844_obj else ''
                else:
                    indirect_customer_location_number = my_indirect_customer.location_number
                    indirect_customer_company_name = my_indirect_customer.company_name
                    indirect_customer_address1 = my_indirect_customer.address1
                    indirect_customer_address2 = my_indirect_customer.address2
                    indirect_customer_city = my_indirect_customer.city
                    indirect_customer_state = my_indirect_customer.state
                    indirect_customer_zip_code = my_indirect_customer.zip_code

                results.append({
                    'chargeback_ref__cbid': cb.cbid,
                    'cblnid': elem.cblnid,
                    'chargeback_ref__customer_ref__name': customer_name,
                    'chargeback_ref__distribution_center_ref__name': distributor_name,
                    'chargeback_ref__number': cb.number,
                    'submitted_contract_no': elem.submitted_contract_no,
                    'contract_ref__number': contract_no,
                    'indirect_customer_ref__location_number': indirect_customer_location_number,
                    'indirect_customer_ref__company_name': indirect_customer_company_name,
                    'indirect_customer_ref__address1': indirect_customer_address1,
                    'indirect_customer_ref__address2': indirect_customer_address2,
                    'indirect_customer_ref__city': indirect_customer_city,
                    'indirect_customer_ref__state': indirect_customer_state,
                    'indirect_customer_ref__zip_code': indirect_customer_zip_code,
                    'item_ref__ndc': item_ndc,
                    'item_ref__description': item_description,
                    'invoice_date': elem.invoice_date,
                    'invoice_number': elem.invoice_number,
                    'wac_submitted': elem.wac_submitted,
                    'wac_system': elem.wac_system,
                    'contract_price_submitted': elem.contract_price_submitted,
                    'contract_price_system': elem.contract_price_system,
                    'claim_amount_submitted': elem.claim_amount_submitted,
                    'claim_amount_system': elem.claim_amount_system,
                    'claim_amount_adjusment': elem.claim_amount_adjusment,
                    'disputes_codes': elem.disputes_codes,
                    'disputes_notes': elem.disputes_notes,
                    'error_count': elem.error_count,
                })
            if export_to == 'excel':
                filename = f"Exceptions_Details_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
                response = export_report_to_excel(results, filename, structure)
            else:
                filename = f"Exceptions_Details_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                response = export_report_to_csv(results, filename, structure)

            time2 = datetime.datetime.now()
            delta = (time2 - time1).total_seconds()
            print(f"Delta Time Export: {delta} sec")

            return response

        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def alter_contract_no(request):
    data = {'title': 'Chargebacks - Exceptions - Alter Contract No.'}
    addGlobalData(request, data)

    try:
        with transaction.atomic():

            # Does "Corrected Contract No" already exist in ApprovedReason table
            approved_reason, _ = ApprovedReason.objects.get_or_create(description='Corrected Contract No')

            new_contract_id = request.POST.get('new_contract_id', '')
            if not new_contract_id:
                return bad_json(message='Contract is required')

            assign_contract_alias = request.POST.get('assign_contract_alias', '0')

            chargebacks_to_process = []
            for chargeback_line_id in request.POST['chargebacks_lines_ids'].split("|"):
                chargeback_line = ChargeBackLine.objects.get(id=chargeback_line_id)
                chargeback = chargeback_line.chargeback_ref

                # 1) Update contract_id
                # (ticket 1250 Reverse EA-1085. Allow user to reassign contract even if contract No is filled in already)
                chargeback_line.contract_id = new_contract_id
                chargeback_line.contract_ref_id = new_contract_id
                chargeback_line.approved_reason_id = approved_reason.id
                chargeback_line.save()

                # EA-1017 - Exception Grid Changes
                if assign_contract_alias == '1':
                    ContractAlias.objects.get_or_create(contract_id=new_contract_id, alias=chargeback_line.submitted_contract_no)

                # inactive active disputes
                chargeback_line.chargebackdispute_set.all().update(is_active=False)

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_ALTER_CONTRACT_NUMBER,
                #             ip_address=get_ip_address(request),
                #             entity1_name=chargeback_line.__class__.__name__,
                #             entity1_id=chargeback_line.get_id_str(),
                #             entity1_reference=chargeback_line.cblnid,
                #             entity2_name=chargeback.__class__.__name__,
                #             entity2_id=chargeback.get_id_str(),
                #             entity2_reference=chargeback.cbid)
                # EA -EA-1548 New Chargeback Audit
                change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_ALTER_CONTRACT_NUMBER}"
                chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                        cblnid=chargeback_line.cblnid,
                                        user_email=request.user.email,
                                        change_text=change_text,
                                        )
                if chargeback not in chargebacks_to_process:
                    chargebacks_to_process.append(chargeback)

            # clean disputes and rerun validations
            ChargeBackDispute.objects.filter(chargeback_ref__in=chargebacks_to_process).update(is_active=False)
            import_validations_function(data['company'].id, data['db_name'], chargebacks_to_process,request)

            return ok_json(data={"message": f"Exception Action succesfully executed ({alter_contract_no.__name__})"})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def dispute_cb(request):
    data = {'title': 'Chargebacks - Exceptions - Dispute CB'}
    addGlobalData(request, data)

    try:
        with transaction.atomic():

            chargebacks_to_process = []
            for chargeback_line_id in request.POST['chargebacks_lines_ids'].split("|"):
                chargeback_line = ChargeBackLine.objects.get(id=chargeback_line_id)
                chargeback = chargeback_line.chargeback_ref

                # ticket 733 overwrite the value in the field, while the status is still PENDING
                # ticket 1000 action_taken has to be populated with D for disputed
                if chargeback_line.line_status == LINE_STATUS_PENDING:
                    chargeback_line.action_taken = EXCEPTION_ACTION_TAKEN_DISPUTED
                    chargeback_line.save()

                # 1) Update Line Status = 3, ClaimAmtIssue = 0, and ClaimAmtAdj = (0 - ClaimAmtSub) s
                chargeback_line.line_status = LINE_STATUS_DISPUTED
                chargeback_line.claim_amount_issue = 0
                chargeback_line.claim_amount_adjusment = 0 - chargeback_line.claim_amount_submitted
                # EA-1418 - if disputed, make the issued field 0.00
                chargeback_line.contract_price_issued = Decimal('0.00')
                chargeback_line.wac_price_issued = Decimal('0.00')
                chargeback_line.save()

                # 2) Ticket EA-736 - Update Dispute Note
                # ticket 937 Strip special characters and extra spaces from dispute notes
                chargeback_line.user_dispute_note = strip_special_characters_and_spaces(request.POST['dispute_note'])
                chargeback_line.save()

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_DISPUTE,
                #             ip_address=get_ip_address(request),
                #             entity1_name=chargeback_line.__class__.__name__,
                #             entity1_id=chargeback_line.get_id_str(),
                #             entity1_reference=chargeback_line.cblnid,
                #             entity2_name=chargeback.__class__.__name__,
                #             entity2_id=chargeback.get_id_str(),
                #             entity2_reference=chargeback.cbid)

                # EA -EA-1548 New Chargeback Audit
                change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_DISPUTE}"
                chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                        cblnid=chargeback_line.cblnid,
                                        user_email=request.user.email,
                                        change_text=change_text
                                        )
                if chargeback not in chargebacks_to_process:
                    chargebacks_to_process.append(chargeback)

            for cb in chargebacks_to_process:
                # Recalculate Amounts
                cb.calculate_claim_totals_by_db(data['db_name'])
                # update stage and substage if not pending lines
                if not cb.get_my_pending_chargeback_lines():
                    cb.stage = STAGE_TYPE_VALIDATED
                    cb.substage = SUBSTAGE_TYPE_NO_ERRORS
                cb.save(using=data['db_name'])

            return ok_json(data={"message": f"Exception Action succesfully executed ({dispute_cb.__name__})"})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def autocorrect_price(request):
    data = {'title': 'Chargebacks - Exceptions - Autocorrect Price'}
    addGlobalData(request, data)

    try:
        with transaction.atomic():

            chargebacks_to_process = []
            skipped_lines = []

            for chargeback_line_id in request.POST['chargebacks_lines_ids'].split("|"):
                chargeback_line = ChargeBackLine.objects.get(id=chargeback_line_id)

                # EA - 1587 - On the Exception page only show actions based on dispute code
                # If the user select 1 or more  lines and clicked on “Auto Correct“ this action should only run on lines
                # where both the system wac and system contract price is available.
                # If either the wac system or contract price system is empty the line should be skipped and remain on the exception page
                if chargeback_line.wac_system and chargeback_line.contract_price_system:

                    chargeback = chargeback_line.chargeback_ref

                    # ticket 733 overwrite the value in the field, while the status is still PENDING
                    # ticket 1000 action_taken has to be populated with A for autocorrect
                    if chargeback_line.line_status == LINE_STATUS_PENDING:
                        chargeback_line.action_taken = EXCEPTION_ACTION_TAKEN_AUTOCORRECT
                        chargeback_line.save()

                    # 1) Update Line Status = 3, ClaimAmtIssue = ClaimAmtSys
                    chargeback_line.line_status = LINE_STATUS_DISPUTED
                    chargeback_line.claim_amount_issue = chargeback_line.claim_amount_system if chargeback_line.claim_amount_system else 0
                    chargeback_line.claim_amount_adjusment = chargeback_line.claim_amount_issue - chargeback_line.claim_amount_submitted
                    # EA-1418 - If autocorrect,  copy wac_system to wac_price_issued & copy contract_price_system to contract_price_issued
                    chargeback_line.contract_price_issued = chargeback_line.contract_price_system
                    chargeback_line.wac_price_issued = chargeback_line.wac_system
                    chargeback_line.save()

                    # 2) Ticket EA-736 - Update Dispute Note
                    chargeback_line.user_dispute_note = strip_special_characters_and_spaces(request.POST['dispute_note'])
                    chargeback_line.save()

                    # Audit Trail
                    # audit_trail(username=request.user.username,
                    #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_AUTOCORRECT_PRICE,
                    #             ip_address=get_ip_address(request),
                    #             entity1_name=chargeback_line.__class__.__name__,
                    #             entity1_id=chargeback_line.get_id_str(),
                    #             entity1_reference=chargeback_line.cblnid,
                    #             entity2_name=chargeback.__class__.__name__,
                    #             entity2_id=chargeback.get_id_str(),
                    #             entity2_reference=chargeback.cbid)

                    # EA -EA-1548 New Chargeback Audit
                    change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_AUTOCORRECT_PRICE}"
                    chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                    cblnid=chargeback_line.cblnid,
                                    user_email=request.user.email,
                                    change_text=change_text
                                    )
                    # cbline disputes
                    cbline_disputes = chargeback_line.get_my_active_disputes()

                    # local vars to make this conditional and flow easier
                    has_dispute_code_SS = cbline_disputes.filter(dispute_code='SS').exists()
                    has_dispute_code_TT = cbline_disputes.filter(dispute_code='TT').exists()
                    has_dispute_code_UU = cbline_disputes.filter(dispute_code='UU').exists()
                    has_dispute_code_VV = cbline_disputes.filter(dispute_code='VV').exists()
                    has_dispute_code_WW = cbline_disputes.filter(dispute_code='WW').exists()
                    has_dispute_code_XX = cbline_disputes.filter(dispute_code='XX').exists()

                    if has_dispute_code_SS and not has_dispute_code_TT:
                        chargeback_dispute = ChargeBackDispute(chargeback_id=chargeback_line.chargeback_id,
                                                               chargebackline_id=chargeback_line_id,
                                                               # new fk fields
                                                               chargeback_ref=chargeback,
                                                               chargebackline_ref=chargeback_line,
                                                               dispute_code='TT')
                        chargeback_dispute.save()

                    if has_dispute_code_UU and not has_dispute_code_VV:
                        chargeback_dispute = ChargeBackDispute(chargeback_id=chargeback_line.chargeback_id,
                                                               chargebackline_id=chargeback_line_id,
                                                               # new fk fields
                                                               chargeback_ref=chargeback,
                                                               chargebackline_ref=chargeback_line,
                                                               dispute_code='VV')
                        chargeback_dispute.save()

                    if has_dispute_code_WW and not has_dispute_code_XX:
                        chargeback_dispute = ChargeBackDispute(chargeback_id=chargeback_line.chargeback_id,
                                                               chargebackline_id=chargeback_line_id,
                                                               # new fk fields
                                                               chargeback_ref=chargeback,
                                                               chargebackline_ref=chargeback_line,
                                                               dispute_code='XX')
                        chargeback_dispute.save()

                    if chargeback not in chargebacks_to_process:
                        chargebacks_to_process.append(chargeback)
                else:
                    skipped_lines.append({
                        'id': chargeback_line.get_id_str(),
                        'cbid': chargeback_line.chargeback_ref.cbid,
                        'cblnid': chargeback_line.cblnid,
                        'direct_customer': chargeback_line.chargeback_ref.customer_ref.name if chargeback_line.chargeback_ref.customer_ref else '',
                        'cbnumber': chargeback_line.chargeback_ref.number,
                        'submitted_contract_number': chargeback_line.submitted_contract_no,
                        'contract_number': chargeback_line.contract_ref.number if chargeback_line.contract_ref else '',
                        'ndc': chargeback_line.item_ref.get_formatted_ndc() if chargeback_line.item_ref else '',
                        'invoice_date': chargeback_line.invoice_date.strftime('%m/%d/%Y') if chargeback_line.invoice_date else '',
                        'wac_submitted': str(chargeback_line.wac_submitted) if chargeback_line.wac_submitted else '',
                        'wac_system': str(chargeback_line.wac_system) if chargeback_line.wac_system else '',
                        'contract_price_submitted': str(chargeback_line.contract_price_submitted) if chargeback_line.contract_price_submitted else '',
                        'contract_price_system': str(chargeback_line.contract_price_system) if chargeback_line.contract_price_system else '',
                    })

            for cb in chargebacks_to_process:
                # Recalculate Amounts
                cb.calculate_claim_totals_by_db(data['db_name'])
                # update stage and substage if not pending lines
                if not cb.get_my_pending_chargeback_lines():
                    cb.stage = STAGE_TYPE_VALIDATED
                    cb.substage = SUBSTAGE_TYPE_NO_ERRORS
                cb.save(using=data['db_name'])

            return ok_json(data={"message": f"Exception Action successfully executed ({autocorrect_price.__name__})", "skipped_lines": skipped_lines})
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def override(request):
    data = {'title': 'Chargebacks - Exceptions - Override'}
    addGlobalData(request, data)
    try:
        with transaction.atomic(using=data['db_name']):

            # Ticket EA-1053 set reason to "Price Override"
            approved_reason, _ = ApprovedReason.objects.get_or_create(description='Price Override')

            chargebacks_to_process = []
            for chargeback_line_id in request.POST['chargebacks_lines_ids'].split("|"):
                chargeback_line = ChargeBackLine.objects.get(id=chargeback_line_id)
                chargeback = chargeback_line.chargeback_ref

                # ticket 733 overwrite the value in the field, while the status is still PENDING
                # ticket 1000 action_taken has to be populated with O for override
                if chargeback_line.line_status == LINE_STATUS_PENDING:
                    chargeback_line.action_taken = EXCEPTION_ACTION_TAKEN_OVERRIDE
                    chargeback_line.save()

                # 1) Update Line Status = 3, ClaimAmtIssue = ClaimAmtSys
                chargeback_line.line_status = LINE_STATUS_APPROVED
                chargeback_line.claim_amount_issue = chargeback_line.claim_amount_submitted
                chargeback_line.claim_amount_adjusment = 0
                # EA-1418 - if override action , copy wac_submitted to wac_price Issued & copy contract_price_submitted to contract_price_issued
                chargeback_line.contract_price_issued = chargeback_line.contract_price_submitted
                chargeback_line.wac_price_issued = chargeback_line.wac_submitted
                chargeback_line.save()

                # 2) Ticket EA-736 - Update Dispute Note
                chargeback_line.user_dispute_note = strip_special_characters_and_spaces(request.POST['dispute_note'])
                chargeback_line.save()

                # 3) Ticket EA-1053 Set reason to Price Override
                chargeback_line.approved_reason_id = approved_reason.id
                chargeback_line.save()

                # 4) Ticket EA-1025 - Override Action should mark all disputes as Resolved
                chargeback_line.chargebackdispute_set.all().update(is_active=False)

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_OVERRIDE,
                #             ip_address=get_ip_address(request),
                #             entity1_name=chargeback_line.__class__.__name__,
                #             entity1_id=chargeback_line.get_id_str(),
                #             entity1_reference=chargeback_line.cblnid,
                #             entity2_name=chargeback.__class__.__name__,
                #             entity2_id=chargeback.get_id_str(),
                #             entity2_reference=chargeback.cbid)

                # EA -EA-1548 New Chargeback Audit
                change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_OVERRIDE}"
                chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                        cblnid=chargeback_line.cblnid,
                                        user_email=request.user.email,
                                        change_text=change_text
                                        )
                if chargeback not in chargebacks_to_process:
                    chargebacks_to_process.append(chargeback)

            for cb in chargebacks_to_process:
                # Recalculate Amounts
                cb.calculate_claim_totals_by_db(data['db_name'])
                # update stage and substage if not pending lines
                if not cb.get_my_pending_chargeback_lines():
                    cb.stage = STAGE_TYPE_VALIDATED
                    cb.substage = SUBSTAGE_TYPE_NO_ERRORS
                cb.save(using=data['db_name'])

            return ok_json(data={"message": f"Exception Action succesfully executed ({override.__name__})"})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def allow_member(request):
    data = {'title': 'Chargebacks - Exceptions - Allow Member'}
    addGlobalData(request, data)

    try:
        with transaction.atomic():

            allow_member_start_date = convert_string_to_date(request.POST['allow_member_start_date']) if request.POST[
                'allow_member_start_date'] else None

            chargebacks_to_process = []
            for chargeback_line_id in request.POST['chargebacks_lines_ids'].split("|"):
                chargeback_line = ChargeBackLine.objects.get(id=chargeback_line_id)
                chargeback = chargeback_line.chargeback_ref
                indirect_customer = chargeback_line.indirect_customer_ref
                contract = chargeback_line.contract_ref

                start_date = contract.start_date
                # EA-1070 - Add input on Allow member exception action to include start date
                if allow_member_start_date:
                    start_date = allow_member_start_date
                    if allow_member_start_date < contract.start_date or allow_member_start_date > contract.end_date:
                        return bad_json(message=f"Submitted date for contract ({contract.number}) is out of range.")
                end_date = contract.end_date

                for existing_cm in ContractMember.objects.filter(contract=contract,
                                                                 indirect_customer=indirect_customer):
                    # As per ticket EA - 955 - Allow member action incorrectly puts current date as start date
                    # To-Do - Remove one of the logic which is not required
                    if start_date <= existing_cm.start_date <= end_date or start_date <= existing_cm.end_date <= end_date:
                        existing_cm.status = STATUS_INACTIVE
                        existing_cm.save()
                    elif start_date > existing_cm.start_date:
                        day_to_adjust = datetime.timedelta(1)
                        # Ending existing line one day prior new start date
                        existing_cm.end_date = start_date - day_to_adjust
                        existing_cm.status = STATUS_INACTIVE
                        existing_cm.save()

                # ticket 926 Add the indirect customer to contract’s membership list
                # with the current date as start_date and contract end date as end_date
                # line just added should be the active line for the Ind Cust
                ContractMember.objects.create(contract=contract,
                                              indirect_customer=indirect_customer,
                                              start_date=start_date,
                                              end_date=end_date,
                                              status=STATUS_ACTIVE)
                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_ALLOW_MEMBER,
                #             ip_address=get_ip_address(request),
                #             entity1_name=chargeback_line.__class__.__name__,
                #             entity1_id=chargeback_line.get_id_str(),
                #             entity1_reference=chargeback_line.cblnid,
                #             entity2_name=chargeback.__class__.__name__,
                #             entity2_id=chargeback.get_id_str(),
                #             entity2_reference=chargeback.cbid)
                # EA -EA-1548 New Chargeback Audit
                change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_ALLOW_MEMBER}"
                chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                        cblnid=chargeback_line.cblnid,
                                        user_email=request.user.email,
                                        change_text=change_text
                                        )
                if chargeback not in chargebacks_to_process:
                    chargebacks_to_process.append(chargeback)

            ChargeBackDispute.objects.using(data['db_name']).filter(chargeback_ref__in=chargebacks_to_process).update(
                is_active=False)
            import_validations_function(data['company'].id, data['db_name'], chargebacks_to_process,request)

            return ok_json(data={"message": f"Exception Action succesfully executed ({override.__name__})"})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def assign_cot(request):
    data = {'title': 'Chargebacks - Exceptions - Assign CoT'}
    addGlobalData(request, data)

    try:
        with transaction.atomic():

            chargebacks_to_process = []
            for chargeback_line_id in request.POST['chargebacks_lines_ids'].split("|"):
                chargeback_line = ChargeBackLine.objects.get(id=chargeback_line_id)
                chargeback = chargeback_line.chargeback_ref
                indirect_customer = chargeback_line.indirect_customer_ref

                # ticket 927 Exception Action: Allow CoT. Assign the selected CoT to the indirect_customer in the line
                indirect_customer.cot_id = request.POST.get('cot_id', None)
                indirect_customer.save()

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_ALLOW_MEMBER,
                #             ip_address=get_ip_address(request),
                #             entity1_name=chargeback_line.__class__.__name__,
                #             entity1_id=chargeback_line.get_id_str(),
                #             entity1_reference=chargeback_line.cblnid,
                #             entity2_name=chargeback.__class__.__name__,
                #             entity2_id=chargeback.get_id_str(),
                #             entity2_reference=chargeback.cbid)

                # EA -EA-1548 New Chargeback Audit
                change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_ALLOW_MEMBER}"
                chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                        cblnid=chargeback_line.cblnid,
                                        user_email=request.user.email,
                                        change_text=change_text
                                        )

                if chargeback not in chargebacks_to_process:
                    chargebacks_to_process.append(chargeback)

            for cb in chargebacks_to_process:
                # Recalculate Amounts
                cb.calculate_claim_totals_by_db(data['db_name'])
                # update stage and substage if not pending lines
                if not cb.get_my_pending_chargeback_lines():
                    cb.stage = STAGE_TYPE_VALIDATED
                    cb.substage = SUBSTAGE_TYPE_NO_ERRORS
                cb.save(using=data['db_name'])

            return ok_json(data={"message": f"Exception Action succesfully executed ({override.__name__})"})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def rerun_validations(request):
    data = {'title': 'Chargebacks - Exceptions - Rerun Validations'}
    addGlobalData(request, data)

    try:
        with transaction.atomic():

            chargebacks_to_process = []
            for chargeback_line_id in request.POST['chargebacks_lines_ids'].split("|"):
                chargeback_line = ChargeBackLine.objects.get(id=chargeback_line_id)
                chargeback = chargeback_line.chargeback_ref

                if chargeback not in chargebacks_to_process:
                    chargebacks_to_process.append(chargeback)

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
                                            change_text=change_text
                                            )
            ChargeBackDispute.objects.using(data['db_name']).filter(chargeback_ref__in=chargebacks_to_process).update(is_active=False)
            import_validations_function(data['company'].id, data['db_name'], chargebacks_to_process,request)

            return ok_json(data={"message": f"Exception Action succesfully executed ({rerun_validations.__name__})"})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def update_dispute_code_container(request):
    dispute_result = []
    response = []
    dispute_results = ChargeBackDispute.objects.filter(is_active=True, chargebackline_ref__line_status=LINE_STATUS_PENDING).exclude(dispute_code='WW').values('dispute_code').order_by().annotate(count=Count("dispute_code"))
    # EA-1155 - Correct the dispute code counts for "ALL" show that its the total number of exception lines
    dispute_result_total_count = ChargeBackLine.objects.filter(line_status=LINE_STATUS_PENDING).count()
    for dr in dispute_results:
        dispute_tootltip_obj = Dispute.objects.get(code=dr['dispute_code'])
        dispute_tootltip = dispute_tootltip_obj.description
        dispute_result.append({
            'dispute_code': dr['dispute_code'],
            'count': dr['count'],
            'tootltip': dispute_tootltip
        })
    response.append({
        'dc_code_data': dispute_result,
        'dispute_result_total_count': dispute_result_total_count
    })

    return JsonResponse({"dc_code_data": dispute_result, 'dispute_result_total_count': dispute_result_total_count}, safe=False)


def get_contract_members(request):
    data_list = []
    exclude_combination = []
    for cb_line in ChargeBackLine.objects.filter(line_status=LINE_STATUS_PENDING, disputes_codes='FF'):
        contract = cb_line.contract_ref.number
        indc_company_name = cb_line.indirect_customer_ref.company_name
        indc_location_number = cb_line.indirect_customer_ref.location_number
        contract_loc = contract +"_-_"+ indc_location_number
        if contract_loc not in exclude_combination:
            data_list.append({
                "contract_number": contract,
                "company_name": indc_company_name,
                "location_number": indc_location_number,
                "contract_start_date": cb_line.contract_ref.start_date.strftime('%m/%d/%Y'),
                "contract_end_date": cb_line.contract_ref.end_date.strftime('%m/%d/%Y'),
                "submitted_start_date": cb_line.contract_ref.start_date.strftime('%m/%d/%Y'),
                "submitted_end_date": cb_line.contract_ref.end_date.strftime('%m/%d/%Y'),
                "contract_loc": contract_loc
            })
        exclude_combination.append(contract_loc)

    return ok_json(data={'data_list': data_list})


def allow_member_update(request):
    data = {'title': 'Chargebacks - Exceptions - Allow Member'}
    addGlobalData(request, data)
    allow_member_data = json.loads(request.POST['allow_member_data'])
    processing_errors = []
    chargebacks_to_process = []
    today = datetime.datetime.now().date()
    for elem in allow_member_data:
        contract = Contract.objects.get(number=elem["contract_number"])
        indc_obj = IndirectCustomer.objects.get(location_number=elem["location_number"])
        line_start_date = convert_string_to_date(elem['submitted_start_date'])
        line_end_date = convert_string_to_date(elem['submitted_end_date'])
        is_checked = elem["is_checked"]

        if is_checked == "1":
            contract_loc = contract.number + "_-_" + indc_obj.location_number

            # Check if submitted lines are not extending contract dates
            if line_start_date < contract.start_date:
                e_messages = [f'Submitted Line start date {line_start_date.strftime("%m/%d/%Y")} is less than contract start date {contract.start_date.strftime("%m/%d/%Y")}']
                processing_errors.append({
                    'type': 'overlapping_ranges',
                    'type_text': 'Range Conflict',
                    'message': e_messages,
                    'contract_number': elem["contract_number"],
                    'location_number': elem["location_number"],
                    'company_name': indc_obj.company_name,
                    "contract_loc": contract_loc,
                    "contract_start_date": contract.start_date.strftime('%m/%d/%Y'),
                    "contract_end_date": contract.end_date.strftime('%m/%d/%Y'),
                    'submitted_start_date': line_start_date.strftime("%m/%d/%Y"),
                    'submitted_end_date': line_end_date.strftime("%m/%d/%Y")
                })
                # Go to next line
                continue

            if line_end_date > contract.end_date:
                e_messages = [f'Submitted Line end date {line_end_date.strftime("%m/%d/%Y")} is greater than contract end date {contract.end_date.strftime("%m/%d/%Y")}']
                processing_errors.append({
                    'type': 'overlapping_ranges',
                    'type_text': 'Range Conflict',
                    'message': e_messages,
                    'contract_number': elem["contract_number"],
                    'location_number': elem["location_number"],
                    'company_name': indc_obj.company_name,
                    "contract_loc": contract_loc,
                    "contract_start_date": contract.start_date.strftime('%m/%d/%Y'),
                    "contract_end_date": contract.end_date.strftime('%m/%d/%Y'),
                    'submitted_start_date': line_start_date.strftime("%m/%d/%Y"),
                    'submitted_end_date': line_end_date.strftime("%m/%d/%Y")
                })
                # Go to next line
                continue
            # Overlapping Validation
            # Get overlapping lines with non active lines
            contract_member_lines_other = ContractMember.objects.filter(Q(contract=contract), Q(status__in=[STATUS_INACTIVE, STATUS_PENDING, STATUS_PROPOSED]), Q(indirect_customer=indc_obj), Q(start_date__range=[line_start_date, line_end_date]) | Q(end_date__range=[line_start_date, line_end_date]))
            contract_member_line_other = contract_member_lines_other if contract_member_lines_other.exists() else None
            if contract_member_line_other:
                e_messages = []
                for clo in contract_member_line_other:
                    e_messages.append(f'Submitted Line conflicts with existing {clo.get_status_display()} line: location : {elem["location_number"]} with range {clo.start_date.strftime("%m/%d/%Y")}-{clo.end_date.strftime("%m/%d/%Y")}')

                processing_errors.append({
                    'type': 'overlapping_ranges',
                    'type_text': 'Range Conflict',
                    'message': e_messages,
                    'contract_number': elem["contract_number"],
                    'location_number': elem["location_number"],
                    'company_name': indc_obj.company_name,
                    "contract_loc": contract_loc,
                    "contract_start_date": contract.start_date.strftime('%m/%d/%Y'),
                    "contract_end_date": contract.end_date.strftime('%m/%d/%Y'),
                    'submitted_start_date': line_start_date.strftime("%m/%d/%Y"),
                    'submitted_end_date': line_end_date.strftime("%m/%d/%Y")
                })
                # Go to next line
                continue

            contract_member_lines_active = ContractMember.objects.filter(contract=contract, indirect_customer=indc_obj, status=STATUS_ACTIVE)
            contract_member_line_active = contract_member_lines_active if contract_member_lines_active.exists() else None
            if contract_member_line_active:
                if len(contract_member_line_active) > 1:  # Means overlapping with more than 1 Active line , which is not correct
                    e_messages = []
                    for cla in contract_member_line_active:
                        e_messages.append(f'Submitted Line conflicts with existing {cla.get_status_display()} line: location : {elem["location_number"]} with range {cla.start_date.strftime("%m/%d/%Y")}-{cla.end_date.strftime("%m/%d/%Y")}')

                    processing_errors.append({
                        'type': 'overlapping_ranges',
                        'type_text': 'Range Conflict',
                        'message': e_messages,
                        'contract_number': elem["contract_number"],
                        'location_number': elem["location_number"],
                        'company_name': indc_obj.company_name,
                        "contract_loc": contract_loc,
                        "contract_start_date": contract.start_date.strftime('%m/%d/%Y'),
                        "contract_end_date": contract.end_date.strftime('%m/%d/%Y'),
                        'submitted_start_date': line_start_date.strftime("%m/%d/%Y"),
                        'submitted_end_date': line_end_date.strftime("%m/%d/%Y")
                    })
                    # Go to next line
                    continue
                else:
                    existing_cline = contract_member_line_active[0]
                    start_date = line_start_date
                    end_date = line_end_date

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
                        e_messages = [f'Submitted Line conflicts with existing {existing_cline.get_status_display()} line: location : {elem["location_number"]} with range {existing_cline.start_date.strftime("%m/%d/%Y")}-{existing_cline.end_date.strftime("%m/%d/%Y")}']
                        processing_errors.append({
                            'type': 'overlapping_ranges',
                            'type_text': 'Range Conflict',
                            'message': e_messages,
                            'contract_number': elem["contract_number"],
                            'location_number': elem["location_number"],
                            'company_name': indc_obj.company_name,
                            "contract_loc": contract_loc,
                            "contract_start_date": contract.start_date.strftime('%m/%d/%Y'),
                            "contract_end_date": contract.end_date.strftime('%m/%d/%Y'),
                            'submitted_start_date': line_start_date.strftime("%m/%d/%Y"),
                            'submitted_end_date': line_end_date.strftime("%m/%d/%Y")
                        })
                        # Go to next line
                        continue

            if today < line_start_date:
                new_status = STATUS_PENDING
            elif today > line_end_date:
                new_status = STATUS_INACTIVE
            else:
                new_status = STATUS_ACTIVE

            # Create or Update membership line
            manage_membership = ContractMember(contract=contract, indirect_customer=indc_obj, start_date=line_start_date, end_date=line_end_date, status=new_status)
            manage_membership.save()

    # As per ticket EA-1318 - Rerun validation for all FFs
    for cb in ChargeBackLine.objects.filter(disputes_codes="FF"):
        if cb.chargeback_ref not in chargebacks_to_process:
            chargebacks_to_process.append(cb.chargeback_ref)
    ChargeBackDispute.objects.using(data['db_name']).filter(chargeback_ref__in=chargebacks_to_process).update(is_active=False)
    import_validations_function(data['company'].id, data['db_name'], chargebacks_to_process,request)

    # Get FF lines after rerunning the validation
    result = []
    data_list = []
    exclude_combination = []
    for cb_line in ChargeBackLine.objects.filter(line_status=LINE_STATUS_PENDING, disputes_codes='FF'):
        contract = cb_line.contract_ref.number
        indc_company_name = cb_line.indirect_customer_ref.company_name
        indc_location_number = cb_line.indirect_customer_ref.location_number
        contract_loc = contract + "_-_" + indc_location_number
        if contract_loc not in exclude_combination:
            submitted_start_date = cb_line.contract_ref.start_date.strftime('%m/%d/%Y')
            submitted_end_date = cb_line.contract_ref.end_date.strftime('%m/%d/%Y')
            message = []

            res = next((sub for sub in processing_errors if sub['contract_loc'] == contract_loc), None)

            if res:
                submitted_start_date = res["submitted_start_date"]
                submitted_end_date = res["submitted_end_date"]
                message = res["message"]

            data_list.append({
                "contract_number": contract,
                "company_name": indc_company_name,
                "location_number": indc_location_number,
                "contract_start_date": cb_line.contract_ref.start_date.strftime('%m/%d/%Y'),
                "contract_end_date": cb_line.contract_ref.end_date.strftime('%m/%d/%Y'),
                "submitted_start_date": submitted_start_date,
                "submitted_end_date": submitted_end_date,
                "contract_loc": contract_loc,
                "message": message
            })
        exclude_combination.append(contract_loc)

    if data_list:
        return ok_json(data={'error': 'y',
                             'error_type': 'processing_errors',
                             'message': 'Following records could not be processed',
                             'processing_errors': data_list,
                             })

    # Everything went well so return success message
    return ok_json(data={'error': 'n', 'message': 'Exception Action successfully executed (allow_member)'})


def get_indirect_customer(request):
    data_list = []
    exclude_combination = []
    for cb_line in ChargeBackLine.objects.filter(line_status=LINE_STATUS_PENDING, disputes_codes='JJ'):
        chargebackline = get_chargebackline_object(cb_line.id)
        my_indirect_customer = chargebackline.get_my_indirect_customer()
        import844_obj = chargebackline.get_my_import844_obj()
        if not my_indirect_customer:
            indc_dea_number = import844_obj.line.get('L_ShipToID', '') if import844_obj else ''
            indc_company_name = import844_obj.line.get('L_ShipToName', '') if import844_obj else ''
            indc_address1 = import844_obj.line.get('L_ShipToAddress', '') if import844_obj else '',
            indc_address2 = ''
            indc_city = import844_obj.line.get('L_ShipToCity', '') if import844_obj else ''
            indc_state = import844_obj.line.get('L_ShipToState', '') if import844_obj else ''
            indc_zip_code = import844_obj.line.get('L_ShipToZipCode', '') if import844_obj else ''
            if indc_dea_number not in exclude_combination:
                data_list.append({
                    "dea_number": indc_dea_number,
                    "location_name": indc_company_name,
                    "address1": indc_address1,
                    "address2": indc_address2,
                    "city": indc_city,
                    "state": indc_state,
                    "zip_code": indc_zip_code
                })
        exclude_combination.append(indc_dea_number)

    return ok_json(data={'data_list': data_list})

@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add_indirect_customer(request):

    data = {'title': 'Chargebacks - Exceptions - Alter Contract No.'}
    addGlobalData(request, data)
    try:
        e_messages = []
        indirect_customer_data = json.loads(request.POST['indirect_customer_data'])
        chargebacks_to_process = []
        data_list = []
        for elem in indirect_customer_data:
            is_checked = elem["is_checked"]
            if is_checked == "1":
                location_number = elem['dea_number']
                indirect_customer = IndirectCustomer.objects.using(data['db_name']).filter(location_number=location_number)
                if not indirect_customer:
                    indirectcustomer = IndirectCustomer(
                                                location_number=elem['dea_number'],
                                                company_name = elem['location_name'],
                                                address1 = elem['address1'],
                                                address2=elem['address2'],
                                                city = elem['city'],
                                                state = elem['state'],
                                                zip_code = elem['zip_code']
                                                )
                    indirectcustomer.save(using=data['db_name'])
                else:
                    data_list.append({
                        "dea_number": location_number,
                        "location_name": elem['location_name'],
                        "address1": elem['address1'],
                        "address2": elem['address2'],
                        "city": elem['city'],
                        "state": elem['state'],
                        "zip_code": elem['zip_code']
                    })
                    # e_messages.append(f'Following Indirect customer : {location_number} already exists.')
        # Re validation again for jj chargeback line
        for cb in ChargeBackLine.objects.filter(disputes_codes="JJ"):
            if cb.chargeback_ref not in chargebacks_to_process:
                chargebacks_to_process.append(cb.chargeback_ref)
        ChargeBackDispute.objects.using(data['db_name']).filter(chargeback_ref__in=chargebacks_to_process).update(
                is_active=False)
        import_validations_function(data['company'].id, data['db_name'], chargebacks_to_process, request)
        if data_list:
                return ok_json(data={'error': 'y',
                                     'error_type': 'processing_errors',
                                     'message': 'Exception Action successfully executed (add_indirect_customer)',
                                     'processing_errors': data_list,
                                     })
        # Everything went well so return success message
        return ok_json(data={'error': 'n', 'message': 'Exception Action successfully executed (add_indirect_customer)'})
    except Exception as ex:
        return bad_json(message=ex.__str__())
