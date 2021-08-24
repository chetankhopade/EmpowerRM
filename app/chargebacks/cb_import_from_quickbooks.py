from decimal import Decimal
import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.constants import (STAGE_TYPE_POSTED, AUDIT_TRAIL_CHARGEBACK_ACTION_IMPORT_FROM_QUICKBOOKS)
from app.management.utilities.functions import (ok_json, bad_json, convert_string_to_date_cb, audit_trail,
                                                get_ip_address,chargeback_audit_trails)
from erms.models import ChargeBack


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def process_quickbooks_file(request):
    try:
        if request.FILES and request.FILES['file']:
            myfile = request.FILES['file']
            myfile.seek(0)
            row = 0
            for line in myfile.read().decode("utf-8").splitlines():
                line = line.strip().split('|')

                cbid = int(line[0])
                qb_credit_memo_number = line[2]
                qb_total_issued = Decimal(line[3])
                qb_post_date = convert_string_to_date_cb(line[4])

                if ChargeBack.objects.filter(cbid=cbid).exists():
                    chargeback = ChargeBack.objects.filter(cbid=cbid)[0]

                    # Validation Ticket EA-637
                    # (If a CB already has Accounting info in the CM fields, it cannot be posted to accounting again (it is skipped))
                    if not chargeback.accounting_credit_memo_number and not chargeback.accounting_credit_memo_date and not chargeback.accounting_credit_memo_amount:
                        # update chargeback
                        chargeback.accounting_credit_memo_number = qb_credit_memo_number
                        chargeback.accounting_credit_memo_amount = qb_total_issued
                        chargeback.accounting_credit_memo_date = qb_post_date
                        chargeback.stage = STAGE_TYPE_POSTED
                        chargeback.save()

                        # Audit Trail
                        # audit_trail(username=request.user.username,
                        #             action=AUDIT_TRAIL_CHARGEBACK_ACTION_IMPORT_FROM_QUICKBOOKS,
                        #             ip_address=get_ip_address(request),
                        #             entity1_name=chargeback.__class__.__name__,
                        #             entity1_id=chargeback.get_id_str(),
                        #             entity1_reference=chargeback.cbid)

                        # EA -EA-1548 New Chargeback Audit
                        change_text = f"{request.user.email} ran action {AUDIT_TRAIL_CHARGEBACK_ACTION_IMPORT_FROM_QUICKBOOKS}"
                        chargeback_audit_trails(cbid=chargeback.get_id_str(),
                                                user_email=request.user.email,
                                                change_text=change_text
                                                )
                row += 1

            return ok_json(data={"message": "File has been imported and related Chargebacks have been processed!"})

        return bad_json(message='File is missing')

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message='Invalid Quickbook file')
