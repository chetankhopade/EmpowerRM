import datetime
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from app.management.utilities.functions import audit_trail, contract_audit_trails
from app.management.utilities.constants import STATUS_PENDING, STATUS_INACTIVE, STATUS_ACTIVE, AUDIT_TRAIL_ACTION_EDITED
from empowerb.settings import DATABASES
from erms.models import ContractLine, Contract

if __name__ == '__main__':

    """
        Ticket: 359, 1181
        Add a service that checks each contract every night at 12:01 AM and 
        converts pending contract lines to active if the date has arrived.
        - Check contract for pending lines.
        - If pending lines start date matches the current date: 
            _ convert the current active line for the same product to inactive and 
            _ set the end date to the day before the new range and 
            _ set the pending line to active
        - If a line end date ended yesterday then mark the line as inactive
        - Make sure these changes are added to the log user who made the change <EmpowerRM>.
        - This will run as a cron job
    """

    for db_name in [x for x in DATABASES.keys() if x != 'default']:
        print(f"\n<<< Checking Contracts Lines for: {db_name} >>>")
        today = datetime.datetime.now().date()

        all_contracts = Contract.objects.using(db_name)
        all_contract_lines = ContractLine.objects.using(db_name)

        # inactive (enddate < today)
        contracts = all_contracts.filter(end_date__lt=today)

        # Contract audit trail for inactive contracts
        for contract in contracts:
            if contract.status != STATUS_INACTIVE:
                change_text = f"For Contract {contract.number} status is changed from {contract.get_status_display()} to Inactive"
                contract_audit_trails(contract=contract.id,
                                      user_email='EmpowerRM',
                                      change_type='header',
                                      field_name='status',
                                      change_text=change_text,
                                      db=db_name)

        contracts.update(status=STATUS_INACTIVE)
        print(f"{contracts.count()} CONTRACTS updated as INACTIVE (enddate < today)")

        contract_lines = all_contract_lines.filter(end_date__lt=today)

        # Contract audit trail for inactive contract lines
        for contract_line in contract_lines:
            if contract_line.status != STATUS_INACTIVE:
                change_text = f"For Contract {contract_line.contract.number} status of line {contract_line.item.get_formatted_ndc() if contract_line.item else ''} with dates {contract_line.start_date.strftime('%m/%d/%Y') if contract_line.start_date else ''} - {contract_line.end_date.strftime('%m/%d/%Y') if contract_line.end_date else ''} is changed from {contract_line.get_status_display()} to Inactive"
                contract_audit_trails(contract=contract_line.contract.id,
                                      product=contract_line.item.id if contract_line.item else None,
                                      user_email='EmpowerRM',
                                      change_type='line',
                                      field_name='status',
                                      change_text=change_text,
                                      db=db_name)

        contract_lines.update(status=STATUS_INACTIVE)
        print(f"{contract_lines.count()} CONTRACTLINES updated as INACTIVE (enddate < today)")

        # pending (startdate > today)
        contracts = all_contracts.filter(start_date__gt=today)

        # Contract audit trail for pending contracts
        for contract in contracts:
            if contract.status != STATUS_PENDING:
                change_text = f"For Contract {contract.number} status is changed from {contract.get_status_display()} to Pending"
                contract_audit_trails(contract=contract.id,
                                      user_email='EmpowerRM',
                                      change_type='header',
                                      field_name='status',
                                      change_text=change_text,
                                      db=db_name)

        contracts.update(status=STATUS_PENDING)
        print(f"{contracts.count()} CONTRACTS updated as PENDING (startdate > today)")

        contract_lines = all_contract_lines.filter(start_date__gt=today)

        # Contract audit trail for pending contract lines
        for contract_line in contract_lines:
            if contract_line.status != STATUS_PENDING:
                change_text = f"For Contract {contract_line.contract.number} status of line {contract_line.item.get_formatted_ndc() if contract_line.item else ''} with dates {contract_line.start_date.strftime('%m/%d/%Y') if contract_line.start_date else ''} - {contract_line.end_date.strftime('%m/%d/%Y') if contract_line.end_date else ''} is changed from {contract_line.get_status_display()} to Pending"
                contract_audit_trails(contract=contract_line.contract.id,
                                      product=contract_line.item.id if contract_line.item else None,
                                      user_email='EmpowerRM',
                                      change_type='line',
                                      field_name='status',
                                      change_text=change_text,
                                      db=db_name)

        contract_lines.update(status=STATUS_PENDING)
        print(f"{contract_lines.count()} CONTRACTLINES updated as PENDING (startdate > today)")

        # active (startdate <= today <= enddate)
        contracts = all_contracts.filter(start_date__lte=today, end_date__gte=today)

        # Contract audit trail for Active contracts
        for contract in contracts:
            if contract.status != STATUS_ACTIVE:
                change_text = f"For Contract {contract.number} status is changed from {contract.get_status_display()} to Active"
                contract_audit_trails(contract=contract.id,
                                      user_email='EmpowerRM',
                                      change_type='header',
                                      field_name='status',
                                      change_text=change_text,
                                      db=db_name)

        contracts.update(status=STATUS_ACTIVE)
        print(f"{contracts.count()} CONTRACTS updated as ACTIVE (startdate <= today <= enddate)")

        contract_lines = all_contract_lines.filter(start_date__lte=today, end_date__gte=today)

        # Contract audit trail for Active contract lines
        for contract_line in contract_lines:
            if contract_line.status != STATUS_ACTIVE:
                change_text = f"For Contract {contract_line.contract.number} status of line {contract_line.item.get_formatted_ndc() if contract_line.item else ''} with dates {contract_line.start_date.strftime('%m/%d/%Y') if contract_line.start_date else ''} - {contract_line.end_date.strftime('%m/%d/%Y') if contract_line.end_date else ''} is changed from {contract_line.get_status_display()} to Active"
                contract_audit_trails(contract=contract_line.contract.id,
                                      product=contract_line.item.id if contract_line.item else None,
                                      user_email='EmpowerRM',
                                      change_type='line',
                                      field_name='status',
                                      change_text=change_text,
                                      db=db_name)

        contract_lines.update(status=STATUS_ACTIVE)
        print(f"{contract_lines.count()} CONTRACTLINES updated as ACTIVE (startdate <= today <= enddate)")


        # for expired_active_contract_lines in ContractLine.objects.using(db_name).filter(end_date__lt=today):
        #     expired_active_contract_lines.status = STATUS_INACTIVE
        #     expired_active_contract_lines.save(using=db_name)

        # pending_contract_lines = ContractLine.objects.using(db_name).filter(status=STATUS_PENDING)
        # if pending_contract_lines:
        #     for contract_line in pending_contract_lines:
        #         print(f"Updating pending Contract Line: {contract_line.get_id_str()}")
        #
        #         history_dict = {}
        #         if contract_line.end_date < today or contract_line.start_date == today:
        #
        #             # get current data Before changes to store in history dict for audit
        #             history_dict['before'] = contract_line.get_current_info_for_audit()
        #
        #             # If a line end date ended yesterday then mark the line as inactive
        #             if contract_line.end_date < today:
        #                 contract_line.status = STATUS_INACTIVE
        #                 print(f"CLine updated as INACTIVE : {contract_line.get_id_str()}")
        #
        #             # If pending lines start date matches the current date
        #             if contract_line.start_date == today:
        #                 # convert the current active line for the same product to inactive
        #                 ContractLine.objects.using(db_name).filter(item=contract_line.item, status=STATUS_ACTIVE).update(status=STATUS_INACTIVE,
        #                                                                                                                  end_date=contract_line.start_date - datetime.timedelta(days=1))
        #                 # set the pending line to active
        #                 contract_line.status = STATUS_ACTIVE
        #                 print(f"CLine updated as ACTIVE : {contract_line.get_id_str()}")
        #
        #             contract_line.save(using=db_name)
        #
        #             # get current data After changes to store in history dict for audit
        #             history_dict['after'] = contract_line.get_current_info_for_audit()
        #
        #             # Audit Trail
        #             audit_trail(username='EmpowerRM',
        #                         action=AUDIT_TRAIL_ACTION_EDITED,
        #                         ip_address='localhost',
        #                         entity1_name=contract_line.__class__.__name__,
        #                         entity1_id=contract_line.get_id_str(),
        #                         entity1_reference=contract_line.get_id_str(),
        #                         entity2_name=contract_line.contract.__class__.__name__,
        #                         entity2_id=contract_line.contract.get_id_str(),
        #                         entity2_reference=contract_line.contract.number,
        #                         history_dict=history_dict,
        #                         db=db_name)
        # else:
        #     print(f"There are not pending Contract Lines for this company")
