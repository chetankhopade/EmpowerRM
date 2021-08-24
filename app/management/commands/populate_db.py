import csv
import os
import time

from django.core.management.base import BaseCommand
from django.db import transaction

from app.management.utilities.constants import APPROVED_REASONS
from empowerb.settings import BASE_DIR

from ermm.models import (Dispute, DirectCustomer, DistributionCenter, ApprovedReason, Company,
                         CompanyModule, Module, QuickbooksConfigurations)

DATASET_PATH = os.path.join(BASE_DIR, 'app', 'management', 'datasets')


def import_approved_reasons():
    try:
        with transaction.atomic():

            print("*" * 50)
            print(">>> Approved Reasons - Migration started ...")
            time.sleep(1)

            for elem in APPROVED_REASONS:
                approved_reason, _ = ApprovedReason.objects.get_or_create(id=elem[0])
                approved_reason.description = elem[1]
                approved_reason.save()
                print(f"ApprovedReason: {approved_reason.id} - {approved_reason.description}")

            print("\n")
            print("*" * 50)
            print("Approved Reasons - Migration Completed !!!")
            print("*" * 50)
            time.sleep(1)

    except Exception as ex:
        print('Error {}'.format(ex.__str__()))
        pass


def import_disputes():

    try:
        with transaction.atomic():

            print("*" * 50)
            print(">>> Disputes - Migration started ...")
            time.sleep(1)

            line = 1
            for row in csv.reader(open(os.path.join(DATASET_PATH, 'disputes.csv'), "rU", encoding='utf-8'), delimiter=','):

                if line > 1:
                    dispute_id = row[0]
                    dispute_type = row[1]
                    dispute_code = row[2]
                    dispute_description = row[3]
                    dispute_explanation = row[4]

                    dispute, _ = Dispute.objects.get_or_create(id=dispute_id)
                    dispute.type = dispute_type
                    dispute.code = dispute_code
                    dispute.description = dispute_description
                    dispute.explanation = dispute_explanation
                    dispute.save()
                    print(f"Dispute: {dispute.id} - {dispute.short_name()}")
                line += 1

            print("\n")
            print("*" * 50)
            print("Disputes - Migration Completed !!!")
            print("*" * 50)
            time.sleep(1)

    except Exception as ex:
        print('Error {}'.format(ex.__str__()))
        pass


def import_direct_customers():

    try:
        with transaction.atomic():

            print("*" * 50)
            print(" >>> Global Direct Customers - Migration Started <<< ")
            time.sleep(1)

            line = 1
            for row in csv.reader(open(os.path.join(DATASET_PATH, 'customers.csv'), "rU", encoding='utf-8'), delimiter=','):

                if line > 1:

                    customer_id = row[0]
                    name = row[1]
                    address1 = row[2]
                    address2 = row[3]
                    city = row[4]
                    state = row[5]
                    zip_code = row[6]

                    customer, _ = DirectCustomer.objects.get_or_create(id=customer_id)
                    customer.name = name
                    customer.address1 = address1
                    customer.address2 = address2
                    customer.city = city
                    customer.state = state
                    customer.zip_code = zip_code
                    customer.save()
                    print(f"Customer: {customer.id} - {customer.name}")
                line += 1

            print("\n")
            print("*" * 50)
            print("Global Customers - Migration Completed !!!")
            print("*" * 50)
            time.sleep(1)

    except Exception as ex:
        print('Error {}'.format(ex.__str__()))
        pass


def import_distribution_centers():
    try:
        with transaction.atomic():

            print("*" * 50)
            print(" >>> Global Distribution Centers - Migration Started <<< ")
            time.sleep(1)

            line = 1
            for row in csv.reader(open(os.path.join(DATASET_PATH, 'distributions_centers.csv'), "rU", encoding='utf-8'), delimiter=','):

                if line > 1:

                    dcenter_id = row[0]
                    customer_id = row[1]
                    name = row[2]
                    dea_number = row[3]
                    hin_number = row[4]
                    address1 = row[5]
                    address2 = row[6]
                    city = row[7]
                    state = row[8]
                    zip_code = row[9]

                    distribution_center, _ = DistributionCenter.objects.get_or_create(id=dcenter_id)
                    distribution_center.customer_id = customer_id
                    distribution_center.name = name
                    distribution_center.dea_number = dea_number
                    distribution_center.hin_number = hin_number
                    distribution_center.address1 = address1
                    distribution_center.address2 = address2
                    distribution_center.city = city
                    distribution_center.state = state
                    distribution_center.zip_code = zip_code
                    distribution_center.save()
                    print(f"Distribution Center: {distribution_center.id} - {distribution_center.name}")
                line += 1

            print("\n")
            print("*" * 50)
            print("Global Distribution Centers - Migration Completed !!!")
            print("*" * 50)
            time.sleep(1)

    except Exception as ex:
        print('Error {}'.format(ex.__str__()))
        pass


def company_modules_update():
    """
    Ticket EA-669
    :return:
    """
    try:
        with transaction.atomic():

            print("*" * 50)
            print(" >>> Company - Modules - Migration Started <<< ")
            time.sleep(1)

            for company in Company.objects.all():
                for module in Module.objects.all():
                    company_module, _ = CompanyModule.objects.get_or_create(company=company, module=module)
                    # Core 'Module' will be enabled by default for all Companies
                    # Migration should set ENABLE Chargeback Module for all existing companies
                    if module.is_chargeback():
                        company_module.enabled = True
                        company_module.save()

            print("\n")
            print("*" * 50)
            print("Company Modules - Migration Completed !!!")
            print("*" * 50)

    except Exception as ex:
        print('Error {}'.format(ex.__str__()))
        pass


def companies_quickbooks_configurations():
    """
    Companies Quickbooks Configurations
    :return:
    """
    try:
        with transaction.atomic():

            print("*" * 50)
            print(" >>> Quickbooks Company Configuration - Started <<< ")
            time.sleep(1)

            for company in Company.objects.all():
                QuickbooksConfigurations.objects.get_or_create(company=company)

            print("\n")
            print("*" * 50)
            print("Quickbooks Company Configuration- Completed !!!")
            print("*" * 50)

    except Exception as ex:
        print('Error {}'.format(ex.__str__()))
        pass


class Command(BaseCommand):

    # def add_arguments(self, parser):
    #     parser.add_argument('database', nargs='+')

    def handle(self, *args, **options):

        try:

            # Import Approved Reason
            import_approved_reasons()

            print("\n")

            # Import Disputes
            import_disputes()

            print("\n")

            # Import Direct Customers
            import_direct_customers()

            print("\n")

            # Import Distribution Centers
            import_distribution_centers()

            print("\n")

            # Create / Update Company - Modules relationship (Ticket EA-669)
            company_modules_update()

            print("\n")

            # Update Tokens for existing companies
            companies_quickbooks_configurations()

            print("<<<< MIGRATION COMPLETED! >>>>")

        except Exception as ex:
            print('Error {}'.format(ex.__str__()))
