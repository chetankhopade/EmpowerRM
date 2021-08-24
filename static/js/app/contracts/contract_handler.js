// buttons
let btnCreateContractTypes = $('.btnCreateContractTypes');
let btnValidationContractOwnerEdit = $("#btnValidationContractOwnerEdit");

// modal
let modalValidationContractOwner = $("#modalValidationContractOwner");
let modalConfirmContractsUpdate = $("#modalConfirmContractsUpdate");

// Contract Form fields
let inputContractNumber = $("#inputContractNumber");
let selectContractStatus = $("#selectContractStatus");
let spanContractStatus = $("#spanContractStatus");
let selectContractCustomer = $("#selectContractCustomer");
let inputContractDescription = $("#inputContractDescription");
let inputContractStartDate = $("#inputContractStartDate");
let inputContractEndDate = $("#inputContractEndDate");
let selectContractEligibility = $("#selectContractEligibility");
let inputContractType = $("#inputContractType");
let inputMembershipValidation = $("#toggleMembershipValidation");
let inputCotValidation = $("#toggleCotValidation");
let actualContractEndDate = $("#actualContractEndDate");
let inputFutureContractEndDate = $("#inputFutureContractEndDate");

// CoT Logic
let spanCoTButtonName = $("#spanCoTButtonName");
let mdlEnableCoT = $("#mdlEnableCoT");
let modalAssignCotToContractAddItem = $("#modalAssignCotToContractAddItem");
let modalAssignCotToContract = $("#modalAssignCotToContract");
let divAssignCotToContractAddCoTContainer = $("#divAssignCotToContractAddCoTContainer");

// Aliases
let modalAssignAliasToContract = $("#modalAssignAliasToContract");
let modalAssignAliasToContractAddItem = $("#modalAssignAliasToContractAddItem");
let divAssignAliasToContractAddAliasContainer = $("#divAssignAliasToContractAddAliasContainer");

// Tables and Datatable
let tableAssignCotToContract = $("#tableAssignCotToContract");
let dtAssignCotToContract = "";

let tableAssignAliasToContract = $("#tableAssignAliasToContract");
let dtAssignAliasToContract = "";

let tableContractActiveContractLineItems = $("#tableContractActiveContractLineItems");
let tableContractActiveManageServer = $("#tableContractActiveManageServer");
let tableContractActiveManageMembership = $('#tableContractActiveManageMembership');
let dtContractActiveContractLineItem;
let dtContractActiveManageServer;
let dtContractActiveManageMembership;
let checked_contract_line_items = [];
let checked_contract_server_line_items = [];
let checked_contract_membership_line_items = [];
let CONTRACT_HANDLER = {

    name: 'CONTRACT_HANDLER',

    new_cots_items: [],

    new_contract_alias_items: [],

    open_active_contracts_modal:function(){

        modalConfirmContractsUpdate.modal('show');
        tableContractActiveContractLineItems.resize();
        $('#step2').hide();
        $('#step3').hide();
        //dtContractActiveContractLineItem.ajax.reload();
        //CONTRACT_HANDLER.load_active_contract_line_items();

    },
    hide_active_contracts_modal:function (){
        modalConfirmContractsUpdate.modal('hide');
    },
    load_active_contract_line_items:function (){

            if (dtContractActiveContractLineItem !== undefined && dtContractActiveContractLineItem !== '') {
            dtContractActiveContractLineItem.destroy();
            }
            dtContractActiveContractLineItem = tableContractActiveContractLineItems.DataTable({
            lengthMenu:     [[25, 50, 100, 250, -1], [25, 50, 100, 250, "All"]],
            scrollY:        '55vh',
            processing:     true,
            serverSide:     true,
            responsive:     true,
            paging    : false,
            order:          [[1, 'desc']],  // default ordered by 1st column
            language : {
                search:             "",
                searchPlaceholder:  "Search ...",
                processing:         SPINNER_LOADER,
            },
            initComplete: function (settings, json) {
                let $searchInput = $('#tableContractActiveContractLineItems input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dtContractActiveContractLineItem.search( this.value ).draw();
                }
            });
            },
            fnDrawCallback: function() {
                // remove Schedule
            },
            ajax: {
                url:    `/${DB_NAME}/contracts/${CONTRACT_ID}/tab_active_contract/load_contract_line_items`,
                type:   'POST',
                data: function ( d ) {
                return $.extend({}, d, {
                    "contract_new_end_date": $('#inputContractEndDate').val(),
                    "contract_end_date": $('#actualContractEndDate').val(),
                });
                }
            },
            'columnDefs': [{
                 'targets': 0,
                 'searchable': false,
                 'orderable': false,
                 'className': 'dt-body-center',
                 'render': function (data, type, full, row){
                     let checked = "checked";
                     for (let i=0; i<checked_contract_line_items.length;i++){
                            if (checked_contract_line_items[i].clid === row["id"]){
                                checked = "checked";
                                break;
                            }
                        }
                     return '<label class="md-check"><input type="checkbox" name="LineItemsid[]" id="chkb_'+full["id"]+'" data-value="'+full["id"]+'" onchange="CONTRACT_HANDLER.contract_line_item_update_checkboxes_array($(this))" class="checkboxContractManagerMembership" '+checked+'/><i class="blue"></i></label>'
                 }
              }],
            columns: [
            {data: ''},
            {data: 'item__ndc'},
            {data: 'item__name'},
            {
                data: 'price',
                render : function(data, type, row) {
                    return data.toFixed(2);
                }
            },
            {
                data: 'start_date',
                render : function(data, type, row) {
                    return data;
                }
            },
            {
                data: 'end_date',
                render : function(data, type, row) {
                    return data;
                }
            },
            {
                data: 'status',
                render : function(data, type, row) {

                     return data;
                }
            },

        ],
            });

        },
    load_acive_contract_server_lines:function (){
        if (dtContractActiveManageServer !== undefined && dtContractActiveManageServer !== '') {
            dtContractActiveManageServer.destroy();
        }
            dtContractActiveManageServer = tableContractActiveManageServer.DataTable({
            lengthMenu:     [[-1], ["All"]],
            scrollY:        '15vh',
            processing:     true,
            serverSide:     true,
            responsive:     true,
            paging    : false,
            order:          [[1, 'desc']],  // default ordered by 1st column
            language : {
                search:             "",
                searchPlaceholder:  "Search ...",
                processing:         SPINNER_LOADER,
            },
            // add datepicker dynamically to dt
            fnDrawCallback: function() {},
            ajax: {
                url:    `/${DB_NAME}/contracts/${CONTRACT_ID}/tab_manage_servers/active_server_load_data`,
                type:   'POST',
                data: {
                    "contract_end_date": $('#actualContractEndDate').val()
                }
            },
            initComplete: function() {
                let $searchInput = $('#tableContractActiveManageServer_filter input');
                $searchInput.unbind();
                $searchInput.bind('keyup', function(e) {
                    if(this.value.length === 0 || this.value.length >= 3) {
                        dtContractActiveManageServer.search( this.value ).draw();
                    }
                });
            },
            'columnDefs': [{
                 'targets': 0,
                 'searchable': false,
                 'orderable': false,
                 'className': 'dt-body-center',
                 'render': function (data, type, full, row){
                     let checked = "checked";
                     for (let i=0; i<checked_contract_server_line_items.length;i++){
                            if (checked_contract_server_line_items[i].sid === row["id"]){
                                checked = "checked";
                                break;
                            }
                        }
                     return '<label class="md-check"><input type="checkbox" name="serverid[]" id="server_chkb_'+full["id"]+'" data-value="'+full["id"]+'" onchange="CONTRACT_HANDLER.contract_server_update_checkboxes_array($(this))" class="checkboxContractManagerMembership" '+checked+'/><i class="blue"></i></label>'
                 }
              }],
            columns: [
                {data: ''},
                {
                    data: 'name',
                    render : function(data, type, row) {
                        return data;
                    }
                },
                {
                    data: 'start_date',
                    render : function(data, type, row) {
                        return data
                    }
                },
                {
                    data: 'end_date',
                    render : function(data, type, row) {
                        return data
                    }
                },
                {data: 'address'},
                {data: 'city'},
                {data: 'state'},
                {data: 'zip_code'},
            ],
        });
    },
    load_active_membership_line_items:function (){

        if (dtContractActiveManageMembership !== undefined && dtContractActiveManageMembership !== '') {
            dtContractActiveManageMembership.destroy();
        }
        dtContractActiveManageMembership = tableContractActiveManageMembership.DataTable({
            lengthMenu:     [[25,100,150,-1], [25,100,150,"All"]],
            scrollY:        '15vh',
            processing:     true,
            serverSide:     true,
            responsive:     true,
            paging    : false,
            order:          [[1, 'desc']],  // default ordered by 1st column
            language : {
                search:             "",
                searchPlaceholder:  "Search ...",
                processing:         SPINNER_LOADER,
            },
            // add datepicker dynamically to dt
            fnDrawCallback: function() {},
            ajax: {
                url:    `/${DB_NAME}/contracts/${CONTRACT_ID}/tab_manage_membership/active_membership_load_data`,
                type:   'POST',
                data: {
                    "contract_end_date": $('#actualContractEndDate').val()
                }
            },
            initComplete: function() {
                let $searchInput = $('#tableContractActiveManageMembership_filter input');
                $searchInput.unbind();
                $searchInput.bind('keyup', function(e) {
                    if(this.value.length === 0 || this.value.length >= 3) {
                        dtContractActiveManageMembership.search( this.value ).draw();
                    }
                });
            },
            'columnDefs': [{
                 'targets': 0,
                 'searchable': false,
                 'orderable': false,
                 'className': 'dt-body-center',
                 'render': function (data, type, full, row){
                     let checked = "checked";
                     for (let i=0; i<checked_contract_membership_line_items.length;i++){
                            if (checked_contract_membership_line_items[i].mid === row["id"]){
                                checked = "checked";
                                break;
                            }
                        }
                     return '<label class="md-check"><input type="checkbox" name="membershipid[]" id="membership_chkb_'+full["id"]+'" data-value="'+full["id"]+'" onchange="CONTRACT_HANDLER.contract_membership_update_checkboxes_array($(this))" class="checkboxContractManagerMembership" '+checked+'/><i class="blue"></i></label>'
                 }
              }],
            columns: [
                {data: ''},
                {data: 'location_number'},
                {data: 'company_name'},
                {data: 'bid_340'},
                {
                    data: 'start_date',
                    render : function(data, type, row) {
                        return data;
                    }
                },
                {
                    data: 'end_date',
                    render : function(data, type, row) {
                        return data;
                    }
                },
                {
                data: 'status',
                render : function(data, type, row) {

                    return data;
                }
              },
            ],
        });
    },
    contract_line_item_update_checkboxes_array: function(elem){
        let id_str = elem.attr('id');
        id = id_str.replace("chkb_","");

         $('input[name=\'LineItemsid[]\']').each(function () {
                    if ($(this).is(':checked') ) {
                        if($(this).attr('data-value')) {
                            checked_contract_line_items.push({"clid": $(this).attr('data-value')});
                        }
                    }
        });
        if (elem.is(':checked')){
            checked_contract_line_items.push({"clid":id});
        }else{
            // If un-checked - Remove id from array
           checked_contract_line_items = checked_contract_line_items.filter(function(itm){ return itm.clid !== id; });
        }
    },
    contract_server_update_checkboxes_array: function(elem){
        let id_str = elem.attr('id');
        id = id_str.replace("server_chkb_","");
        $('input[name=\'serverid[]\']').each(function () {
                    if ($(this).is(':checked') ) {
                        if($(this).attr('data-value')) {
                            checked_contract_server_line_items.push({"sid": $(this).attr('data-value')});
                        }
                    }
                });
        if (elem.is(':checked')){
            checked_contract_server_line_items.push({"sid":id});
        }else{
            // If un-checked - Remove id from array
           checked_contract_server_line_items = checked_contract_server_line_items.filter(function(itm){ return itm.sid !== id; });
        }
    },
    contract_membership_update_checkboxes_array: function(elem){
        let id_str = elem.attr('id');
        id = id_str.replace("membership_chkb_","");
        $('input[name=\'membershipid[]\']').each(function () {
                    if ($(this).is(':checked') ) {
                        if($(this).attr('data-value')) {
                            checked_contract_membership_line_items.push({"mid": $(this).attr('data-value')});
                        }
                    }
                });
        if (elem.is(':checked')){
            checked_contract_membership_line_items.push({"mid":id});
        }else{
            // If un-checked - Remove id from array
           checked_contract_membership_line_items = checked_contract_membership_line_items.filter(function(itm){ return itm.mid !== id; });
        }
    },
    continue: function(step){
        if(step == '2'){
            $('#step1').hide();
            $('#step3').hide();
            $('#step2').show();
           tableContractActiveManageServer.resize()
        }else if(step == '3'){
            $('#step1').hide();
            $('#step2').hide();
            $('#step3').show();
           tableContractActiveManageMembership.resize()
        }
    },
    updateback: function (backstep){
          if(backstep == '1'){
            $('#step1').show();
            $('#step2').hide();
            $('#step3').hide();
            tableContractActiveContractLineItems.resize()
        }else if(backstep == '2'){
            $('#step1').hide();
            $('#step2').show();
            $('#step3').hide();
            tableContractActiveManageServer.resize()
        }
    },
    // Create or Edit
    // source = required parameter cause we are calling this from modal on contract upload
    submit: function (action, source="", contract_number="",is_cancel=false,skip_steps=true){
        if(source === "membership_missing_modal"){
            inputContractNumber = $("#inputContractNumber");
            selectContractStatus = $("#selectContractStatus");
            spanContractStatus = $("#spanContractStatus");
            selectContractCustomer = $("#selectContractCustomer");
            inputContractDescription = $("#inputContractDescription");
            inputContractStartDate = $("#inputContractStartDate");
            inputContractEndDate = $("#inputContractEndDate");
            selectContractEligibility = $("#selectContractEligibility");
            inputContractType = $("#inputContractType");
            inputMembershipValidation = $("#toggleMembershipValidation");
            inputCotValidation = $("#toggleCotValidation");
        }

        if (inputContractStartDate.val() && inputContractEndDate.val()){
            let is_valid = validate_dates_with_month_first(inputContractStartDate, inputContractEndDate, false);
            if(!is_valid) {
                show_toast_error_message("Contract End date cannot be earlier than start date");
                return false;
            }
        }

        if (!inputContractNumber.val()){
            show_toast_error_message("Contract Number is required");
            return false;
        }

        if (!selectContractCustomer.val()){
            show_toast_error_message("Customer is required");
            return false;
        }
        let is_line_item_update = true;
        if(is_cancel){
            is_line_item_update = false;
            CONTRACT_HANDLER.hide_active_contracts_modal();
        }

        if (action === 'edit' && inputFutureContractEndDate.val() == "1" && skip_steps){
            CONTRACT_HANDLER.open_active_contracts_modal();
            return false;
        }
        let url = `/${DB_NAME}/contracts/create`;
        if (action === 'edit'){
            url = `/${DB_NAME}/contracts/${CONTRACT_ID}/edit`;
        }

        let member_eval = 0;
        if($(inputMembershipValidation).prop("checked") === true){
            member_eval = 1;
        }
        let cot_eval = 0;
        if($(inputCotValidation).prop("checked") === true){
            cot_eval = 1;
        }
        let contract_line_item = [];
        let contract_server_line_items = [];
        let contract_membership_line_items = [];
        contract_line_item = checked_contract_line_items;
        contract_membership_line_items = checked_contract_membership_line_items;
        contract_server_line_items = checked_contract_server_line_items;
        if(checked_contract_line_items.length==0 && is_line_item_update == true) {
                $('input[name=\'LineItemsid[]\']').each(function () {
                    if ($(this).is(':checked') ) {
                        if($(this).attr('data-value')) {
                            checked_contract_line_items.push({"clid": $(this).attr('data-value')});
                        }
                    }
                });
                contract_line_item = checked_contract_line_items;

        }
        if(checked_contract_server_line_items.length==0 && is_line_item_update == true) {
                $('input[name=\'serverid[]\']').each(function () {
                    if ($(this).is(':checked') ) {
                        if($(this).attr('data-value')) {
                            checked_contract_server_line_items.push({"sid": $(this).attr('data-value')});
                        }
                    }
                });
                contract_server_line_items = checked_contract_server_line_items;
        }
        if(checked_contract_membership_line_items.length==0 && is_line_item_update == true) {

                $('input[name=\'membershipid[]\']').each(function () {
                    if ($(this).is(':checked') ) {
                        if($(this).attr('data-value')) {
                            checked_contract_membership_line_items.push({"mid": $(this).attr('data-value')});
                        }
                    }
                });
                contract_membership_line_items = checked_contract_membership_line_items;
        }

        $.ajax({
            url: url,
            data: {
                'number': inputContractNumber.val(),
                'description': inputContractDescription.val(),
                'customer_id': selectContractCustomer.val(),
                'start_date': inputContractStartDate.val(),
                'end_date': inputContractEndDate.val(),
                'eligibility': selectContractEligibility.val(),
                'status': selectContractStatus.val(),
                // 'cots': inputContractCOTs.val(),
                'ctype': inputContractType.val(),
                'member_eval':member_eval,
                'cot_eval':cot_eval,
                'is_line_item_update': is_line_item_update,
                'contract_line_item': JSON.stringify(contract_line_item),
                'contract_server_line_items': JSON.stringify(contract_server_line_items),
                'contract_membership_line_items': JSON.stringify(contract_membership_line_items)
            },
            type: "POST",
            dataType: "json",
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
                if(action === 'edit'){
                    CONTRACT_HANDLER.hide_active_contracts_modal();
                }
                APP.show_app_loader();
            },
            success: function (response) {
                    
                if(response.result === 'ok') {
                    // send success message
                    //dtContractActiveContract.ajax.reload();
                    show_toast_success_message(response.message, 'topRight');
                    if (source === "contract_view_missing_modal"){
                        let html = CONTRACTS_VIEW.draw_upload_missing_table(missing_contract_list, missing_item_list, contract_number);
                        $("#addMissingContract").modal('hide');
                        $("#modalUploadUpdatesContractsResults").find('.modal-body').html(html);
                    }
                    else if(source === "membership_missing_modal"){
                        let html = CONTRACT_Membership.draw_upload_missing_table(missing_contract_list, contract_number);
                        $("#addMissingContract").modal('hide');
                        $("#modalContractMembersUploadResults").find('.modal-body').html(html);
                    }
                    else{

                        // redirect or reload
                       setTimeout(function () {
                            location.href = response.redirect_url;
                        }, 300);
                    }


                }else{
                    if (response.extradata){
                        let ex_data = response.extradata;
                        modalValidationContractOwner.find(".modal-body").html(
                            "A direct contract for that customer already exists.  " +
                            "Only one Direct contract per customer is allowed. <br/>" +
                            "Please edit the existing contract " + ex_data.existing_contract_no +
                            " or alter the contract you were working on.");
                        btnValidationContractOwnerEdit.attr('href', ex_data.edit_url).html("Edit " + ex_data.existing_contract_no);
                        modalValidationContractOwner.modal('show');
                    }else{
                        show_toast_error_message(response.message);
                    }
                }
            },
            complete: function () {
                APP.hide_app_loader();
            },
            error: function (response) {
                show_toast_error_message(response.message);
            }
        });
    },

    // set contract type
    set_contract_type: function(elem){

        // update style in buttons (to mark it as active)
        btnCreateContractTypes.removeClass('btn-warning').addClass('btn-default');
        elem.addClass('btn-warning');

        // assign the value to the hidden input
        $("#inputContractType").val(elem.attr('value'));

        // ticket 917 If contract type Direct is selected, do not show CoT and Membership fields (disabled)
        if (inputContractType.attr('value') === '1'){
            inputMembershipValidation.prop('checked', false).prop('disabled', true);
            inputCotValidation.prop('checked', false).prop('disabled', true);
            spanCoTButtonName.parent().removeClass('btn-warning').addClass('btn-secondary text-white').prop('disabled', true);
        }else {
            inputMembershipValidation.prop('disabled', false);
            inputCotValidation.prop('disabled', false);
            spanCoTButtonName.parent().removeClass('btn-secondary text-white').addClass('btn-warning').prop('disabled', false);
        }
    },

    // COT Section (Enable Cot and Show Current Cot related with contract)
    enable_cot: function () {

        $.ajax({
            url: `/${DB_NAME}/settings`,
            type: "POST",
            data: {
                'opt': 'class_of_trade_validation_enabled',
                'value': 1
            },
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            },
            success: function (response) {
                if (response.result === 'ok'){
                    mdlEnableCoT.modal('hide');
                    spanCoTButtonName.html('Manage');
                    modalAssignCotToContract.modal('show');
                    show_toast_success_message(response.message, 'bottomRight');
                }else{
                    show_toast_error_message(response.message);
                }
            },
            error: function () {
                show_toast_error_message('Internal Error');
            }
        });
    },

    // Cot Manager - load data
    load_active_cots: function () {
        if (dtAssignCotToContract !== undefined && dtAssignCotToContract !== '') {
            dtAssignCotToContract.destroy();
        }
        dtAssignCotToContract = tableAssignCotToContract.DataTable({
            lengthMenu:     [[-1], ["All"]],
            scrollY:        '40vh',
            processing:     true,
            responsive:     true,
            info:           false,
            order:          [[1, 'asc']],
            language : {
                search:             "",
                searchPlaceholder:  "Search ...",
                loadingRecords:     "",
                processing:         SPINNER_LOADER,
            },
            // add datepicker dynamically to dt
            fnDrawCallback: function() {
                // remove CoT
                $(".btnRemoveCoT").click(function () {
                    let elem = $(this);
                    let cotid = elem.attr('cotid');
                    let loadingText = '<i class="fa fa-circle-o-notch fa-spin"></i> Removing...';
                    let originalText = elem.html();
                    $.ajax({
                        url: `/${DB_NAME}/contracts/${CONTRACT_ID}/cots/${cotid}/remove`,
                        type: "POST",
                        data: {},
                        beforeSend: function(xhr, settings) {
                            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                            }
                            elem.addClass('disabled').html(loadingText);
                        },
                        success: function (response) {
                            if (response.result === 'ok'){
                                show_toast_success_message(response.message, 'bottomRight');
                                CONTRACT_HANDLER.load_active_cots();
                            }else{
                                show_toast_error_message(response.message);
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
                });
            },
            ajax: {
                url:    `/${DB_NAME}/contracts/${CONTRACT_ID}/cots/load_active_cots`,
                type:   'POST',
                data: {}
            },
            initComplete: function() {
                let $searchInput = $('#tableAssignCotToContract_filter input');
                $searchInput.unbind();
                $searchInput.bind('keyup', function(e) {
                    if(this.value.length === 0 || this.value.length >= 3) {
                        dtAssignCotToContract.search( this.value ).draw();
                    }
                });
            },
            columnDefs: [
                {
                    "targets": [0],
                    "visible": false,
                    "searchable": false,
                    "orderable": false,
                },
                {
                    "targets": [3],
                    "searchable": false,
                    "orderable": false,
                }
            ],
            columns: [
                {data: 'id'},
                {
                    data: 'name',
                    orderDataType: "dom-text",
                    type: 'string',
                    render : function(data, type, row) {
                        return  '<div class="form-group m-1">' +
                            '<input type="text" class="inputCoTName form-control font-12" value="'+data+'"/>' +
                            '</div>';
                    }
                },
                {
                    data: 'description',
                    orderDataType: "dom-text",
                    type: 'string',
                    render : function(data, type, row) {
                        return  '<div class="form-group m-1">' +
                            '<input type="text" class="inputCoTDescription form-control font-12" value="'+data+'"/>' +
                            '</div>';
                    }
                },
                {
                    data: '',
                    class: 'text-center',
                    render : function(data, type, row) {
                        if (row['is_assigned_to_contract'] === 'true'){
                            return  '<label class="md-check">' +
                                '<input type="checkbox" class="checkboxCoTEnabled" checked />' +
                                '<i class="blue"></i>' +
                                '</label>'
                        }else{
                            return  '<label class="md-check">' +
                                '<input type="checkbox" class="checkboxCoTEnabled" />' +
                                '<i class="blue"></i>' +
                                '</label>'
                        }
                    }
                },
                // Ticket 960 Remove icons from CoT Assign to Contract Modal
                // {
                //     data: '',
                //     class: 'text-center',
                //     render : function(data, type, row) {
                //         return '<div class="dropleft">' +
                //                     '<a href="#" id="dropdownRemoveCoT" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
                //                         '<i class="fas fa-trash"></i>' +
                //                     '</a>' +
                //                     '<div class="dropdown-menu" aria-labelledby="dropdownRemoveCoT">' +
                //                         '<div class="dropdown-item">' +
                //                             'Are you sure you want to delete this entry: <span class="_700">' + row["name"] + '?</span>' +
                //                         '</div>' +
                //                         '<div class="dropdown-item">' +
                //                             '<a cotid="'+row["id"]+'" class="btn btn-warning btn-sm width-80px btnRemoveCoT"> Yes</a>' +
                //                             '<a class="btn btn-primary btn-sm ml-2 width-80px">No</a>' +
                //                         '</div>' +
                //                     '</div>' +
                //                 '</div>';
                //     }
                // },
            ],
        });
        $('#tableAssignCotToContract_paginate').css("display", "none");
        $('#tableAssignCotToContract_length').html(
            '<a class="btn btn-warning" data-toggle="modal" data-target="#modalAssignCotToContractAddItem">' +
            '<i class="fa fa-plus font-9"></i> ' +
            '<span class="font-11">Add Item</span>' +
            '</a>');
    },

    save_cots: function (elem) {
        let loadingText = '<i class="fa fa-circle-o-notch fa-spin"></i> Saving...';
        let originalText = elem.html();

        let cots = [];
        $('#tableAssignCotToContract > tbody  > tr').each(function() {
            let cotID = $(this).attr('id');
            let cotName = $(this).find('.inputCoTName').val();
            let cotDescription = $(this).find('.inputCoTDescription').val();
            let cotEnabled = 1 ? $(this).find('.checkboxCoTEnabled').is(':checked') : 0;

            if (cotName) {
                cots.push({
                    "id": cotID,
                    "name": cotName,
                    "description": cotDescription,
                    "enabled": cotEnabled,
                });
            }
        });

        $.ajax({
            url: `/${DB_NAME}/contracts/${CONTRACT_ID}/cots/save`,
            type: "POST",
            data: {
                "cots": JSON.stringify(cots)
            },
            dataType: "json",
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
                elem.addClass('disabled').html(loadingText);
            },
            success: function (response) {
                if(response.result === 'ok') {
                    modalAssignCotToContract.modal('hide');
                    show_toast_success_message(response.message, 'bottomRight');
                }else{
                    show_toast_error_message(response.message, 'bottomRight');
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

    update_input_border_color: function () {
        $(".inputCoTNameAddItem").each(function () {
            let elem = $(this);
            if (elem.val() && elem.val() !== undefined && elem.val() !== ' '){
                elem.removeClass('border-red');
                elem.addClass('border-green');
            }else{
                elem.removeClass('border-green');
                elem.addClass('border-red');
            }
        });
        $(".inputCoTDescriptionAddItem ").each(function () {
            let elem = $(this);
            if (elem.val() && elem.val() !== undefined && elem.val() !== ' '){
                elem.removeClass('border-red');
                elem.addClass('border-green');
            }else{
                elem.removeClass('border-green');
                elem.addClass('border-red');
            }
        });
    },

    remove_new_item_inputs: function (elem) {
        let index = elem.attr('index');
        if (CONTRACT_HANDLER.new_cots_items.length === 0){
            show_toast_warning_message('At least one row is required')
        }else{
            CONTRACT_HANDLER.new_cots_items.splice(index, 1);
            CONTRACT_HANDLER.update_new_cot_items();
        }
    },

    update_new_cot_items: function() {

        divAssignCotToContractAddCoTContainer.empty();

        if (CONTRACT_HANDLER.new_cots_items.length === 0){
            divAssignCotToContractAddCoTContainer.append(
                '<div class="row my-2" index="0">' +
                '<div class="col-5">' +
                '<input type="text" class="inputCoTNameAddItem form-control font-12" onblur="CONTRACT_HANDLER.update_input_border_color($(this))" value=""/>' +
                '</div>' +
                '<div class="col-6">' +
                '<input type="text" class="inputCoTDescriptionAddItem form-control font-12" onblur="CONTRACT_HANDLER.add_new_item_inputs($(this))" value=""/>' +
                '</div>' +
                '<div class="col">' +
                '<a onclick="CONTRACT_HANDLER.remove_new_item_inputs($(this));" index="0">' +
                '<i class="fa fa-times text-danger"></i>' +
                '</a>' +
                '</div>' +
                '</div>'
            );

        }else{
            for (let i in CONTRACT_HANDLER.new_cots_items) {
                let item = CONTRACT_HANDLER.new_cots_items[i];
                divAssignCotToContractAddCoTContainer.append(
                    '<div class="row my-2" index="'+i+'">' +
                    '<div class="col-5">' +
                    '<input type="text" class="inputCoTNameAddItem form-control font-12" onblur="CONTRACT_HANDLER.update_input_border_color($(this))" value="'+item["name"]+'"/>' +
                    '</div>' +
                    '<div class="col-6">' +
                    '<input type="text" class="inputCoTDescriptionAddItem form-control font-12" onblur="CONTRACT_HANDLER.add_new_item_inputs($(this))" value="'+item["description"]+'"/>' +
                    '</div>' +
                    '<div class="col">' +
                    '<a onclick="CONTRACT_HANDLER.remove_new_item_inputs($(this));" index="'+i+'">' +
                    '<i class="fa fa-times text-danger"></i>' +
                    '</a>' +
                    '</div>' +
                    '</div>'
                );
            }
            let index = CONTRACT_HANDLER.new_cots_items.length;
            divAssignCotToContractAddCoTContainer.append(
                '<div class="row my-2" index="'+index+'">' +
                '<div class="col-5">' +
                '<input type="text" class="inputCoTNameAddItem form-control font-12" onblur="CONTRACT_HANDLER.update_input_border_color($(this))" value=""/>' +
                '</div>' +
                '<div class="col-6">' +
                '<input type="text" class="inputCoTDescriptionAddItem form-control font-12" onblur="CONTRACT_HANDLER.add_new_item_inputs($(this))" value=""/>' +
                '</div>' +
                '<div class="col">' +
                '<a onclick="CONTRACT_HANDLER.remove_new_item_inputs($(this));" index="'+index+'">' +
                '<i class="fa fa-times text-danger"></i>' +
                '</a>' +
                '</div>' +
                '</div>'
            );
        }
        CONTRACT_HANDLER.update_input_border_color();
    },

    add_new_item_inputs: function (elem) {
        let rowParent = elem.parent().parent();
        let inputCoTName = rowParent.find('.inputCoTNameAddItem');
        if (parseInt(rowParent.attr('index')) === parseInt(CONTRACT_HANDLER.new_cots_items.length)) {
            if (elem.val() && elem.val() !== undefined && inputCoTName.val() && inputCoTName.val() !== undefined){
                CONTRACT_HANDLER.new_cots_items.push({
                    name: inputCoTName.val(),
                    description: elem.val(),
                });
                CONTRACT_HANDLER.update_new_cot_items();
            }
        }
    },

    add_new_cots: function () {
        if (CONTRACT_HANDLER.new_cots_items.length !== 0){
            $.ajax({
                url: `/${DB_NAME}/contracts/${CONTRACT_ID}/cots/add_new_cots`,
                type: "POST",
                data: {
                    "cots": JSON.stringify(CONTRACT_HANDLER.new_cots_items)
                },
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    if(response.result === 'ok') {
                        modalAssignCotToContractAddItem.modal('hide');
                        CONTRACT_HANDLER.load_active_cots();
                        show_toast_success_message(response.message, 'bottomRight');
                    }else{
                        show_toast_error_message(response.message, 'topCenter');
                    }
                },
            });

        }
    },
    // END COT Section


    // ALIAS Section

    load_aliases: function () {
        if (dtAssignAliasToContract !== undefined && dtAssignAliasToContract !== '') {
            dtAssignAliasToContract.destroy();
        }
        dtAssignAliasToContract = tableAssignAliasToContract.DataTable({
            lengthMenu:     [[-1], ["All"]],
            scrollY:        '40vh',
            processing:     true,
            responsive:     true,
            info:           false,
            order:          [[1, 'asc']],
            language : {
                search:             "",
                searchPlaceholder:  "Search ...",
                loadingRecords:     "",
                processing:         SPINNER_LOADER,
            },
            fnDrawCallback: function() {
                // remove CoT
                $(".btnRemoveAlias").click(function () {
                    let elem = $(this);
                    let caid = elem.attr('caid');
                    let loadingText = '<i class="fa fa-circle-o-notch fa-spin"></i> Removing...';
                    let originalText = elem.html();
                    $.ajax({
                        url: `/${DB_NAME}/contracts/${CONTRACT_ID}/contract_aliases/${caid}/remove`,
                        type: "POST",
                        data: {},
                        beforeSend: function(xhr, settings) {
                            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                            }
                            elem.addClass('disabled').html(loadingText);
                        },
                        success: function (response) {
                            if (response.result === 'ok'){
                                show_toast_success_message(response.message, 'bottomRight');
                                CONTRACT_HANDLER.load_aliases();
                            }else{
                                show_toast_error_message(response.message);
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
                });
            },
            ajax: {
                url:    `/${DB_NAME}/contracts/${CONTRACT_ID}/contract_aliases/load_aliases`,
                type:   'POST',
                data: {}
            },
            initComplete: function() {
                let $searchInput = $('#tableAssignAliasToContract_filter input');
                $searchInput.unbind();
                $searchInput.bind('keyup', function(e) {
                    if(this.value.length === 0 || this.value.length >= 3) {
                        dtAssignAliasToContract.search( this.value ).draw();
                    }
                });
            },
            columnDefs: [
                {
                    "targets": [0],
                    "visible": false,
                    "searchable": false,
                    "orderable": false,
                },
                {
                    "targets": [2],
                    "searchable": false,
                    "orderable": false,
                }
            ],
            columns: [
                {data: 'id'},
                {
                    data: 'alias',
                    orderDataType: "dom-text",
                    type: 'string',
                    render : function(data, type, row) {
                        return  '<div class="form-group m-1">' +
                            '<input type="text" class="inputAlias form-control font-12" value="'+data+'"/>' +
                            '</div>';
                    }
                },
                {
                    data: '',
                    class: 'text-center',
                    render : function(data, type, row) {
                        return '<div class="dropleft">' +
                            '<a href="#" id="dropdownRemoveAlias" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
                            '<i class="fas fa-trash"></i>' +
                            '</a>' +
                            '<div class="dropdown-menu" aria-labelledby="dropdownRemoveAlias">' +
                            '<div class="dropdown-item">' +
                            'Are you sure you want to delete this entry: <span class="_700">' + row["alias"] + '?</span>' +
                            '</div>' +
                            '<div class="dropdown-item">' +
                            '<a caid="'+row["id"]+'" class="btn btn-warning btn-sm width-80px btnRemoveAlias"> Yes</a>' +
                            '<a class="btn btn-primary btn-sm ml-2 width-80px">No</a>' +
                            '</div>' +
                            '</div>' +
                            '</div>';
                    }
                },
            ],
        });
        $('#tableAssignAliasToContract_paginate').css("display", "none");
        $('#tableAssignAliasToContract_length').html(
            '<a class="btn btn-warning" data-toggle="modal" data-target="#modalAssignAliasToContractAddItem">' +
            '<i class="fa fa-plus font-9"></i> ' +
            '<span class="font-11">Add Alias</span>' +
            '</a>');
    },

    save_aliases: function (elem) {
        let loadingText = '<i class="fa fa-circle-o-notch fa-spin"></i> Saving...';
        let originalText = elem.html();

        let aliases = [];
        $('#tableAssignAliasToContract > tbody  > tr').each(function() {
            let caID = $(this).attr('id');
            let caAlias = $(this).find('.inputAlias').val();
            if (caAlias) {
                aliases.push({
                    "id": caID,
                    "alias": caAlias,
                });
            }
        });

        let valueArr = aliases.map(function(item){ return item.alias });
        let isDuplicate = valueArr.some(function(item, idx){
            return valueArr.indexOf(item) !== idx
        });

        if (isDuplicate) {
            show_toast_error_message('You have duplicated aliases in the list', 'topCenter');
        }else{
            $.ajax({
                url: `/${DB_NAME}/contracts/${CONTRACT_ID}/contract_aliases/save`,
                type: "POST",
                data: {
                    "aliases": JSON.stringify(aliases)
                },
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                    elem.addClass('disabled').html(loadingText);
                },
                success: function (response) {
                    if(response.result === 'ok') {

                        if(response.error == "y") {
                            show_toast_error_message(response.message, 'topCenter');
                        }
                        else{
                            modalAssignAliasToContract.modal('hide');
                            APP.show_app_loader();
                            setTimeout(function () {
                                location.href = response.redirect_url;
                            }, 200);
                            show_toast_success_message(response.message, 'bottomRight');
                        }
                    }else{
                        show_toast_error_message(response.message, 'bottomRight');
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
        }
    },

    update_input_border_color_for_aliases: function () {
        $(".inputContractAliasAddItem ").each(function () {
            let elem = $(this);
            if (elem.val() && elem.val() !== undefined && elem.val() !== ' '){
                elem.removeClass('border-red');
                elem.addClass('border-green');
            }else{
                elem.removeClass('border-green');
                elem.addClass('border-red');
            }
        });
    },

    remove_new_alias_inputs: function (elem) {
        let index = elem.attr('index');
        if (CONTRACT_HANDLER.new_contract_alias_items.length === 0){
            show_toast_warning_message('At least one row is required')
        }else{
            CONTRACT_HANDLER.new_contract_alias_items.splice(index, 1);
            CONTRACT_HANDLER.update_new_contract_alias_items();
        }
    },

    update_new_contract_alias_items: function() {

        divAssignAliasToContractAddAliasContainer.empty();

        if (CONTRACT_HANDLER.new_contract_alias_items.length === 0){
            divAssignAliasToContractAddAliasContainer.append(
                '<div class="row my-2" index="0">' +
                '<div class="col-10">' +
                '<input type="text" class="inputContractAliasAddItem form-control font-12" onblur="CONTRACT_HANDLER.add_new_alias_inputs($(this));" value=""/>' +
                '</div>' +
                '<div class="col">' +
                '<a onclick="CONTRACT_HANDLER.remove_new_alias_inputs($(this));" index="0">' +
                '<i class="fa fa-times text-danger"></i>' +
                '</a>' +
                '</div>' +
                '</div>'
            );

        }else{
            for (let i in CONTRACT_HANDLER.new_contract_alias_items) {
                let item = CONTRACT_HANDLER.new_contract_alias_items[i];
                divAssignAliasToContractAddAliasContainer.append(
                    '<div class="row my-2" index="'+i+'">' +
                    '<div class="col-10">' +
                    '<input type="text" class="inputContractAliasAddItem form-control font-12" onblur="CONTRACT_HANDLER.add_new_alias_inputs($(this));" value="'+item["name"]+'"/>' +
                    '</div>' +
                    '<div class="col">' +
                    '<a onclick="CONTRACT_HANDLER.remove_new_alias_inputs($(this));" index="'+i+'">' +
                    '<i class="fa fa-times text-danger"></i>' +
                    '</a>' +
                    '</div>' +
                    '</div>'
                );
            }
            let index = CONTRACT_HANDLER.new_contract_alias_items.length;
            divAssignAliasToContractAddAliasContainer.append(
                '<div class="row my-2" index="'+index+'">' +
                '<div class="col-10">' +
                '<input type="text" class="inputContractAliasAddItem form-control font-12" onblur="CONTRACT_HANDLER.add_new_alias_inputs($(this));" value=""/>' +
                '</div>' +
                '<div class="col">' +
                '<a onclick="CONTRACT_HANDLER.remove_new_alias_inputs($(this));" index="'+index+'">' +
                '<i class="fa fa-times text-danger"></i>' +
                '</a>' +
                '</div>' +
                '</div>'
            );
        }
        CONTRACT_HANDLER.update_input_border_color_for_aliases();
    },

    add_new_alias_inputs: function (elem) {
        CONTRACT_HANDLER.update_input_border_color_for_aliases(elem);
        let rowParent = elem.parent().parent();
        let inputContractAliasAddItem = rowParent.find('.inputContractAliasAddItem');
        if (parseInt(rowParent.attr('index')) === parseInt(CONTRACT_HANDLER.new_contract_alias_items.length)) {
            CONTRACT_HANDLER.new_contract_alias_items.push({
                name: inputContractAliasAddItem.val()
            });
            CONTRACT_HANDLER.update_new_contract_alias_items();
        }
    },

    add_new_alias: function () {
        CONTRACT_HANDLER.new_contract_alias_items = [];
        $('.inputContractAliasAddItem').each(function () {
            let elem = $(this);
            if (elem.val()){
                CONTRACT_HANDLER.new_contract_alias_items.push({
                    name: elem.val()
                });
            }
        });

        if (CONTRACT_HANDLER.new_contract_alias_items !== 0){
            $.ajax({
                url: `/${DB_NAME}/contracts/${CONTRACT_ID}/contract_aliases/add_new_aliases`,
                type: "POST",
                data: {
                    "aliases": JSON.stringify(CONTRACT_HANDLER.new_contract_alias_items)
                },
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    console.log(response);
                    if(response.result === 'ok') {
                        modalAssignAliasToContractAddItem.modal('hide');
                        CONTRACT_HANDLER.load_aliases();
                        if(response.error == "y"){
                            show_toast_error_message(response.message, 'topCenter');
                        }
                        // show_toast_success_message(response.message, 'bottomRight');
                    }else{
                        show_toast_error_message(response.message, 'topCenter');
                    }
                },
            });
        }
    },

    // END ALIAS Section



    change_manage_membership_validation: function(){
        if($(inputMembershipValidation).prop("checked") === true){
            $.ajax({
                url: `/${DB_NAME}/settings`,
                type: "POST",
                data: {
                    "opt": "membership_validation_enable",
                    "value": 1
                },
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    if(response.result === 'ok') {
                        //show_toast_success_message(response.message, 'bottomRight');
                    }else{
                        show_toast_error_message(response.message, 'topCenter');
                    }
                },
            });
        }
    },

    // update status based on dates ranges
    update_status_from_dates_range: function () {

        spanContractStatus.removeClass('text-warning').removeClass('text-danger').removeClass('text-success');
        if (inputContractStartDate.val() && inputContractEndDate.val()){
            let is_valid = validate_dates_with_month_first(inputContractStartDate, inputContractEndDate);
            if(!is_valid) {
                inputContractStartDate.addClass('border-red');
                inputContractEndDate.addClass('border-red');
                spanContractStatus.html('-');
                show_toast_error_message("Contract End date cannot be earlier than start date");
                return false;
            }else{
                inputContractStartDate.removeClass('border-red');
                inputContractEndDate.removeClass('border-red');
                let status_obj = derive_status_based_on_date_ranges_with_month_first(inputContractStartDate, inputContractEndDate);
                spanContractStatus.addClass(status_obj.cls).html(status_obj.status);
            }
        }
        //EA-1460 Extending Contract End Date extends Contract Lines and Membership, Servers
        if (inputContractEndDate.val() && isFutureDate(inputContractEndDate.val())){
           inputFutureContractEndDate.val('1');
         }
    }

};

$(function (){

    /* Create an array with the values of all the input boxes in a column */
    // https://datatables.net/examples/plug-ins/dom_sort.html
    $.fn.dataTable.ext.order['dom-text'] = function (settings, col){
        return this.api().column( col, {order:'index'} ).nodes().map( function (td, i) {
            return $('input', td).val();
        });
    };

    modalConfirmContractsUpdate.on('shown.bs.modal', function (e) {
        // initialize and load data in dtable when modal opens
        CONTRACT_HANDLER.load_active_contract_line_items();
        CONTRACT_HANDLER.load_acive_contract_server_lines();
        CONTRACT_HANDLER.load_active_membership_line_items();
    });

    // modals COT and ALIAS
    modalAssignCotToContract.on('shown.bs.modal', function (e) {
        // initialize and load data in dtable when modal opens
        CONTRACT_HANDLER.load_active_cots();
    });

    modalAssignAliasToContract.on('shown.bs.modal', function (e) {
        // initialize and load data in dtable when modal opens
        CONTRACT_HANDLER.load_aliases();
    });

    // Add Item Cot
    modalAssignCotToContractAddItem.on('shown.bs.modal', function (e) {
        // initialize empty values when modal opens
        $(".inputCoTNameAddItem").val('');
        $(".inputCoTDescriptionAddItem").val('');
        CONTRACT_HANDLER.new_cots_items = [];
        CONTRACT_HANDLER.update_new_cot_items();
    });

    // Add Item Alias
    modalAssignAliasToContractAddItem.on('shown.bs.modal', function (e) {
        // initialize empty values when modal opens
        $(".inputContractAliasAddItem").val('');
        CONTRACT_HANDLER.new_contract_alias_items = [];
        CONTRACT_HANDLER.update_new_contract_alias_items();
    });

    // // Add Item Alias
    // modalAssignContractAddItem.on('shown.bs.modal', function (e) {
    //     // initialize empty values when modal opens
    //     $(".inputCoTNameAddItem").val('');
    //     $(".inputCoTDescriptionAddItem").val('');
    //     CONTRACT_HANDLER.new_cots_items = [];
    //     CONTRACT_HANDLER.update_new_cot_items();
    // });

    // $(document).on('keydown', 'input.inputContractAliasAddItem', function(e) {
    //     let keyCode = e.keyCode || e.which;
    //     if (keyCode === 9) {
    //         e.preventDefault();
    //         CONTRACT_HANDLER.add_new_alias_inputs($(this));
    //     }
    // });


});
