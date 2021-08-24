import datetime
import os
import sys
import time

import django
import json
from dateutil.relativedelta import relativedelta


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from ermm.models import Company
from erms.models import ScheduledReport
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_USER_REPORTS_SCHEDULE
from app.management.utilities.constants import (REPORT_SCHEDULE_FREQUENCY_DAILY, REPORT_SCHEDULE_FREQUENCY_WEEKLY,
                                                REPORT_SCHEDULE_FREQUENCY_MONTHLY,REPORT_SCHEDULE_FREQUENCY_QUARTARLY)


"""
    Ticket: 48
    Set up automatic reports to be sent via email on a schedule
    Runs as a service regardless of whether user is logged into ERM or not
"""


class ScheduleReportServiceException(Exception):

    def __init__(self, error, filename):
        self.error = error
        self.filename = filename


class ScheduleReportHandler:

    # def validate_is_file(self):
    #     try:
    #         is_file = Path(self.file).is_file()
    #     except AttributeError and OSError:
    #         is_file = False
    #     return is_file
    def run_report(self,all_scheduled_reports):

        if all_scheduled_reports:
            for key,value in all_scheduled_reports.items():
                scheduled_report = ScheduledReport.objects.using(value['company_database']).get(id=value['schedule_id'])

                # EA-1603 Disabled scheduled report was still sent
                if scheduled_report.is_enabled:
                    scheduled_report.report_schedule_handler(db=value['company_database'], from_web=False, company_id=value['company_id'])
                    print(f'Report successfully generated and an email has been sent to recipients:')
                else:
                    print(f'Report schedule - {scheduled_report.get_schedule_rep()} is not matching with current time:')


    def process(self):
        try:
            scheduled_report = {};
            for company_id in os.listdir(CLIENTS_DIRECTORY):
                try:
                    company = Company.objects.get(id=company_id)
                    print(f"\n<<< Service START - Scheduled Reports ({company.database}) >>>")
                    if os.path.isdir(os.path.join(CLIENTS_DIRECTORY, company_id)):
                        i = 0
                        for file_name in [fn for fn in os.listdir(os.path.join(CLIENTS_DIRECTORY, company_id, DIR_NAME_USER_REPORTS_SCHEDULE))]:
                            now = datetime.datetime.now()
                            with open(os.path.join(CLIENTS_DIRECTORY, company_id, DIR_NAME_USER_REPORTS_SCHEDULE, file_name)) as f:
                                data = json.load(f)
                                # In json file following keys must be there
                                schedule_id = data["id"]
                                schedule_frequency = data["frequency"]
                                schedule_hour = data["hour"]
                                schedule_minute = data["minute"]
                                schedule_monthday = data["monthday"]
                                schedule_weekday = data["weekday"]
                                is_enabled = data["is_enabled"]
                                scheduled_report_name = data["name"]
                                # EA-1603 Disabled scheduled report was still sent
                                if is_enabled == True :
                                    if REPORT_SCHEDULE_FREQUENCY_MONTHLY == schedule_frequency:
                                        if now.day == schedule_monthday and schedule_hour == now.hour and now.minute == schedule_minute:
                                            scheduled_report.update({i: {'schedule_id': schedule_id,'company_database': company.database,'company_id': company_id}})
                                            i = i + 1
                                    elif REPORT_SCHEDULE_FREQUENCY_WEEKLY == schedule_frequency:
                                        if now.today().isoweekday() == schedule_weekday and schedule_hour == now.hour and now.minute == schedule_minute:
                                            scheduled_report.update({i: {'schedule_id': schedule_id,'company_database': company.database,'company_id': company_id}})
                                            i = i + 1
                                    # EA-1555 Add Quartarly as an option to the Email Scheduler
                                    elif REPORT_SCHEDULE_FREQUENCY_QUARTARLY == schedule_frequency:
                                        currQuarter = int((now.month - 1) / 3 + 1)
                                        QuaterFirstDay = datetime.datetime(now.year, 3 * currQuarter - 2, 1)
                                        QuaterLastDay = QuaterFirstDay + relativedelta(months=3, days=-1)
                                        # Send report every quatarly end date +1
                                        QuaterLastDay += datetime.timedelta(days=1)
                                        if now.today().date() == QuaterLastDay.date() and schedule_hour == now.hour and now.minute == schedule_minute:
                                            scheduled_report.update({i: {'schedule_id': schedule_id,'company_database': company.database,'company_id': company_id}})
                                            i = i + 1
                                    else:
                                        # if not above 2 assumed that it is DAILY
                                        if schedule_hour == now.hour and now.minute == schedule_minute:
                                            scheduled_report.update({i: {'schedule_id': schedule_id,'company_database': company.database,'company_id': company_id}})
                                            i = i + 1

                                else:
                                    print(f'Report schedule - {scheduled_report_name} is disabled.')

                    return scheduled_report
                except Company.DoesNotExist:
                    print(f'Company does not exist: {company_id}')
                except Exception as ex:
                    print(f'Error: {ex.__str__()}')

        except Exception as ex:
            print(ex.__str__())


if __name__ == '__main__':
    # Run process as soon as service is started
    print(f"\n<<< SCHEDULE REPORT SERVICE STARTED AT {datetime.datetime.today().strftime('%m/%d/%Y %H:%M:%S')}")
    sc = ScheduleReportHandler()
    all_scheduled_report = sc.process()
    sc.run_report(all_scheduled_report)

    try:
        while True:
            # Get json files data after each 1 minute
            time.sleep(60)
            all_scheduled_report = sc.process()
            sc.run_report(all_scheduled_report)
    except Exception as ex:
        print(ex.__str__())
