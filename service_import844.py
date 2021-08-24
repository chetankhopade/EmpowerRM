import datetime
import os
import shutil
import sys
import time
import django
from django.db import transaction

from watchdog import events
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

# custom imports (needs to be here after django setup)
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_844_ERM_INTAKE, DIR_NAME_844_PROCESSED, DIR_NAME_844_ERM_ERROR

from app.chargebacks.cb_import import ImportProcess
from app.tasks import import_validations_function
from app.management.utilities.functions import move_file_to_bad_folder, validate_844_header
from ermm.models import Company
from erms.models import ChargeBackLine, ChargeBackDispute, Import844History


class Import844ServiceException(Exception):

    def __init__(self, error, filename):
        self.error = error
        self.filename = filename


class Import844Handler(PatternMatchingEventHandler):

    patterns = ["*.txt", "*.edi"]

    def __init__(self):
        super().__init__()

        self.file = None

    def validate_is_file(self):
        try:
            is_file = Path(self.file).is_file()
        except AttributeError and OSError:
            is_file = False
        return is_file

    def check_existing_files(self):
        try:
            existing_files_events = []
            # check for existing files and triggers FileHandler watchdog events
            for company_id in os.listdir(CLIENTS_DIRECTORY):
                try:
                    company = Company.objects.get(id=company_id)
                    company_setting = company.my_company_settings()
                    # ticket EA-1369 if company automate is enabled then check existing files
                    if company_setting.automate_import:
                        if os.path.isdir(os.path.join(CLIENTS_DIRECTORY, company_id)):
                            for file_name in [fn for fn in os.listdir(os.path.join(CLIENTS_DIRECTORY, company_id, DIR_NAME_844_ERM_INTAKE))]:
                                existing_files_events.append(events.FileCreatedEvent(os.path.join(CLIENTS_DIRECTORY, company_id, DIR_NAME_844_ERM_INTAKE, file_name)))
                except Company.DoesNotExist:
                    print(f'Company does not exist: {company_id}')
                except Exception as ex:
                    print(f'Error: {ex.__str__()}')

            # trigger existing files if exist
            for file_event in existing_files_events:
                self.on_created(file_event)

        except Exception as ex:
            print(ex.__str__())

    def on_created(self, event):

        try:
            self.file = Path(event.src_path)
            filename = os.path.basename(self.file)
            parent_directory_name = Path(self.file).parent.name
            company_id = Path(self.file).parent.parent.name
            company = Company.objects.get(id=company_id)
            database = company.database
            company_setting = company.my_company_settings()
            company_directory = os.path.join(CLIENTS_DIRECTORY, company.get_id_str())

            # EA-1459 - HOTFIX: Autoimport service causes outbound files to be moved to 849_ERM_error folder
            # Process file only and only if it's 844 erm intake
            if parent_directory_name == DIR_NAME_844_ERM_INTAKE:

                # ticket EA-1369 If the Automate Import Setting is enabled, Update the Auto Import Service
                if company_setting.automate_import:

                    # validate the file
                    if not self.validate_is_file():
                        move_file_to_bad_folder(self.file)
                        raise Import844ServiceException(error='It is not a file', filename=filename)

                    # Is Valid 844 File
                    if not validate_844_header(self.file):
                        move_file_to_bad_folder(self.file)
                        raise Import844ServiceException(error='The file is not a valid 844 file', filename=filename)

                    # Wrong parent directory
                    if parent_directory_name != DIR_NAME_844_ERM_INTAKE:
                        raise Import844ServiceException(error='It is not a valid 844 directory', filename=filename)

                    # ImportProcess instance
                    import_process = ImportProcess(company, self.file)

                    print(f"Automatic Import process is starting (Company: {company.name}, File: {self.file})")

                    try:
                        # Import844 (read file and store data in the Import844 table)
                        time1 = datetime.datetime.now()
                        import_process.save_import844()
                        time2 = datetime.datetime.now()
                        delta = (time2 - time1).total_seconds()
                        print(f"\nSave Import844 Process: {delta} sec")

                        time1 = datetime.datetime.now()
                        cbs_created = import_process.save_chargebacks(True)
                        time2 = datetime.datetime.now()
                        delta = (time2 - time1).total_seconds()
                        print(f"\nSave CB/CBL/Imp844H Process: {delta} sec")

                        # Validations
                        # if company.processing_option == PROCESSING_OPTION_ORIGINAL_ID:
                        import_validations_function(company_id, database, [], None)
                        # Move it to "DIR_NAME_844_PROCESSED" folder
                        shutil.move(self.file, os.path.join(Path(''.join(os.path.join(company_directory, DIR_NAME_844_PROCESSED))), os.path.basename(self.file)))
                        print(f"Automatic Import process is completed (Company: {company.name}, File: {self.file})")

                    except Exception as ex:
                        # EA-1507 - AutoImport is moving files to error folder 844_ERM_error
                        # We are rechecking this existing file and creating file create event only if mysql server has gone away
                        if cbs_created:
                            for cb in cbs_created:
                                chargeback_id = cb.id
                                # deleting CBs and entities associated with it on exception
                                # Delete ChargeBackLine
                                ChargeBackLine.objects.using(database).filter(chargeback_id=chargeback_id).delete()

                                # Delete ChargeBackDisputes (for cblines and cb)
                                ChargeBackDispute.objects.using(database).filter(chargebackline_id__in=[x.__str__() for x in cb.get_my_chargeback_lines().values_list('id', flat=True)]).delete()
                                ChargeBackDispute.objects.using(database).filter(chargeback_id=chargeback_id).delete()

                                # Delete Import844
                                Import844History.objects.using(database).filter(id=cb.import844_id).delete()

                                cb.delete(using=database)
                        ex_string = ex.__str__()
                        print(ex_string)
                        mysql_server_gone_away_string = "MySQL server has gone away"
                        if ex_string.find(mysql_server_gone_away_string) == -1:
                            # EA-1479 - HOTFIX: AutoImport Service moves files to processed without importing them
                            shutil.move(self.file, os.path.join(Path(''.join(os.path.join(company_directory, DIR_NAME_844_ERM_ERROR))), os.path.basename(self.file)))
                            print(f" File: {self.file}) is moved to bad folder {DIR_NAME_844_ERM_ERROR}")
                        else:
                            time.sleep(5)
                            file_create_event = (events.FileCreatedEvent(os.path.join(CLIENTS_DIRECTORY, company_id, DIR_NAME_844_ERM_INTAKE, filename)))
                            self.on_created(file_create_event)

                else:
                    print(f"Automatic Import is disabled for company: {company.name}")

        except Exception as ex:
            print(ex.__str__())


if __name__ == '__main__':

    import844_handler = Import844Handler()

    # check existing files (first)
    import844_handler.check_existing_files()

    observer = Observer()
    observer.schedule(import844_handler, CLIENTS_DIRECTORY, recursive=True)
    observer.start()
    print(f'Observer is ready and watching at {CLIENTS_DIRECTORY}')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
