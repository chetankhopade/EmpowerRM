// a options tab
let divContractTabOptions = $("#divContractTabOptions");
let divContractActiveContractContainerButtons = $("#divContractActiveContractContainerButtons");

// table
let tableContractActiveContract = $("#tableContractActiveContract");
let dtContractActiveContract;

let inputActiveContractStatusID = $("#inputActiveContractStatusID");

// for delete cline
let modalDeleteContractLine = $("#modalDeleteContractLine");
let tableDeleteContractLine = $("#tableDeleteContractLine");
let inputDeleteContractLineID = $("#inputDeleteContractLineID");
let inputDeleteContractLineText = $("#inputDeleteContractLineText");
let helpTextinputDeleteContractLineText = $("#helpTextinputDeleteContractLineText");


let TAB_ACTIVE_CONTRACT = {

    name: 'TAB_ACTIVE_CONTRACT',

    // Edit Lines
    enable_disable_lines: function (enable) {

        if (enable){
            // enable components to edit and show buttons
            tableContractActiveContract.find('input').prop('disabled', false);
            tableContractActiveContract.find('select').prop('disabled', false);
            $('.btnDeleteContractLine').show();
            divContractActiveContractContainerButtons.fadeIn(300);
        }else{
            // disable components again and hide buttons
            tableContractActiveContract.find('input').prop('disabled', true);
            tableContractActiveContract.find('select').prop('disabled', true);
            $('.btnDeleteContractLine').hide();
            divContractActiveContractContainerButtons.hide();
        }
    },

    // Active Contract DataTable Section
    load_data: function (elem, query){
        // css active class
        if (elem){
            divContractTabOptions.find('a').removeClass('active');
            elem.addClass('active');
        }else{
            //$("#divContractTabOptions a:first-child").addClass('active');
            //EA-1598 Product status display : 'Active' tab data displays under 'Inactive' tab.
            $("#contract_status_1").addClass('active');
            $("#contract_status_0").removeClass('active');
            $("#contract_status_2").removeClass('active');
            $("#contract_status_3").removeClass('active');
            $("#contract_status_4").removeClass('active');
        }
        // update status filter input to pass it to the ajax
        inputActiveContractStatusID.val(query);
        // reload data table ajax
        dtContractActiveContract.ajax.reload();
    },

    // Save lines
    update_lines_changes: function () {

        let clines_list = '';
        tableContractActiveContract.find('tr').each(function () {
            let elem = $(this);
            let clid = elem.attr('id');
            if (clid !== undefined){
                let price = elem.find('.inputActiveContractPrice').val();
                let startdate = elem.find('.inputActiveContractStartDate').val();
                let enddate = elem.find('.inputActiveContractEndDate').val();
                let status = elem.find('.inputActiveContractStatus').val();
                clines_list += clid + ':' + price + ':' + startdate + ':' + enddate + ':'+ status +'|';
            }
        });

        if (clines_list.length > 0){
            clines_list = clines_list.substring(0, clines_list.length-1);

            $.ajax({
                url: `/${DB_NAME}/contracts/${CONTRACT_ID}/tab_active_contract/update_lines_changes`,
                type: "POST",
                data: {
                    "clines_list": clines_list
                },
                dataType: "json",
                success: function (response) {
                    if(response.result === 'ok') {
                        show_toast_success_message(response.message, 'bottomRight');
                    }else{
                        show_toast_error_message(response.message);
                    }
                },
                complete: function(){
                    // disable components again
                    TAB_ACTIVE_CONTRACT.enable_disable_lines(false);
                },
                error: function (response) {
                    show_toast_error_message(response.message);
                }
            });
        }
    },

    delete_contract_line: function (elem) {
        if (!inputDeleteContractLineText.val()){
            inputDeleteContractLineText.addClass('border-coral');
        } else if (inputDeleteContractLineText.val().toUpperCase() !== 'DELETE') {
            helpTextinputDeleteContractLineText.removeClass('hide').html('The keyword is not <b>DELETE</b>');
        }else{
            let clid = inputDeleteContractLineID.val();
            let loadingText = '<i class="fa fa-circle-o-notch fa-spin font-10"></i> Removing...';
            let originalText = elem.html();
            $.ajax({
                url: `/${DB_NAME}/contracts/${CONTRACT_ID}/contract_lines/${clid}/delete`,
                type: "POST",
                data: {},
                beforeSend: function(xhr, settings) {
                    elem.addClass('disabled').html(loadingText);
                },
                success: function (response) {
                    if (response.result === 'ok'){
                        modalDeleteContractLine.modal('hide');
                        show_toast_success_message(response.message, 'bottomRight');
                        dtContractActiveContract.ajax.reload();
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
        }
    },

};

$(function () {

    dtContractActiveContract = tableContractActiveContract.DataTable({
        lengthMenu:     [[25, 50, 100, 250, -1], [25, 50, 100, 250, "All"]],
        scrollY:        '17vh',
        processing:     true,
        serverSide:     true,
        responsive:     true,
        deferRender:    true,
        order:          [[0, 'desc']],  // default ordered by 1st column
        language : {
            search:             "",
            searchPlaceholder:  "Search ...",
            processing:         SPINNER_LOADER,
        },
        fnDrawCallback: function() {
            // datepicker
            $('.datepicker').datepicker({
                autoclose: true,
                format: "mm/dd/yyyy"
            });
            //tooltip
            $('.tt').tooltip({
                placement: 'top'
            });
            // delete ContractLine
            $(".btnDeleteContractLine").click(function () {
                let ndc = $(this).attr('ndc');
                let desc = $(this).attr('desc');
                let price = $(this).attr('price');
                let start = $(this).attr('start');
                let end = $(this).attr('end');
                let status = $(this).attr('status');
                let clid = $(this).attr('clid');
                inputDeleteContractLineID.val(clid);
                tableDeleteContractLine.find('tbody').html(
                    '<tr>' +
                             '<td>'+ndc+'</td>' +
                             '<td>'+desc+'</td>' +
                             '<td>'+price+'</td>' +
                             '<td>'+start+'</td>' +
                             '<td>'+end+'</td>' +
                             '<td>'+status+'</td>' +
                          '</tr>');
                modalDeleteContractLine.modal('show');
            });

        },
        initComplete: function() {
            let $searchInput = $('#tableContractActiveContract_filter input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dtContractActiveContract.search( this.value ).draw();
                }
            });
        },
        ajax: {
            url:    `/${DB_NAME}/contracts/${CONTRACT_ID}/tab_active_contract/load_data`,
            type:   'POST',
            data: function ( d ) {
                return $.extend({}, d, {
                    "q": inputActiveContractStatusID.val(),
                });
            }
        },
        columnDefs: [
            {
                "targets": [0],
                "visible": false,
                "searchable": false,
            },
        ],
        columns: [
            {data: 'id'},
            {data: 'item__ndc'},
            {data: 'item__name'},
            {
                data: 'price',
                render : function(data, type, row) {
                    return '<input type="text" class="inputActiveContractPrice input-no-border form-control width-60" value="'+data.toFixed(2)+'" disabled />'
                }
            },
            {
                data: 'start_date',
                render : function(data, type, row) {
                    return '<input type="text" class="inputActiveContractStartDate input-no-border form-control width-80 datepicker" value="'+data+'" disabled />'
                }
            },
            {
                data: 'end_date',
                render : function(data, type, row) {
                    return '<input type="text" class="inputActiveContractEndDate input-no-border form-control width-80 datepicker" value="'+data+'" disabled />'
                }
            },
            {
                data: 'status',
                render : function(data, type, row) {

                    let option_active = '<option value="' + STATUS_ACTIVE +'">Active</option>';
                    if (data === 'Active'){
                        option_active = '<option value="' + STATUS_ACTIVE +'" selected>Active</option>';
                    }

                    let option_inactive = '<option value="' + STATUS_INACTIVE +'">Inactive</option>';
                    if (data === 'Inactive'){
                        option_inactive = '<option value="' + STATUS_INACTIVE +'" selected>Inactive</option>';
                    }

                    let option_pending = '<option value="' + STATUS_PENDING +'">Pending</option>';
                    if (data === 'Pending'){
                        option_pending = '<option value="' + STATUS_PENDING +'" selected>Pending</option>';
                    }

                    let option_proposed = '<option value="' + STATUS_PROPOSED +'">Proposed</option>';
                    if (data === 'Proposed'){
                        option_proposed = '<option value="' + STATUS_PROPOSED +'" selected>Proposed</option>';
                    }

                    return '<select value="'+data+'" class="inputActiveContractStatus form-control" disabled>' +
                                option_active +
                                option_inactive +
                                option_pending +
                                option_proposed +
                            '</select>'
                }
            },
            {
                data: '',
                render : function(data, type, row) {
                    return '<i class="fa fa-times btnDeleteContractLine tt" title="Delete" ' +
                                'style="display: none; cursor: pointer;" ' +
                                'ndc="'+row["item__ndc"]+'" ' +
                                'desc="'+row["item__name"]+'" ' +
                                'price="'+row["price"]+'" ' +
                                'start="'+row["start_date"]+'" ' +
                                'end="'+row["end_date"]+'" ' +
                                'status="'+row["status"]+'" ' +
                                'clid="'+row["id"]+'">' +
                            '</i>'
                }
            },
        ],
    });

});

