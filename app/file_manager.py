import os
import time
from datetime import datetime, timezone

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import bad_json, scan_dir, ok_json
from app.management.utilities.globals import addGlobalData
from empowerb.settings import (CLIENTS_DIRECTORY, DIR_NAME_844_ERM_INTAKE, DIR_NAME_844_ERM_ERROR,
                               DIR_NAME_849_ERM_OUT, DIR_NAME_849_ERM_HISTORY, DIR_NAME_FILES_STORAGE,
                               FOLDERS_STRUCTURE, DIR_NAME_844_PROCESSED, DIR_NAME_849_ERM_MANUAL,
                               DIR_NAME_USER_REPORTS)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def view(request):
    data = {'title': 'File Manager', 'header_title': 'File Manager'}
    addGlobalData(request, data)

    if request.method == 'POST':
        try:
            params = {
                "stage": request.POST.get('stage', ''),
                "create_date": "",
                "end_date": ""
            }

            cdate_string = request.POST.get('cdate', '')
            if cdate_string:
                cdate = datetime.strptime(cdate_string, "%m/%d/%Y")
                ctimestamp = cdate.replace(tzinfo=timezone.utc).timestamp()
                params["create_date"] = ctimestamp
            else:
                params["create_date"] = 0

            edate_string = request.POST.get('edate', '')
            if edate_string:
                edate = datetime.strptime(edate_string, "%m/%d/%Y")
                etimestamp = edate.replace(tzinfo=timezone.utc).timestamp()
                params["end_date"] = etimestamp
            else:
                params["end_date"] = int(time.time())

            # Process Dir/Files tree
            children = []
            root = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str())
            scan_dir(root, children, "", params)

            return JsonResponse({"root": children})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    # 844 Folders
    data['844_folders_structure'] = (
        (DIR_NAME_844_ERM_INTAKE, FOLDERS_STRUCTURE[DIR_NAME_844_ERM_INTAKE]),
        (DIR_NAME_844_PROCESSED, FOLDERS_STRUCTURE[DIR_NAME_844_PROCESSED])
    )

    # 849 Folders
    data['849_folders_structure'] = (
        (DIR_NAME_849_ERM_OUT, FOLDERS_STRUCTURE[DIR_NAME_849_ERM_OUT]),
        (DIR_NAME_849_ERM_HISTORY, FOLDERS_STRUCTURE[DIR_NAME_849_ERM_HISTORY]),
        (DIR_NAME_849_ERM_MANUAL, FOLDERS_STRUCTURE[DIR_NAME_849_ERM_MANUAL])
    )

    # User Files Storage
    data['user_uploads_folders_structure'] = (
        (DIR_NAME_FILES_STORAGE, FOLDERS_STRUCTURE[DIR_NAME_FILES_STORAGE]),
        (DIR_NAME_USER_REPORTS, FOLDERS_STRUCTURE[DIR_NAME_USER_REPORTS])
    )

    # EA-872 - 849 files are showing on the File Manager page with the type "844"
    data['errors_folders_structure'] = (DIR_NAME_844_ERM_ERROR, FOLDERS_STRUCTURE[DIR_NAME_844_ERM_ERROR])

    data['menu_option'] = 'menu_file_manager'
    return render(request, 'file_manager/view.html', data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def file_view(request, dirname, filename):
    data = {'title': 'File Manager - File View', 'header_title': 'File View'}
    addGlobalData(request, data)

    file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), dirname, filename)
    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application")
        return response


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def file_download(request, dirname, filename):
    data = {'title': 'File Manager - File Download', 'header_title': 'File Download'}
    addGlobalData(request, data)

    file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), dirname, filename)
    with open(file_path, 'rb') as f:
        response = HttpResponse(f, content_type="application/force-download")
        response['Content-Disposition'] = f'attachment; filename=%s' % smart_str(filename)
        response['X-Sendfile'] = smart_str(file_path)
    return response


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def file_delete(request, dirname, filename):
    data = {'title': 'File Manager - File Delete', 'header_title': 'File Delete'}
    addGlobalData(request, data)

    try:
        file_path = os.path.join(CLIENTS_DIRECTORY, data['company'].get_id_str(), dirname, filename)
        os.remove(file_path)
        time.sleep(1)
        return ok_json()

    except Exception as ex:
        return bad_json(message=ex.__str__())
