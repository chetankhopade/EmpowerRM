import os
import sys

import django
from django.db.models import Q

from app.management.utilities.functions import move_chargebackdisputes_to_chargebackdispute_history_table

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from empowerb.settings import DATABASES
from erms.models import (ChargeBack, ChargeBackHistory, ChargeBackLine, ChargeBackLineHistory, ChargeBackDispute)


def update_history_chargebacks_disputes(db):

    cbs_ids = [x.__str__() for x in ChargeBack.objects.using(db).values_list('id', flat=True)]
    for cbdispute in ChargeBackDispute.objects.using(db).filter(chargeback_id__isnull=False).exclude(chargeback_id__in=cbs_ids).order_by('-created_at'):
        try:
            if ChargeBackHistory.objects.using(db).filter(id=cbdispute.chargeback_id).exists():
                move_chargebackdisputes_to_chargebackdispute_history_table([cbdispute], db)
            else:
                print(f'check cb ID: {cbdispute.chargeback_id}')
        except Exception as ex:
            print(ex.__str__())

    cblines_ids = [x.__str__() for x in ChargeBackLine.objects.using(db).values_list('id', flat=True)]
    for cbdispute in ChargeBackDispute.objects.using(db).filter(chargebackline_id__isnull=False).exclude(chargebackline_id__in=cblines_ids).order_by('-created_at'):
        try:
            if ChargeBackLineHistory.objects.using(db).filter(id=cbdispute.chargebackline_id).exists():
                move_chargebackdisputes_to_chargebackdispute_history_table([cbdispute], db)
            else:
                print(f'check cbline ID: {cbdispute.chargebackline_id}')
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

        # ChargeBackDisputeHistory
        print('\n<<< CHARGEBACK DISPUTE HISTORY >>>')
        update_history_chargebacks_disputes(db)

        print(f"\n<<< PROCESS COMPLETED - Company: {db} >>>")
