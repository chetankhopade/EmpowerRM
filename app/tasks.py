from decimal import Decimal

from app.management.utilities.constants import (STAGE_TYPE_IMPORTED, SUBSTAGE_TYPE_ERRORS, LINE_STATUS_APPROVED,
                                                APPROVED_REASON_NO_ERRORS_ID, STAGE_TYPE_VALIDATED,
                                                SUBSTAGE_TYPE_RESUBMISSIONS, STAGE_TYPE_IN_PROCESS,
                                                SUBSTAGE_TYPE_NO_ERRORS, SUBSTAGE_TYPE_DUPLICATES, LINE_STATUS_DISPUTED,
                                                STAGE_TYPE_POSTED, STAGE_TYPE_PROCESSED, STAGES_TYPES, SUBSTAGES_TYPES)
from app.management.utilities.functions import chargeback_audit_trails
from ermm.models import Company
from erms.models import (DistributionCenter, DirectCustomer, ChargeBack, ChargeBackHistory, Contract, Item,
                         ChargeBackDispute, Import844History, ContractAlias)


# Preprocess handler class
class DataHandler:

    def __init__(self, db):
        # header
        self.dcenters = DistributionCenter.objects.using(db).values('id', 'dea_number', 'customer__account_number')
        self.dcustomers = DirectCustomer.objects.using(db).values('id', 'account_number')
        self.cbs_open = ChargeBack.objects.using(db).filter(type__in=['00', '18', '41']).values('number')
        self.cbs_history = ChargeBackHistory.objects.using(db).filter(type__in=['00', '18', '41']).values('number', 'cbid')

        # lines
        self.contracts = Contract.objects.using(db).values('id', 'number')
        self.contracts_aliases = ContractAlias.objects.using(db).values('contract_id', 'alias')
        self.items = Item.objects.using(db).values('id', 'ndc')

        # values
        self.credit_amt_total = 0
        self.is_auto_add_new_indirect_customer = False
        self.is_add_membership_validation = False

        # chargebacks_list
        self.chargebacks_list = None


def import_validations(company_id, db, chargebacks_list=None,request=None):
    print(f"Import Validations")
    print(f"Database: {db}")
    data_handler = DataHandler(db)
    company = Company.objects.get(id=company_id)
    print(f"Getting company object")
    company_settings = company.my_company_settings()
    print("Getting company settings")
    is_membership_validation_enabled = company_settings.membership_validation_enable
    data_handler.is_cb_threshold_validation_enabled = company_settings.enable_expired_cb_threshold
    data_handler.cb_threshold_value = company_settings.expired_cb_threshold
    data_handler.is_auto_add_new_indirect_customer = company_settings.auto_add_new_indirect_customer
    data_handler.is_add_membership_validation = company_settings.proactive_membership_validation
    data_handler.is_for_import844 = False if chargebacks_list and len(chargebacks_list) > 0 else True

    chargebacks = chargebacks_list if chargebacks_list else ChargeBack.objects.using(db).filter(stage=STAGE_TYPE_IN_PROCESS)
    print("Getting chargebacks to process")
    for chargeback in chargebacks:
        try:
            print(f"ChargebackID: {chargeback.id}")
            print(f"CBID: {chargeback.cbid}")
            import844 = chargeback.import_844_ref  # new FK field
            cb_errors_flag = False
            data_handler.cbs_open = data_handler.cbs_open.exclude(id=chargeback.id)
            data_handler.credit_amt_total = sum([Decimal(x.line['L_ItemCreditAmt']) for x in Import844History.objects.using(db).filter(bulk_id=import844.bulk_id, header__H_CBNumber=import844.header['H_CBNumber'])])
            # EA -EA-1548 New Chargeback Audit
            change_text = f"Moved to stage {str(dict(STAGES_TYPES)[chargeback.stage]), str(dict(SUBSTAGES_TYPES)[chargeback.substage])}"
            chargeback_audit_trails(cbid=chargeback.id,
                                    user_email=request.user.email if request else 'EmpowerRM',
                                    change_text=change_text,
                                    db=db
                                    )
            # HEADER Import validations
            print('header import validations')
            header_validations = import844.header_import_validations(data_handler)
            # fields updates after header validations (only for not manual cb because values are already assigned to fields)
            if chargeback.is_received_edi:
                chargeback.distribution_center_id = header_validations['distribution_center_id']
                chargeback.customer_id = header_validations['direct_customer_id']
                chargeback.original_chargeback_id = header_validations['original_chargeback_id']
                # update FK fields
                chargeback.distribution_center_ref_id = header_validations['distribution_center_id']
                chargeback.customer_ref_id = header_validations['direct_customer_id']
                chargeback.substage = header_validations['substage']
                chargeback.save(using=db)
            # disputes
            for dispute in header_validations["disputes"]:
                cb_dispute = ChargeBackDispute(chargeback_id=chargeback.id,
                                               chargeback_ref=chargeback,
                                               dispute_code=dispute['code'],
                                               dispute_note=dispute['error'],
                                               field_name=dispute['field'],
                                               field_value=dispute['value'],
                                               is_active=True)
                cb_dispute.save(using=db)


                cb_errors_flag = True

            cbline_errors_flag = []
            cbline_membership_errors_flag = []
            cbline_cot_errors_flag = []
            cbline_validations_errors_flag = []

            # If CB substage == Duplicates then lines will be disputed
            if chargeback.substage == SUBSTAGE_TYPE_DUPLICATES:
                chargeback.get_my_pending_chargeback_lines_by_db(db).update(line_status=LINE_STATUS_DISPUTED)

            for chargeback_line in chargeback.get_my_pending_chargeback_lines_by_db(db):
                # using new fk fields
                chargeback_line.chargebackdispute_set.all().update(is_active=False)
                import844 = chargeback_line.import_844_ref

                # Line Import Validations
                print(f'line_import_validations -> CBLNID: {chargeback_line.cblnid}')
                line_validations = import844.line_import_validations(db, data_handler, chargeback_line)

                # fields update after lin validations (only for not manual cb because values are already assigned to fields)
                if chargeback.is_received_edi:
                    chargeback_line.contract_id = line_validations['contract_id']
                    chargeback_line.indirect_customer_id = line_validations['indirect_customer_id']
                    chargeback_line.item_id = line_validations['item_id']
                    # update FK fields
                    chargeback_line.contract_ref_id = line_validations['contract_id']
                    chargeback_line.indirect_customer_ref_id = line_validations['indirect_customer_id']
                    chargeback_line.item_ref_id = line_validations['item_id']
                    chargeback_line.save(using=db)

                # disputes
                # EA-1505 - Import validation A2 logic
                if len(line_validations['disputes']) == 1 and line_validations['disputes'][0]['code'] == "A2":
                    cbline_dispute = ChargeBackDispute(chargebackline_id=chargeback_line.id,
                                                       chargebackline_ref=chargeback_line,
                                                       dispute_code=line_validations['disputes'][0]['code'],
                                                       dispute_note=line_validations['disputes'][0]['error'],
                                                       field_name=line_validations['disputes'][0]['field'],
                                                       field_value=line_validations['disputes'][0]['value'],
                                                       is_active=True)
                    cbline_dispute.save(using=db)
                else:
                    for dispute in line_validations['disputes']:
                        cbline_dispute = ChargeBackDispute(chargebackline_id=chargeback_line.id,
                                                           chargebackline_ref=chargeback_line,
                                                           dispute_code=dispute['code'],
                                                           dispute_note=dispute['error'],
                                                           field_name=dispute['field'],
                                                           field_value=dispute['value'],
                                                           is_active=True)
                        cbline_dispute.save(using=db)
                        cbline_errors_flag.append(chargeback_line.get_id_str())

                # membership validations
                if not any(x == chargeback_line.get_id_str() for x in cbline_errors_flag) and is_membership_validation_enabled:
                    print('membership_validations')
                    membership_validations_disputes = chargeback_line.membership_validations(db, data_handler)
                    for dispute in membership_validations_disputes:
                        cbline_dispute = ChargeBackDispute(chargebackline_id=chargeback_line.id,
                                                           chargebackline_ref=chargeback_line,
                                                           dispute_code=dispute['code'],
                                                           dispute_note=dispute['error'],
                                                           field_name=dispute['field'],
                                                           field_value=dispute['value'],
                                                           is_active=True)
                        cbline_dispute.save(using=db)
                        cbline_membership_errors_flag.append(chargeback_line.get_id_str())

                # cot validations
                if not any(x == chargeback_line.get_id_str() for x in cbline_errors_flag) and not any(x == chargeback_line.get_id_str() for x in cbline_membership_errors_flag):
                    print('cot_validations')
                    cot_validations_disputes = chargeback_line.cot_validations(db)
                    for dispute in cot_validations_disputes:
                        cbline_dispute = ChargeBackDispute(chargebackline_id=chargeback_line.id,
                                                           chargebackline_ref=chargeback_line,
                                                           dispute_code=dispute['code'],
                                                           dispute_note=dispute['error'],
                                                           field_name=dispute['field'],
                                                           field_value=dispute['value'],
                                                           is_active=True)
                        cbline_dispute.save(using=db)
                        cbline_cot_errors_flag.append(chargeback_line.get_id_str())

                # chargebacks validations (ticket 888 if cb_type = 15 leaves lines pending, do not validate)
                if not any(x == chargeback_line.get_id_str() for x in cbline_errors_flag) and not any(x == chargeback_line.get_id_str() for x in cbline_membership_errors_flag) and not any(x == chargeback_line.get_id_str() for x in cbline_cot_errors_flag):
                    # from Jeremy's feedback we need to run validations for manual cbs (even if is resubmission)
                    if not chargeback.is_received_edi or chargeback.substage != SUBSTAGE_TYPE_RESUBMISSIONS:
                        print('cb_validations')
                        try:
                            cb_validations_disputes = chargeback_line.cb_validations(db)
                            if not cb_validations_disputes:
                                chargeback_line.line_status = LINE_STATUS_APPROVED
                                chargeback_line.approved_reason_id = APPROVED_REASON_NO_ERRORS_ID
                                chargeback_line.save(using=db)
                            else:
                                for dispute in cb_validations_disputes:
                                    cbline_dispute = ChargeBackDispute(chargebackline_id=chargeback_line.id,
                                                                       chargebackline_ref=chargeback_line,
                                                                       dispute_code=dispute['code'],
                                                                       dispute_note=dispute['error'],
                                                                       field_name=dispute['field'],
                                                                       field_value=dispute['value'],
                                                                       is_active=True)
                                    cbline_dispute.save(using=db)
                                    cbline_validations_errors_flag.append(cbline_dispute.get_id_str())
                        except Exception as ex:
                            print(ex.__str__())
                # ticket EA-1000 Once marked as True this field should never be changed.
                # Rerun validation should not clear this. If one of the validations have a dispute then mark it as True
                if not chargebacks_list and (cbline_errors_flag or cbline_membership_errors_flag or cbline_cot_errors_flag or cbline_validations_errors_flag):
                    chargeback_line.received_with_errors = 1 if line_validations['disputes'] else 0
                    chargeback_line.save(using=db)

                # update disputes_codes and disputes_notes fields in cbline
                chargeback_line.disputes_codes = chargeback_line.list_of_active_disputes_codes()
                chargeback_line.disputes_notes = chargeback_line.list_of_active_disputes_notes()
                chargeback_line.save(using=db)

            # Calculate Amounts
            chargeback.calculate_claim_totals_by_db(db)
            chargeback.save(using=db)

            # ticket 1008 Stage should not be reset on CBs that have been Posted or Gen849'd.
            if chargeback.stage != STAGE_TYPE_POSTED and chargeback.stage != STAGE_TYPE_PROCESSED:
                # header/import validations flags
                print('Stage / Substage Update')
                if cb_errors_flag or cbline_errors_flag:
                    chargeback.stage = STAGE_TYPE_IMPORTED
                    if chargebacks_list or (chargeback.substage != SUBSTAGE_TYPE_RESUBMISSIONS and chargeback.substage != SUBSTAGE_TYPE_DUPLICATES):
                        chargeback.substage = SUBSTAGE_TYPE_ERRORS
                else:
                    chargeback.stage = STAGE_TYPE_VALIDATED
                    if chargebacks_list or chargeback.substage != SUBSTAGE_TYPE_RESUBMISSIONS:
                        if cbline_membership_errors_flag or cbline_cot_errors_flag or cbline_validations_errors_flag:
                            chargeback.substage = SUBSTAGE_TYPE_ERRORS
                        else:
                            chargeback.substage = SUBSTAGE_TYPE_NO_ERRORS
                chargeback.save(using=db)
                # EA -EA-1548 New Chargeback Audit
                change_text = f"Moved to stage {str(dict(STAGES_TYPES)[chargeback.stage]), str(dict(SUBSTAGES_TYPES)[chargeback.substage])}"
                chargeback_audit_trails(cbid=chargeback.id,
                                        user_email=request.user.email if request else 'EmpowerRM',
                                        change_text=change_text,
                                        db=db
                                        )

                if(chargeback.stage == STAGE_TYPE_IMPORTED and chargeback.substage == SUBSTAGE_TYPE_ERRORS ):
                    # EA -EA-1548 New Chargeback Audit
                    change_text = f"Imported with Errors"
                    chargeback_audit_trails(cbid=chargeback.id,
                                            user_email=request.user.email if request else 'EmpowerRM',
                                            change_text=change_text,
                                            db=db
                                            )
                elif(chargeback.stage == STAGE_TYPE_IMPORTED and chargeback.substage == SUBSTAGE_TYPE_NO_ERRORS ):
                    # EA -EA-1548 New Chargeback Audit
                    change_text = f"Imported and passed Validation"
                    chargeback_audit_trails(cbid=chargeback.id,
                                            user_email=request.user.email if request else 'EmpowerRM',
                                            change_text=change_text,
                                            db=db
                                            )


        except Exception as ex:
            print(ex.__str__())

def import_validations_function(company_id, db, chargebacks_list,request):
    import_validations(company_id, db, chargebacks_list,request)