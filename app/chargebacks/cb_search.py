import json
from itertools import chain

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import (convert_string_to_date, datatable_handler, bad_json)
from app.management.utilities.globals import addGlobalData
from erms.models import (ChargeBackHistory, ChargeBack, DirectCustomer)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'Chargebacks - Search', 'header_title': 'Chargeback > Search', 'header_target': '/chargebacks'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # for filters
    data['my_customers'] = DirectCustomer.objects.all()
    # for active tab
    data['active_tab'] = 's'
    data['menu_option'] = 'menu_chargebacks'
    return render(request, "chargebacks/search/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request):
    """
    call DT Handler function with the required params: request, queryset and search_fields
    """
    try:
        if not request.POST['payload']:
            response = {
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0
            }
        else:
            kwargs = {}
            payload = json.loads(request.POST['payload'])

            cb_cbid = payload.get('cbid', '')
            cb_customer_id = payload.get('customer_id', '')
            cb_number = payload.get('cbnumber', '')
            cb_distributor_id = payload.get('distributor_id', '')
            cb_credit_memo = payload.get('credit_memo', '')
            cb_start_date = payload.get('start_date', '')
            cb_unique_line = payload.get('unique_line', '')
            cb_end_date = payload.get('end_date', '')

            if cb_cbid and cb_cbid.isdigit():
                kwargs['cbid'] = int(cb_cbid)

            if cb_customer_id:
                kwargs['customer_ref_id'] = cb_customer_id

            if cb_distributor_id and cb_distributor_id != 'null':
                kwargs['distribution_center_ref_id'] = cb_distributor_id

            if cb_number:
                kwargs['number__icontains'] = cb_number

            if cb_start_date:
                kwargs['updated_at__gte'] = convert_string_to_date(cb_start_date)

            if cb_end_date:
                kwargs['updated_at__lte'] = convert_string_to_date(cb_end_date)

            if cb_credit_memo:
                kwargs['accounting_credit_memo_number__icontains'] = cb_credit_memo

            if cb_unique_line:
                kwargs['chargebackline__invoice_line_no'] = cb_unique_line

            chargebacks_open = ChargeBack.objects.filter(**kwargs).distinct()
            chargebacks_history = ChargeBackHistory.objects.filter(**kwargs).distinct()

            queryset = list(chain(chargebacks_history, chargebacks_open))

            search_fields = ['cbid', 'cbnumber']
            response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields, is_summary=True)

        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())
