let tableContractLines = $("#tableContractLines");
let dtTableContractLines;

// Modal
let modalContractLineEdit = $("#modalContractLineEdit");

// Divs
divListTabOptions = $("#divListTabOptions");

// Variables
let contractLineId = $("#contractLineId");
let clNdc = $("#clNdc");
let clDescription = $("#clDescription");
let clPrice = $("#clPrice");
let clStartDate = $("#clStartDate");
let clEndDate = $("#clEndDate");
let clStatus = $("#clStatus");

let inputContractStatusId = $("#inputContractStatusId");

let PRODUCTS_ON_CONTRACTS = {
    // modal (create or edit)
    show_contract_line_edit_modal: function (elem){
        let contract_line_id = elem.attr('contract_line_id');
        let price = elem.attr('price');
        let start_date = elem.attr('start_date');
        let end_date = elem.attr('end_date');
        let ndc = elem.attr('ndc');
        let description = elem.attr('description');
        let modal_title = "Edit Line " + ndc;
        let status = elem.attr('status');

        modalContractLineEdit.find('.modal-title').html(modal_title);
        modalContractLineEdit.modal('show');

        // set values to components within modal
        contractLineId.val(contract_line_id);
        clNdc.val(ndc);
        clDescription.val(description);
        clPrice.val(price);
        clStartDate.val(start_date);
        clEndDate.val(end_date);
        clStatus.val(status);
    },

    update_contract_line:function () {

        // fields
        let cline = '';
        let clid = contractLineId.val();
        let price = clPrice.val();
        let startdate = clStartDate.val();
        let enddate = clEndDate.val();
        let status = clStatus.val();

        // validations (required fields)
        let price_is_valid = validate_required_input(clPrice);
        let startdate_is_valid = validate_required_input(clStartDate);
        let enddate_is_valid = validate_required_input(clEndDate);

        let is_dates_range_valid = false;
        if (startdate && enddate){
            is_dates_range_valid = validate_dates_with_month_first(clStartDate, clEndDate, true);
        }

        // if all validations passed then execute action
        if (price_is_valid && startdate_is_valid && enddate_is_valid && is_dates_range_valid){

            cline += clid + ':' + price + ':' + startdate + ':' + enddate + ':'+ status +'|';
            cline = cline.substring(0, cline.length-1);

            $.ajax({
                url: `/${DB_NAME}/contracts/${CONTRACT_ID}/tab_active_contract/update_lines_changes`,
                type: "POST",
                data: {
                    "clines_list": cline
                },
                dataType: "json",
                success: function (response) {
                    if(response.result === 'ok') {
                        show_toast_success_message(response.message, 'bottomRight');
                        dtTableContractLines.ajax.reload();
                        modalContractLineEdit.modal('hide');
                    }else{
                        show_toast_error_message(response.message);
                    }
                },
                error: function (response) {
                    show_toast_error_message(response.message);
                }
            });
        }
    },

    load_products_data: function (elem, query){
        // css active class
        if (elem){
            divListTabOptions.find('a').removeClass('active');
            elem.addClass('active');
        }else{
            $("#divListTabOptions a:first-child").addClass('active');
        }
        // update status filter input to pass it to the ajax
        inputContractStatusId.val(query);
        // reload data table ajax
        dtTableContractLines.ajax.reload();
    },
};

$(function () {
// DataTable
    dtTableContractLines = tableContractLines.DataTable({
        lengthMenu:     [[50, 100, 150, -1], [50, 100, 150, "All"]],
        scrollY:        '48vh',
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
                return 'Products_on_Contracts_' + n;
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
                return 'Products_on_Contracts_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },

            }
            ],
        scrollX:        true,
        processing:     true,
        serverSide:     true,
        responsive:     true,
        deferRender:    true,
        autoWidth:      false,
        infoFiltered:       "",
        order:          [[1, 'desc']],
        language : {
            search:             "",
            searchPlaceholder:  "Search...",
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
            url:    `/${DB_NAME}/contracts/contract_lines_load_data`,
            type:   'POST',
            data: function ( d ) {
                return $.extend({}, d, {
                    "q": inputContractStatusId.val(),
                    "contract_id": CONTRACT_ID
                });
            }
        },
        initComplete: function() {
            let $searchInput = $('#tableContractLines_filter input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dtTableContractLines.search( this.value ).draw();
                }
            });
        },
        columnDefs: [
            {
                "targets": [0],
                "visible": false,
                "searchable": false,
            },
            {
                type:'date',
                "targets":[4,5]
            },
            {
                "targets": [7],
                "sortable": false,
            }
        ],
        columns: [
            {data: 'id'},
            {data: 'item__ndc__formatted'},
            {data: 'item__name'},
            {
                data: 'price',
                class:'text-center'
            },
            {
                data: 'start_date',
                class:'text-center'
            },
            {
                data: 'end_date',
                class:'text-center'
            },
            {
                data: 'status',
                class:'text-center',
                render: function(data, type, row) {
                    let html = '';
                    if (data === 'Active'){
                        html = '<span class="text-success">'+data+'</span>';
                    }else if (data === 'Inactive'){
                        html = '<span class="text-danger">'+data+'</span>';
                    }else{
                        html = '<span class="text-warning">'+data+'</span>';
                    }
                    return html
                }
            },
            {
                data: '',
                render : function(data, type, row) {
                    if(is_read_only_user) {
                        return '<a onclick="APP.get_read_only_user_error();" class="tt" title="Edit">' +
                            '<i class="fa fa-pencil"></i>' +
                            '</a>';
                    }else{
                        return '<a onclick="PRODUCTS_ON_CONTRACTS.show_contract_line_edit_modal(elem=$(this));" ' +
                            'contract_line_id="' + row["id"] + '" ' +
                            'price="' + row["price"] + '" ' +
                            'start_date="' + row["start_date"] + '" ' +
                            'end_date="' + row["end_date"] + '" ' +
                            'ndc="' + row["item__ndc"] + '" ' +
                            'description="' + row["item__name"] + '" ' +
                            'status="' + row["status_id"] + '" ' +
                            'class="tt" title="Edit">' +
                            '<i class="fa fa-pencil"></i>' +
                            '</a>';
                    }
                }
            },
        ],
    });
});