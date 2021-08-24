import os.path

from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import ok_json, bad_json
from app.management.utilities.globals import addGlobalData
from empowerb.settings import MEDIA_ROOT
from ermm.models import EDIMappingTemplate


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'Administration - EDI Mappings - Step 1', 'header_title': 'EDI Mappings > Step 1'}
    addGlobalData(request, data)

    data['mappings_templates'] = EDIMappingTemplate.objects.all()
    data['menu_option'] = 'menu_administration_edi_mapper'
    return render(request, "administration/edi_mapping/step1.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def upload_edi_file(request):
    data = {'title': 'Administration - EDI Mappings - Upload EDI File'}
    addGlobalData(request, data)

    try:
        if request.FILES:
            new_edi_file = request.FILES['file']
            path_file = os.path.join(MEDIA_ROOT, new_edi_file.name)

            if os.path.exists(path_file):
                os.remove(path_file)

            # store the file
            fs = FileSystemStorage()
            fs.save(new_edi_file.name, new_edi_file)

            # validate if is a valid raw edi
            with open(path_file, 'r') as reader:
                # read the file content
                content = reader.read().split("\n")
                if not content[0].startswith('ISA'):
                    return bad_json(message='The file is not a valid EDI File')

            return ok_json()

        return bad_json(message='File not found')
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def delete_edi_file(request):
    data = {'title': 'Administration - EDI Mappings - Delete EDI File'}
    addGlobalData(request, data)

    try:
        filename = request.POST['fn']
        path_file = os.path.join(MEDIA_ROOT, filename)
        if os.path.exists(path_file):
            os.remove(path_file)
            return ok_json(data={'message': 'File has been removed'})

        return bad_json(message='File does not exist')
    except Exception as ex:
        return bad_json(message=ex.__str__())
