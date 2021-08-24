import asyncio
import datetime
import os
import sys
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
from empowerb.settings import CLIENTS_DIRECTORY, DIR_NAME_USER_REPORTS_SCHEDULE, DIR_NAME_USER_REPORTS_RUN
from app.management.utilities.constants import (REPORT_SCHEDULE_FREQUENCY_DAILY, REPORT_SCHEDULE_FREQUENCY_WEEKLY,
                                                REPORT_SCHEDULE_FREQUENCY_MONTHLY,REPORT_SCHEDULE_FREQUENCY_QUARTARLY)


from asgiref.sync import sync_to_async


@sync_to_async
def get_compaany(company_id):
    return Company.objects.using('default').get(id=company_id)

@sync_to_async
def get_schedule(schedule_id,company_database):
    return ScheduledReport.objects.using(company_database).get(id=schedule_id)

async def create_scheduled_report():
    try:
         for company_id in os.listdir(CLIENTS_DIRECTORY):

            company = await get_compaany(company_id)
            print(f"\n<<< Service START - Scheduled Reports ({company.database}) >>>")
            if os.path.isdir(os.path.join(CLIENTS_DIRECTORY, company_id)):
                for file_name in [fn for fn in os.listdir(
                        os.path.join(CLIENTS_DIRECTORY, company_id, DIR_NAME_USER_REPORTS_SCHEDULE))]:
                    now = datetime.datetime.now()
                    with open(os.path.join(CLIENTS_DIRECTORY, company_id, DIR_NAME_USER_REPORTS_SCHEDULE,
                                           file_name)) as f:
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
                        scheduled_report = await get_schedule(schedule_id,company.database)
                        file_data = {"schedule_id": data["id"],"company_database":company.database,"company_id":company_id}
                        # EA-1603 Disabled scheduled report was still sent
                        if is_enabled == True:
                            if REPORT_SCHEDULE_FREQUENCY_MONTHLY == schedule_frequency:
                                if now.day == schedule_monthday and schedule_hour == now.hour and now.minute == schedule_minute:

                                    filename = f"sc_{schedule_frequency}_{schedule_hour}_{schedule_minute}_{scheduled_report.id}.json"
                                    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company_id}",
                                                             f"{DIR_NAME_USER_REPORTS_RUN}", f"{filename}")
                                    if os.path.isfile(file_path) == False:
                                        print(f'Monthly task created -{scheduled_report_name} # {schedule_id}.')
                                        with open(file_path, 'w') as outfile:
                                                  json.dump(file_data, outfile)

                            elif REPORT_SCHEDULE_FREQUENCY_WEEKLY == schedule_frequency:
                                if now.today().isoweekday() == schedule_weekday and schedule_hour == now.hour and now.minute == schedule_minute:

                                    filename = f"sc_{schedule_frequency}_{schedule_hour}_{schedule_minute}_{scheduled_report.id}.json"
                                    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company_id}",
                                                             f"{DIR_NAME_USER_REPORTS_RUN}", f"{filename}")
                                    if os.path.isfile(file_path) == False:
                                        print(f'WEEKLY Task created -{scheduled_report_name} # {schedule_id} .')
                                        with open(file_path, 'w') as outfile:
                                                  json.dump(file_data, outfile)



                            # EA-1555 Add Quartarly as an option to the Email Scheduler
                            elif REPORT_SCHEDULE_FREQUENCY_QUARTARLY == schedule_frequency:
                                currQuarter = int((now.month - 1) / 3 + 1)
                                QuaterFirstDay = datetime.datetime(now.year, 3 * currQuarter - 2, 1)
                                QuaterLastDay = QuaterFirstDay + relativedelta(months=3, days=-1)
                                # Send report every quatarly end date +1
                                QuaterLastDay += datetime.timedelta(days=1)
                                if now.today().date() == QuaterLastDay.date() and schedule_hour == now.hour and now.minute == schedule_minute:

                                    filename = f"sc_{schedule_frequency}_{schedule_hour}_{schedule_minute}_{scheduled_report.id}.json"
                                    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company_id}",
                                                             f"{DIR_NAME_USER_REPORTS_RUN}", f"{filename}")
                                    if os.path.isfile(file_path) == False:
                                        print(f'QUARTARLY Task created -{scheduled_report_name} # {schedule_id} .')
                                        with open(file_path, 'w') as outfile:
                                                  json.dump(file_data, outfile)


                            else:
                                # if not above 2 assumed that it is DAILY
                                if schedule_hour == now.hour and now.minute == schedule_minute:

                                    filename = f"sc_{schedule_frequency}_{schedule_hour}_{schedule_minute}_{scheduled_report.id}.json"
                                    file_path = os.path.join(f"{CLIENTS_DIRECTORY}", f"{company_id}",
                                                             f"{DIR_NAME_USER_REPORTS_RUN}", f"{filename}")
                                    if os.path.isfile(file_path) == False:
                                        print(f'Daily Task created -{scheduled_report_name} # {schedule_id}.')
                                        with open(file_path, 'w') as outfile:
                                                  json.dump(file_data, outfile)

                        else:
                                    print(f'Report schedule - {scheduled_report_name} is disabled.')
    except Exception as ex:
        print(ex.__str__())

async def main():
   while True:
        await asyncio.sleep(60)
        print("Task Executed")
        res = await create_scheduled_report()


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    try:
        asyncio.ensure_future(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing Loop")
        loop.close()