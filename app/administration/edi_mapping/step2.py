import json
import time

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from app.administration.edi_mapping.handler import EDIFileHandler
from app.management.utilities.constants import (EDI_MAPPING_OUTPUT_FORMATS, EDI_MAPPING_OUTPUT_FORMAT_TEXT,
                                                EDI_MAPPING_OUTPUT_FORMAT_CSV)
from app.management.utilities.functions import ok_json, bad_json, model_to_dict_safe
from app.management.utilities.globals import addGlobalData
from ermm.models import EDIMappingTemplate, EDIMappingTemplateDetail


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def view(request):
    data = {'title': 'Administration - EDI Mappings > Step 2', 'header_title': 'EDI Mappings > Step 2'}
    addGlobalData(request, data)

    # if user selected an existing mapper
    if 'mapid' in request.GET and request.GET['mapid'] != '0':
        data['selected_mapping_template'] = EDIMappingTemplate.objects.get(id=request.GET['mapid'])

    # get filename from request and create EDIFileHandler instance
    data['edi_fh'] = edi_fh = EDIFileHandler(request.GET['fn'])  # send handler obj to frontend
    data['segments_list'] = edi_fh.get_segment_list()

    data['edi_mapping_output_formats'] = EDI_MAPPING_OUTPUT_FORMATS
    data['edi_mapping_output_format_text'] = EDI_MAPPING_OUTPUT_FORMAT_TEXT
    data['edi_mapping_output_format_csv'] = EDI_MAPPING_OUTPUT_FORMAT_CSV
    data['existing_mappings_templates'] = EDIMappingTemplate.objects.all()

    data['menu_option'] = 'menu_administration_edi_mapper'
    return render(request, "administration/edi_mapping/step2.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def mapping_details(request):

    # get mapid from request (0 -> New Map)
    mapid = request.POST['mapid']

    # new map
    if mapid == '0':
        selected_mapping_obj = None
        mapping_details = []

    # existing map
    else:
        selected_mapping = EDIMappingTemplate.objects.get(id=mapid)
        mapping_details = [model_to_dict_safe(x) for x in selected_mapping.get_my_details()]
        selected_mapping_obj = model_to_dict_safe(selected_mapping)

    time.sleep(1)
    return ok_json(data={'mapping_obj': selected_mapping_obj, 'mapping_details': mapping_details})


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def save_template(request):
    data = {'title': 'Administration - EDI Mappings - Save EDI Mapping Template'}
    addGlobalData(request, data)

    try:
        with transaction.atomic():
            file_name = request.POST['file_name']
            mapping_name = request.POST['mapping_name']
            document_type = request.POST['document_type']
            output_format = request.POST['output_format']
            delimiter = request.POST['delimiter']
            mapping_type = int(request.POST['mapping_type']) if int(request.POST['mapping_type']) else None
            show_header = int(request.POST['show_header']) == 1
            # items (mapping details)
            items = json.loads(request.POST['items'])
            # loops segments
            main_loop_segment = request.POST['main_loop_segment']
            nested_loop_segment = request.POST['nested_loop_segment']
            end_loop_segment = request.POST['end_loop_segment']

            if not mapping_name:
                return bad_json(message='Mapping Name is required')

            if not items:
                return bad_json(message='Empty List')

            emt, _ = EDIMappingTemplate.objects.get_or_create(name=mapping_name, document_type=document_type)
            emt.output_format = output_format
            emt.delimiter = delimiter
            emt.mapping_type = mapping_type
            emt.show_header = show_header
            emt.main_loop_segment = main_loop_segment
            emt.nested_loop_segment = nested_loop_segment
            emt.end_loop_segment = end_loop_segment
            emt.save()

            # delete details to recreate it again (it's helpful when user deletes rows)
            emt.get_my_details().delete()

            for item in items:
                map_name = item['map_name']
                map_segment = item['map_segment']
                map_descriptor = item['map_descriptor']
                fw_row = item['fw_row']
                fw_char = item['fw_char']
                fw_length = item['fw_length']
                is_enabled = int(item['map_enable']) == 1

                if map_name and map_segment:
                    emt_det = EDIMappingTemplateDetail(emt=emt,
                                                       map_name=map_name,
                                                       map_segment=map_segment,
                                                       map_descriptor=map_descriptor,
                                                       fw_row=fw_row,
                                                       fw_char=fw_char,
                                                       fw_length=fw_length,
                                                       is_enabled=is_enabled)
                    emt_det.save()

            return ok_json(data={'message': 'EDI Mapping succesfully saved!',
                                 'redirect_url': f"/default/administration/edi_mapping/s3?mapid={emt.id}&fn={file_name}"})

    except Exception as ex:
        return bad_json(message=ex.__str__())
