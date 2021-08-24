import subprocess
import shlex
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

def report_schedule_process():
    process_tasks_cmd = "python report_schedule.py"
    process_tasks_args = shlex.split(process_tasks_cmd)
    process_tasks_subprocess = subprocess.Popen(process_tasks_args)

def report_run_prcoess():
    process_tasks_cmd = "python run_report.py"
    process_tasks_args = shlex.split(process_tasks_cmd)
    process_tasks_subprocess = subprocess.Popen(process_tasks_args)

