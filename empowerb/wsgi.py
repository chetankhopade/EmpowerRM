"""
WSGI config for tychetools project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os
from tasks import report_schedule_process,report_run_prcoess
from django.core.wsgi import get_wsgi_application
import subprocess
import shlex

from empowerb.settings import USE_EXTERNAL_IMPORT_SERVICE, USE_EXTERNAL_REPORT_SERVICE

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'empowerb.settings')

application = get_wsgi_application()
if not USE_EXTERNAL_IMPORT_SERVICE:
    process_tasks_cmd = "python service_import844.py"
    process_tasks_args = shlex.split(process_tasks_cmd)
    process_tasks_subprocess = subprocess.Popen(process_tasks_args)

if not USE_EXTERNAL_REPORT_SERVICE:
    # EA-1612 both below function
    report_schedule_process()
    report_run_prcoess()
