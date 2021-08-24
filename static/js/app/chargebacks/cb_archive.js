

let CB_ARCHIVE = {

    name: 'CB_ARCHIVE',

    submit: function (elem) {
        let loadingText = "<span class='font-11'><i class='fa fa-circle-o-notch fa-spin'></i> Archiving ...</span>";
        let originalText = elem.html();
        CB_VIEW.get_all_selected_lines();
        if (selected_chargebacks_ids.length > 0) {

            $.ajax({
                type: "POST",
                url: `/${DB_NAME}/chargebacks/archive`,
                data: {
                    'chargebacks_ids': selected_chargebacks_ids
                },
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                    elem.addClass('disabled').html(loadingText);
                },
                success: function (response) {
                    if (response.result === 'ok'){
                        if (response.cbids_not_archived){
                            show_toast_warning_message(response.message, 'topCenter');
                        }else{
                            show_toast_success_message(response.message, 'bottomRight');
                        }
                        // stay in the same bucket
                        let elem = divChargebackFilters.find('.card-body.active').parent().parent();
                        CB_VIEW.load_cb_data(elem);
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
            })
        }else{
            show_toast_warning_message("Select at least 1 Chargeback to continue");
        }
    },

};
