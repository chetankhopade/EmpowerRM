import os
import time

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt

from app.administration.edi_mapping.handler import EDIFileHandler
from app.management.utilities.functions import ok_json, model_to_dict_safe, bad_json
from app.management.utilities.globals import addGlobalData
from empowerb.settings import MEDIA_ROOT
from ermm.models import EDIMappingTemplate


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def view(request):
    data = {'title': 'Administration - EDI Mappings - Step 3', 'header_title': 'EDI Mappings > Step 3'}
    addGlobalData(request, data)

    data['filename'] = request.GET['fn']
    data['mapid'] = request.GET['mapid']

    data['menu_option'] = 'menu_administration_edi_mapper'
    return render(request, "administration/edi_mapping/step3.html", data)


def update_mapping_status(request, map_id, status_id):
    data = {'title': 'Administration - EDI Mappings - Step 3 - Update Mapping Status'}
    addGlobalData(request, data)

    try:
        mapping = EDIMappingTemplate.objects.get(id=map_id)
        mapping.status = status_id
        mapping.save()

        source_file_path = os.path.join(MEDIA_ROOT, request.POST['sourceFileName'])
        if os.path.exists(source_file_path):
            os.remove(source_file_path)

        destination_file_path = os.path.join(MEDIA_ROOT, request.POST['destinationFileName'])
        if os.path.exists(destination_file_path):
            os.remove(destination_file_path)

        time.sleep(1)
        return ok_json(data={'message': f'Mapping has been updated with status: {mapping.get_status_display()}',
                             'redirect_url': '/default/administration/edi_mapping/s1'})

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def source_data(request):

    # EDIFileHandler instance to handle and process file
    edi_fh = EDIFileHandler(filename=request.POST['fn'])

    # get segments based on output
    segments = edi_fh.content if request.POST['output'] == 'file' else edi_fh.get_segment_list()

    # Get Mapping and create destination file
    mapping = EDIMappingTemplate.objects.get(id=request.POST['mapid'])
    # send list of defined descriptors for the mapping
    descriptors = mapping.get_map_descriptors_list()

    time.sleep(1)
    return ok_json(data={'segments': segments,
                         'descriptors': descriptors,
                         'separator': edi_fh.separator,
                         'doctype': edi_fh.doctype,
                         'filename': edi_fh.filename})


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def destination_data(request):

    try:
        # EDIFileHandler instance to handle and process file
        edi_fh = EDIFileHandler(filename=request.POST['fn'])
        # Get Mapping and create destination file
        mapping = EDIMappingTemplate.objects.get(id=request.POST['mapid'])
        #  create destination file
        result_file, result_filename = mapping.create_destination_file(edi_fh=edi_fh)

        # open file and read it to process it (send it to the frontend)
        with open(result_file, 'r') as reader:
            # read the file content
            content = reader.read()

            segments = content.split("\n")
            # segment id row derived from header row
            segm_ids_rows = [mapping.get_segment_name_and_descriptor_based_on_map_name(x) for x in segments[0].split(mapping.delimiter)]

            matrix = []
            for item in segments:
                row_content = []
                for index, value in enumerate(item.split(mapping.delimiter)):
                    row_content.append({
                        'value': value,
                        'seg_name': segm_ids_rows[index][0],
                        'segm_descriptor': segm_ids_rows[index][1]
                    })
                matrix.append(row_content)

        time.sleep(1)
        return ok_json(data={'mapping_obj': model_to_dict_safe(mapping),
                             'rows_matrix': matrix,
                             'content': content,
                             'result_filename': result_filename})

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


def destination_data_view(request, filename):
    data = {'title': 'Administration - EDI Mappings - Step 3 - View Destination File'}
    addGlobalData(request, data)

    try:

        file_path = os.path.join(MEDIA_ROOT, filename)
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application")
            return response

    except Exception as ex:
        print(ex.__str__())
        return bad_json(message=ex.__str__())


def destination_data_download(request, filename):
    data = {'title': 'Administration - EDI Mappings - Step 3 - Download Destination File'}
    addGlobalData(request, data)

    file_path = os.path.join(MEDIA_ROOT, filename)
    f = open(file_path, 'r')
    response = HttpResponse(f, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(filename)
    response['X-Sendfile'] = smart_str(file_path)
    f.close()
    return response

