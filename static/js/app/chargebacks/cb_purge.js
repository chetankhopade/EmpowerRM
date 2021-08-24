// vars
let inputPurgeCB = $("#inputPurgeCB");
let tbodyCbPurge = $("#tbodyCbPurge");
let helpTextPurgeCB = $("#helpTextPurgeCB");
let modalCbPurge = $("#modalCbPurge");
let modalCbPurgeResults = $("#modalCbPurgeResults");
let inputSelectedChargebacksIds = $("#inputSelectedChargebacksIds");


let CB_PURGE = {

    name: 'CB_PURGE',

    show_modal: function () {
        inputPurgeCB.val('');
        helpTextPurgeCB.addClass('hide');
        CB_VIEW.get_all_selected_lines();
        if (selected_chargebacks_ids.length > 0){
            inputSelectedChargebacksIds.val(selected_chargebacks_ids);
            let cb_list = selected_chargebacks_ids.split('|');
            let html = "";
            for (let i=0; i < cb_list.length; i++){
                let cid = cb_list[i];
                let tr_elem = $("#"+cid);
                let td_child = tr_elem.find("td:first");
                let cbid = td_child.find('span').text();
                let cbnumber = td_child.find('span').attr('cbno');
                html += "<tr class='font-11'>" +
                            "<td style='width: 50px'>"+cbid+"</td>" +
                            "<td>"+cbnumber+"</td>" +
                        "</tr>";
            }
            tbodyCbPurge.html(html);

            // show modal with animation
            modalCbPurge.modal({'backdrop':'static'}).modal("show");

        }else{
            show_toast_warning_message("Select at least 1 Chargeback to continue", 'bottomRight');
        }

    },

    purge: function (elem) {
        if (!inputPurgeCB.val()){
            inputPurgeCB.addClass('border-coral');

        } else if (inputPurgeCB.val().toUpperCase() !== 'DELETE') {
            helpTextPurgeCB.removeClass('hide').html('The keyword is not <b>DELETE</b>');

        }else{

            let loadingText = "<span class='font-11'><i class='fa fa-circle-o-notch fa-spin'></i> Purging... </span>";
            let originalText = elem.html();

            if (inputSelectedChargebacksIds.val()) {
                $.ajax({
                    type: "POST",
                    url: `/${DB_NAME}/chargebacks/purge`,
                    data: {
                        'chargebacks_ids': inputSelectedChargebacksIds.val()
                    },
                    beforeSend: function(xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                        }
                        elem.addClass('disabled').html(loadingText);
                    },
                    success: function (response) {
                        if (response.result === 'ok'){
                            // hide modal
                            modalCbPurge.fadeOut(300, function(){
                                modalCbPurge.modal('hide');
                            });
                            // chargebacks which could not be deleted for some reason
                            let html = '';
                            if (response.chargebacks_not_deleted.length > 0){
                                html += "<h6 class='_700'>" +
                                            "<i class='empower-color-blue fas fa-info-circle fa-3x mr-1'></i> " +
                                            "<span style='margin-top: -10px'>The following Chargebacks could not be purged</span>" +
                                        "</h6>";

                                html += "<table class='table table-condensed table-striped table-borderless mt-1'>" +
                                            "<thead>" +
                                                "<tr class='font-11'>" +
                                                    "<th style='width: 50px'>CBID</th>" +
                                                    "<th style='width: 100px'>Number</th>" +
                                                    "<th>Reason</th>" +
                                                "</tr>" +
                                            "</thead>" +
                                            "<tbody>";
                                            for (let i=0; i < response.chargebacks_not_deleted.length; i++){
                                                let cb_obj = response.chargebacks_not_deleted[i];
                                                html += "<tr class='font-11'>" +
                                                            "<td style='width: 50px'>"+cb_obj.cbid+"</td>" +
                                                            "<td>"+cb_obj.number+"</td>" +
                                                            "<td>"+cb_obj.reason+"</td>" +
                                                        "</tr>";
                                            }
                                            html += "</tbody></table>";

                            }else{
                                html = "<h6 class='text-center _700'>" +
                                            "All Chargebacks have been sucessfully purged!" +
                                        "</h6>";
                            }

                            // show modal dialog with results purged
                            modalCbPurgeResults.find('.modal-body').html(html);
                            modalCbPurgeResults.fadeIn(500, function(){
                                modalCbPurgeResults.modal({'backdrop':'static'}).modal("show");
                            });

                            // stay in the same bucket
                            let elem = divChargebackFilters.find('.card-body.active').parent().parent();
                            CB_VIEW.load_cb_data(elem);

                        }else{
                            show_toast_error_message(response.message, 'bottomRight');
                        }
                    },
                    complete: function() {
                        elem.removeClass('disabled').html(originalText);
                        // update counters
                        CB_VIEW.load_cbs_counters_data();
                    },
                    error: function () {
                        elem.removeClass('disabled').html(originalText);
                        show_toast_error_message('Internal Error', 'bottomRight');
                    }
                })
            }else {
                show_toast_warning_message("Select at least 1 Chargeback to continue", 'bottomRight');
            }
        }
    },

};
