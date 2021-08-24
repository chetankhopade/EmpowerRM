// vars
let tbodyEDIMappingDestinationFormat = $("#tbodyEDIMappingDestinationFormat");
let selectExistingEDIMapping = $("#selectExistingEDIMapping");
let checkboxEDIMappingShowHeaderRow = $("#checkboxEDIMappingShowHeaderRow");
let spanEDIMappingDocumentType = $("#spanEDIMappingDocumentType");
let inputEDIMappingName = $("#inputEDIMappingName");
let selectEDIMappingOutputFormat = $("#selectEDIMappingOutputFormat");
let radioEDIMappingDelimited = $("#radioEDIMappingDelimited");
let radioEDIMappingFixedWidth = $("#radioEDIMappingFixedWidth");
let inputEDIMappingDelimiter = $("#inputEDIMappingDelimiter");
let inputMainLoopSegment = $("#inputMainLoopSegment");
let inputNestedLoopSegment = $("#inputNestedLoopSegment");
let inputEndLoopSegment = $("#inputEndLoopSegment");


let EDIMAPPING_STEP2 = {

    name: 'EDIMAPPING_STEP2',

    counter: 1,

    fileName: FILENAME,

    // click in segment id -> find and process loops
    assign_loop_term: function (term, sid){
        let tdSegmentID = $(".tdSegmentsIDs"+sid);
        let spanLoopTerm = $(".spanLoopTerm"+sid);
        // elem.html(term);
        if (term === 'ML'){
            if (tdSegmentID.hasClass('alert-success')){
                tdSegmentID.removeClass('alert-success');
                spanLoopTerm.html('');
                inputMainLoopSegment.val('');
            }else{
                spanLoopTerm.html(term);
                inputMainLoopSegment.val(sid);
                tdSegmentID.addClass('alert-success');
            }
        }else if (term === 'NL'){
            if (tdSegmentID.hasClass('alert-primary')){
                tdSegmentID.removeClass('alert-primary');
                spanLoopTerm.html('');
                inputNestedLoopSegment.val('');
            }else{
                spanLoopTerm.html(term);
                inputNestedLoopSegment.val(sid);
                tdSegmentID.addClass('alert-primary');
            }
        }else{
            if (tdSegmentID.hasClass('alert-danger')){
                tdSegmentID.removeClass('alert-danger');
                spanLoopTerm.html('');
                inputEndLoopSegment.val('');
            }else{
                spanLoopTerm.html(term);
                inputEndLoopSegment.val(sid);
                tdSegmentID.addClass('alert-danger');
            }
        }
    },

    // delete rows -> destination format
    removeRow: function (elem) {
        if (EDIMAPPING_STEP2.counter <= 1){
            show_toast_warning_message('The mapper needs at least 1 row', 'bottomRight')
        }else{
            elem.parent().parent().remove();
            EDIMAPPING_STEP2.counter -= 1;
        }
    },

    // add rows -> destination format
    addRow: function (detail) {

        // fields
        let map_name = '';
        let map_segment = '';
        let map_descriptor = '';
        let fw_row = '';
        let fw_char = '';
        let fw_length = '';
        let checked = '';

        if (!detail){
            // remove first row added by DT if is new map
            tableEDIMappingDestinationFormat.find("tr.odd").remove();
        }else{
            map_name = detail.map_name;
            map_segment = detail.map_segment;
            map_descriptor = detail.map_descriptor;
            fw_row = detail.fw_row;
            fw_char = detail.fw_char;
            fw_length = detail.fw_length;
            if (detail.is_enabled){
                checked = 'checked';
            }
        }

        // add row dynamically
        tbodyEDIMappingDestinationFormat.append('<tr class="trDestinationFormat">' +
            '<td class="text-center">' + EDIMAPPING_STEP2.counter + '.</td>' +
            '<td><input type="text" class="form-control height-22 inputMapName" value="'+map_name+'"/></td>' +
            '<td class="text-center"><input type="text" class="form-control height-22 inputMapSegment" value="'+map_segment+'" onclick="EDIMAPPING_STEP2.set_focus($(this))" /></td>' +
            '<td class="text-center"><input type="text" class="form-control height-22 inputMapDescriptor" value="'+map_descriptor+'" /></td>' +
            '<td class="text-center"><input type="text" class="form-control height-22 inputFixedWidthRow" value="'+fw_row+'" /></td>' +
            '<td class="text-center"><input type="text" class="form-control height-22 inputFixedWidthCharStart" value="'+fw_char+'" /></td>' +
            '<td class="text-center"><input type="text" class="form-control height-22 inputFixedWidthLength" value="'+fw_length+'" /></td>' +
            '<td class="text-center"><label class="md-check"><input type="checkbox" class="checkboxMapEnable" checked="'+checked+'" /><i class="primary"></i></label></td>' +
            '<td class="text-center"><a onclick="EDIMAPPING_STEP2.removeRow($(this));"><i class="fa fa-times text-danger tt" title="Remove"></i></a></td>' +
            '</tr>');

        EDIMAPPING_STEP2.counter ++;

        // enable or disable fixed width columns
        EDIMAPPING_STEP2.enable_disable_fixed_width_columns();

        // remove focused elements
        let lastRow = tableEDIMappingDestinationFormat.find("tr:last").find('.inputMapSegment');
        EDIMAPPING_STEP2.set_focus(lastRow);

    },

    // select EDI Mapping
    select_existing_edi_mapping: function () {
        let map_id = selectExistingEDIMapping.val();

        $.ajax({
            type: "POST",
            url: "/default/administration/edi_mapping/s2/mapping_details",
            data: {
                "mapid": map_id,
            },
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
                // disabled all fields until get response
                inputEDIMappingName.prop('disabled', true).val('');
                selectEDIMappingOutputFormat.prop('disabled', true).val('');
                inputEDIMappingDelimiter.prop('disabled', true).val('');
                checkboxEDIMappingShowHeaderRow.prop('checked', false);
                radioEDIMappingDelimited.prop('checked', false);
                radioEDIMappingFixedWidth.prop('checked', false);

                tbodyEDIMappingDestinationFormat.html(
                    "<tr>" +
                            "<td><td><td>" +
                            "<td><img src='/static/images/loading2.gif' width='50' height='50' alt='gifLoader'/></td>" +
                            "<td><td><td>" +
                          "</tr>");
            },
            success: function (response) {
                tbodyEDIMappingDestinationFormat.html('');

                let mapping_obj = response.mapping_obj;
                let mapping_details = response.mapping_details;

                // fill metadata fields based on mapping_obj
                if (mapping_obj){
                    // hidden inputs for loops segments and set css styling to left side
                    let ML_sid = mapping_obj.main_loop_segment;
                    inputMainLoopSegment.val(ML_sid);
                    $(".spanLoopTerm"+ML_sid).html('ML');
                    $(".tdSegmentsIDs"+ML_sid).addClass('alert-success');

                    let NL_sid = mapping_obj.nested_loop_segment;
                    inputNestedLoopSegment.val(NL_sid);
                    $(".spanLoopTerm"+NL_sid).html('NL');
                    $(".tdSegmentsIDs"+NL_sid).addClass('alert-primary');

                    let EL_sid = mapping_obj.end_loop_segment;
                    inputEndLoopSegment.val(EL_sid);
                    $(".spanLoopTerm"+EL_sid).html('EL');
                    $(".tdSegmentsIDs"+EL_sid).addClass('alert-danger');

                    // inputs and select
                    inputEDIMappingName.val(mapping_obj.name);
                    selectEDIMappingOutputFormat.val(mapping_obj.output_format);
                    inputEDIMappingDelimiter.val(mapping_obj.delimiter);
                    // checkbox show_header
                    if (mapping_obj.show_header){
                        checkboxEDIMappingShowHeaderRow.prop('checked', true)
                    }
                    // radios mapping_type
                    if (mapping_obj.mapping_type === EDI_MAPPING_TYPE_DELIMITED){
                        radioEDIMappingDelimited.prop('checked', true);
                    }
                    if (mapping_obj.mapping_type === EDI_MAPPING_TYPE_FIXED_WIDTH){
                        radioEDIMappingFixedWidth.prop('checked', true);
                    }

                    // initialize counter
                    EDIMAPPING_STEP2.counter = 1;

                    // populate details fields based on mapping_details
                    for (let i = 0; i < mapping_details.length; i++) {
                        let detail = mapping_details[i];
                        EDIMAPPING_STEP2.addRow(detail);
                    }
                }else{
                    EDIMAPPING_STEP2.addRow(null);
                }
            },
            complete: function () {
                // enable all fields after complete ajax
                inputEDIMappingName.prop('disabled', false);
                selectEDIMappingOutputFormat.prop('disabled', false);
                inputEDIMappingDelimiter.prop('disabled', false);
            },
            error: function () {
                tbodyEDIMappingDestinationFormat.html('Internal Error');
                show_toast_error_message('Internal Error');
            }
        });

    },

    // change file type -> update checkboxes and inputs
    change_mapping_type: function () {
        let val = selectEDIMappingOutputFormat.val();

        //  If option is text, show the Delimited/Fixed Width Radio buttons and Delimiter Field (Ticket 697)
        if (val === EDI_MAPPING_OUTPUT_FORMAT_TEXT){
            // radios
            radioEDIMappingDelimited.attr('disabled', false).prop('checked', true).parent().find('span').removeClass('strikeout');
            radioEDIMappingFixedWidth.attr('disabled', false).prop("checked", false).parent().find('span').removeClass('strikeout');
            // input and label
            inputEDIMappingDelimiter.attr('disabled', false);
            $('label[for="inputEDIMappingDelimiter"]').removeClass('strikeout');

            // If Option csv, show Delimiter Field
        } else if (val === EDI_MAPPING_OUTPUT_FORMAT_CSV) {
            radioEDIMappingDelimited.attr('disabled', true).prop("checked", false).parent().find('span').addClass('strikeout');
            radioEDIMappingFixedWidth.attr('disabled', true).prop("checked", false).parent().find('span').addClass('strikeout');
            // input and label
            inputEDIMappingDelimiter.attr('disabled', false);
            $('label[for="inputEDIMappingDelimiter"]').removeClass('strikeout');

            // If Option is xml, disabled all fields
        } else {
            // radios
            radioEDIMappingDelimited.attr('disabled', true).prop("checked", false).parent().find('span').addClass('strikeout');
            radioEDIMappingFixedWidth.attr('disabled', true).prop("checked", false).parent().find('span').addClass('strikeout');
            // input and label
            inputEDIMappingDelimiter.attr('disabled', true).val('');
            $('label[for="inputEDIMappingDelimiter"]').addClass('strikeout');
        }

        EDIMAPPING_STEP2.enable_disable_fixed_width_columns();

    },

    enable_disable_fixed_width_columns: function () {

        $(".trDestinationFormat").each(function () {
            let fwRows = $(this).find('.inputFixedWidthRow');
            let fwCharStart = $(this).find('.inputFixedWidthCharStart');
            let fwLength = $(this).find('.inputFixedWidthLength');
            if (radioEDIMappingFixedWidth.is(':checked')){
                fwRows.attr('disabled', false);
                fwCharStart.attr('disabled', false);
                fwLength.attr('disabled', false);
            }else{
                fwRows.val('').attr('disabled', true);
                fwCharStart.val('').attr('disabled', true);
                fwLength.val('').attr('disabled', true);
            }
        });
    },

    // set focus in destination input segment
    set_focus: function (elem) {
        $(".inputMapSegment").each(function () {
            $(this).removeClass('focused2');
        });
        elem.addClass('focused2').focus();
    },

    add_segment_in_current_row: function (elem) {
        let focusedElement = tableEDIMappingDestinationFormat.find('.focused2');
        if (!focusedElement){
            focusedElement = tableEDIMappingDestinationFormat.find("tr:last").find('.inputMapSegment');
        }
        focusedElement.val(elem.text());
    },

    save_mapping_template: function (elem) {

        if (!inputEDIMappingName.val()) {
            inputEDIMappingName.addClass('border-red');
            show_toast_error_message('Mapping Name is required', 'bottomRight');
            return false;
        }else{
            inputEDIMappingName.removeClass('border-red');
        }

        if (tbodyEDIMappingDestinationFormat.find('tr').length <= 1){
            show_toast_error_message('Mapping needs more than 1 row', 'bottomRight');
            return false;
        }

        // loops segments and validations of loops to have end loop segment
        let main_loop_segment = inputMainLoopSegment.val();
        let nested_loop_segment = inputNestedLoopSegment.val();
        let end_loop_segment = inputEndLoopSegment.val();

        if (!end_loop_segment){
            if (main_loop_segment){
                show_toast_error_message('A Main Loop (ML) is defined without an End Loop (EL)', 'bottomLeft');
                return false;
            }
            if (nested_loop_segment){
                show_toast_error_message('A Nested Loop (NL) is defined without an End Loop (EL)', 'bottomLeft');
                return false;
            }
        }

        // Send to the server (if all data is ok)
        let loadingText = '<i class="fa fa-circle-o-notch fa-spin"/> Saving ...';
        let originalText = elem.html();

        let items = []; // rows with configuration (segment - map name)
        $(".trDestinationFormat").each(function () {
            let mapName = $(this).find('.inputMapName').val();
            let mapSegment = $(this).find('.inputMapSegment').val();
            let mapDescriptor = $(this).find('.inputMapDescriptor').val();
            let fwRow = $(this).find('.inputFixedWidthRow').val();
            let fwCharStart = $(this).find('.inputFixedWidthCharStart').val();
            let fwLength = $(this).find('.inputFixedWidthLength').val();
            let map_enable = 1 ? $(this).find('.checkboxMapEnable').is(':checked') : 0;

            if (mapName && mapSegment){
                items.push({
                    "map_name": mapName,
                    "map_segment": mapSegment,
                    "map_descriptor": mapDescriptor,
                    "fw_row": fwRow,
                    "fw_char": fwCharStart,
                    "fw_length": fwLength,
                    "map_enable": map_enable,
                });
            }
        });

        // radios
        let mapping_type = 0;
        if (radioEDIMappingDelimited.is(':checked')){
            mapping_type = EDI_MAPPING_TYPE_DELIMITED
        }
        if (radioEDIMappingFixedWidth.is(':checked')){
            mapping_type = EDI_MAPPING_TYPE_FIXED_WIDTH;
        }

        // checkbox show header
        let show_header = 0;
        if (checkboxEDIMappingShowHeaderRow.is(':checked')){
            show_header = 1;
        }

        $.ajax({
            type: "POST",
            url: "/default/administration/edi_mapping/s2/save_template",
            data: {
                "file_name": EDIMAPPING_STEP2.fileName,
                "mapping_name": inputEDIMappingName.val(),
                "document_type": spanEDIMappingDocumentType.html(),
                "output_format": selectEDIMappingOutputFormat.val(),
                "delimiter": inputEDIMappingDelimiter.val(),
                "mapping_type": mapping_type,
                "show_header": show_header,
                "main_loop_segment": main_loop_segment,
                "nested_loop_segment": nested_loop_segment,
                "end_loop_segment": end_loop_segment,
                "items": JSON.stringify(items)
            },
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
                elem.addClass('disabled').html(loadingText);
            },
            success: function (response) {
                if (response.result === 'ok'){
                    show_toast_success_message(response.message, 'topRight');
                    APP.show_app_loader();
                    setTimeout(function () {
                        location.href = response.redirect_url;
                    }, 500);

                }else{
                    show_toast_error_message(response.message);
                }
            },
            complete: function() {
                elem.removeClass('disabled').html(originalText);
            },
            error: function () {
                elem.removeClass('disabled').html(originalText);
                show_toast_error_message('Internal Error');
            }
        });
    },

};





