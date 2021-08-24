import datetime
import os
import sys
import django
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from app.management.utilities.functions import audit_trail
from app.management.utilities.constants import STATUS_PENDING, STATUS_INACTIVE, STATUS_ACTIVE, AUDIT_TRAIL_ACTION_EDITED
from empowerb.settings import DATABASES
from erms.models import ContractMember, Contract, IndirectCustomer

if __name__ == '__main__':

    for db_name in [x for x in DATABASES.keys() if x != 'default']:
        print(f"\n<<< Checking pending Members for: {db_name} >>>")
        today = datetime.datetime.now().date()
        time.sleep(0.5)

        for pending_member in ContractMember.objects.using(db_name).filter(status__in=[STATUS_ACTIVE, STATUS_PENDING]):
            print(f"Updating pending members: {pending_member.get_id_str()}")

            history_dict = {
                'before': pending_member.get_current_info_for_audit()
            }

            # get current data Before changes to store in history dict for audit
            if pending_member.status == STATUS_PENDING:

                if pending_member.start_date == today:
                    try:
                        contract = Contract.objects.using(db_name).get(id=pending_member.contract_id)
                    except:
                        contract = None

                    try:
                        indirect_customer = IndirectCustomer.objects.using(db_name).get(id=pending_member.indirect_customer_id)
                    except:
                        indirect_customer = None

                    if contract and indirect_customer:
                        for existing_cm in ContractMember.objects.using(db_name).filter(contract=contract, indirect_customer=indirect_customer, status=STATUS_ACTIVE):
                            # Changing any active existing records inactive
                            print("Changing any active existing records inactive")
                            existing_cm.status = STATUS_INACTIVE
                            existing_cm.save(using=db_name)

                        # For Pending member setting status to active
                        print("For Pending member setting status to active")
                        pending_member.status = STATUS_ACTIVE
                        pending_member.save(using=db_name)

            if pending_member.status == STATUS_ACTIVE and pending_member.end_date == today:
                # get current data Before changes to store in history dict for audit
                history_dict['before'] = pending_member.get_current_info_for_audit()
                # For active member setting status to inactive
                pending_member.status = STATUS_INACTIVE
                pending_member.save(using=db_name)

            # get current data After changes to store in history dict for audit
            history_dict['after'] = pending_member.get_current_info_for_audit()

            # Audit Trail
            # audit_trail(username='EmpowerRM',
            #             action=AUDIT_TRAIL_ACTION_EDITED,
            #             ip_address='localhost',
            #             entity1_name=pending_member.__class__.__name__,
            #             entity1_id=pending_member.get_id_str(),
            #             entity1_reference=pending_member.get_id_str(),
            #             history=history_dict,
            #             db=db_name)
