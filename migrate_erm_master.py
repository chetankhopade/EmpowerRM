import datetime
import os
import sys

import django


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from empowerb import settings
from empowerb.settings import DATABASES
from ermm.models import Company, Account, Subscription, IntegrationSystem, QuickbooksConfigurations, \
    QuickbooksTransactions, QuickbooksErrors, CompanySetting, UserCompany, CompanyModule, Module, UserRole, Role
from django.contrib.auth.models import User
from django.db import connections, OperationalError, transaction as db_trans


def migrate(company, database_id, file_path):
    with open(file_path, "a", newline='\r\n') as f:
        try:
            print(f"<<< Getting data from source database for company - {company.name} >>>")
            f.write(f"\n<<< Migrating data for {company.name} >>>")
            account = Account.objects.get(id=company.account_id)
            print(f"Account - {account.name}")
            user = User.objects.get(id=account.owner_id)
            print(f"User - {user.email}")
            # if account.subscription_id:
            #     subscription = Subscription.objects.get(id=account.subscription_id)
            # else:
            #     subscription = None
            #     subscription_id = None

            if company.integration_system:
                integration_system = IntegrationSystem.objects.get(id=company.integration_system.id)
            else:
                integration_system = None
                integration_system_id = None

            quickbooksConfigurations = QuickbooksConfigurations.objects.filter(company=company).order_by('id')
            print(f"QuickbooksConfigurations - {len(quickbooksConfigurations)}")
            quickbooksTransactions = QuickbooksTransactions.objects.filter(company=company).order_by('id')
            print(f"QuickbooksTransactions - {len(quickbooksTransactions)}")
            quickbooksErrors = QuickbooksErrors.objects.filter(company=company).order_by('id')
            print(f"QuickbooksErrors - {len(quickbooksErrors)}")

            print(f"Getting Company Settings")
            companySetting = CompanySetting.objects.filter(company=company).order_by('id')
            print(f"Getting User Company")
            userCompany = UserCompany.objects.filter(company=company, user=user).order_by('id')

            print(f"Getting Company Modules")
            companyModules = CompanyModule.objects.filter(company=company).order_by('id')
            companyModuleIdList = []
            for companyModule in companyModules:
                companyModuleIdList.append(companyModule.module_id)

            print(f"Getting Modules related to company and company module")
            if companyModuleIdList:
                modules = Module.objects.filter(id__in=companyModuleIdList).order_by('id')
            else:
                modules = None

            print(f"Getting User Role related to user - {user.email} id({user.id})")
            # get User role
            userRole = UserRole.objects.filter(user=user).order_by('id')
            userRoleIdList = []
            for u in userRole:
                userRoleIdList.append(u.role_id)

            roles = None
            if userRoleIdList:
                print(f"Getting Roles by user and userRole")
                roles = Role.objects.filter(id__in=userRoleIdList).order_by('id')

            account_id = account.id if account else None
            user_id = user.id if user else None
            # subscription_id = subscription.id
            integration_system_id = integration_system.id if integration_system else None

            # Inserting into destination db
            destination_account = None
            destination_user = None
            destination_integration_system = None
            try:
                with db_trans.atomic(using=database_id):
                    print(f"Migrating records to destination database")
                    if user:
                        try:
                            destination_user = User.objects.using(database_id).get(email=user.email)
                        except:
                            destination_user = User(
                                id=user.id,
                                username=user.username,
                                password=user.password,
                                last_login=user.last_login,
                                is_superuser=user.is_superuser,
                                first_name=user.first_name,
                                last_name=user.last_name,
                                email=user.email,
                                is_staff=user.is_staff,
                                is_active=user.is_active,
                                date_joined=user.date_joined,
                                )
                            destination_user.save(using=database_id)
                        f.write(f"\nSource Table Name - (User), Source row id - ({user.id}), Destination Table Name - (User), Destination row id - ({destination_user.id})")
                        print(f"User Id - {destination_user.id}")
                    if account:
                        try:
                            destination_account = Account.objects.using(database_id).get(name=account.name)
                        except:
                            destination_account = Account(id=account.id,owner=destination_user, name=account.name)
                            destination_account.save(using=database_id)
                        f.write(f"\nSource Table Name - (accounts), Source row id - ({account.id}), Destination Table Name - (accounts), Destination row id - ({destination_account.id})")
                        print(f"Account Id - {destination_account.id}")
                    if integration_system:
                        try:
                            destination_integration_system = IntegrationSystem(id=integration_system.id, name=integration_system.name)
                            destination_integration_system.save(using=database_id)
                            f.write(f"\nSource Table Name - (integration_systems), Source row id - ({integration_system.id}), Destination Table Name - (integration_systems), Destination row id - ({destination_integration_system.id})")
                            print(f"Integration systems Id - {destination_integration_system.id}")
                        except:
                            destination_integration_system = None

                    if roles:
                        for r in roles:
                            try:
                                destination_role = Role.objects.using(database_id).get(name=r.name)
                            except:
                                destination_role = Role(name=r.name)
                                destination_role.save(using=database_id)
                            f.write(f"\nSource Table Name - (roles), Source row id - ({r.id}), Destination Table Name - (roles), Destination row id - ({destination_role.id})")
                            print(f"Role Id - {destination_role.id}")
                            try:
                                destination_user_role = UserRole.objects.using(database_id).get(user=destination_user, role=destination_role)
                            except:
                                destination_user_role = UserRole(user=destination_user, role=destination_role)
                                destination_user_role.save(using=database_id)
                            f.write(f"\nDestination Table Name - (users_roles), Destination row id - ({destination_user_role.id})")
                            print(f"UserRole Id - {destination_user_role.id}")

                    destination_company = Company(
                        id=company.id,
                        account=destination_account,
                        name=company.name,
                        database=company.database,
                        address1=company.address1,
                        address2=company.address2,
                        city=company.city,
                        state=company.state,
                        zip_code=company.zip_code,
                        last_quickbook_file=company.last_quickbook_file,
                        integration_system=destination_integration_system,
                        integration_config=company.integration_config,
                        generate_transaction_number=company.generate_transaction_number,
                        show_only_disputed_lines_in_849=company.show_only_disputed_lines_in_849,
                        cbid_counter=company.cbid_counter,
                        processing_option=company.processing_option,
                    )
                    destination_company.save(using=database_id)
                    f.write(f"\nSource Table Name - (companies), Source row id - ({company.id}), Destination Table Name - (companies), Destination row id - ({destination_company.id})")
                    print(f"Company Id - {destination_company.id}")

                    for quickbooksConfiguration in quickbooksConfigurations:
                        qbc = QuickbooksConfigurations(
                            company=destination_company,
                            token=quickbooksConfiguration.token,
                            path=quickbooksConfiguration.path,
                            interval=quickbooksConfiguration.interval,
                        )
                        qbc.save(using=database_id)
                        f.write(f"\nSource Table Name - (quickbooks_configurations), Source row id - ({quickbooksConfiguration.id}), Destination Table Name - (quickbooks_configurations), Destination row id - ({qbc.id})")
                        print(f"QuickbooksConfigurations Id - {qbc.id}")

                    for quickbooksTransaction in quickbooksTransactions:
                        qbt = QuickbooksTransactions(
                            status=quickbooksTransaction.status,
                            company=destination_company,
                            cbid=quickbooksTransaction.cbid,
                            cb_number=quickbooksTransaction.cb_number,
                            cb_amount_issue=quickbooksTransaction.cb_amount_issue,
                            customer_accno=quickbooksTransaction.customer_accno,
                            post_date=quickbooksTransaction.post_date,
                            items=quickbooksTransaction.items,
                            cb_cm_number=quickbooksTransaction.cb_cm_number,
                            cb_cm_date=quickbooksTransaction.cb_cm_date,
                            cb_cm_amount=quickbooksTransaction.cb_cm_amount,
                        )
                        qbt.save(using=database_id)
                        f.write(f"\nSource Table Name - (quickbooks_transactions), Source row id - ({quickbooksTransaction.id}), Destination Table Name - (quickbooks_transactions), Destination row id - ({qbt.id})")
                        print(f"QuickbooksTransactions Id - {qbt.id}")

                    for quickbooksError in quickbooksErrors:
                        qbe = QuickbooksErrors(
                            company=destination_company,
                            cbid=quickbooksError.cbid,
                            error=quickbooksError.error
                        )
                        qbe.save(using=database_id)
                        f.write(f"\nSource Table Name - (quickbooks_errors), Source row id - ({quickbooksError.id}), Destination Table Name - (quickbooks_errors), Destination row id - ({qbe.id})")
                        print(f"QuickbooksErrors Id - {qbe.id}")

                    for destination_companySetting in companySetting:
                        dcs = CompanySetting(
                            company=destination_company,
                            auto_contact_notifications=destination_companySetting.auto_contact_notifications,
                            auto_chargeback_reports_enable=destination_companySetting.auto_chargeback_reports_enable,
                            enable_daily_report=destination_companySetting.enable_daily_report,
                            default_wac_enable=destination_companySetting.default_wac_enable,
                            auto_assign_big_3_as_contract_servers=destination_companySetting.auto_assign_big_3_as_contract_servers,
                            global_customer_list_updates_overrides_local_changes=destination_companySetting.global_customer_list_updates_overrides_local_changes,
                            alert_enabled=destination_companySetting.alert_enabled,
                            alert_sent_in_single_daily_digest=destination_companySetting.alert_sent_in_single_daily_digest,
                            membership_validation_enable=destination_companySetting.membership_validation_enable,
                            proactive_membership_validation=destination_companySetting.proactive_membership_validation,
                            auto_contract_notification_enabled=destination_companySetting.auto_contract_notification_enabled,
                            class_of_trade_validation_enabled=destination_companySetting.class_of_trade_validation_enabled,
                            automatic_chargeback_processing=destination_companySetting.automatic_chargeback_processing,
                            automate_import=destination_companySetting.automate_import,
                            quickbooks_api_integration=destination_companySetting.quickbooks_api_integration,
                            auto_add_new_indirect_customer=destination_companySetting.auto_add_new_indirect_customer,
                            allow_experimental=destination_companySetting.allow_experimental,
                            enable_expired_cb_threshold=destination_companySetting.enable_expired_cb_threshold,
                            expired_cb_threshold=destination_companySetting.expired_cb_threshold,
                            cb_start_page=destination_companySetting.cb_start_page,
                            enable_contract_expiration_threshold=destination_companySetting.enable_contract_expiration_threshold,
                            contract_expiration_threshold=destination_companySetting.contract_expiration_threshold,
                        )
                        dcs.save(using=database_id)
                        f.write(f"\nSource Table Name - (companies_settings), Source row id - ({destination_companySetting.id}), Destination Table Name - (companies_settings), Destination row id - ({dcs.id})")
                        print(f"CompanySetting Id - {dcs.id}")

                    # for destinationUserCompany in userCompany:
                    if destination_user and destination_user:
                        duc = UserCompany(
                            user=destination_user,
                            company=destination_company
                        )
                        duc.save(using=database_id)
                        f.write(f"\nSource Table Name - (users_companies), Source row id - ({destination_companySetting.id}), Destination Table Name - (users_companies), Destination row id - ({duc.id})")
                        print(f"CompanySetting Id - {duc.id}")

                    old_new_module_list = {}
                    for dm in modules:
                        try:
                            dem = Module.objects.using(database_id).get(name=dm.name)
                        except:
                            dem = Module(name=dm.name, order=dm.order)
                            dem.save(using=database_id)
                        old_new_module_list[f"{dm.id}"] = dem.id
                        f.write(f"\nSource Table Name - (modules), Source row id - ({dm.id}), Destination Table Name - (modules), Destination row id - ({dem.id})")
                        print(f"Module Id - {dem.id}")

                    if old_new_module_list:
                        for companyModule in companyModules:
                            destinationCompanyModule = CompanyModule(
                                company=destination_company,
                                module_id=old_new_module_list[f"{companyModule.module_id}"],
                                enabled=companyModule.enabled
                            )
                            destinationCompanyModule.save(using=database_id)
                            f.write(f"\nSource Table Name - (companies_modules), Source row id - ({companyModule.id}), Destination Table Name - (companies_modules), Destination row id - ({destinationCompanyModule.id})")
                            print(f"CompanyModule Id - {dem.id}")
            except Exception as ex:
                db_trans.rollback(database_id)
                f.write(f"\nError occurred during database transaction - {ex.__str__()}")
                f.write(f"\nRolling back transaction")
                print(ex.__str__())
        except Exception as ex:
            f.write(f"\nError occurred during database transaction - {ex.__str__()}")
            print(ex.__str__())



if __name__ == '__main__':

    print(f'Running script to migrate erm_master: {sys.argv[0]}')  # prints the name of the Python script

    if len(sys.argv) < 4:
        print(f'This script requires at least 3 arguments 1st Host, 2nd Username, 3rd Password, 4th(Optional) Company Name. Only {len(sys.argv)-1} are provided.')

    else:
        company_obj = None
        host = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]
        # db_name = sys.argv[4]
        db_name = 'erm_master'
        port = '3306'

        # Making dynamic connection
        database_id = "uniqueMigrateId"
        newDatabase = {}
        newDatabase["id"] = database_id
        newDatabase['ENGINE'] = 'django.db.backends.mysql'
        newDatabase['NAME'] = db_name
        newDatabase['USER'] = username
        newDatabase['PASSWORD'] = password
        newDatabase['HOST'] = host
        newDatabase['PORT'] = port
        newDatabase['ATOMIC_REQUESTS'] = True
        settings.DATABASES[database_id] = newDatabase

        # Check if db settings are correct
        db_conn = connections[database_id]
        try:
            c = db_conn.cursor()
        except OperationalError as ex:
            print(ex.__str__())
        else:
            print("Connected")
            if len(sys.argv) > 4:
                company_obj_get = Company.objects.using('default').filter(name=sys.argv[4])
                if company_obj_get:
                    company_obj = company_obj_get
                else:
                    print(f"There is no company named as {sys.argv[4]}")
            else:
                company_obj = Company.objects.using('default').all()

            if company_obj:
                log_file_name = f"company_migration_{datetime.datetime.today().strftime('%Y%m%d%H%M%S%f')}.log"
                file_path = (os.path.join(os.getcwd(), log_file_name))
                for company in company_obj:
                    print(company)
                    migrate(company, database_id, file_path)