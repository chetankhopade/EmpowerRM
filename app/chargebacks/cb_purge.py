from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from app.management.utilities.constants import (STAGE_TYPE_ARCHIVED, ACCOUNTING_TRANSACTION_STATUS_PENDING,
                                                AUDIT_TRAIL_CHARGEBACK_ACTION_PURGE)
from app.management.utilities.functions import (ok_json, bad_json, audit_trail, get_ip_address,chargeback_audit_trails)
from app.management.utilities.globals import addGlobalData
from erms.models import (ChargeBackHistory, ChargeBack, Import844History, ChargeBackLine, ChargeBackDispute,
                         AccountingTransaction)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'Chargebacks - Purge'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        chargebacks_ids = request.POST.get('chargebacks_ids', '')
        if not chargebacks_ids:
            return bad_json(message='Not Chargebacks Found')

        chargebacks_not_deleted = []

        for chargeback_id in chargebacks_ids.split("|"):
            # chargeback object
            chargeback = ChargeBack.objects.get(id=chargeback_id)

            # Checking conditions to see which CB can be deleted based on ticket requirements (EA-304)
            can_be_deleted = True
            reason = ''
            # 1) Chargebacks can NOT be purged if a Credit Memo has been issued (Credit Memo # field is filled in)
            if chargeback.accounting_credit_memo_number:
                can_be_deleted = False
                reason += 'Credit Memo Issued, '

            # 2) 849 has been sent (849 sent flag field is True)
            if chargeback.is_export_849:
                can_be_deleted = False
                reason += '849 Issued, '

            # 3) Archived Chargebacks Stage 5 cannot be deleted
            if chargeback.stage == STAGE_TYPE_ARCHIVED:
                can_be_deleted = False
                reason += 'Already Fully Processed, '

            # 4) Chargebacks stored in the CB History tables cannot be deleted
            if ChargeBackHistory.objects.filter(chargeback_id=chargeback_id).exists():
                can_be_deleted = False
                reason += 'Chargeback History record related'

            # 5) Chargebacks stored in no pending Accounting Transactions cannot be deleted
            if AccountingTransaction.objects.filter(cbid=chargeback.cbid).exclude(status=ACCOUNTING_TRANSACTION_STATUS_PENDING).exists():
                can_be_deleted = False
                reason += 'Accounting Transaction record related'

            if not can_be_deleted:
                chargebacks_not_deleted.append({
                    "id": chargeback_id,
                    "cbid": chargeback.cbid,
                    "number": chargeback.number,
                    "reason": reason[:-2]   # remove last comma
                })

            else:

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_PURGE,
                #             ip_address=get_ip_address(request),
                #             entity1_name=chargeback.__class__.__name__,
                #             entity1_id=chargeback.get_id_str(),
                #             entity1_reference=chargeback.cbid)

                # EA-1548 New Chargeback Audit
                change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_PURGE}"
                chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                        user_email=request.user.email,
                                        change_text=change_text,
                                        )
                # If passed all above verifications it means we can delete the chargeback and its related entities
                # Delete ChargeBackLine
                ChargeBackLine.objects.filter(chargeback_id=chargeback_id).delete()

                # Delete ChargeBackDisputes (for cblines and cb)
                ChargeBackDispute.objects.filter(chargebackline_id__in=[x.__str__() for x in chargeback.get_my_chargeback_lines().values_list('id', flat=True)]).delete()
                ChargeBackDispute.objects.filter(chargeback_id=chargeback_id).delete()

                # Delete Import844
                Import844History.objects.filter(id=chargeback.import844_id).delete()

                # Delete Accounting Transactions
                AccountingTransaction.objects.filter(cbid=chargeback.cbid, status=ACCOUNTING_TRANSACTION_STATUS_PENDING).delete()

                # Delete Chargeback
                chargeback.delete()

        return ok_json(data={"message": "Chargebacks succesfully purged",
                             "chargebacks_not_deleted": chargebacks_not_deleted})

    except Exception as ex:
        return bad_json(message=ex.__str__())
