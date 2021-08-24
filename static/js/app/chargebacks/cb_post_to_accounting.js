// vars
let modalCbProcessingPostToAccounting = $("#modalCbProcessingPostToAccounting");
let modalCbProcessingErrorPostToAccounting = $("#modalCbProcessingErrorPostToAccounting");
let modalCbProcessingPostToAccountingAcumaticaAndDs365Integration = $("#modalCbProcessingPostToAccountingAcumaticaAndDs365Integration");
let tableProcessingPostToAccountingAcumaticaAndDs365Error = $("#tableProcessingPostToAccountingAcumaticaAndDs365Error");
let textPostToAccountingAcumaticaAndDs365 = $("#textPostToAccountingAcumaticaAndDs365");
let divProcessingPostToAccountingAcumaticaAndDs365ProgressBar = $("#divProcessingPostToAccountingAcumaticaAndDs365ProgressBar");
let btnCloseModalPostToAccountingAcumaticaAndDs365Integration = $("#btnCloseModalPostToAccountingAcumaticaAndDs365Integration");

let divPostDate = $("#divPostDate");
let divImportFromQB = $("#divImportFromQB");
let inputPostDate = $("#inputPostDate");


let CB_POST_TO_ACCOUNTING = {

    name: 'CB_POST_TO_ACCOUNTING',

    submit: function (elem) {

        if (!inputPostDate.val()) {
            show_toast_error_message('Please enter a post date');
            return false;
        }
        CB_VIEW.get_all_selected_lines();
        let selected_cbs_ids = selected_chargebacks_ids;
        let post_date = inputPostDate.val();

        if (selected_cbs_ids.length > 0) {

            let loadingText = "<span class='font-11'><i class='fa fa-circle-o-notch fa-spin'></i> Posting...</span>";
            let originalText = elem.html();

            // Acumatica or DS365 accounting integration
            if (acc_handler === 'acumatica'){
                modalCbProcessingPostToAccountingAcumaticaAndDs365Integration.modal('show');

                // connecting //
                $.ajax({
                    url: `/${DB_NAME}/chargebacks/post_to_accounting/acumatica/connection`,
                    data: {},
                    type: 'POST',
                    dataType: 'json',
                    beforeSend: function (){
                        textPostToAccountingAcumaticaAndDs365.html('Connecting ...');
                    },
                    success  : function () {
                        // validating //
                        $.ajax({
                            url: `/${DB_NAME}/chargebacks/post_to_accounting/acumatica/validations`,
                            data: {
                                'chargebacks_ids': selected_cbs_ids,
                            },
                            type: 'POST',
                            dataType: 'json',
                            beforeSend: function (){
                                textPostToAccountingAcumaticaAndDs365.html('Validating (items & customers) ...');
                            },
                            success  : function (response) {

                                if (response.extradata){
                                    let cbs_with_wrong_customers = response.extradata.cbs_with_wrong_customers;
                                    let cbs_with_wrong_items = response.extradata.cbs_with_wrong_items;
                                    let cbs_with_existing_transactions = response.extradata.cbs_with_existing_transactions;

                                    let html = '';
                                    for (let i=0; i<cbs_with_wrong_customers.length; i++){
                                        let elem = cbs_with_wrong_customers[i];
                                        html += '<tr>' +
                                                    '<td>'+elem.cbid+'</td>' +
                                                    '<td>'+elem.customer_accno+'</td>' +
                                                    '<td>'+elem.error+'</td>' +
                                                 '</tr>';
                                    }

                                    for (let i=0; i<cbs_with_wrong_items.length; i++){
                                        let elem = cbs_with_wrong_items[i];
                                        html += '<tr>' +
                                                    '<td>'+elem.cbid+'</td>' +
                                                    '<td>'+elem.item_accno+'</td>' +
                                                    '<td>'+elem.error+'</td>' +
                                                 '</tr>';
                                    }

                                    for (let i=0; i<cbs_with_existing_transactions.length; i++){
                                        let elem = cbs_with_existing_transactions[i];
                                        html += '<tr>' +
                                                    '<td>'+elem.cbid+'</td>' +
                                                    '<td>'+elem.transaction_no+'</td>' +
                                                    '<td>'+elem.error+'</td>' +
                                                 '</tr>';
                                    }

                                    // handle errors
                                    divProcessingPostToAccountingAcumaticaAndDs365ProgressBar.removeClass('bg-success').addClass('bg-danger');
                                    tableProcessingPostToAccountingAcumaticaAndDs365Error.find('tbody').html(html);
                                    btnCloseModalPostToAccountingAcumaticaAndDs365Integration.show();
                                    tableProcessingPostToAccountingAcumaticaAndDs365Error.show()

                                }else{

                                    // sending //
                                    $.ajax({
                                        url: `/${DB_NAME}/chargebacks/post_to_accounting/acumatica/sending`,
                                        data: {
                                            'chargebacks_ids': selected_cbs_ids,
                                            'post_date': post_date,
                                        },
                                        type: 'POST',
                                        dataType: 'json',
                                        cache: false,
                                        beforeSend: function (){
                                            textPostToAccountingAcumaticaAndDs365.html('Sending ...');
                                        },
                                        success  : function (response) {

                                            // updating
                                            $.ajax({
                                                url: `/${DB_NAME}/chargebacks/post_to_accounting/acumatica/updating`,
                                                data: {
                                                    'cbs_with_transaction_success': JSON.stringify(response.cbs_with_transaction_success),
                                                    'cbs_with_transaction_errors': JSON.stringify(response.cbs_with_transaction_errors),
                                                    'post_date': post_date,
                                                },
                                                type: 'POST',
                                                dataType: 'json',
                                                cache: false,
                                                beforeSend: function (){
                                                    textPostToAccountingAcumaticaAndDs365.html('Updating Chargebacks ...');
                                                },
                                                success  : function (response) {
                                                    show_toast_success_message(response.message, 'bottomRight');
                                                    modalCbProcessingPostToAccountingAcumaticaAndDs365Integration.modal('hide');
                                                    // stay in the same bucket
                                                    let elem = divChargebackFilters.find('.card-body.active').parent().parent();
                                                    CB_VIEW.load_cb_data(elem);
                                                },
                                                complete: function () {
                                                    // update counters
                                                    CB_VIEW.load_cbs_counters_data();
                                                },
                                                error: function (){
                                                    show_toast_error_message('Ajax error', 'bottomRight');
                                                }
                                            });

                                        },
                                        error: function (){
                                            show_toast_error_message('Ajax error');
                                        }
                                    });
                                }
                            },
                            error: function (){
                                show_toast_error_message('Ajax error');
                            }
                        });
                    },
                    error: function (){
                        show_toast_error_message('Ajax error');
                    }
                });
            }

            else if (acc_handler === 'dynamics365'){
                modalCbProcessingPostToAccountingAcumaticaAndDs365Integration.modal('show');

                // connecting //
                $.ajax({
                    url: `/${DB_NAME}/chargebacks/post_to_accounting/dynamics365/connection`,
                    data: {},
                    type: 'POST',
                    dataType: 'json',
                    beforeSend: function (){
                        textPostToAccountingAcumaticaAndDs365.html('Connecting ...');
                    },
                    success  : function (response) {
                        // validating //
                        $.ajax({
                            url: `/${DB_NAME}/chargebacks/post_to_accounting/dynamics365/validations`,
                            data: {
                                'chargebacks_ids': selected_cbs_ids,
                                'access_token': response.access_token
                            },
                            type: 'POST',
                            dataType: 'json',
                            beforeSend: function (){
                                textPostToAccountingAcumaticaAndDs365.html('Validating (items & customers) ...');
                            },
                            success  : function (response) {

                                if (response.extradata){
                                    let cbs_with_wrong_customers = response.extradata.cbs_with_wrong_customers;
                                    let cbs_with_wrong_items = response.extradata.cbs_with_wrong_items;

                                    let html = '';
                                    for (let i=0; i<cbs_with_wrong_customers.length; i++){
                                        let elem = cbs_with_wrong_customers[i];
                                        html += '<tr>' +
                                                    '<td>'+elem.cbid+'</td>' +
                                                    '<td>'+elem.customer_accno+'</td>' +
                                                    '<td>'+elem.error+'</td>' +
                                                 '</tr>';
                                    }

                                    for (let i=0; i<cbs_with_wrong_items.length; i++){
                                        let elem = cbs_with_wrong_items[i];
                                        html += '<tr>' +
                                                    '<td>'+elem.cbid+'</td>' +
                                                    '<td>'+elem.item_accno+'</td>' +
                                                    '<td>'+elem.error+'</td>' +
                                                 '</tr>';
                                    }

                                    // handle errors
                                    divProcessingPostToAccountingAcumaticaAndDs365ProgressBar.removeClass('bg-success').addClass('bg-danger');
                                    tableProcessingPostToAccountingAcumaticaAndDs365Error.find('tbody').html(html);
                                    btnCloseModalPostToAccountingAcumaticaAndDs365Integration.show();
                                    tableProcessingPostToAccountingAcumaticaAndDs365Error.show()

                                }else{

                                    // sending and updating cbs //
                                    $.ajax({
                                        url: `/${DB_NAME}/chargebacks/post_to_accounting/dynamics365/sending_and_updating`,
                                        data: {
                                            'chargebacks_ids': selected_cbs_ids,
                                            'post_date': post_date,
                                        },
                                        type: 'POST',
                                        dataType: 'json',
                                        cache: false,
                                        beforeSend: function (){
                                            textPostToAccountingAcumaticaAndDs365.html('Sending and Updating ...');
                                        },
                                        success: function (response) {
                                            show_toast_success_message(response.message, 'bottomRight');
                                            modalCbProcessingPostToAccountingAcumaticaAndDs365Integration.modal('hide');
                                            // stay in the same bucket
                                            let elem = divChargebackFilters.find('.card-body.active').parent().parent();
                                            CB_VIEW.load_cb_data(elem);
                                        },
                                        complete: function () {
                                            // update counters
                                            CB_VIEW.load_cbs_counters_data();
                                        },
                                        error: function (){
                                            show_toast_error_message('Ajax error');
                                        }
                                    });
                                }
                            },
                            error: function (){
                                show_toast_error_message('Ajax error');
                            }
                        });
                    },
                    error: function (){
                        show_toast_error_message('Ajax error');
                    }
                });
            }
            else{
                $.ajax({
                    type: "POST",
                    url: `/${DB_NAME}/chargebacks/post_to_accounting/${acc_handler}`,
                    data: {
                        'chargebacks_ids': selected_chargebacks_ids,
                        'post_date': inputPostDate.val(),
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
                            show_toast_success_message(response.message, 'bottomRight');

                            let html = '';
                            if (acc_handler === 'manual'){
                                html += '<div class="row">' +
                                            '<div class="col"><b>'+response.message+'</b></div>' +
                                                '<div class="col-sm-4 text-right">' +
                                                '<a href="'+response.file_path+'" download class="btn btn-primary btn-sm" target="_blank">' +
                                                '<i class="fa fa-download"></i> download' +
                                                '</a>' +
                                            '</div>' +
                                        '</div>';
                            }else{
                                html += '<div class="row">' +
                                            '<div class="col-sm-12">' +
                                                '<b>Count of Posted CB: </b>'+response.count_of_cb_without_errors +
                                            '</div>' +
                                        '</div>';
                            }
                            modalCbProcessingPostToAccounting.find('.modal-body').html(html);
                            modalCbProcessingPostToAccounting.modal({'backdrop':'static'}).modal("show");
                            // stay in the same bucket
                            let elem = divChargebackFilters.find('.card-body.active').parent().parent();
                            CB_VIEW.load_cb_data(elem);
                        }else{
                            if (acc_handler === 'manual') {
                                let html = '';
                                for (let i = 0; i < response.extradata.length; i++) {
                                    let item_ndc = response.extradata[i];
                                    html += '<div class="row">' +
                                        '<div class="col-sm-10">' + item_ndc + ' does not have an accounting number</div>' +
                                        '</div>';
                                }
                                modalCbProcessingErrorPostToAccounting.find('.modal-body').html(html);
                                modalCbProcessingErrorPostToAccounting.modal({'backdrop': 'static'}).modal("show");
                            }else{
                                show_toast_error_message(response.message, 'bottomRight');
                            }
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
            }


        }else{
            show_toast_warning_message("Select at least 1 Chargeback to continue", "bottomRight");
        }

    },

};


$(function () {

    // show or hide post_date
    $('.divPostToAccounting').hover(
        function(){
            divPostDate.fadeIn(200);
            divImportFromQB.addClass('mt-2');
        },
    ).on('mouseleave', function () {
        divPostDate.hide();
        divImportFromQB.removeClass('mt-2');
    });

});