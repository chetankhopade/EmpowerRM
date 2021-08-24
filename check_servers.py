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

from app.management.utilities.functions import audit_trail, contract_audit_trails
from app.management.utilities.constants import STATUS_PENDING, STATUS_INACTIVE, STATUS_ACTIVE, AUDIT_TRAIL_ACTION_EDITED
from empowerb.settings import DATABASES
from erms.models import ContractCustomer

if __name__ == '__main__':

    """
        Ticket: 365
        Add a service that checks each Contract Server every night at 12:01 AM and 
        converts pending servers lines to active if the date has arrived.
            - Check_contract service needs to copy contract line (product) functionality and apply to contract server lines.
            - Every night the service will check today’s date against date ranges.
            - If Pending and the start date is today, change to Active. Change the current Active row to Inactive
    """

    for db_name in [x for x in DATABASES.keys() if x != 'default']:
        print(f"\n<<< Checking pending Servers for: {db_name} >>>")
        today = datetime.datetime.now().date()
        time.sleep(0.5)
        pending_servers = ContractCustomer.objects.using(db_name).filter(status=STATUS_PENDING)
        if pending_servers:
            for pending_server in pending_servers:
                print(f"Updating pending server: {pending_server.get_id_str()}")

                history_dict = {}

                if pending_server.end_date < today or pending_server.start_date == today:

                    # get current data Before changes to store in history dict for audit
                    history_dict['before'] = pending_server.get_current_info_for_audit()

                    # If a line end date ended yesterday then mark the line as inactive
                    if pending_server.end_date < today:
                        pending_server.status = STATUS_INACTIVE
                        print(f"updated  server as INACTIVE : {pending_server.get_id_str()}")

                    # If pending lines start date matches the current date
                    if pending_server.start_date == today:
                        # convert the current active line for the same product to inactive
                        ContractCustomer.objects.using(db_name).filter(item=pending_server.item, status=STATUS_ACTIVE).update(status=STATUS_INACTIVE, end_date=pending_server.start_date - datetime.timedelta(days=1))
                        # set the pending line to active
                        pending_server.status = STATUS_ACTIVE
                        print(f"updated  server as ACTIVE : {pending_server.get_id_str()}")

                    pending_server.save(using=db_name)

                    # get current data After changes to store in history dict for audit
                    history_dict['after'] = pending_server.get_current_info_for_audit()

                    changed_items = [(k, history_dict['after'][k], v) for k, v in history_dict['before'].items() if history_dict['after'][k] != v]
                    if changed_items:
                        for elem in changed_items:
                            if elem[0] != 'type':
                                change_text = f"For Contract {pending_server.contract.number} {elem[0]} is changed from {elem[2]} to {elem[1]}"
                                contract_audit_trails(contract=pending_server.contract.id,
                                                      user_email='EmpowerRM',
                                                      change_type='server',
                                                      field_name=elem[0],
                                                      change_text=change_text,
                                                      db=db_name)

                    # Audit Trail
                    # audit_trail(username='EmpowerRM',
                    #             action=AUDIT_TRAIL_ACTION_EDITED,
                    #             ip_address='localhost',
                    #             entity1_name=pending_server.__class__.__name__,
                    #             entity1_id=pending_server.get_id_str(),
                    #             entity1_reference=pending_server.get_id_str(),
                    #             history=history_dict,
                    #             db=db_name)

        else:
            print(f"There are not pending Servers for this company")
