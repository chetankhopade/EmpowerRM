import os
import sys

import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from empowerb.settings import DATABASES
from erms.models import ChargeBackLine, ChargeBackLineHistory


def update_chargebacklines_disputes_codes_and_notes(db):

    chargebacklines_with_active_disputes = ChargeBackLine.objects.using(db).filter(chargebackdispute__isnull=False, chargebackdispute__is_active=True, disputes_codes__isnull=True).order_by('-cblnid')
    print(f"CBLines (with active disputes) to be updated: {chargebacklines_with_active_disputes.count()}")
    for cbline in chargebacklines_with_active_disputes.iterator():
        try:
            cbline.disputes_codes = cbline.list_of_active_disputes_codes()
            cbline.disputes_notes = cbline.list_of_active_disputes_notes()
            cbline.save(using=db)
            print(f"{cbline.cblnid} -> {cbline.disputes_codes} - {cbline.disputes_notes}")
        except Exception as ex:
            print(ex.__str__())


def update_chargebacklines_history_disputes_codes_and_notes(db):

    chargebacklines_history_with_active_disputes = ChargeBackLineHistory.objects.using(db).filter(chargebackdisputehistory__isnull=False, chargebackdisputehistory__is_active=True, disputes_codes__isnull=True).order_by('-cblnid')
    print(f"CBLinesHistory (with active disputes) to be updated: {chargebacklines_history_with_active_disputes.count()}")
    for cblineh in chargebacklines_history_with_active_disputes.iterator():
        try:
            cblineh.disputes_codes = cblineh.list_of_active_disputes_codes()
            cblineh.disputes_notes = cblineh.list_of_active_disputes_notes()
            cblineh.save(using=db)
            print(f"{cblineh.cblnid} -> {cblineh.disputes_codes} - {cblineh.disputes_notes}")
        except Exception as ex:
            print(ex.__str__())


if __name__ == '__main__':

    print(f'Running script to move Disputes to DisputeHistory: {sys.argv[0]}')  # prints the name of the Python script

    try:
        dbs = [sys.argv[1]]
    except:
        dbs = [x for x in DATABASES.keys() if x != 'default']

    for db in dbs:
        print(f"\n<<< PROCESS START - Company: {db} >>>")

        # Chargeback Lines History (update disputes codes and notes from Active Disputes in CBLineHistory table)
        update_chargebacklines_history_disputes_codes_and_notes(db)

        # Chargeback Lines (update disputes codes and notes from Active Disputes in CBLine)
        update_chargebacklines_disputes_codes_and_notes(db)

        print(f"\n<<< PROCESS COMPLETED - Company: {db} >>>")
