import time

from django.core.management.base import BaseCommand
from django.core.management import call_command

from empowerb.settings import DATABASES


class Command(BaseCommand):

    def handle(self, *args, **options):

        try:

            print("\n")
            print("*" * 50)
            print("ERM Migration Process - STARTED")
            print("*"*50)
            print("\n")

            print(">>> Master DB")
            time.sleep(1)
            call_command('migrate', 'ermm', '--database=default')
            print("\n")

            for dbName in [k for k in DATABASES.keys() if k != 'default']:
                print(f">>> Local DB: {dbName}")
                time.sleep(1)
                call_command('migrate', 'erms', f'--database={dbName}')
                print("\n")

            print("*" * 50)
            print("ERM Migration Process - COMPLETED!!!")
            print("*" * 50)

        except Exception as ex:
            print('Error {}'.format(ex.__str__()))
