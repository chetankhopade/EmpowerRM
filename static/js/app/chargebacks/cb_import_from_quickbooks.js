
let modalCbProcessingImportfromQuickbooks = $("#modalCbProcessingImportfromQuickbooks");

let CB_IMPORT_FROM_QUICKBOOKS = {

    name: 'CB_IMPORT_FROM_QUICKBOOKS',

    process: function () {

        let qbFile = $("#filestyle-0");

        if (qbFile.val()){
            let formData = new FormData();
            formData.append('file', qbFile[0].files[0]);
                $.ajax({
                url: `/${DB_NAME}/chargebacks/import_file_from_quickbooks/process`,
                type: "POST",
                data: formData,
                processData: false,
                contentType: false,
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    if (response.result === 'ok'){
                        qbFile.val('');
                        modalCbProcessingImportfromQuickbooks.modal('hide');
                        show_toast_success_message(response.message, 'bottomRight');
                        // stay in the same bucket
                        let elem = divChargebackFilters.find('.card-body.active').parent().parent();
                        CB_VIEW.load_cb_data(elem);
                    }else{
                        show_toast_error_message(response.message, 'bottomRight');
                    }
                },
                complete: function() {
                    // update counters
                    CB_VIEW.load_cbs_counters_data();
                },
                error: function () {
                    show_toast_error_message('Internal Error');
                }
            });
        }else{
            show_toast_warning_message('Select select a file to continue', 'bottomRight')
        }
    },

};
