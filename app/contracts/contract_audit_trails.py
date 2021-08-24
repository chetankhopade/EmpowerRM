from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import datatable_handler, bad_json
from erms.models import Contract, ContractAuditTrail


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def load_data(request, contract_id):
    try:
        contract = Contract.objects.get(id=contract_id)
        queryset = contract.get_audits().filter(contract_id=contract_id)

        if not queryset:
            return JsonResponse({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
            })

        search_fields = ['contract__number', 'user_email', 'change_type', 'field_name', 'product__ndc', 'change_text']
        response = datatable_handler(request=request, queryset=queryset, search_fields=search_fields)
        return JsonResponse(response)

    except Exception as ex:
        return bad_json(message=ex.__str__())