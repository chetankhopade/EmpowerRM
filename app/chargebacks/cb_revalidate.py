from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import datetime
from app.management.utilities.constants import AUDIT_TRAIL_CHARGEBACK_ACTION_REVALIDATE
from app.management.utilities.functions import (ok_json, bad_json, audit_trail, get_ip_address, chargeback_audit_trails)
from app.management.utilities.globals import addGlobalData
from app.tasks import import_validations
from erms.models import ChargeBack, ChargeBackDispute


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def view(request):
    data = {'title': 'Chargebacks - Rerun Validations'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        chargebacks_ids = request.POST.get('chargebacks_ids', '')
        if not chargebacks_ids:
            return bad_json(message='Not Chargebacks Found')

        chargebacks_to_process = []
        for chargeback_id in chargebacks_ids.split("|"):
            chargeback = ChargeBack.objects.get(id=chargeback_id)
            if chargeback not in chargebacks_to_process:
                chargebacks_to_process.append(chargeback)

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_REVALIDATE,
                #             ip_address=get_ip_address(request),
                #             entity1_name=chargeback.__class__.__name__,
                #             entity1_id=chargeback.get_id_str(),
                #             entity1_reference=chargeback.cbid)
                #
                # EA -EA-1548 New Chargeback Audit
                change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_REVALIDATE}"
                chargeback_audit_trails(cbid=chargeback.get_id_str(),
                           user_mail=request.user.email,
                           change_text=change_text)

        ChargeBackDispute.objects.using(data['db_name']).filter(chargeback_ref__in=chargebacks_to_process).update(is_active=False)
        # EA-1690 HOTFIX: Rerun Validation on main chargeback page not working
        import_validations(data['company'].id, data['db_name'], chargebacks_to_process,request)

        return ok_json(data={"message": "Chargebacks have been succesfully revalidated"})

    except Exception as ex:
        return bad_json(message=ex.__str__())
