from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from app.management.utilities.constants import (STAGE_TYPE_PROCESSED, STAGE_TYPE_ARCHIVED, STAGE_TYPE_POSTED,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_ARCHIVE)
from app.management.utilities.functions import (ok_json, bad_json, move_chargeback_to_chargeback_history_table,
                                                move_chargebacklines_to_chargebackline_history_table,
                                                move_chargebackdisputes_to_chargebackdispute_history_table,
                                                audit_trail, get_ip_address, chargeback_audit_trails)
from app.management.utilities.globals import addGlobalData
from erms.models import (ChargeBack, ChargeBackDispute)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
    Archive the CB, actions:
    - All selected CBs are changed to stage 5
    - The CB header rows are moved to the chargeback_history table
    - The associated CB Lines are moved to the chargebackline_history table
    - The associated CB Lines are deleted the chargebackline table
    - The CB header rows are deleted from the chargeback table
    :param request:
    :return:
    """
    data = {'title': 'Chargebacks - Archive'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():

            chargebacks_ids = request.POST.get('chargebacks_ids', '')
            if not chargebacks_ids:
                return bad_json(message='Not Chargebacks Found')

            cbids_not_archived = []
            for chargeback_id in chargebacks_ids.split("|"):
                chargeback = ChargeBack.objects.get(id=chargeback_id)
                chargeback_lines = chargeback.get_my_chargeback_lines()
                disputes = ChargeBackDispute.objects.filter(Q(chargeback_ref=chargeback) | Q(chargebackline_ref__in=chargeback_lines)).distinct()

                # Before requirement: The process can only run against CBs in Stage 4
                # New Ticket EA-676: If Chargeback is entered manually allow user to archive without first creating 849
                if chargeback.stage == STAGE_TYPE_PROCESSED or (chargeback.stage == STAGE_TYPE_POSTED and not chargeback.is_received_edi):

                    # 1) selected CBs are changed to stage 5
                    chargeback.stage = STAGE_TYPE_ARCHIVED
                    chargeback.save()

                    # 2) CB header rows are moved to the chargeback_history table
                    move_chargeback_to_chargeback_history_table(chargeback)

                    # 3) The associated CB Lines are moved to the chargebackline_history table
                    move_chargebacklines_to_chargebackline_history_table(chargeback_lines)

                    # 4) Move disputes to disputes history
                    move_chargebackdisputes_to_chargebackdispute_history_table(disputes, data['db_name'])

                    # Audit Trail
                    # audit_trail(username=request.user.username,
                    #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_ARCHIVE,
                    #             ip_address=get_ip_address(request),
                    #             entity1_name=chargeback.__class__.__name__,
                    #             entity1_id=chargeback.get_id_str(),
                    #             entity1_reference=chargeback.cbid)

                    # EA -EA-1548 New Chargeback Audit
                    change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_ARCHIVE}"
                    chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                            user_email=request.user.email,
                                            change_text=change_text,
                                            )

                    # 4) Delete Open Chargebacklines
                    chargeback_lines.delete()

                    # 5) Delete Open Disputes
                    disputes.delete()

                    # 6) Delete Open Chargeback
                    chargeback.delete()

                else:
                    cbids_not_archived.append(chargeback.cbid)

            if cbids_not_archived:
                return ok_json(data={"message": f"Some chargebacks could not be archived: ({','.join([str(x) for x in cbids_not_archived])})",
                                     'cbids_not_archived': cbids_not_archived})
            else:
                return ok_json(data={"message": "All selected Chargebacks have been archived"})

    except Exception as ex:
        return bad_json(message=ex.__str__())
