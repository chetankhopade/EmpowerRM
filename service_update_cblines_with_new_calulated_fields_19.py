# This script should be executed only 1 time just after migration ran for new calculated fields
# Following fields from chargebacks_lines and chargebacks_lines_history will get updated in this script
# contract_price_issued
# wac_price_issued
# submitted_wac_extended_amount
# submitted_contract_price_extended_amount
# system_wac_extended_amount
# system_contract_price_extended_amount
import os
import sys

import django
from django.db.models import Case, When, Value, F

from app.management.utilities.constants import (EXCEPTION_ACTION_TAKEN_AUTOCORRECT, EXCEPTION_ACTION_TAKEN_OVERRIDE, EXCEPTION_ACTION_TAKEN_DISPUTED)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from empowerb.settings import DATABASES
from erms.models import ChargeBackLine, ChargeBackLineHistory
from decimal import Decimal


# def update_chargebacklines_history_calculated_fields(db):
#     for cblineh in ChargeBackLineHistory.objects.using(db).all().only('cblnid',
#                                                                       'action_taken',
#                                                                       'contract_price_system',
#                                                                       'wac_system',
#                                                                       'contract_price_submitted',
#                                                                       'wac_submitted',
#                                                                       'contract_price_issued',
#                                                                       'wac_price_issued',
#                                                                       'item_qty',
#                                                                       'submitted_wac_extended_amount',
#                                                                       'submitted_contract_price_extended_amount',
#                                                                       'system_wac_extended_amount',
#                                                                       'system_contract_price_extended_amount').order_by('cblnid').iterator():
#         try:
#             action_taken = cblineh.action_taken
#             # EA-1418 - If autocorrect,  copy wac_system to wac_price_issued & copy contract_price_system to contract_price_issued
#             if action_taken == EXCEPTION_ACTION_TAKEN_AUTOCORRECT:
#                 contract_price_issued_value = cblineh.contract_price_system
#                 wac_price_issued_value = cblineh.wac_system
#             elif action_taken == EXCEPTION_ACTION_TAKEN_OVERRIDE:
#                 # EA-1418 - if override action , copy wac_submitted to wac_price Issued & copy contract_price_submitted to contract_price_issued
#                 contract_price_issued_value = cblineh.contract_price_submitted
#                 wac_price_issued_value = cblineh.wac_submitted
#             elif action_taken == EXCEPTION_ACTION_TAKEN_DISPUTED:
#                 # EA-1418 - if disputed, make the issued field 0.00
#                 contract_price_issued_value = Decimal('0.00')
#                 wac_price_issued_value = Decimal('0.00')
#             else:
#                 contract_price_issued_value = None
#                 wac_price_issued_value = None
#
#             cblineh.contract_price_issued = contract_price_issued_value
#             cblineh.wac_price_issued = wac_price_issued_value
#
#             item_qty = cblineh.item_qty if cblineh.item_qty else 0
#             wac_submitted = cblineh.wac_submitted if cblineh.wac_submitted else 0
#             contract_price_submitted = cblineh.contract_price_submitted if cblineh.contract_price_submitted else 0
#             wac_system = cblineh.wac_system if cblineh.wac_system else 0
#             contract_price_system = cblineh.contract_price_system if cblineh.contract_price_system else 0
#
#             # EA-1427
#             # - submitted_wac_extended_amount(wac_submitted * item_qty)
#             # - submitted_contract_price_extended_amount(contract_price_submitted * item_qty)
#             # - system_wac_extended_amount(wac_system * item_qty)
#             # - system_contract_price_extended_amount(contract_price_system * item_qty)
#
#             cblineh.submitted_wac_extended_amount = Decimal(wac_submitted*item_qty).quantize(Decimal(10) ** -2)
#             cblineh.submitted_contract_price_extended_amount = Decimal(contract_price_submitted*item_qty).quantize(Decimal(10) ** -2)
#             cblineh.system_wac_extended_amount = Decimal(wac_system*item_qty).quantize(Decimal(10) ** -2)
#             cblineh.system_contract_price_extended_amount = Decimal(contract_price_system*item_qty).quantize(Decimal(10) ** -2)
#
#             cblineh.save(using=db)
#             print(f"History CBLNID {cblineh.cblnid}")
#             print(f"contract_price_issued {contract_price_issued_value}")
#             print(f"wac_price_issued_value {wac_price_issued_value}")
#             print(f"submitted_wac_extended_amount {cblineh.submitted_wac_extended_amount}")
#             print(f"submitted_contract_price_extended_amount {cblineh.submitted_contract_price_extended_amount}")
#             print(f"system_wac_extended_amount {cblineh.system_wac_extended_amount}")
#             print(f"system_contract_price_extended_amount {cblineh.system_contract_price_extended_amount}")
#             print("-----*****-----")
#         except Exception as ex:
#             print(ex.__str__())
#
# def update_chargebacklines_calculated_fields(db):
#     # chargebacklines = ChargeBackLine.objects.using(db).all()
#     # print(f"CBLines to be updated: {chargebacklines.count()}")
#     for cbline in ChargeBackLine.objects.using(db).all().only('cblnid',
#                                                               'action_taken',
#                                                               'contract_price_system',
#                                                               'wac_system',
#                                                               'contract_price_submitted',
#                                                               'wac_submitted',
#                                                               'contract_price_issued',
#                                                               'wac_price_issued',
#                                                               'item_qty',
#                                                               'submitted_wac_extended_amount',
#                                                               'submitted_contract_price_extended_amount',
#                                                               'system_wac_extended_amount',
#                                                               'system_contract_price_extended_amount').order_by('cblnid').iterator():
#         try:
#             action_taken = cbline.action_taken
#             # EA-1418 - If autocorrect,  copy wac_system to wac_price_issued & copy contract_price_system to contract_price_issued
#             if action_taken == EXCEPTION_ACTION_TAKEN_AUTOCORRECT:
#                 contract_price_issued_value = cbline.contract_price_system
#                 wac_price_issued_value = cbline.wac_system
#             elif action_taken == EXCEPTION_ACTION_TAKEN_OVERRIDE:
#                 # EA-1418 - if override action , copy wac_submitted to wac_price Issued & copy contract_price_submitted to contract_price_issued
#                 contract_price_issued_value = cbline.contract_price_submitted
#                 wac_price_issued_value = cbline.wac_submitted
#             elif action_taken == EXCEPTION_ACTION_TAKEN_DISPUTED:
#                 # EA-1418 - if disputed, make the issued field 0.00
#                 contract_price_issued_value = Decimal('0.00')
#                 wac_price_issued_value = Decimal('0.00')
#             else:
#                 contract_price_issued_value = None
#                 wac_price_issued_value = None
#
#             cbline.contract_price_issued = contract_price_issued_value
#             cbline.wac_price_issued = wac_price_issued_value
#
#             item_qty = cbline.item_qty if cbline.item_qty else 0
#             wac_submitted = cbline.wac_submitted if cbline.wac_submitted else 0
#             contract_price_submitted = cbline.contract_price_submitted if cbline.contract_price_submitted else 0
#             wac_system = cbline.wac_system if cbline.wac_system else 0
#             contract_price_system = cbline.contract_price_system if cbline.contract_price_system else 0
#
#             # EA-1427
#             # - submitted_wac_extended_amount(wac_submitted * item_qty)
#             # - submitted_contract_price_extended_amount(contract_price_submitted * item_qty)
#             # - system_wac_extended_amount(wac_system * item_qty)
#             # - system_contract_price_extended_amount(contract_price_system * item_qty)
#
#             cbline.submitted_wac_extended_amount = Decimal(wac_submitted * item_qty).quantize(Decimal(10) ** -2)
#             cbline.submitted_contract_price_extended_amount = Decimal(contract_price_submitted * item_qty).quantize(Decimal(10) ** -2)
#             cbline.system_wac_extended_amount = Decimal(wac_system * item_qty).quantize(Decimal(10) ** -2)
#             cbline.system_contract_price_extended_amount = Decimal(contract_price_system * item_qty).quantize(Decimal(10) ** -2)
#
#             cbline.save(using=db)
#             print(f"CBLNID {cbline.cblnid}")
#             print(f"contract_price_issued {contract_price_issued_value}")
#             print(f"wac_price_issued_value {wac_price_issued_value}")
#             print(f"submitted_wac_extended_amount {cbline.submitted_wac_extended_amount}")
#             print(f"submitted_contract_price_extended_amount {cbline.submitted_contract_price_extended_amount}")
#             print(f"system_wac_extended_amount {cbline.system_wac_extended_amount}")
#             print(f"system_contract_price_extended_amount {cbline.system_contract_price_extended_amount}")
#             print("-----*****-----")
#         except Exception as ex:
#             print(ex.__str__())


def update_cblinehistory_calculated_fields(db):
    print("<<< UPDATING CBLINESHISTORY >>>")
    cblh = ChargeBackLineHistory.objects.using(db).update(
        contract_price_issued=Case(
            When(action_taken=EXCEPTION_ACTION_TAKEN_AUTOCORRECT, then=F('contract_price_system')),
            When(action_taken=EXCEPTION_ACTION_TAKEN_OVERRIDE, then=F('contract_price_submitted')),
            When(action_taken=EXCEPTION_ACTION_TAKEN_DISPUTED, then=Value(Decimal('0.00'))),
            default=None
        ),
        wac_price_issued=Case(
            When(action_taken=EXCEPTION_ACTION_TAKEN_AUTOCORRECT, then=F('wac_system')),
            When(action_taken=EXCEPTION_ACTION_TAKEN_OVERRIDE, then=F('wac_submitted')),
            When(action_taken=EXCEPTION_ACTION_TAKEN_DISPUTED, then=Value(Decimal('0.00'))),
            default=None
      ),
      submitted_wac_extended_amount=F('wac_submitted') * F('item_qty') if F('wac_submitted') and F('item_qty') else None,
      submitted_contract_price_extended_amount=F('contract_price_submitted') * F('item_qty') if F('contract_price_submitted') and F('item_qty') else None,
      system_wac_extended_amount=F('wac_system') * F('item_qty') if F('wac_system') and F('item_qty') else None,
      system_contract_price_extended_amount=F('contract_price_system') * F('item_qty') if F('contract_price_system') and F('item_qty') else None,

    )
    print("<<< UPDATING CBLINESHISTORY DONE >>>")


def update_cbline_calculated_fields(db):
    print("\n<<< UPDATING CBLINES >>>")
    cblh = ChargeBackLine.objects.using(db).update(
        contract_price_issued=Case(
            When(action_taken=EXCEPTION_ACTION_TAKEN_AUTOCORRECT, then=F('contract_price_system')),
            When(action_taken=EXCEPTION_ACTION_TAKEN_OVERRIDE, then=F('contract_price_submitted')),
            When(action_taken=EXCEPTION_ACTION_TAKEN_DISPUTED, then=Value(Decimal('0.00'))),
            default=None
        ),
        wac_price_issued=Case(
            When(action_taken=EXCEPTION_ACTION_TAKEN_AUTOCORRECT, then=F('wac_system')),
            When(action_taken=EXCEPTION_ACTION_TAKEN_OVERRIDE, then=F('wac_submitted')),
            When(action_taken=EXCEPTION_ACTION_TAKEN_DISPUTED, then=Value(Decimal('0.00'))),
            default=None
      ),
      submitted_wac_extended_amount=F('wac_submitted') * F('item_qty') if F('wac_submitted') and F('item_qty') else None,
      submitted_contract_price_extended_amount=F('contract_price_submitted') * F('item_qty') if F('contract_price_submitted') and F('item_qty') else None,
      system_wac_extended_amount=F('wac_system') * F('item_qty') if F('wac_system') and F('item_qty') else None,
      system_contract_price_extended_amount=F('contract_price_system') * F('item_qty') if F('contract_price_system') and F('item_qty') else None,

    )
    print("<<< UPDATING CBLINES DONE >>>")


if __name__ == '__main__':

    print(f'Running script to update new calculated fields: {sys.argv[0]}')  # prints the name of the Python script

    try:
        dbs = [sys.argv[1]]
    except:
        dbs = [x for x in DATABASES.keys() if x != 'default']

    for db in dbs:
        print(f"\n<<< PROCESS START - Company: {db} >>>")

        # Chargeback Lines History (update new calculated fields in CBLineHistory table)
        update_cblinehistory_calculated_fields(db)

        # Chargeback Lines (update new calculated fields in CBLine)
        update_cbline_calculated_fields(db)

        print(f"\n<<< PROCESS COMPLETED - Company: {db} >>>")