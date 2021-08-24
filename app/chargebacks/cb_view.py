import os
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (STAGE_TYPE_IMPORTED, SUBSTAGE_TYPE_DUPLICATES, SUBSTAGE_TYPE_INVALID,
                                                SUBSTAGE_TYPE_ERRORS, STAGE_TYPE_VALIDATED, SUBSTAGE_TYPE_NO_ERRORS,
                                                STAGE_TYPE_POSTED, STAGE_TYPE_PROCESSED,
                                                SUBSTAGE_TYPE_WAITING_FOR_RESPONSE, LINE_STATUS_PENDING,
                                                LINE_STATUS_DISPUTED, LINE_STATUS_APPROVED)
from app.management.utilities.functions import (datatable_handler, bad_json, get_stage_and_substage_based_on_key,
                                                get_chargeback_object, get_chargebackline_object,
                                                strip_special_characters_and_spaces)
from app.management.utilities.globals import addGlobalData
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_844_ERM_INTAKE
from erms.models import (ChargeBack, Contract,
                         DirectCustomer, Item, DistributionCenter, ChargeBackHistory, AuditChargeBack)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'Chargebacks - Processing', 'header_title': 'Chargebacks > Processing'}

    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    data['844files'] = [x for x in os.listdir(os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), DIR_NAME_844_ERM_INTAKE))]

    # for modals manual CB creation
    data['my_customers'] = DirectCustomer.objects.order_by('name')
    data['my_contracts'] = Contract.objects.order_by('number')
    data['my_items'] = Item.objects.order_by('ndc')

    # for acct integrations
    data['is_quickbooks_integration'] = data['company'].is_quickbooks_integration
    data['is_acumatica_integration'] = data['company'].is_acumatica_integration
    data['is_manual_integration'] = data['company'].is_manual_integration
    data['is_none_integration'] = data['company'].is_none_integration

    # automate import ?
    data['automate_import'] = data['company'].my_company_settings().automate_import

    # active tab
    data['active_tab'] = 'p'
    data['menu_option'] = 'menu_chargebacks'
    return render(request, "chargebacks/processing/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_cbs_counters_data(request):
    cbs = ChargeBack.objects.order_by('cbid')

    if not cbs:
        return JsonResponse({
            "total": {
                'count': 0,
                'subtotal': 0,
                'issued': 0,
            },
            "resubmissions": {
                'count': 0,
                'subtotal': 0,
                'issued': 0,
            },
            "duplicates": {
                'count': 0,
                'subtotal': 0,
                'issued': 0,
            },
            "invalids": {
                'count': 0,
                'subtotal': 0,
                'issued': 0,
            },
            "issues": {
                'count': 0,
                'subtotal': 0,
                'issued': 0,
            },
            "failed_validations": {
                'count': 0,
                'subtotal': 0,
                'issued': 0,
            },
            "ready_to_post": {
                'count': 0,
                'subtotal': 0,
                'issued': 0,
            },
            "generate_849": {
                'count': 0,
                'subtotal': 0,
                'issued': 0,
            },
            "archive": {
                'count': 0,
                'subtotal': 0,
                'issued': 0,
            }
        })

    # Total
    count = cbs.count(),
    subtotal = float(Decimal(cbs.aggregate(sum=Sum('claim_subtotal'))['sum']).quantize(Decimal(10) ** -2)) if cbs else 0
    issued = float(Decimal(cbs.aggregate(sum=Sum('claim_issue'))['sum']).quantize(Decimal(10) ** -2)) if cbs else 0
    total_obj = {
        'count': count,
        'subtotal': subtotal,
        'issued': issued,
    }

    # Resubmissions
    resubmissions = cbs.filter(type='15')   # Ticket EA-1132 Filter should be based just on CBType
    count = resubmissions.count(),
    subtotal = float(Decimal(resubmissions.aggregate(sum=Sum('claim_subtotal'))['sum']).quantize(Decimal(10) ** -2)) if resubmissions else 0
    issued = float(Decimal(resubmissions.aggregate(sum=Sum('claim_issue'))['sum']).quantize(Decimal(10) ** -2)) if resubmissions else 0
    resubmissions_obj = {
        'count': count,
        'subtotal': subtotal,
        'issued': issued
    }

    # Duplicates
    duplicates = cbs.filter(stage=STAGE_TYPE_IMPORTED, substage=SUBSTAGE_TYPE_DUPLICATES)
    count = duplicates.count(),
    subtotal = float(Decimal(duplicates.aggregate(sum=Sum('claim_subtotal'))['sum']).quantize(Decimal(10) ** -2)) if duplicates else 0
    issued = float(Decimal(duplicates.aggregate(sum=Sum('claim_issue'))['sum']).quantize(Decimal(10) ** -2)) if duplicates else 0
    duplicates_obj = {
        'count': count,
        'subtotal': subtotal,
        'issued': issued
    }

    # Invalids
    invalids = cbs.filter(stage=STAGE_TYPE_IMPORTED, substage=SUBSTAGE_TYPE_INVALID)
    count = invalids.count(),
    subtotal = float(Decimal(invalids.aggregate(sum=Sum('claim_subtotal'))['sum']).quantize(Decimal(10) ** -2)) if invalids else 0
    issued = float(Decimal(invalids.aggregate(sum=Sum('claim_issue'))['sum']).quantize(Decimal(10) ** -2)) if invalids else 0
    invalids_obj = {
        'count': count,
        'subtotal': subtotal,
        'issued': issued
    }

    # Issues
    issues = cbs.filter(stage=STAGE_TYPE_IMPORTED, substage=SUBSTAGE_TYPE_ERRORS)
    count = issues.count(),
    subtotal = float(Decimal(issues.aggregate(sum=Sum('claim_subtotal'))['sum']).quantize(Decimal(10) ** -2)) if issues else 0
    issued = float(Decimal(issues.aggregate(sum=Sum('claim_issue'))['sum']).quantize(Decimal(10) ** -2)) if issues else 0
    issues_obj = {
        'count': count,
        'subtotal': subtotal,
        'issued': issued
    }

    # Failed Validations
    failed_validations = cbs.filter(stage=STAGE_TYPE_VALIDATED, substage=SUBSTAGE_TYPE_ERRORS)
    count = failed_validations.count(),
    subtotal = float(Decimal(failed_validations.aggregate(sum=Sum('claim_subtotal'))['sum']).quantize(Decimal(10) ** -2)) if failed_validations else 0
    issued = float(Decimal(failed_validations.aggregate(sum=Sum('claim_issue'))['sum']).quantize(Decimal(10) ** -2)) if failed_validations else 0
    failed_validations_obj = {
        'count': count,
        'subtotal': subtotal,
        'issued': issued
    }

    # Ready to Post
    ready_to_post = cbs.filter(Q(stage=STAGE_TYPE_VALIDATED, substage=SUBSTAGE_TYPE_NO_ERRORS) |
                               Q(stage=STAGE_TYPE_POSTED, substage=SUBSTAGE_TYPE_WAITING_FOR_RESPONSE) |
                               Q(stage=STAGE_TYPE_POSTED, substage=SUBSTAGE_TYPE_ERRORS))
    count = ready_to_post.count(),
    subtotal = float(Decimal(ready_to_post.aggregate(sum=Sum('claim_subtotal'))['sum']).quantize(Decimal(10) ** -2)) if ready_to_post else 0
    issued = float(Decimal(ready_to_post.aggregate(sum=Sum('claim_issue'))['sum']).quantize(Decimal(10) ** -2)) if ready_to_post else 0
    ready_to_post_obj = {
        'count': count,
        'subtotal': subtotal,
        'issued': issued
    }

    # Generate 849
    generate_849 = cbs.filter(stage=STAGE_TYPE_POSTED, substage=SUBSTAGE_TYPE_NO_ERRORS)
    count = generate_849.count(),
    subtotal = float(Decimal(generate_849.aggregate(sum=Sum('claim_subtotal'))['sum']).quantize(Decimal(10) ** -2)) if generate_849 else 0
    issued = float(Decimal(generate_849.aggregate(sum=Sum('claim_issue'))['sum']).quantize(Decimal(10) ** -2)) if generate_849 else 0
    generate_849_obj = {
        'count': count,
        'subtotal': subtotal,
        'issued': issued
    }

    # Archive
    archive = cbs.filter(stage=STAGE_TYPE_PROCESSED, substage=SUBSTAGE_TYPE_NO_ERRORS)
    count = archive.count(),
    subtotal = float(Decimal(archive.aggregate(sum=Sum('claim_subtotal'))['sum']).quantize(Decimal(10) ** -2)) if archive else 0
    issued = float(Decimal(archive.aggregate(sum=Sum('claim_issue'))['sum']).quantize(Decimal(10) ** -2)) if archive else 0
    archive_obj = {
        'count': count,
        'subtotal': subtotal,
        'issued': issued
    }

    response = {
        "total": total_obj,
        "resubmissions": resubmissions_obj,
        "duplicates": duplicates_obj,
        "invalids": invalids_obj,
        "issues": issues_obj,
        "failed_validations": failed_validations_obj,
        "ready_to_post": ready_to_post_obj,
        "generate_849":generate_849_obj,
        "archive": archive_obj
    }
    return JsonResponse(response)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    try:
        queryset = ChargeBack.objects.order_by('cbid')

        key = request.POST['k']
        if key:
            # get stage (obj[0]) and substage (obj[1]) from utility function and filter cbs
            obj = get_stage_and_substage_based_on_key(key)
            # specific for new substage Waiting for response
            if key == 'ready_to_post':
                queryset = queryset.filter(Q(stage=obj[0], substage=obj[1]) |
                                           Q(stage=obj[2], substage=obj[3]) |
                                           Q(stage=obj[4], substage=obj[5]))
            elif key == 'resubmissions':
                queryset = queryset.filter(type='15')
            else:
                queryset = queryset.filter(stage=obj[0], substage=obj[1])

        search_fields = ['cbid', 'number', 'stage', 'substage', 'customer', 'distributor']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def chargeback_details(request, chargeback_id):
    """
        Company's Chargeback - Detail
    """
    data = {'title': 'Chargeback Details', 'header_target': '/chargebacks'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get CB
    data['chargeback'] = chargeback = get_chargeback_object(chargeback_id)

    # vars to pass to the html
    data['my_customer'] = chargeback.get_my_customer()
    data['my_distribution_center'] = chargeback.get_my_distribution_center()
    data['sum_lines_credit_amt'] = chargeback.get_my_chargeback_lines_sum_claim_amt()

    # lines
    data['chargebacks_lines'] = chargebacks_lines = chargeback.get_my_chargeback_lines()
    data['chargebacks_lines_dict_representation'] = [x.get_my_dict_representation() for x in chargebacks_lines]

    # 844 Import
    import844_obj = chargeback.get_my_import844_obj()
    data['my_import844_header'] = import844_obj.header if import844_obj else None
    data['my_import844_filename'] = import844_obj.file_name if import844_obj else ''

    # Errors (disputes)
    data['my_disputes'] = chargeback.get_my_active_disputes()

    # Lists needed to populate data in manual cb modals
    data['my_customers'] = DirectCustomer.objects.order_by('name')
    data['my_distributions_centers'] = DistributionCenter.objects.order_by('name')
    data['my_contracts'] = Contract.objects.order_by('number')
    data['my_items'] = Item.objects.order_by('ndc')

    data['header_title'] = f"Chargeback > Detail: CB #{chargeback.cbid}"
    data['menu_option'] = 'menu_chargebacks'
    return render(request, "chargebacks/processing/cb_details.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data_cblines(request, chargeback_id):
    try:
        try:
            chargeback = ChargeBack.objects.get(id=chargeback_id)
        except:
            # EA-1456 - HOTFIX: 1.8 CB Details Lines tab, does not show lines if CB is archived
            chargeback = ChargeBackHistory.objects.get(id=chargeback_id)
        queryset = chargeback.get_my_chargeback_lines()

        # query by status
        q = int(request.POST.get('q', 0))
        if q:
            if q == LINE_STATUS_PENDING:
                queryset = queryset.filter(line_status=LINE_STATUS_PENDING)
            elif q == LINE_STATUS_DISPUTED:
                queryset = queryset.filter(line_status=LINE_STATUS_DISPUTED)
            else:
                queryset = queryset.filter(line_status=LINE_STATUS_APPROVED)

        search_fields = ['contract_no', 'item_ndc', 'item_description', 'cblnid','invoice_no']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=True)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def chargeback_line_details(request, chargebackline_id):
    """
        Company's Chargeback Line - Detail
    """
    data = {'title': 'ChargebackLine Details', 'header_title': 'Chargeback', 'header_target': '/chargebacks'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Company Items
    data['chargebackline'] = chargebackline = get_chargebackline_object(chargebackline_id)

    data['my_chargeback'] = my_chargeback = chargebackline.get_my_chargeback()

    # vars to pass to the html
    data['my_contract'] = chargebackline.get_my_contract()

    # disputes
    data['my_disputes'] = chargebackline.get_my_disputes().order_by("-created_at")
    data['my_disputes_count'] = chargebackline.count_of_active_disputes()

    # Purcharser
    data['my_indirect_customer'] = chargebackline.get_my_indirect_customer()

    # Invoice
    data['my_item'] = chargebackline.get_my_item()

    # Approved Reason
    data['my_approved_reason'] = chargebackline.get_my_approved_reason()

    # 844 Import
    import844_obj = chargebackline.get_my_import844_obj()
    if not data['my_indirect_customer']:
        data['my_indirect_customer'] = {'company_name':import844_obj.line.get('L_ShipToName', '') if import844_obj else '',
                                        'address1':import844_obj.line.get('L_ShipToAddress', '') if import844_obj else '',
                                        'address2':'',
                                        'city': import844_obj.line.get('L_ShipToCity', '') if import844_obj else '',
                                        'state': import844_obj.line.get('L_ShipToState', '') if import844_obj else '',
                                        'zip_code': import844_obj.line.get('L_ShipToZipCode', '') if import844_obj else '',
                                        'location_number': import844_obj.line.get('L_ShipToID', '') if import844_obj else ''}
        
    data['my_import844_line'] = import844_obj.line if import844_obj else None
    data['my_submitted_contract'] = import844_obj.line['L_ContractNo'] if import844_obj else None
    data['my_import844_filename'] = import844_obj.file_name if import844_obj else ''

    # CB Line history
    data['my_cbline_history'] = AuditChargeBack.objects.all().filter(user_email=request.user.email,cblnid=chargebackline.cblnid)

    if request.method == 'POST':
        chargebackline.user_dispute_note = strip_special_characters_and_spaces(request.POST['disputeNotesInput'])
        chargebackline.save()

    data['breadcrumb_title1'] = f' > CB #{my_chargeback.cbid}'
    data['breadcrumb_target1'] = f'/chargebacks/{my_chargeback.get_id_str()}/details'
    data['breadcrumb_title2'] = f' > Line #{chargebackline.cblnid}'
    data['menu_option'] = 'menu_chargebacks'
    return render(request, "chargebacks/processing/line_details.html", data)



@login_required(redirect_field_name='ret', login_url='/login')
def chargeback_line_modal_details(request, chargebackline_id):
    """
        Company's Chargeback Line - Detail
    """
    data = {'title': 'ChargebackLine Details', 'header_title': 'Chargeback', 'header_target': '/chargebacks'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Company Items
    data['chargebackline'] = chargebackline = get_chargebackline_object(chargebackline_id)

    # vars to pass to the html
    data['my_contract'] = chargebackline.get_my_contract()

    # 844 Import
    # EA-962 - CBLine Detail Error tab not showing Inactive disputes , So getting them all
    data['my_disputes'] = my_disputes = chargebackline.get_my_disputes()
    data['my_disputes_count'] = my_disputes.count()

    # Purcharser
    data['my_indirect_customer'] = chargebackline.get_my_indirect_customer()

    # Invoice
    data['my_item'] = chargebackline.get_my_item()

    # Approved Reason
    data['my_approved_reason'] = chargebackline.get_my_approved_reason()

    # 844 Import
    import844_obj = chargebackline.get_my_import844_obj()
    data['my_import844_line'] = import844_obj.line if import844_obj else None
    data['my_submitted_contract'] = import844_obj.line['L_ContractNo'] if import844_obj else None
    data['menu_option'] = 'menu_chargebacks'
    return render(request, 'chargebacks/modals/modals_details_lines.html', data)


@login_required(redirect_field_name='ret', login_url='/login')
def chargeback_modal_details(request, chargeback_id):
    """
        Company's Chargeback - Modal Detail
    """
    data = {'title': 'Chargeback Details', 'header_target': '/chargebacks'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # Get CB
    data['chargeback'] = chargeback = get_chargeback_object(chargeback_id)
    # vars to pass to the html
    data['my_customer'] = chargeback.get_my_customer()
    data['my_distribution_center'] = chargeback.get_my_distribution_center()
    data['sum_lines_credit_amt'] = chargeback.get_my_chargeback_lines_sum_claim_amt()

    # lines
    data['chargebacks_lines'] = chargeback.get_my_chargeback_lines()

    # 844 Import
    import844_obj = chargeback.get_my_import844_obj()
    data['my_import844_header'] = import844_obj.header if import844_obj else None

    # Errors (disputes)
    data['my_disputes'] = chargeback.get_my_disputes()

    data['header_title'] = f"Chargeback > Detail: CB #{chargeback.cbid}"
    data['menu_option'] = 'menu_chargebacks'
    return render(request, "chargebacks/modals/modals_details_cb.html", data)

@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data_cbhistory(request, chargeback_id):
    try:

        chargeback = ChargeBack.objects.get(id=chargeback_id)
        # query by status
        queryset = AuditChargeBack.objects.all()
        queryset = queryset.filter(user_email=request.user.email,cbid=chargeback_id)
        search_fields = ['date', 'time', 'change_text','cbid__cbid']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)
    except Exception as ex:
        return bad_json(message=ex.__str__())
