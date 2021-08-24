// vars
let modalGenerate849Results = $("#modalGenerate849Results");
let btnDownloadAllFilesGenerate849 = $("#btnDownloadAllFilesGenerate849");


let CB_GENERATE_849 = {

    name: 'CB_GENERATE_849',

    submit: function (elem) {
        let loadingText = "<span class='font-11'><i class='fa fa-circle-o-notch fa-spin mr-1'></i> Generating 849 ...</span>";
        let originalText = elem.html();
        CB_VIEW.get_all_selected_lines();
        if (selected_chargebacks_ids.length > 0) {
            $.ajax({
                type: "POST",
                url: `/${DB_NAME}/chargebacks/generate_849`,
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
                    let show_all_download_btn = 0;
                    if (response.result === 'ok'){
                        // chargebacks which could not be deleted for some reason
                        let html = '';
                        if (response.invalid_cbs_to_process.length > 0){
                            html += "<div class='row'>" +
                                        "<div class='col-1'>" +
                                            "<i class='empower-color-yellow fas fa-info-circle fa-3x mr-1'></i> " +
                                        "</div>" +
                                        "<div class='col'>" +
                                            "<p class='text-justify ml-1'>" +
                                                "Some chargebacks are missing their Credit Memo information or " +
                                                "have lines with Pending status. Please check the following " +
                                                "Chargebacks were properly Posted to Accounting before " +
                                                "attempting to add them to an 849." +
                                            "</p>" +
                                        "</div>" +
                                    "</div>";

                            html += "<table class='table table-condensed table-striped table-borderless mt-2'>" +
                                        "<thead>" +
                                            "<tr class='font-11'>" +
                                                "<th style='width: 60px'>CBID</th>" +
                                                "<th style='width: 120px'>Number</th>" +
                                                "<th>Reason</th>" +
                                            "</tr>" +
                                        "</thead>" +
                                    "<tbody>";
                                    for (let i=0; i < response.invalid_cbs_to_process.length; i++){
                                        let elem = response.invalid_cbs_to_process[i];
                                        html += "<tr class='font-11'>" +
                                                    "<td style='width: 50px'>"+elem[0]+"</td>" +
                                                    "<td>"+elem[1]+"</td>" +
                                                    "<td>"+elem[2]+"</td>" +
                                                "</tr>";
                                    }
                                    html += "</tbody></table>";

                        }else{
                            html = "<h6 class='text-center _700'>" +
                                        "The following files were generated:" +
                                    "</h6>" +
                                    "<table class='table table-condensed table-striped table-borderless mt-1'>" +
                                        "<thead>" +
                                            "<tr class='font-11'>" +
                                                "<th></th>" +
                                                "<th style='width: 250px'></th>" +
                                                "<th style='width: 100px'></th>" +
                                            "</tr>" +
                                        "</thead>" +
                                        "<tbody>";
                                        for (let i=0; i < response.results.length; i++){
                                            let elem = response.results[i];
                                            html += "<tr class='font-11'>" +
                                                        "<td>"+elem.customer+"</td>" +
                                                        "<td>"+elem.text+"</td>" +
                                                    "<td>";
                                            if (elem.show_download_btn){
                                                // EA-856 - When generating 849s for EDI wholesalers there is an option to Download Manual Files
                                                if (show_all_download_btn !== 1){
                                                    show_all_download_btn = 1
                                                }
                                                html += "<a href='/"+DB_NAME+"/chargebacks/generate_849/"+elem.filename+"/download' class='btnGenerate849ResultsFile tt' title='"+elem.filename+"'>" +
                                                            "<i class='fa fa-download'></i> Download" +
                                                        "</a>";
                                            }
                                        html+= "</td></tr>";
                            }
                            html += "</tbody></table>";

                            // show button to download all files
                            if (show_all_download_btn === 1){
                                btnDownloadAllFilesGenerate849.show();
                            }
                        }

                        // show modal dialog with results generate 849
                        modalGenerate849Results.find('.modal-body').html(html);
                        modalGenerate849Results.fadeIn(500, function(){
                            modalGenerate849Results.modal({'backdrop':'static'}).modal("show");
                        });

                    }else{
                        show_toast_error_message(response.message, 'bottomRight');
                    }
                    // stay in the same bucket
                    let elem = divChargebackFilters.find('.card-body.active').parent().parent();
                    CB_VIEW.load_cb_data(elem);
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
            });
        }else{
            show_toast_warning_message("Select at least 1 Chargeback to continue", 'bottomRight');
        }
    },

    download_849_files: function () {
        $(".btnGenerate849ResultsFile").each(function () {
            window.open($(this).attr('href'), '_blank');
        });
    },

};
