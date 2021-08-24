// vars
let modalImport844Files = $("#modalImport844Files");


// Dropzone for Import 844 files
Dropzone.options.formImport844FilesDropZone = {
    paramName: "file",  // The name that will be used to transfer the file
    maxFilesize: 2,         // MB
    acceptedFiles: '.txt',
    uploadMultiple: true,
    parallelUploads: 20,
    maxFiles: 20,
    init: function() {
        this.on("complete", function(response) {
            CB_IMPORT_844.get_844_files_html();
            this.removeAllFiles();
        });
    }
};


let CB_IMPORT_844 = {

    name: 'CB_IMPORT_844',

    // Function get all 844 files from client folder
    get_844_files_html: function () {
        $('#844_list_container').empty();
        $.ajax({
            url: `/${DB_NAME}/chargebacks/files/list`,
            data: {},
            type: "GET",
            dataType: "html",
            processData: false,
            contentType: false,
            success: function (response) {
                $('#844_list_container').html(response);
                $('#import_844').show();
                modalImport844Files.modal({'backdrop':'static'}).modal("show");
            },
            error: function (response) {
                show_toast_error_message(response.message);
            }
        });
    },

    delete_844_file: function (elem, file) {

        $.ajax({
            type: "POST",
            url: `/${DB_NAME}/chargebacks/files/delete`,
            data: {
                'file': file
            },
            success: function (response) {
                if (response.result === 'ok'){
                    show_toast_success_message(response.message, 'bottomRight');
                    CB_IMPORT_844.get_844_files_html();
                }else{
                    show_toast_error_message(response.message);
                }
            },
            complete: function() {
                elem.removeClass('disabled').html(originalText);
                // update counters
                CB_VIEW.load_cbs_counters_data();
            },
            error: function () {
                elem.removeClass('disabled').html(originalText);
                show_toast_error_message('Internal Error');
            }
        });
    },

    import_844_files: function (elem) {
        let loadingText = '<i class="fa fa-circle-o-notch fa-spin"></i> Processing ...';
        let originalText = elem.html();

        let selected_844_files = '';
        $(".checkbox_844Files").each(function () {
            if ($(this).is(':checked')){
                selected_844_files += $(this).attr('value') + '|';
            }
        });

        if (selected_844_files.length > 0){
            selected_844_files = selected_844_files.substring(0, selected_844_files.length-1);

            $.ajax({
                type: "POST",
                url: `/${DB_NAME}/chargebacks/import_844_files`,
                data: {
                    '844_files': selected_844_files
                },
                beforeSend: function(xhr, settings) {
                    elem.addClass('disabled').html(loadingText);
                    /*
                        EA-1429-Import Microservice
                        This will send call to api so we need to close the dialog box
                    */
                    show_toast_success_message("These file(s) will be processed and you can see chargebacks here as soon as file gets processed", 'bottomRight');
                    modalImport844Files.modal('hide');
                },
                success: function (response) {
                    if (response.result === 'ok'){
                        // hide modal
                        modalImport844Files.modal('hide');
                        // show success message
                        show_toast_success_message(response.message, 'bottomRight');
                        // stay in the same bucket
                        let elem = divChargebackFilters.find('.card-body.active').parent().parent();
                        CB_VIEW.load_cb_data(elem);
                    }else{
                        // EA-1604 Chargeback Module : Invalid chargebacks are not displaying under 'Invalid Chargebacks' bucket.
                        if(response.extradata.invalid_files.length >0 ){
                            $("#action_col").text("Status")
                            for (i = 0; i < response.extradata.invalid_files.length; i++) {
                                    x = response.extradata.invalid_files[i]
                                    $("#file_"+x).addClass("ct-active-red")
                                    $("#del_"+x).html("")
                                    $("#del_"+x).text("Removed")
                            }
                        }
                        if(response.extradata.valid_files.length > 0){
                            $("#action_col").text("Status")
                            for (j = 0; j < response.extradata.valid_files.length; j++) {
                                    y = response.extradata.valid_files[j]
                                    $("#file_"+y).addClass("ct-active-green")
                                    $("#del_"+y).html("")
                                    $("#del_"+y).text("Imported")
                            }
                        }
                        $('#import_844').hide();
                        // EA-1604 code end here
                        show_toast_error_message(response.message);
                    }
                },
                complete: function() {
                    elem.removeClass('disabled').html(originalText);
                    // update counters
                    CB_VIEW.load_cbs_counters_data();
                },
                error: function () {
                    elem.removeClass('disabled').html(originalText);
                    show_toast_error_message('Internal Error');
                }
            })
        }else {
            show_toast_error_message("Select at least one file to be imported")
        }
    },

};
