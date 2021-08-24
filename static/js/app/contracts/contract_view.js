// Chart elements
let divContractPerformanceSpinnerLoader = $("#divContractPerformanceSpinnerLoader");
let canvasContractPerformance = $("#canvasContractPerformance");

// DataTable
let divContractsListTabOptionsStatuses = $("#divContractsListTabOptionsStatuses");
let divExpiringContractsListTabOptionsStatuses = $("#divExpiringContractsListTabOptionsStatuses");
let divContractsListTabOptionsCustomers = $("#divContractsListTabOptionsCustomers");
let divExpiringContractsListTabOptionsCustomers = $("#divExpiringContractsListTabOptionsCustomers");
let inputContractsListStatusFilterID = $("#inputContractsListStatusFilterID");
let inputExpiringContractsListCustomerFilterID = $("#inputExpiringContractsListCustomerFilterID");
let inputContractsListCustomerFilterID = $("#inputContractsListCustomerFilterID");
let inputExpiringContractsListStatusFilterID = $("#inputExpiringContractsListStatusFilterID");
let tableContractViewAllContracts = $("#tableContractViewAllContracts");
let tableContractViewExpiringContracts = $("#tableContractViewExpiringContracts");
let dtContractViewAllContracts;
let dtContractViewExpiringContracts;
let tableContractInformation = $("#tableContractInformation");
let dttableContractInformation;

// Modal
let modalUploadUpdatesContracts = $("#modalUploadUpdatesContracts");
let modalUploadUpdatesContractsResults = $("#modalUploadUpdatesContractsResults");
let modalUploadConfirmContractsResults = $("#modalUploadConfirmContractsResults");
let modalMembershipFileUpload = $("#modalMembershipFileUpload");
let modalContractMembersUploadResults = $("#modalContractMembersUploadResults");
let modalUploadMemberConfirmContractsResults = $('#modalUploadMemberConfirmContractsResults');
// Upload, Add missing product
let modalProduct = $("#modalProduct");
let inputProductNDC = $("#inputProductNDC");
let inputProductDescription = $("#inputProductDescription");
let inputProductAccountNumber = $("#inputProductAccountNumber");
let inputProductStrength = $("#inputProductStrength");
let inputProductSize = $("#inputProductSize");
let inputProductBrand = $("#inputProductBrand");
let inputProductUPC = $("#inputProductUPC");
let toggleProductStatus = $("#toggleProductStatus");
let btnProductSubmit = $("#btnProductSubmit");

// Upload, Add missing Contract
let addMissingContract = $("#addMissingContract");
let action_close_modal = $("#action_close_modal");
let action_create_contract = $("#action_create_contract");

// form
let formUploadUpdatesContractsDropZone = $("#formUploadUpdatesContractsDropZone");

// Div
let addContractAliasContainer = $("#addContractAliasContainer");

// chart
let chartContractPerformance = '';

// Global Variables for missing lists
let missing_contract_list = [];
let missing_item_list = [];

let missing_contract_list_exclude = [];
let missing_item_list_exclude = [];

// Others
let uploadContinue = $("#uploadContinue");
let uploadClose = $("#uploadClose");
let uploadConfirmContinue = $("#uploadConfirmContinue");
let uploadConfirmClose = $("#uploadConfirmClose");
// Member upload
let uploadMembersContinue = $("#uploadMembersContinue");
let uploadMembersClose = $("#uploadMembersClose");

let uploadMemberConfirmContinue = $("#uploadMemberConfirmContinue");
let uploadMemberConfirmClose = $("#uploadMemberConfirmClose");

let pleaseWait = $('#pleaseWaitDialog');


let uploadDropzone = '';

// Dropzone for Import Company Data
uploadDropzone = Dropzone.options.formUploadUpdatesContractsDropZone = {
    paramName: "file",  // The name that will be used to transfer the file
    maxFilesize: 5,     // MB
    acceptedFiles: ".xls, .xlsx",
    uploadMultiple: false,
    maxFiles: 1,
    success: function(file, response){
        this.removeFile(file);
        contract_upload_update_process_finished(response);
    },
    error:function (file) {
        this.removeFile(file);
    },
};

let contract_upload_update_process_finished = function(response){
    if(response.result === "bad"){
        show_toast_error_message(response.message, "bottomRight");
    }
    else{

        if(response.result === "ok" && response.error === "y"){
            let error_type = '';
            error_type = response.error_type;
            let html = '';
            let error_message = response.message
            if(error_type === "primary_validations"){
                uploadConfirmContinue.hide();
                let errors = response.errors
                if (errors.length > 0){
                    html += '<p>' + error_message +'</p><ul>';
                    for (let i=0; i < errors.length; i++){
                        let elem = errors[i];
                        html += '<li>'+elem+'</li>';
                    }
                    html += '</u>';
                }
                modalUploadConfirmContractsResults.find('.modal-body').addClass("height-200");
                modalUploadConfirmContractsResults.find('.modal-body').removeClass("height-500");
                modalUploadConfirmContractsResults.find('.modal-dialog').removeClass("modal-xxl");
            }
            else if(error_type == "missing_error"){
                let errors_missing_contracts = response.errors_missing_contracts
                let errors_missing_items = response.errors_missing_items
                if(errors_missing_contracts.length > 0 || errors_missing_items.length > 0){
                    missing_contract_list = errors_missing_contracts;
                    missing_item_list = errors_missing_items;

                    html = CONTRACTS_VIEW.draw_upload_missing_table(missing_contract_list, missing_item_list);

                }
                uploadConfirmClose.attr('filename', response.filename)
                uploadConfirmContinue.show();
                if ($('#download_error_file').length){
                    $( "#download_error_file" ).remove();
                }
            }
            else if(error_type === "confirm_validations"){ // Ticket EA-1436 changes

                let contract_list = response.contract_list;
                const arr = Object.keys(contract_list).map((key) => [key, contract_list[key]]);
               if(arr.length ==0){
                     uploadConfirmContinue.hide();
                     modalUploadUpdatesContracts.modal('hide');
                     modalUploadConfirmContractsResults.modal('hide');
                     show_toast_error_message("No record exist", "bottomRight");
                }else{
                html += '<table class="table table-striped table-bordered" border="1">';
                html += '<thead><tr><th>Contracts</th><th>Lines Count</th></tr></thead>';
                html += '<tbody>';
                 for(let i = 0; i < arr.length; i++) {
                        for(let j=0; j<1; j++ ) {
                            html += '<tr>';
                            html += '<td>' + arr[i][0] + '</td>';
                            html += '<td>' + arr[i][1] + '</td>';
                        }
                    }
                     html += '</td>';
                     html += '</tr>';
                     html += '</tbody>';
                     html += '</table>';
                    uploadConfirmClose.attr('filename', response.filename)
                    uploadConfirmContinue.show();
                    if ($('#download_error_file').length){
                        $( "#download_error_file" ).remove();
                    }
                }

            } // end here EA-1436
            // If there is an error but it is not primary or missing then it is assumed that it is processing
            else{
                uploadConfirmContinue.hide();
                uploadConfirmClose.attr("filename", '');
                let errors = response.errors
                html += '<h5>' + error_message +'</h5>';
                if ($('#download_error_file').length){
                    $( "#download_error_file" ).remove();
                }
                $('<a class="btn btn-warning" id="download_error_file" href="/'+DB_NAME+'/contract_upload/update/'+response.filename+'/download">Download the error file</a>').insertAfter("#uploadConfirmContinue");
                html += '<table class="table table-striped table-bordered">';
                if(errors.length > 0){
                    html += '<thead><tr><th>Contract</th><th>Product</th><th>Submitted Price</th><th>Submitted Start date</th><th>Submitted End date</th><th>Error Type</th><th>Error Detail</th></tr></thead>';
                    html += '<tbody>';
                    for (let i=0; i < errors.length; i++){
                        html += '<tr>';

                        let elem = errors[i];
                        let processing_error_messages = elem.message
                        html += '<td>'+elem.contract+'</td>';
                        html += '<td>'+elem.product+'</td>';
                        html += '<td>'+elem.submitted_price+'</td>';
                        html += '<td>'+elem.submitted_start_date+'</td>';
                        html += '<td>'+elem.submitted_end_date+'</td>';
                        html += '<td>'+elem.type_text+'</td>';
                        html += '<td>';
                        for (let j=0;j < processing_error_messages.length;j++){
                            html += processing_error_messages[j];

                            if(j != processing_error_messages.length -1){
                                html += '</br>';
                            }
                        }
                        html += '</td>';
                        html += '</tr>';
                    }
                    html += '</tbody>';
                    html += '</table>';
                }
                modalUploadConfirmContractsResults.find('.modal-dialog').addClass("modal-xxl");
                modalUploadConfirmContractsResults.find('.modal-body').removeClass("height-200");
                modalUploadConfirmContractsResults.find('.modal-body').addClass("height-500");
            }

            // If errors , display errors in Results Modal
            modalUploadUpdatesContracts.modal('hide');
            modalUploadConfirmContractsResults.find('.modal-body').html(html);
            modalUploadConfirmContractsResults.modal({backdrop: 'static', keyboard: false}).modal('show');
        }
        else{
            modalUploadUpdatesContracts.modal('hide');
            show_toast_success_message(response.message, "bottomRight");
        }
    }
};


let CONTRACTS_VIEW = {

    name: 'CONTRACTS_VIEW',
    openModalUploadUpdatesContracts:function(){
        modalUploadUpdatesContracts.modal({backdrop: 'static', keyboard: false}).modal('show');
    },

    closeModalUploadUpdatesContracts:function(){
        // formUploadUpdatesContractsDropZone.removeAllFiles();
        modalUploadUpdatesContracts.modal('hide');
    },

    draw_upload_missing_table:function(missing_contract_list, missing_item_list, exclude=''){
        let rowCounter = 0;
        let html = '<h5>We could not process the file due to following missing entities</h5>';
        html += '<div id="missing_error_container">';
        html += '<table class="table table-striped table-bordered">';
        html += '<thead><tr><th>Type</th><th>Number</th><th>Action</th></tr></thead>';
        html += '<tbody>';
        for (let i=0; i < missing_contract_list.length; i++) {
            let elem = missing_contract_list[i];
            let contract_number = "'"+elem.entity+"'";
            if(exclude !== elem.entity && !missing_contract_list_exclude.includes(elem.entity)){
                rowCounter += 1;
                html += '<tr>';

                html += '<td>'+elem.type+'</td>';
                html += '<td>'+elem.entity+'</td>';
                html += '<td><button class="btn btn-sm btn-primary" onclick="CONTRACTS_VIEW.add_contract_modal('+contract_number+')">Add Contract</button></td>';

                html += '</tr>';
            }else{
                missing_contract_list_exclude.push(elem.entity);
            }

        }
        for (let i=0; i < missing_item_list.length; i++) {
            let elem = missing_item_list[i];
            let ndc = elem.entity;
            if(exclude !== ndc && !missing_item_list_exclude.includes(elem.entity)) {
                rowCounter += 1;
                html += '<tr>';

                html += '<td>' + elem.type + '</td>';
                html += '<td>' + elem.entity + '</td>';
                html += '<td><button class="btn btn-sm btn-primary" onclick="CONTRACTS_VIEW.add_product_modal(' + ndc + ')">Add Product</button></td>';

                html += '</tr>';
            }else{
                missing_item_list_exclude.push(elem.entity);
            }
        }
        html += '</tbody>';
        html += '</table>';
        html += '</div>';

        if (rowCounter === 0){
            html = "<h5 style='color: green'>All missing entities are added successfully! Please click on Continue to process the file</h5>";
        }

        return html;
    },

    add_product_modal:function(ndc){
        let formatted_ndc = ndc.toString().substring(0, 5) + "-" + ndc.toString().substring(5, 9) + "-" + ndc.toString().substring(9);
        inputProductNDC.val(formatted_ndc);
        modalProduct.find('.modal-title').html("Add Product");
        inputProductNDC.prop('disabled', 'true');
        btnProductSubmit.html("Submit");
        btnProductSubmit.attr('onclick', 'CONTRACTS_VIEW.product_submit('+ndc+')');
        modalProduct.modal('show');
    },

    add_contract_modal:function(contract_number){
        $("#action_buttons").appendTo("#addMissingContractFooter");
        $("#inputContractNumber").val(contract_number).prop("disabled", true);
        action_close_modal.attr('data-dismiss',"modal");
        action_close_modal.attr('onclick', '');
        action_create_contract.attr('onclick', 'CONTRACT_HANDLER.submit("create","contract_view_missing_modal","'+contract_number+'")');
        addMissingContract.modal('show');
    },

    product_submit:function(ndc){
        let url = `/${DB_NAME}/products/create`;

        let item_status = '2';
        if (toggleProductStatus.is(":checked")){
            item_status = '1';
        }
        ndc = ndc.toString();
        let formData = {
            'item_ndc': inputProductNDC.val(),
            'item_description': inputProductDescription.val(),
            'item_account_number': inputProductAccountNumber.val(),
            'item_strength': inputProductStrength.val(),
            'item_size': inputProductSize.val(),
            'item_brand': inputProductBrand.val(),
            'item_upc': inputProductUPC.val(),
            'item_status': item_status,
        };

        // validations
        if (!formData.item_ndc){
            inputProductNDC.addClass('border-red');
            show_toast_error_message('Item NDC is required', 'bottomRight');
            return false;
        }
        if (!formData.item_account_number){
            inputProductAccountNumber.addClass('border-red');
            show_toast_error_message('Item Account Number is required', 'bottomRight');
            return false;
        }

        $.ajax({
            url: url,
            type: "POST",
            data: formData,
            dataType: "json",
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            },
            success: function (response) {
                if(response.result === 'ok') {
                    let html = CONTRACTS_VIEW.draw_upload_missing_table(missing_contract_list, missing_item_list, ndc);
                    modalProduct.modal('hide');
                    modalUploadUpdatesContractsResults.find('.modal-body').html(html);
                    show_toast_success_message(response.message, 'bottomRight');
                }else{
                    show_toast_error_message(response.message, 'bottomRight');
                }
            },
            error: function (response) {
                show_toast_error_message(response.message, 'bottomRight');
            }
        });

    },

    close_upload_result_modal:function(elem){
        let filename = elem.attr('filename');
        let url = `/${DB_NAME}/contract_upload/${filename}/delete`;
        if(filename !== ""){
            $.ajax({
                url: url,
                type: "POST",
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    if(response.result === 'ok') {
                        modalUploadUpdatesContractsResults.modal('hide');
                        modalUploadConfirmContractsResults.modal('hide');
                        // show_toast_success_message(response.message, 'bottomRight');
                    }else{
                        show_toast_error_message(response.message, 'bottomRight');
                    }
                },
                error: function (response) {
                    show_toast_error_message(response.message, 'bottomRight');
                }
            });
        }
        else{
            modalUploadConfirmContractsResults.modal('hide');
            modalUploadUpdatesContractsResults.modal('hide');
        }

    },

    check_and_process_upload:function(){
        let filename = uploadClose.attr('filename');
        if((filename !== "") && (missing_contract_list.length > 0 || missing_item_list.length > 0)){
            $.ajax({
                url: `/${DB_NAME}/contracts/upload_update`,
                type: "POST",
                data: {'confirm_upload':"1",'check_missing':"1",'filename':filename ,'missing_contract_list': JSON.stringify(missing_contract_list), 'missing_item_list': JSON.stringify(missing_item_list)},
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    if(response.result === 'ok') {
                        // modalUploadUpdatesContractsResults.modal('hide');
                        // show_toast_success_message(response.message, 'bottomRight');
                        if(response.result == "bad"){
                            show_toast_error_message(response.message, "bottomRight");
                        }
                        else{

                            if(response.result == "ok" && response.error == "y"){
                                let error_type = '';
                                error_type = response.error_type;
                                let html = '';
                                let error_message = response.message
                                if(error_type == "primary_validations"){
                                    uploadContinue.hide();
                                    let errors = response.errors
                                    if (errors.length > 0){
                                        html += '<p>' + error_message +'</p><ul>';
                                        for (let i=0; i < errors.length; i++){
                                            let elem = errors[i];
                                            html += '<li>'+elem+'</li>';
                                        }
                                        html += '</u>';
                                    }
                                    modalUploadUpdatesContractsResults.find('.modal-body').addClass("height-200");
                                    modalUploadUpdatesContractsResults.find('.modal-body').removeClass("height-500");
                                    modalUploadUpdatesContractsResults.find('.modal-dialog').removeClass("modal-xxl");
                                }
                                else if(error_type == "missing_error"){
                                    let errors_missing_contracts = response.errors_missing_contracts
                                    let errors_missing_items = response.errors_missing_items
                                    if(errors_missing_contracts.length > 0 || errors_missing_items.length > 0){
                                        missing_contract_list = errors_missing_contracts;
                                        missing_item_list = errors_missing_items;

                                        html = CONTRACTS_VIEW.draw_upload_missing_table(missing_contract_list, missing_item_list);

                                    }
                                    uploadClose.attr('filename', response.filename)
                                    uploadContinue.show();
                                    if ($('#download_error_file').length){
                                        $( "#download_error_file" ).remove();
                                    }
                                }
                                // If there is an error but it is not primary or missing then it is assumed that it is processing
                                else{
                                    uploadContinue.hide();
                                    uploadClose.attr("filename", '');
                                    let errors = response.errors
                                    html += '<h5>' + error_message +'</h5>';
                                    if ($('#download_error_file').length){
                                        $( "#download_error_file" ).remove();
                                    }
                                    $('<a class="btn btn-warning" id="download_error_file" href="/'+DB_NAME+'/contract_upload/update/'+response.filename+'/download">Download the error file</a>').insertAfter("#uploadContinue");
                                    html += '<table class="table table-striped table-bordered">';
                                    if(errors.length > 0){
                                        html += '<thead><tr><th>Contract</th><th>Product</th><th>Submitted Price</th><th>Submitted Start date</th><th>Submitted End date</th><th>Error Type</th><th>Error Detail</th></tr></thead>';
                                        html += '<tbody>';
                                        for (let i=0; i < errors.length; i++){
                                            html += '<tr>';

                                            let elem = errors[i];
                                            let processing_error_messages = elem.message
                                            html += '<td>'+elem.contract+'</td>';
                                            html += '<td>'+elem.product+'</td>';
                                            html += '<td>'+elem.submitted_price+'</td>';
                                            html += '<td>'+elem.submitted_start_date+'</td>';
                                            html += '<td>'+elem.submitted_end_date+'</td>';
                                            html += '<td>'+elem.type_text+'</td>';
                                            html += '<td>';
                                            for (let j=0;j < processing_error_messages.length;j++){
                                                html += processing_error_messages[j];

                                                if(j != processing_error_messages.length -1){
                                                    html += '</br>';
                                                }
                                            }
                                            html += '</td>';
                                            html += '</tr>';
                                        }
                                        html += '</tbody>';
                                        html += '</table>';
                                    }
                                    modalUploadUpdatesContractsResults.find('.modal-dialog').addClass("modal-xxl");
                                    modalUploadUpdatesContractsResults.find('.modal-body').removeClass("height-200");
                                    modalUploadUpdatesContractsResults.find('.modal-body').addClass("height-500");
                                }

                                // If errors , display errors in Results Modal
                                modalUploadUpdatesContracts.modal('hide');
                                modalUploadUpdatesContractsResults.find('.modal-body').html(html);
                                modalUploadUpdatesContractsResults.modal({backdrop: 'static', keyboard: false}).modal('show');
                            }
                            else{
                                modalUploadUpdatesContractsResults.modal('hide');
                                modalUploadUpdatesContracts.modal('hide');
                                show_toast_success_message(response.message, "bottomRight");
                            }
                        }
                    }else{
                        show_toast_error_message(response.message, 'bottomRight');
                    }
                },
                error: function (response) {
                    show_toast_error_message(response.message, 'bottomRight');
                }
            });
        }
    },
    confirm_and_process_upload:function(){
        let filename = uploadConfirmClose.attr('filename');
        pleaseWait.modal('show');
        $.ajax({
                url: `/${DB_NAME}/contracts/upload_update`,
                type: "POST",
                data: {'confirm_upload':"1",'filename':filename},
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    pleaseWait.modal('hide');
                    if(response.result === 'ok') {
                        // modalUploadUpdatesContractsResults.modal('hide');
                        // show_toast_success_message(response.message, 'bottomRight');
                        if(response.result == "bad"){
                            show_toast_error_message(response.message, "bottomRight");
                        }
                        else{

                            if(response.result == "ok" && response.error == "y"){
                                let error_type = '';
                                error_type = response.error_type;
                                let html = '';
                                let error_message = response.message
                                if(error_type == "primary_validations"){
                                    uploadContinue.hide();
                                    let errors = response.errors
                                    if (errors.length > 0){
                                        html += '<p>' + error_message +'</p><ul>';
                                        for (let i=0; i < errors.length; i++){
                                            let elem = errors[i];
                                            html += '<li>'+elem+'</li>';
                                        }
                                        html += '</u>';
                                    }
                                    modalUploadUpdatesContractsResults.find('.modal-body').addClass("height-200");
                                    modalUploadUpdatesContractsResults.find('.modal-body').removeClass("height-500");
                                    modalUploadUpdatesContractsResults.find('.modal-dialog').removeClass("modal-xxl");
                                }
                                else if(error_type == "missing_error"){
                                    let errors_missing_contracts = response.errors_missing_contracts
                                    let errors_missing_items = response.errors_missing_items
                                    if(errors_missing_contracts.length > 0 || errors_missing_items.length > 0){
                                        missing_contract_list = errors_missing_contracts;
                                        missing_item_list = errors_missing_items;

                                        html = CONTRACTS_VIEW.draw_upload_missing_table(missing_contract_list, missing_item_list);

                                    }
                                    uploadClose.attr('filename', response.filename)
                                    uploadContinue.show();
                                    if ($('#download_error_file').length){
                                        $( "#download_error_file" ).remove();
                                    }
                                }
                                // If there is an error but it is not primary or missing then it is assumed that it is processing
                                else{
                                    uploadContinue.hide();
                                    uploadClose.attr("filename", '');
                                    let errors = response.errors
                                    html += '<h5>' + error_message +'</h5>';
                                    if ($('#download_error_file').length){
                                        $( "#download_error_file" ).remove();
                                    }
                                    $('<a class="btn btn-warning" id="download_error_file" href="/'+DB_NAME+'/contract_upload/update/'+response.filename+'/download">Download the error file</a>').insertAfter("#uploadContinue");
                                    html += '<table class="table table-striped table-bordered">';
                                    if(errors.length > 0){
                                        html += '<thead><tr><th>Contract</th><th>Product</th><th>Submitted Price</th><th>Submitted Start date</th><th>Submitted End date</th><th>Error Type</th><th>Error Detail</th></tr></thead>';
                                        html += '<tbody>';
                                        for (let i=0; i < errors.length; i++){
                                            html += '<tr>';

                                            let elem = errors[i];
                                            let processing_error_messages = elem.message
                                            html += '<td>'+elem.contract+'</td>';
                                            html += '<td>'+elem.product+'</td>';
                                            html += '<td>'+elem.submitted_price+'</td>';
                                            html += '<td>'+elem.submitted_start_date+'</td>';
                                            html += '<td>'+elem.submitted_end_date+'</td>';
                                            html += '<td>'+elem.type_text+'</td>';
                                            html += '<td>';
                                            for (let j=0;j < processing_error_messages.length;j++){
                                                html += processing_error_messages[j];

                                                if(j != processing_error_messages.length -1){
                                                    html += '</br>';
                                                }
                                            }
                                            html += '</td>';
                                            html += '</tr>';
                                        }
                                        html += '</tbody>';
                                        html += '</table>';
                                    }
                                    modalUploadUpdatesContractsResults.find('.modal-dialog').addClass("modal-xxl");
                                    modalUploadUpdatesContractsResults.find('.modal-body').removeClass("height-200");
                                    modalUploadUpdatesContractsResults.find('.modal-body').addClass("height-500");
                                }

                                // If errors , display errors in Results Modal
                                modalUploadUpdatesContracts.modal('hide');
                                modalUploadConfirmContractsResults.modal('hide');
                                modalUploadUpdatesContractsResults.find('.modal-body').html(html);
                                modalUploadUpdatesContractsResults.modal({backdrop: 'static', keyboard: false}).modal('show');
                            }
                            else{
                                modalUploadUpdatesContractsResults.modal('hide');
                                modalUploadConfirmContractsResults.modal('hide');
                                modalUploadUpdatesContracts.modal('hide');
                                show_toast_success_message(response.message, "bottomRight");
                            }
                        }
                    }else{
                        show_toast_error_message(response.message, 'bottomRight');
                    }
                },
                error: function (response) {
                    show_toast_error_message(response.message, 'bottomRight');
                }
            });
    },

    download_sample_upload:function(){
         window.open('/'+DB_NAME+'/contracts/download_sample_upload', '_blank');
    },

    // Chart Section
    // dropdown change to update chart
    update_perfomance_chart: function (elem) {
        let data_range = 'MTD';
        if (elem){
            data_range = elem.val();
        }
        CONTRACTS_VIEW.drawChart_ContractPerformance(data_range);
    },

    // performance chart
    drawChart_ContractPerformance: function (range) {
        if(chartContractPerformance !== ""){
            chartContractPerformance.destroy();
        }
        // init chart
        chartContractPerformance = new Chart(canvasContractPerformance, {
            type: 'bar',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                tooltips: {
                    callbacks: {
                        label: function(tooltipItem, data) {
                            let value = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index];
                            return "$" + value;
                        }
                    }
                },
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            // Include a dollar sign in the ticks
                            callback: function(value, index, values) {
                                return '$' + value;
                            }
                        }
                    }],
                    xAxes: [{
                        ticks: {
                            autoSkip: false
                        }
                    }],
                },
                legend: {
                    display: false,
                    labels: {
                        fontColor: 'rgb(255, 99, 132)'
                    }
                },
                title: {
                    display: false,
                    text: 'Contract Performance'
                }
            }
        });

        $.ajax({
            url: `/${DB_NAME}/contracts/charts/performance`,
            beforeSend: function(){
                canvasContractPerformance.hide();
                divContractPerformanceSpinnerLoader.show();
            },
            type: 'POST',
            data: {
                'range': range
            },
            dataType: 'json'
        }).done(function(response){
            divContractPerformanceSpinnerLoader.hide();
            chartContractPerformance.data.labels = response.labels;
            chartContractPerformance.data.datasets = response.datasets;
            chartContractPerformance.update();
            canvasContractPerformance.show();
        });

    },

    // Contract Overview DataTable Section
    load_data: function (elem){
        let query_sf = elem.attr('sf');     // status filter
        let query_cf = elem.attr('cf');     // customer filter

        if (!query_sf){
            query_sf = inputContractsListStatusFilterID.val();
            if (elem){
                divContractsListTabOptionsCustomers.find('a').removeClass('active');
                elem.addClass('active');
            }else{
                $("#divContractsListTabOptionsCustomers a:first-child").addClass('active');
            }
        }
        if (!query_cf){
            query_cf = inputContractsListCustomerFilterID.val();
            if (elem){
                divContractsListTabOptionsStatuses.find('a').removeClass('active');
                elem.addClass('active');
            }else{
                $("#divContractsListTabOptionsStatuses a:first-child").addClass('active');

            }
        }

        // update status filter input to pass it to the ajax
        inputContractsListStatusFilterID.val(query_sf);
        inputContractsListCustomerFilterID.val(query_cf);
        // reload data table ajax
        dtContractViewAllContracts.ajax.reload();
    },


    // Expiring Contract DataTable Section
    load_expiring_data: function (elem){
        let query_sf = elem.attr('sf');     // status filter
        let query_cf = elem.attr('cf');     // customer filter

        if (!query_sf){
            query_sf = inputExpiringContractsListStatusFilterID.val();
            if (elem){
                divExpiringContractsListTabOptionsCustomers.find('a').removeClass('active');
                elem.addClass('active');
            }else{
                $("#divExpiringContractsListTabOptionsCustomers a:first-child").addClass('active');
            }
        }
        if (!query_cf){
            query_cf = inputExpiringContractsListCustomerFilterID.val();
            if (elem){
                divExpiringContractsListTabOptionsStatuses.find('a').removeClass('active');
                elem.addClass('active');
            }else{
                $("#divExpiringContractsListTabOptionsStatuses a:first-child").addClass('active');

            }
        }

        // update status filter input to pass it to the ajax
        inputExpiringContractsListStatusFilterID.val(query_sf);
        inputExpiringContractsListCustomerFilterID.val(query_cf);
        // reload data table ajax
        dtContractViewExpiringContracts.ajax.reload();
    },
};

// Dropzone for Import Contract Membership Data
Dropzone.options.formMembershipFileUploadDZ = {
    paramName: "file",  // The name that will be used to transfer the file
    // maxFilesize: 5,     // MB EA-1510
    acceptedFiles: ".xls, .xlsx",
    uploadMultiple: false,
    maxFiles: 1,
    timeout: 180000,
    success: function(file, response){
        this.removeFile(file);
        contract_upload_members_finished(response);
    },
    error:function (file) {
        this.removeFile(file);
        show_toast_error_message('Allowed file types are .xls and .xlsx', 'bottomRight');
    },
     //Called just before each file is sent
     sending: function(file, xhr, formData) {
         //Execute on case of timeout only
         xhr.ontimeout = function(e) {
             //Output timeout error message here
                     show_toast_error_message('Server Timeout', 'bottomRight');

         };
     }
};

let contract_upload_members_finished = function(response){
    if(response.result === "bad"){
        show_toast_error_message(response.message, "bottomRight");
    }
    else{
        if(response.result === "ok" && response.error === "y"){
            let error_type = response.error_type;
            let html = '';
            let error_message = response.message
            if(error_type === "primary_validations"){
                uploadMemberConfirmContinue.hide();
                let errors = response.errors
                if (errors.length > 0){
                    html += '<p>' + error_message +'</p><ul>';
                    for (let i=0; i < errors.length; i++){
                        let elem = errors[i];
                        html += '<li>'+elem+'</li>';
                    }
                    html += '</u>';
                }
                modalUploadMemberConfirmContractsResults.find('.modal-body').addClass("height-200");
                modalUploadMemberConfirmContractsResults.find('.modal-body').removeClass("height-500");
                modalUploadMemberConfirmContractsResults.find('.modal-dialog').removeClass("modal-xxl");
            }else if(error_type === "confirm_validations"){ // Ticket EA-1436 changes

                let contract_list = response.contract_list;
                const arr = Object.keys(contract_list).map((key) => [key, contract_list[key]]);
               if(arr.length ==0){
                     uploadMemberConfirmContinue.hide();
                     modalUploadUpdatesContracts.modal('hide');
                     modalUploadConfirmContractsResults.modal('hide');
                     show_toast_error_message("No record exist", "bottomRight");
                }else{
                html += '<table class="table table-striped table-bordered" border="1">';
                html += '<thead><tr><th>Contracts</th><th>Lines Count</th></tr></thead>';
                html += '<tbody>';
                 for(let i = 0; i < arr.length; i++) {
                        for(let j=0; j<1; j++ ) {
                            html += '<tr>';
                            html += '<td>' + arr[i][0] + '</td>';
                            html += '<td>' + arr[i][1] + '</td>';
                        }
                    }
                     html += '</td>';
                     html += '</tr>';
                     html += '</tbody>';
                     html += '</table>';
                     uploadMemberConfirmClose.attr('filename', response.filename)
                     uploadMemberConfirmContinue.show();
                    if ($('#download_error_file').length){
                        $( "#download_error_file" ).remove();
                    }
                }

            } // end here EA-1436
            else if(error_type == "missing_error"){
                let errors_missing_contracts = response.errors_missing_contracts
                if(errors_missing_contracts.length > 0){
                    missing_contract_list = errors_missing_contracts;
                    html = CONTRACT_Membership.draw_upload_missing_table(missing_contract_list);

                }
                uploadMemberConfirmClose.attr('filename', response.filename)
                uploadMemberConfirmContinue.show();
                if ($('#download_error_file').length){
                    $( "#download_error_file" ).remove();
                }
                modalUploadMemberConfirmContractsResults.find('.modal-body').addClass("height-200");
                // modalContractMembersUploadResults.find('.modal-body').removeClass("height-500");
                modalUploadMemberConfirmContractsResults.find('.modal-dialog').removeClass("modal-xxl");
                modalUploadMemberConfirmContractsResults.find('.modal-dialog').addClass("modal-xl");
            }
            // If errors , display errors in Results Modal
            modalMembershipFileUpload.modal('hide');
            modalUploadMemberConfirmContractsResults.find('.modal-body').html(html);
            modalUploadMemberConfirmContractsResults.modal({backdrop: 'static', keyboard: false}).modal('show');
        }
        else{
            let processed_records = response.processed_records;
            let processing_errors = response.processing_errors;
            let filename = response.filename
            let htmlData = CONTRACT_Membership.draw_success_table(processed_records, processing_errors, filename);

            if(htmlData != ''){
                uploadMemberConfirmClose.attr('filename','');
                uploadMemberConfirmContinue.hide();
                modalMembershipFileUpload.modal('hide');
                modalUploadMemberConfirmContractsResults.find('.modal-dialog').addClass('modal-xxl');
                modalUploadMemberConfirmContractsResults.find('.modal-body').html(htmlData);
                uploadMemberConfirmClose.html("Close");
                modalUploadMemberConfirmContractsResults.modal({backdrop: 'static', keyboard: false}).modal('show');
            }

            modalMembershipFileUpload.modal('hide');
            // show_toast_success_message(response.message, "bottomRight");
        }
    }
};

let CONTRACT_Membership = {
    name: 'CONTRACT_Membership',

    draw_upload_missing_table:function(missing_contract_list, exclude=''){
        let rowCounter = 0;
        let html = '<h5>Following contract numbers does not exists in the system. Please add them to continue.</h5>';
        html += '<div id="missing_error_container">';
        html += '<table class="table table-striped table-bordered">';
        html += '<thead><tr><th>Number</th><th>Action</th></tr></thead>';
        html += '<tbody>';
        for (let i=0; i < missing_contract_list.length; i++) {
            let elem = missing_contract_list[i];
            let contract_number = "'"+elem.entity+"'";
            if(exclude !== elem.entity && !missing_contract_list_exclude.includes(elem.entity)){
                rowCounter += 1;
                html += '<tr>';

                // html += '<td>'+elem.type+'</td>';
                html += '<td>'+elem.entity+'</td>';
                html += '<td><button class="btn btn-sm btn-primary" onclick="CONTRACT_Membership.add_contract_modal('+contract_number+')">Add Contract</button></td>';

                html += '</tr>';
            }else{
                missing_contract_list_exclude.push(elem.entity);
            }

        }
        html += '</tbody>';
        html += '</table>';
        html += '</div>';

        if (rowCounter == 0){
            html = "<h5 style='color: green'>All missing contracts are added successfully! Please click on Continue to process the file</h5>";
        }

        return html;
    },

    draw_success_table:function(processed_records, processing_errors, filename=''){
        let html = '';
        if(processed_records.length > 0){
            html += '<h5 style="color: green">Number of relationships processed successfully</h5>';
            html += '<div id="processed_records_table">';
            html += '<table class="table table-striped table-bordered">';
            html += '<thead><tr><th>Number</th><th>Count</th></tr></thead>';
            html += '<tbody>';
            for (let i=0; i < processed_records.length; i++) {
                let elem = processed_records[i];
                html += '<tr>';

                html += '<td>'+elem.contract+'</td>';
                html += '<td>'+elem.processed_successfully+'</td>';

                html += '</tr>';
            }
            html += '</tbody>';
            html += '</table>';
            html += '</div>';

        }
        if(processing_errors.length > 0){
            if ($('#download_error_file').length){
                $( "#download_error_file" ).remove();
            }
            $('<a class="btn btn-warning" id="download_error_file" href="/'+DB_NAME+'/contract_upload/update/'+filename+'/download">Download the error file</a>').insertAfter("#uploadMembersContinue");
            html += '<div class="row"><div class="col-6 text-left"><h5 style="color: red">Records failed to processed</h5></div></div><br/>';
            html += '<div id="processing_errors_table">';
            html += '<table class="table table-striped table-bordered">';
            html += '<thead><tr><th>CONTRACT</th><th>MEMBER_LOCNO</th><th>COT</th><th>Start_Date</th><th>End_Date</th><th>Error Type</th><th>Error Detail</th></tr></thead>';
            html += '<tbody>';

            for (let i=0; i < processing_errors.length; i++) {
                let elem = processing_errors[i];
                let processing_error_messages = elem.message
                html += '<tr>';

                html += '<td>'+elem.contract+'</td>';
                html += '<td>'+elem.indc_loc_number+'</td>';
                html += '<td>'+elem.cot+'</td>';
                html += '<td>'+elem.submitted_start_date+'</td>';
                html += '<td>'+elem.submitted_end_date+'</td>';
                html += '<td>'+elem.type_text+'</td>';
                html += '<td>';
                for (let j=0;j < processing_error_messages.length;j++){
                    html += processing_error_messages[j];

                    if(j != processing_error_messages.length -1){
                        html += '</br>';
                    }
                }
                // html += '<td>'+elem.message+'</td>';
                html += '</td>';
                html += '</tr>';
            }
            html += '</tbody>';
            html += '</table>';
            html += '</div>';

        }
        return html
    },

    close_upload_result_modal:function(elem){
        let filename = elem.attr('filename');
        let url = `/${DB_NAME}/contract_members_upload/${filename}/delete`;
        if(filename !== ""){
            $.ajax({
                url: url,
                type: "POST",
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    if(response.result === 'ok') {
                        modalUploadMemberConfirmContractsResults.modal('hide');
                        modalContractMembersUploadResults.modal('hide');
                        // show_toast_success_message(response.message, 'bottomRight');
                    }else{
                        show_toast_error_message(response.message, 'bottomRight');
                    }
                },
                error: function (response) {
                    show_toast_error_message(response.message, 'bottomRight');
                }
            });
        }
        else{
            modalContractMembersUploadResults.modal('hide');
            modalUploadMemberConfirmContractsResults.modal('hide');
        }

    },

    add_contract_modal:function(contract_number){
        $("#action_buttons").appendTo("#addMissingContractFooter");
        $("#inputContractNumber").val(contract_number);
        $("#inputContractNumber").prop("disabled", true);
        action_close_modal.attr('data-dismiss',"modal");
        action_close_modal.attr('onclick', '');
        action_create_contract.attr('onclick', 'CONTRACT_HANDLER.submit("create","membership_missing_modal","'+contract_number+'")');
        addMissingContract.modal('show');
    },

    check_and_process_upload:function(){
        let filename = uploadMembersClose.attr('filename');
        if((filename !== "") && (missing_contract_list.length > 0 || missing_item_list.length > 0)) {
            $.ajax({
                url: `/${DB_NAME}/settings/uploads/membership_data`,
                type: "POST",
                data: {
                    'confirm_upload': "1",
                    'check_missing': "1",
                    'filename': filename,
                    'missing_contract_list': JSON.stringify(missing_contract_list),
                },
                dataType: "json",
                beforeSend: function (xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    if(response.result === "bad"){
                        show_toast_error_message(response.message, "bottomRight");
                    }
                    else {
                        if(response.result === "ok" && response.error === "y"){
                            let error_type = response.error_type;
                            let html = '';
                            let error_message = response.message
                            if(error_type === "primary_validations"){
                                uploadMembersContinue.hide();
                                let errors = response.errors
                                if (errors.length > 0){
                                    html += '<p>' + error_message +'</p><ul>';
                                    for (let i=0; i < errors.length; i++){
                                        let elem = errors[i];
                                        html += '<li>'+elem+'</li>';
                                    }
                                    html += '</u>';
                                }
                                modalContractMembersUploadResults.find('.modal-body').addClass("height-200");
                                modalContractMembersUploadResults.find('.modal-body').removeClass("height-500");
                                modalContractMembersUploadResults.find('.modal-dialog').removeClass("modal-xxl");
                            }
                            else if(error_type == "missing_error"){
                                let errors_missing_contracts = response.errors_missing_contracts
                                if(errors_missing_contracts.length > 0){
                                    missing_contract_list = errors_missing_contracts;
                                    html = CONTRACT_Membership.draw_upload_missing_table(missing_contract_list);

                                }
                                uploadMembersClose.attr('filename', response.filename)
                                uploadMembersContinue.show();


                                if ($('#download_error_file').length){
                                    $( "#download_error_file" ).remove();
                                }
                                modalContractMembersUploadResults.find('.modal-body').addClass("height-200");
                                // modalContractMembersUploadResults.find('.modal-body').removeClass("height-500");
                                modalContractMembersUploadResults.find('.modal-dialog').removeClass("modal-xxl");
                                modalContractMembersUploadResults.find('.modal-dialog').addClass("modal-xl");
                            }
                            // If errors , display errors in Results Modal
                            modalMembershipFileUpload.modal('hide');
                            modalContractMembersUploadResults.find('.modal-body').html(html);
                            modalContractMembersUploadResults.modal({backdrop: 'static', keyboard: false}).modal('show');
                        }
                        else{
                            let processed_records = response.processed_records;
                            let processing_errors = response.processing_errors;
                            let filename = response.filename
                            let htmlData = CONTRACT_Membership.draw_success_table(processed_records, processing_errors, filename);

                            if(htmlData != ''){
                                uploadMembersClose.attr('filename','');
                                uploadMembersContinue.css('display','none');
                                modalMembershipFileUpload.modal('hide');
                                modalContractMembersUploadResults.find('.modal-body').html(htmlData);
                                modalContractMembersUploadResults.find('.modal-dialog').addClass("modal-xxl");
                                uploadMembersClose.html("Close");
                                modalContractMembersUploadResults.modal({backdrop: 'static', keyboard: false}).modal('show');
                            }

                            modalMembershipFileUpload.modal('hide');
                            // show_toast_success_message(response.message, "bottomRight");
                        }
                    }
                }
            });
        }
    },

    confirm_and_process_upload:function(){
        let filename = uploadMemberConfirmClose.attr('filename');
            pleaseWait.modal('show');
            $.ajax({
                url: `/${DB_NAME}/settings/uploads/membership_data`,
                type: "POST",
                data: {
                    'confirm_upload': "1",
                    'filename': filename,
                },
                dataType: "json",
                beforeSend: function (xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    pleaseWait.modal('hide');
                    if(response.result === "bad"){
                        show_toast_error_message(response.message, "bottomRight");
                    }
                    else {
                        if(response.result === "ok" && response.error === "y"){
                            let error_type = response.error_type;
                            let html = '';
                            let error_message = response.message
                            if(error_type === "primary_validations"){
                                uploadMembersContinue.hide();
                                let errors = response.errors
                                if (errors.length > 0){
                                    html += '<p>' + error_message +'</p><ul>';
                                    for (let i=0; i < errors.length; i++){
                                        let elem = errors[i];
                                        html += '<li>'+elem+'</li>';
                                    }
                                    html += '</u>';
                                }
                                modalContractMembersUploadResults.find('.modal-body').addClass("height-200");
                                modalContractMembersUploadResults.find('.modal-body').removeClass("height-500");
                                modalContractMembersUploadResults.find('.modal-dialog').removeClass("modal-xxl");
                            }
                            else if(error_type == "missing_error"){
                                let errors_missing_contracts = response.errors_missing_contracts
                                if(errors_missing_contracts.length > 0){
                                    missing_contract_list = errors_missing_contracts;
                                    html = CONTRACT_Membership.draw_upload_missing_table(missing_contract_list);

                                }
                                uploadMembersClose.attr('filename', response.filename)
                                uploadMembersContinue.show();

                                if ($('#download_error_file').length){
                                    $( "#download_error_file" ).remove();
                                }
                                modalContractMembersUploadResults.find('.modal-body').addClass("height-200");
                                // modalContractMembersUploadResults.find('.modal-body').removeClass("height-500");
                                modalContractMembersUploadResults.find('.modal-dialog').removeClass("modal-xxl");
                                modalContractMembersUploadResults.find('.modal-dialog').addClass("modal-xl");
                            }
                            // If errors , display errors in Results Modal
                            modalMembershipFileUpload.modal('hide');
                            modalUploadMemberConfirmContractsResults.modal('hide');
                            modalContractMembersUploadResults.find('.modal-body').html(html);
                            modalContractMembersUploadResults.modal({backdrop: 'static', keyboard: false}).modal('show');
                        }
                        else{
                            let processed_records = response.processed_records;
                            let processing_errors = response.processing_errors;
                            let filename = response.filename
                            let htmlData = CONTRACT_Membership.draw_success_table(processed_records, processing_errors, filename);

                            if(htmlData != ''){
                                uploadMembersClose.attr('filename','');
                                uploadMembersContinue.css('display','none');
                                modalMembershipFileUpload.modal('hide');
                                modalContractMembersUploadResults.find('.modal-body').html(htmlData);
                                modalContractMembersUploadResults.find('.modal-dialog').addClass("modal-xxl");
                                uploadMembersClose.html("Close");
                                modalContractMembersUploadResults.modal({backdrop: 'static', keyboard: false}).modal('show');
                            }
                            modalUploadMemberConfirmContractsResults.modal('hide');
                            modalMembershipFileUpload.modal('hide');
                            // show_toast_success_message(response.message, "bottomRight");
                        }
                    }
                }
            });

    },

    download_cm_list: function () {
        window.open('/'+DB_NAME+'/settings/download_cm_list', '_blank');
    },

};



$(function () {

    // triggers select when page loads (default: MTD)
    CONTRACTS_VIEW.update_perfomance_chart('');

    // DataTable
    dtContractViewAllContracts = tableContractViewAllContracts.DataTable({
        lengthMenu:     [[10, 20, 50, -1], [10, 20, 50, "All"]],
        dom: "<'row'<'col-sm-6'l><'col-sm-6'f>>" + "<'row'<'col-sm-12'tr>>" + "<'row dt_footer'<'col-sm-5' B><'col-sm-7'p>>",
        buttons: [
            {
                extend:    'excelHtml5',
                text:     '<i class="fa fa-file-excel-o">',
                titleAttr: 'Download Excel',
                className: 'btn btn-sm btn-default tt excel_dt_footer',
				title: '',
                action: newexportaction,
                filename: function(){
                var d = new Date();
                // var n = d.getTime();
                var n = get_current_date_in_ymdhms_for_export();
                return 'Contracts_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },

            },
            {
                extend:    'csvHtml5',
                text:      '<i class="fa fa-file-text-o"></i>',
                titleAttr: 'Download CSV',
				className: 'btn btn-sm btn-default tt csv_dt_footer',
				title: '',
                action: newexportaction,
                filename: function(){
                var d = new Date();
                // var n = d.getTime();
                var n = get_current_date_in_ymdhms_for_export();
                return 'Contracts_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },
            }
            ],
        scrollY:        SCROLLY,
        scrollX:        true,
        processing:     true,
        serverSide:     true,
        responsive:     true,
        deferRender:    true,
        autoWidth:      false,
        order:          [[1, 'desc']],
        language : {
            search:             "",
            searchPlaceholder:  "Search ...",
            loadingRecords:     "&nbsp;",
            processing:         SPINNER_LOADER,
        },
        // add datepicker dynamically to dt
        fnDrawCallback: function() {
            $('.datepicker').datepicker({
                autoclose: true,
                format: "mm/dd/yyyy"
            });
            $('.tt').tooltip({
                placement: 'top'
            })
        },
        ajax: {
            url:    `/${DB_NAME}/contracts/load_data`,
            type:   'POST',
            data: function ( d ) {
                return $.extend({}, d, {
                    "q_sf": inputContractsListStatusFilterID.val(),
                    "q_cf": inputContractsListCustomerFilterID.val(),
                });
            }
        },
        initComplete: function() {
            let $searchInput = $('#tableContractViewAllContracts_filter input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dtContractViewAllContracts.search( this.value ).draw();
                }
            });
        },
        columnDefs: [
            {
                "targets":      [0],
                "visible":      false,
                "searchable":   false,
            },
            {
                "targets":      [8],
                "orderable":    false,
                "searchable":   false,
            }
        ],
        columns: [
            {data: 'id'},
            {
                data:   'number',
                render: function(data, type, row) {
                    return '<span db="'+DB_NAME+'" target="/contracts/'+row["id"]+'/details">' +
                        '<a onclick="APP.execute_url($(this))" class="empower-color-blue">' + data + '</a>' +
                        '</span>'
                }
            },
            {data: 'description'},
            {data: 'customer_name'},
            {data: 'type'},
            {data: 'start_date'},
            {data: 'end_date'},
            {
                data: 'status_name',
                render: function(data, type, row) {
                    let html = '';
                    if (data === 'Active'){
                        html = '<span class="text-success">'+data+'</span>';
                    }else if (data === 'Inactive'){
                        html = '<span class="text-danger">'+data+'</span>';
                    }else{
                        html = '<span class="text-muted">'+data+'</span>';
                    }
                    return html
                }
            },
            {
                data: '',
                render: function(data, type, row) {
                    if(is_read_only_user) {
                        return '<span>' +
                            '<a onclick="APP.get_read_only_user_error()" class="tt" title="Edit">' +
                            '<i class="fa fa-pencil"></i>' +
                            '</a>' +
                            '</span>'
                    }else{
                        return '<span db="' + DB_NAME + '" target="/contracts/' + row["id"] + '/edit">' +
                            '<a onclick="APP.execute_url($(this))" class="tt" title="Edit">' +
                            '<i class="fa fa-pencil"></i>' +
                            '</a>' +
                            '</span>'
                    }
                }
            },
        ],
    });

    dtContractViewExpiringContracts = tableContractViewExpiringContracts.DataTable({
        lengthMenu:     [[10, 20, 50, -1], [10, 20, 50, "All"]],
        dom: "<'row'<'col-sm-6'l><'col-sm-6'f>>" + "<'row'<'col-sm-12'tr>>" + "<'row dt_footer'<'col-sm-5' B><'col-sm-7'p>>",
        buttons: [
            {
                extend:    'excelHtml5',
                text:     '<i class="fa fa-file-excel-o">',
                titleAttr: 'Download Excel',
                className: 'btn btn-sm btn-default tt excel_dt_footer',
				title: '',
                action: newexportaction,
                filename: function(){
                var d = new Date();
                // var n = d.getTime();
                var n = get_current_date_in_ymdhms_for_export();
                return 'Expiring_Contracts_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },
            },
            {
                extend:    'csvHtml5',
                text:      '<i class="fa fa-file-text-o"></i>',
                titleAttr: 'Download CSV',
				className: 'btn btn-sm btn-default tt csv_dt_footer',
				title: '',
                action: newexportaction,
                filename: function(){
                var d = new Date();
                // var n = d.getTime();
                var n = get_current_date_in_ymdhms_for_export();
                return 'Expiring_Contracts_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },
            }
            ],

        scrollY:        SCROLLY,
        scrollX:        true,
        processing:     true,
        serverSide:     true,
        responsive:     true,
        deferRender:    true,
        autoWidth:      false,
        order:          [[1, 'desc']],
        language : {
            search:             "",
            searchPlaceholder:  "Search ...",
            loadingRecords:     "&nbsp;",
            processing:         SPINNER_LOADER,
        },
        // add datepicker dynamically to dt
        fnDrawCallback: function() {
            $('.datepicker').datepicker({
                autoclose: true,
                format: "mm/dd/yyyy"
            });
            $('.tt').tooltip({
                placement: 'top'
            })
        },
        ajax: {
            url:    `/${DB_NAME}/contracts/load_expiring_data`,
            type:   'POST',
            data: function ( d ) {
                return $.extend({}, d, {
                    "q_sf": inputExpiringContractsListStatusFilterID.val(),
                    "q_cf": inputExpiringContractsListCustomerFilterID.val(),
                });
            }
        },
        initComplete: function() {
            let $searchInput = $('#tableContractViewExpiringContracts_filter input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dtContractViewExpiringContracts.search( this.value ).draw();
                }
            });
        },
        columnDefs: [
            {
                "targets":      [0],
                "visible":      false,
                "searchable":   false,
            },
            {
                "targets":      [8],
                "orderable":    false,
                "searchable":   false,
            }
        ],
        columns: [
            {data: 'id'},
            {
                data:   'number',
                render: function(data, type, row) {
                    return '<span db="'+DB_NAME+'" target="/contracts/'+row["id"]+'/details">' +
                        '<a onclick="APP.execute_url($(this))" class="empower-color-blue">' + data + '</a>' +
                        '</span>'
                }
            },
            {data: 'description'},
            {data: 'customer_name'},
            {data: 'type'},
            {data: 'start_date'},
            {data: 'end_date'},
            {
                data: 'status_name',
                render: function(data, type, row) {
                    let html = '';
                    if (data === 'Active'){
                        html = '<span class="text-success">'+data+'</span>';
                    }else if (data === 'Inactive'){
                        html = '<span class="text-danger">'+data+'</span>';
                    }else{
                        html = '<span class="text-muted">'+data+'</span>';
                    }
                    return html
                }
            },
            {
                data: '',
                render: function(data, type, row) {
                    if(is_read_only_user) {
                        return '<span>' +
                            '<a onclick="APP.get_read_only_user_error()" class="tt" title="Edit">' +
                            '<i class="fa fa-pencil"></i>' +
                            '</a>' +
                            '</span>'
                    }else {
                        return '<span db="' + DB_NAME + '" target="/contracts/' + row["id"] + '/edit">' +
                            '<a onclick="APP.execute_url($(this))" class="tt" title="Edit">' +
                            '<i class="fa fa-pencil"></i>' +
                            '</a>' +
                            '</span>'
                    }
                }
            },
        ],
    });

    dttableContractInformation = tableContractInformation.DataTable({
        lengthMenu:     [[10, 20, 50, -1], [10, 20, 50, "All"]],
        scrollY:        '35vh',
        dom: "<'row'<'col-sm-4'l><'col-sm-4'i><'col-sm-4'f>>" + "<'row'<'col-sm-12'tr>>" + "<'row dt_footer'<'col-sm-5' B><'col-sm-7'p>>",
        buttons: [
            {
                extend:    'excelHtml5',
                text:     '<i class="fa fa-file-excel-o">',
                titleAttr: 'Download Excel',
                className: 'btn btn-sm btn-default tt excel_dt_footer',
				title: '',
                action: newexportaction,
                filename: function(){
                var d = new Date();
                // var n = d.getTime();
                var n = get_current_date_in_ymdhms_for_export();
                return 'Contract_Information_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },

            },
            {
                extend:    'csvHtml5',
                text:      '<i class="fa fa-file-text-o"></i>',
                titleAttr: 'Download CSV',
				className: 'btn btn-sm btn-default tt csv_dt_footer',
				title: '',
                action: newexportaction,
                filename: function(){
                var d = new Date();
                // var n = d.getTime();
                var n = get_current_date_in_ymdhms_for_export();
                return 'Contract_Information_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },
            }
            ],
        processing:     true,
        serverSide:     true,
        responsive:     true,
        deferRender:    true,
        autoWidth:      false,
        order:          [[0, 'desc']],  // default ordered by 1st column
        language : {
            search:             "",
            searchPlaceholder:  "Search ...",
            loadingRecords:     "&nbsp;",
            processing:         SPINNER_LOADER,
            infoFiltered:       "",
        },
        ajax: {
            url:    `/${DB_NAME}/contracts/contracts_performance_information`,
            type:   'POST',
            data:  {}
        },
        initComplete: function() {
            let $searchInput = $('#tableContractInformation_filter input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dttableContractInformation.search( this.value ).draw();
                }
            });
        },
        columnDefs: [],
        columns: [
            {data: 'number'},
            {data: 'total_amount'},
            {data: 'units_sold'},
            {data: 'indirect_purchasers'},
        ],
    });

    // EA-1471 Contract Data Table Column Header Not Aligned with Data on My Contracts page.
    $(window).bind('resize', function () {
      dtContractViewAllContracts.draw();
      dttableContractInformation.draw();
   });
});