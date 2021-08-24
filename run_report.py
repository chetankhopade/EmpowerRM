import datetime
import os
import sys
import time
import django
import json


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from ermm.models import Company
from erms.models import ScheduledReport
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_USER_REPORTS_RUN
from django.contrib.auth.models import User

from watchdog import events
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from pathlib import Path

class RunReportHandlerServiceException(Exception):

    def __init__(self, error, filename):
        self.error = error
        self.filename = filename


class RunReportHandler(PatternMatchingEventHandler):

    patterns = ["*.json"]

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
                    company = Company.objects.using("default").get(id=company_id)
                    if os.path.isdir(os.path.join(CLIENTS_DIRECTORY, company_id)):
                            for file_name in [fn for fn in os.listdir(os.path.join(CLIENTS_DIRECTORY, company_id, DIR_NAME_USER_REPORTS_RUN))]:
                                existing_files_events.append(events.FileCreatedEvent(os.path.join(CLIENTS_DIRECTORY, company_id, DIR_NAME_USER_REPORTS_RUN, file_name)))
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
            company = Company.objects.using("default").get(id=company_id)
            database = company.database
            company_id_str = company.get_id_str()
            company_directory = os.path.join(CLIENTS_DIRECTORY, company.get_id_str())
            src_path = os.path.join(company_directory, DIR_NAME_USER_REPORTS_RUN, self.file)

            # Process file only and only if it's reports run take
            if parent_directory_name == DIR_NAME_USER_REPORTS_RUN:
                    # validate the file
                    if not self.validate_is_file():
                        raise RunReportHandlerServiceException(error='It is not a file', filename=filename)
                    try:
                        with open(self.file) as f:
                            data = json.load(f)
                            schedule_id = data["schedule_id"]
                            company_database = data["company_database"]
                            company_id = data["company_id"]
                            # scheduled_report = ScheduledReport.objects.using(company_database).select_related('report').get(id=schedule_id)
                            scheduled_report = ScheduledReport.objects.using(company_database).get(id=schedule_id)
                            print(f"Report run start {scheduled_report.name}...")
                            if scheduled_report.is_enabled:
                                userinfo = User.objects.using('default').filter(username=scheduled_report.updated_by).values('email').distinct()
                                # print(userinfo[0]['email'])
                                scheduled_report.report_schedule_handler(db=company_database, from_web=False,company_id=company_id,user_email=userinfo[0]['email'])
                                # time.sleep(60)
                                print(f'{company_database} {scheduled_report.get_schedule_rep()} Report  successfully generated and an email has been sent to recipients:')
                                # Remove json created file
                            else:
                                print(f'Report schedule - {scheduled_report.get_schedule_rep()} is not matching with current time:')
                        print(f'{self.file}')
                        os.remove(self.file)
                    except Exception as ex:
                        print(ex.__str__())

        except Exception as ex:
            print(ex.__str__())


if __name__ == '__main__':

    run_report_handler = RunReportHandler()

    # check existing files (first)
    run_report_handler.check_existing_files()

    observer = Observer()
    observer.schedule(run_report_handler, CLIENTS_DIRECTORY, recursive=True)
    observer.start()
    print(f'Observer is ready and watching at {CLIENTS_DIRECTORY}')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
