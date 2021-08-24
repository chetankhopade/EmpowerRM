import os
import sys

import django
from django.db.models import Q

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from empowerb.settings import DATABASES
from erms.models import (ChargeBack, ChargeBackHistory, ChargeBackLine, ChargeBackLineHistory, ChargeBackDispute,
                         DirectCustomer, DistributionCenter, Import844History, Contract, IndirectCustomer, Item,
                         ContractCoT, ClassOfTrade)


def update_open_chargebacks(db):

    chargebacks_to_be_processed = ChargeBack.objects.using(db).filter(
        Q(customer_id__isnull=False, customer_ref__isnull=True) |
        Q(distribution_center_ref_id__isnull=False, distribution_center_ref__isnull=True) |
        Q(import844_id__isnull=False, import_844_ref__isnull=True)).only('cbid',
                                                                         'customer_ref',
                                                                         'customer_id',
                                                                         'distribution_center_ref',
                                                                         'distribution_center_id',
                                                                         'import_844_ref',
                                                                         'import844_id').iterator()
    for cb in chargebacks_to_be_processed:
        if cb.customer_id and not cb.customer_ref:
            try:
                cb.customer_ref = DirectCustomer.objects.using(db).get(id=cb.customer_id)
                cb.save(using=db)
                print(f"Updated CB: {cb.cbid} -> <customer_ref>")
            except:
                pass

        if cb.distribution_center_id and not cb.distribution_center_ref:
            try:
                cb.distribution_center_ref = DistributionCenter.objects.using(db).get(id=cb.distribution_center_id)
                cb.save(using=db)
                print(f"Updated CB: {cb.cbid} -> <distribution_center_ref>")
            except:
                pass

        if cb.import844_id and not cb.import_844_ref:
            try:
                cb.import_844_ref = Import844History.objects.using(db).get(id=cb.import844_id)
                cb.save(using=db)
                print(f"Updated CB: {cb.cbid} -> <import_844_ref>")
            except:
                pass


def update_history_chargebacks(db):

    chargebacks_history_to_be_processed = ChargeBackHistory.objects.using(db).filter(
        Q(customer_id__isnull=False, customer_ref__isnull=True) |
        Q(distribution_center_ref_id__isnull=False, distribution_center_ref__isnull=True) |
        Q(import844_id__isnull=False, import_844_ref__isnull=True)).only('cbid',
                                                                         'customer_ref',
                                                                         'customer_id',
                                                                         'distribution_center_ref',
                                                                         'distribution_center_id',
                                                                         'import_844_ref',
                                                                         'import844_id').iterator()
    for cb in chargebacks_history_to_be_processed:

        if cb.customer_id and not cb.customer_ref:
            try:
                cb.customer_ref = DirectCustomer.objects.using(db).get(id=cb.customer_id)
                cb.save(using=db)
                print(f"Updated CBH: {cb.cbid} -> <customer_ref>")
            except:
                pass

        if cb.distribution_center_id and not cb.distribution_center_ref:
            try:
                cb.distribution_center_ref = DistributionCenter.objects.using(db).get(id=cb.distribution_center_id)
                cb.save(using=db)
                print(f"Updated CBH: {cb.cbid} -> <distribution_center_ref>")
            except:
                pass

        if cb.import844_id and not cb.import_844_ref:
            try:
                cb.import_844_ref = Import844History.objects.using(db).get(id=cb.import844_id)
                cb.save(using=db)
                print(f"Updated CBH: {cb.cbid} -> <import_844_ref>")
            except:
                pass


def update_open_chargebacks_lines(db):

    chargebackslines_to_be_processed = ChargeBackLine.objects.using(db).filter(
        Q(chargeback_id__isnull=False, chargeback_ref__isnull=True) |
        Q(contract_id__isnull=False, contract_ref__isnull=True) |
        Q(indirect_customer_id__isnull=False, indirect_customer_ref__isnull=True) |
        Q(item_id__isnull=False, item_ref__isnull=True) |
        Q(import844_id__isnull=False, import_844_ref__isnull=True)).only('cblnid',
                                                                         'chargeback_ref',
                                                                         'chargeback_id',
                                                                         'contract_ref',
                                                                         'contract_id',
                                                                         'indirect_customer_ref',
                                                                         'indirect_customer_id',
                                                                         'item_ref',
                                                                         'item_id',
                                                                         'import_844_ref',
                                                                         'import844_id').iterator()
    for cbline in chargebackslines_to_be_processed:

        if cbline.chargeback_id and not cbline.chargeback_ref:
            try:
                cbline.chargeback_ref = ChargeBack.objects.using(db).get(id=cbline.chargeback_id)
                cbline.save(using=db)
                print(f"Updated CBL: {cbline.cblnid} -> <chargeback_ref>")
            except:
                pass

        if cbline.contract_id and not cbline.contract_ref:
            try:
                cbline.contract_ref = Contract.objects.using(db).get(id=cbline.contract_id)
                cbline.save(using=db)
                print(f"Updated CBL: {cbline.cblnid} -> <contract_ref>")
            except:
                pass

        if cbline.indirect_customer_id and not cbline.indirect_customer_ref:
            try:
                cbline.indirect_customer_ref = IndirectCustomer.objects.using(db).get(id=cbline.indirect_customer_id)
                cbline.save(using=db)
                print(f"Updated CBL: {cbline.cblnid} -> <indirect_customer_ref>")
            except:
                pass

        if cbline.item_id and not cbline.item_ref:
            try:
                cbline.item_ref = Item.objects.using(db).get(id=cbline.item_id)
                cbline.save(using=db)
                print(f"Updated CBL: {cbline.cblnid} -> <item_ref>")
            except:
                pass

        if cbline.import844_id and not cbline.import_844_ref:
            try:
                cbline.import_844_ref = Import844History.objects.using(db).get(id=cbline.import844_id)
                cbline.save(using=db)
                print(f"Updated CBL: {cbline.cblnid} -> <import_844_ref>")
            except:
                pass


def update_history_chargebacks_lines(db):

    chargebackslines_history_to_be_processed = ChargeBackLineHistory.objects.using(db).filter(
        Q(chargeback_id__isnull=False, chargeback_ref__isnull=True) |
        Q(contract_id__isnull=False, contract_ref__isnull=True) |
        Q(indirect_customer_id__isnull=False, indirect_customer_ref__isnull=True) |
        Q(item_id__isnull=False, item_ref__isnull=True) |
        Q(import844_id__isnull=False, import_844_ref__isnull=True)).only('cblnid',
                                                                         'chargeback_ref',
                                                                         'chargeback_id',
                                                                         'contract_ref',
                                                                         'contract_id',
                                                                         'indirect_customer_ref',
                                                                         'indirect_customer_id',
                                                                         'item_ref',
                                                                         'item_id',
                                                                         'import_844_ref',
                                                                         'import844_id').iterator()
    for cbline in chargebackslines_history_to_be_processed:

        if cbline.chargeback_id and not cbline.chargeback_ref:
            try:
                cbline.chargeback_ref = ChargeBackHistory.objects.using(db).get(id=cbline.chargeback_id)
                cbline.save(using=db)
                print(f"Updated CBLH: {cbline.cblnid} -> <chargeback_ref>")
            except:
                pass

        if cbline.contract_id and not cbline.contract_ref:
            try:
                cbline.contract_ref = Contract.objects.using(db).get(id=cbline.contract_id)
                cbline.save(using=db)
                print(f"Updated CBLH: {cbline.cblnid} -> <contract_ref>")
            except:
                pass

        if cbline.indirect_customer_id and not cbline.indirect_customer_ref:
            try:
                cbline.indirect_customer_ref = IndirectCustomer.objects.using(db).get(id=cbline.indirect_customer_id)
                cbline.save(using=db)
                print(f"Updated CBLH: {cbline.cblnid} -> <indirect_customer_ref>")
            except:
                pass

        if cbline.item_id and not cbline.item_ref:
            try:
                cbline.item_ref = Item.objects.using(db).get(id=cbline.item_id)
                cbline.save(using=db)
                print(f"Updated CBLH: {cbline.cblnid} -> <item_ref>")
            except:
                pass

        if cbline.import844_id and not cbline.import_844_ref:
            try:
                cbline.import_844_ref = Import844History.objects.using(db).get(id=cbline.import844_id)
                cbline.save(using=db)
                print(f"Updated CBLH: {cbline.cblnid} -> <import_844_ref>")
            except:
                pass


def update_open_chargebacks_disputes(db):

    chargebacks_disputes_to_be_processed = ChargeBackDispute.objects.using(db).filter(
        Q(chargeback_id__isnull=False, chargeback_ref__isnull=True) |
        Q(chargebackline_id__isnull=False, chargebackline_ref__isnull=True)).only('id',
                                                                                  'chargeback_ref',
                                                                                  'chargeback_id',
                                                                                  'chargebackline_ref',
                                                                                  'chargebackline_id').iterator()
    for cbdispute in chargebacks_disputes_to_be_processed:

        if cbdispute.chargeback_id and not cbdispute.chargeback_ref:
            try:
                cbdispute.chargeback_ref = ChargeBack.objects.using(db).get(id=cbdispute.chargeback_id)
                cbdispute.save(using=db)
                print(f"Updated CBDP: {cbdispute.get_id_str()} -> <chargeback_ref>")
            except Exception as ex:
                pass

        if cbdispute.chargebackline_id and not cbdispute.chargebackline_ref:
            try:
                cbdispute.chargebackline_ref = ChargeBackLine.objects.using(db).get(id=cbdispute.chargebackline_id)
                cbdispute.save(using=db)
                print(f"Updated CBDP: {cbdispute.get_id_str()} -> <chargebackline_ref>")
            except Exception as ex:
                pass


def update_cots(db):

    contracts_cots_to_be_processed = ContractCoT.objects.using(db).filter(
        Q(contract_id__isnull=False, contract_ref__isnull=True) |
        Q(cot_id__isnull=False, cot_ref__isnull=True)).only('id', 'contract_ref', 'contract_id', 'cot_ref', 'cot_id')

    for contrat_cot in contracts_cots_to_be_processed:

        if contrat_cot.contract_id and not contrat_cot.contract_ref:
            try:
                contrat_cot.contract_ref = Contract.objects.using(db).get(id=contrat_cot.contract_id)
                contrat_cot.save(using=db)
                print(f"Updated ContractCOT: {contrat_cot.get_id_str()} -> <contract_ref> ")
            except:
                pass

        if contrat_cot.cot_id and not contrat_cot.cot_ref:
            try:
                contrat_cot.cot_ref = ClassOfTrade.objects.using(db).get(id=contrat_cot.cot_id)
                contrat_cot.save(using=db)
                print(f"Updated ContractCOT: {contrat_cot.get_id_str()} -> <cot_ref>")
            except:
                pass


if __name__ == '__main__':

    print(f'Running script: {sys.argv[0]}')  # prints the name of the Python script

    try:
        dbs = [sys.argv[1]]
    except:
        dbs = [x for x in DATABASES.keys() if x != 'default']

    for db in dbs:
        print(f"\n<<< PROCESS START - Company: {db} >>>")

        # ChargeBacks
        print('\n<<< CHARGEBACKS >>>')
        update_open_chargebacks(db)

        # ChargeBackHistory
        print('\n<<< CHARGEBACKS HISTORY >>>')
        update_history_chargebacks(db)

        # ChargeBackLine
        print('\n<<< CHARGEBACKLINES >>>')
        update_open_chargebacks_lines(db)

        # ChargeBackLineHistory
        print('\n<<< CHARGEBACKLINES HISTORY >>>')
        update_history_chargebacks_lines(db)

        # ChargeBackDispute
        print('\n<<< CHARGEBACK DISPUTE >>>')
        update_open_chargebacks_disputes(db)

        # Contract CoT
        print('\n<<< CONTRACT COT >>>')
        update_cots(db)

        print(f"\n<<< PROCESS COMPLETED - Company: {db} >>>")
