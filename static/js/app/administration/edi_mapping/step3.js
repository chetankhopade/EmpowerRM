// Source Data
let divStep3SourceFileContainer = $("#divStep3SourceFileContainer");
let tdStep3SourceFileName = $("#tdStep3SourceFileName");
let tdStep3SourceDocType = $("#tdStep3SourceDocType");
let btnSourceFileOutputFile = $("#btnSourceFileOutputFile");
let btnSourceFileOutputHtml = $("#btnSourceFileOutputHtml");

// Destination Data
let divStep3DestinationFileContainer = $("#divStep3DestinationFileContainer");
let tdStep3DestinationMappingName = $("#tdStep3DestinationMappingName");
let tdStep3DestinationMappingType = $("#tdStep3DestinationMappingType");
let tdStep3DestinationMappingOutput = $("#tdStep3DestinationMappingOutput");
let tdStep3DestinationMappingDelimiter = $("#tdStep3DestinationMappingDelimiter");
let tdStep3DestinationMappingShowHeader = $("#tdStep3DestinationMappingShowHeader");
let divStep3DestinationButtons = $("#divStep3DestinationButtons");
let btnDestinationFileOutputFile = $("#btnDestinationFileOutputFile");
let btnDestinationFileOutputHtml = $("#btnDestinationFileOutputHtml");
let divStep3DestinationFileViewDownload = $("#divStep3DestinationFileViewDownload");


let EDIMAPPING_STEP3 = {

    name: 'EDIMAPPING_STEP3',

    sourceFileName: FILENAME,
    destinationFileName: '',    // updated in destination data function

    mapID: MAPID,

    // source data (file or html)
    get_source_data: function (output) {

        let html = '';
        $.ajax({
            type: "POST",
            url: "/default/administration/edi_mapping/s3/source_data",
            data: {
                "fn": EDIMAPPING_STEP3.sourceFileName,
                "mapid": EDIMAPPING_STEP3.mapID,
                "output": output,
            },
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
                tdStep3SourceFileName.html('');
                tdStep3SourceDocType.html('');
                divStep3SourceFileContainer.html("<div class='text-center'>" +
                                                            "<img src='/static/images/loading2.gif' width='50' height='50' alt='gifLoader'/>" +
                                                        "</div>");
            },
            success: function (response) {
                tdStep3SourceFileName.html(response.filename);
                tdStep3SourceDocType.html(response.doctype);

                divStep3SourceFileContainer.html('');

                if (output === 'file'){
                    btnSourceFileOutputHtml.removeClass('outputActive');
                    btnSourceFileOutputFile.addClass('outputActive');
                    html += response.segments;  // file content
                }else{
                    btnSourceFileOutputFile.removeClass('outputActive');
                    btnSourceFileOutputHtml.addClass('outputActive');
                    let separator = "<span class='spanSeparator'>"+response.separator+"</span>";

                    // html file data
                    for (let s = 0; s < response.segments.length; s++) {
                        html += "<div class='font-1em'>";
                        let segm = response.segments[s];
                        let segm_id = segm['id'];
                        // segment id
                        html += "<span class='spanSegmentId'>"+segm_id+"</span>";
                        html += separator;

                        // segment elements
                        let my_elements = segm['elements'];
                        let descriptor = '';
                        if (response.descriptors.includes(my_elements[0]['value'])){
                            descriptor = my_elements[0]['value'];
                        }
                        for (let e = 0; e < my_elements.length; e++) {
                            let elem = my_elements[e];
                            let value = elem['value'];
                            let elem_id = elem['id'];
                            if (descriptor){
                                elem_id = elem_id + ":" + descriptor;
                            }
                            html += "<a class='btnSourceElement' eid='"+elem_id+"' title='"+elem_id+"'>"+value+"</a>";
                            if (e < my_elements.length - 1){
                                html += separator;
                            }
                        }
                        html += "</div>";
                    }

                }

            },
            complete: function () {
                // add the html to container
                divStep3SourceFileContainer.html(html);
                if (output === 'html'){
                    // highlight common elems
                    $(".btnSourceElement").click(function () {
                        let eid = $(this).attr('eid');
                        let randomBGColor = EDIMAPPING_STEP3.getRandomBackgroundColor();
                        if ($(this).hasClass('focused')){
                            $(".btnSourceElement[eid='"+eid+"']").removeClass('focused').css('backgroundColor', 'transparent');
                            $(".btnElementHighligther[eid='"+eid+"']").removeClass('focused').css('backgroundColor', 'transparent');
                        }else{
                            $(".btnSourceElement[eid='"+eid+"']").addClass('focused').css('backgroundColor', randomBGColor);
                            $(".btnElementHighligther[eid='"+eid+"']").addClass('focused').css('backgroundColor', randomBGColor);
                        }
                    });
                }
            },
            error: function () {
                divStep3SourceFileContainer.html('Internal Error');
                show_toast_error_message('Internal Error');
            }

        });

    },

    // destination data
    get_destination_data: function (output) {

        let html = '';
        $.ajax({
            type: "POST",
            url: "/default/administration/edi_mapping/s3/destination_data",
            data: {
                "fn": EDIMAPPING_STEP3.sourceFileName,
                "mapid": EDIMAPPING_STEP3.mapID,
                "output": output,
            },
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
                divStep3DestinationButtons.hide();
                tdStep3DestinationMappingName.html('');
                tdStep3DestinationMappingOutput.html('');
                tdStep3DestinationMappingType.html('');
                tdStep3DestinationMappingDelimiter.html('');
                tdStep3DestinationMappingShowHeader.html('');
                divStep3DestinationFileViewDownload.hide();

                divStep3DestinationFileContainer.html("<div class='text-center'>" +
                                                                "<img src='/static/images/loading2.gif' width='50' height='50' alt='gifLoader'/>" +
                                                            "</div>");
            },
            success: function (response) {
                let mapping_obj = response.mapping_obj;
                let delimiter = mapping_obj.delimiter;
                let rows_matrix = response.rows_matrix;

                // metadata
                tdStep3DestinationMappingName.html(mapping_obj.name);
                tdStep3DestinationMappingOutput.html(mapping_obj.output_format);
                tdStep3DestinationMappingDelimiter.html(mapping_obj.delimiter);
                if (mapping_obj.mapping_type === EDI_MAPPING_TYPE_DELIMITED){
                    tdStep3DestinationMappingType.html('Delimited');
                }
                if (mapping_obj.mapping_type === EDI_MAPPING_TYPE_FIXED_WIDTH){
                    tdStep3DestinationMappingType.html('Fixed Width');
                }
                if (mapping_obj.show_header){
                    tdStep3DestinationMappingShowHeader.html("<i class='fa fa-check'></i>");
                }

                // File Content
                divStep3DestinationFileContainer.html('');

                if (output === 'file'){
                    btnDestinationFileOutputHtml.removeClass('outputActive');
                    btnDestinationFileOutputFile.addClass('outputActive');
                    html += response.content;  // file content
                }else{
                    btnDestinationFileOutputFile.removeClass('outputActive');
                    btnDestinationFileOutputHtml.addClass('outputActive');

                    let separator = "<span class='spanDelimiter'>"+delimiter+"</span>";

                    for (let i = 0; i < rows_matrix.length; i++) {
                        let row = rows_matrix[i];
                        html += "<div class='font-11em'>";

                        for (let r = 0; r < row.length; r++) {
                             let elem = row[r];
                             let value = elem['value'];
                             let elem_id = elem['seg_name'];
                             let segm_descriptor = elem['segm_descriptor'];
                             if (segm_descriptor){
                                 elem_id = elem_id + ":" + segm_descriptor;
                             }
                             html += "<a class='btnElementHighligther' eid='"+elem_id+"' title='"+elem_id+"'>"+value+"</a>";
                             if (r < row.length - 1){
                                html += separator;
                            }
                        }
                        html += "</div>";
                    }
                }

                // update destinationFileName to be used in approve action and show buttons to download and view result file
                EDIMAPPING_STEP3.destinationFileName = response.result_filename;
                divStep3DestinationFileViewDownload.html("<a class='btn btn-default btn-xs' href='/default/administration/edi_mapping/s3/destination_data/"+EDIMAPPING_STEP3.destinationFileName+"/view' target='_blank'>" +
                                                                    "<i class='fa fa-file-text'></i> View File" +
                                                               "</a>" +
                                                                "<a class='btn btn-default btn-xs ml-2' href='/default/administration/edi_mapping/s3/destination_data/"+EDIMAPPING_STEP3.destinationFileName+"/download'>" +
                                                                    "<i class='fa fa-download'></i> Download File" +
                                                               "</a>");
                divStep3DestinationFileViewDownload.show();
            },
            complete: function () {
                divStep3DestinationFileContainer.html(html);
                divStep3DestinationButtons.fadeIn(300);

                // highlight common elems
                $(".btnElementHighligther").click(function () {
                    let eid = $(this).attr('eid');
                    let randomBGColor = EDIMAPPING_STEP3.getRandomBackgroundColor();
                    if ($(this).hasClass('focused')){
                        $(".btnSourceElement[eid='"+eid+"']").removeClass('focused').css('backgroundColor', 'transparent');
                        $(".btnElementHighligther[eid='"+eid+"']").removeClass('focused').css('backgroundColor', 'transparent');
                    }else{
                        $(".btnSourceElement[eid='"+eid+"']").addClass('focused').css('backgroundColor', randomBGColor);
                        $(".btnElementHighligther[eid='"+eid+"']").addClass('focused').css('backgroundColor', randomBGColor);
                    }
                });
            },
            error: function () {
                divStep3DestinationFileContainer.html('').hide();
                divStep3DestinationFileContainer.html('Internal Error');
                show_toast_error_message('Internal Error');
            }
        });

    },

    // random bg color
    getRandomBackgroundColor: function (){
        // 16777215 (decimal) == ffffff in hexidecimal
        let newColor = '#'+Math.floor(Math.random()*16777215).toString(16);
        // Convert hex to RGB:
        let rgbColor = newColor.replace('#','');
        let r = parseInt(rgbColor.substring(0,2), 16);
        let g = parseInt(rgbColor.substring(2,4), 16);
        let b = parseInt(rgbColor.substring(4,6), 16);
        return 'rgba(' + r + ',' + g + ',' + b + ')';
    },

    // approve mapping
    approve_mapping: function (elem) {

        let loadingText = "<span class='font-11'><i class='fa fa-circle-o-notch fa-spin'></i> Approving... </span>";
        let originalText = elem.html();

        let html = '';
        $.ajax({
            type: "POST",
            url: "/default/administration/edi_mapping/s3/"+EDIMAPPING_STEP3.mapID+"/update_status/"+EDI_MAPPING_STATUS_COMPLETE,
            data: {
                'sourceFileName': EDIMAPPING_STEP3.sourceFileName,
                'destinationFileName': EDIMAPPING_STEP3.destinationFileName,
            },
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
                elem.addClass('disabled').html(loadingText);
            },
            success: function (response) {
                if (response.result === 'ok'){
                    // show success message
                    show_toast_success_message(response.message, 'topRight');
                    // app loader
                    APP.show_app_loader();
                    // redirect
                    setTimeout(function () {
                        location.href = response.redirect_url;
                    }, 300)
                }
            },
            complete: function () {
                elem.removeClass('disabled').html(originalText);
            },
            error: function () {
                elem.removeClass('disabled').html(originalText);
                show_toast_error_message('Internal Error');
            }

        });

    },
};
