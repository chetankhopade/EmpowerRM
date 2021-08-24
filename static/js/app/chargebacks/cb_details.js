// vars
let inputCBDetailsLinesFilterID = $("#inputCBDetailsLinesFilterID");
let divCBDetailsLinesTabOptions = $("#divCBDetailsLinesTabOptions");

let tableCBDetailsLines = $("#tableCBDetailsLines");
let dtCBDetailsLines = '';
let dttableChargebackAudit;

let CB_DETAILS = {

    name: 'CB_DETAILS',

    // Products DataTable Section
    load_data_cblines: function (elem, query){
        // css active class
        if (elem){
            divCBDetailsLinesTabOptions.find('a').removeClass('active');
            elem.addClass('active');
        }else{
            $("#divCBDetailsLinesTabOptions a:last-child").addClass('active');
        }
        // update status filter input to pass it to the ajax
        inputCBDetailsLinesFilterID.val(query);
        // reload data table ajax
        dtCBDetailsLines.ajax.reload();
    },

};


$(function () {

    // DataTable
    dtCBDetailsLines = tableCBDetailsLines.DataTable({
        lengthMenu:     [[10, 20, 50, 100, -1], [10, 20, 50, 100, "All"]],
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
                return 'Chargeback_Lines_' + n;
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
                return 'Chargeback_Lines_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },

            }
            ],
        scrollY:        '45vh',
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
        },
        // add datepicker dynamically to dt
        fnDrawCallback: function() {
            $('.tt').tooltip({
                placement: 'top'
            })
        },
        ajax: {
            url:    `/${DB_NAME}/chargebacks/${CHARGEBACK_ID}/details/load_data_cblines`,
            type:   'POST',
            data: function ( d ) {
                return $.extend({}, d, {
                    "q": inputCBDetailsLinesFilterID.val(),
                });
            }
        },
        initComplete: function() {
            let $searchInput = $('#tableCBDetailsLines_filter input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dtCBDetailsLines.search( this.value ).draw();
                }
            });
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
            {
                data:   'cblnid',
                render: function(data, type, row) {
                    return '<span db="'+DB_NAME+'" target="/chargebacks/'+row["id"]+'/line_details">' +
                                '<a onclick="APP.execute_url($(this))" class="empower-color-blue">' + data + '</a>' +
                            '</span>'
                }
            },
            {data: 'invoice_no'},
            {data: 'invoice_date'},
            {data: 'contract_no'},
            {data: 'item_ndc'},
            {data: 'wac_submitted'},
            {data: 'wac_system'},
            {data: 'cp_submitted'},
            {data: 'cp_system'},
            {data: 'claim_amount_submitted'},
            {data: 'claim_amount_system'},
            {data: 'cline_claim_amount_issue'},
            {data: 'error_count'},
            {
                data: 'line_status',
                render : function(data, type, row) {
                    let html = '';
                    if (data === 'APPROVED'){
                        html  = '<span class="text-success">' + data + '</span>';
                    }else if (data === 'DISPUTED'){
                        html  = '<span class="text-warning">' + data + '</span>';
                    }else {
                        html  = '<span class="text-muted">' + data + '</span>';
                    }
                    return html
                }
            },
        ],
    });

    // CB History Datatable

    // DataTable
    if (dttableChargebackAudit !== undefined && dttableChargebackAudit !== '') {
        $(dttableChargebackAudit).DataTable().clear();
        dttableChargebackAudit.destroy();
    }
    dttableChargebackAudit = $("#tableChargebackAudit").DataTable({
            lengthMenu:     [[50, 100, 150, -1], [50, 100, 150, "All"]],
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
                return 'Audit_Chargeback_' + n;
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
                return 'Audit_Chargeback_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },
            }
            ],
            scrollY: '40vh',
            processing: true,
            serverSide: true,
            responsive: true,
            order:[0, "desc"],
            info: true,
            language: {
                search: "",
                searchPlaceholder: "Search ...",
                processing: SPINNER_LOADER,
                infoFiltered: "",
            },
            // add datepicker dynamically to dt
            fnDrawCallback: function () {

            },
            initComplete: function (settings, json) {},
            ajax: {
                url: `/${DB_NAME}/chargebacks/${CHARGEBACK_ID}/details/load_data_cbhistory`,
                type: 'POST',
            },
            // Settings
            columnDefs: [
                {
                    targets: [0],
                    visible: false,
                    searchable: false,
                },
                {
                    targets: [1, 2, 3,4],
                    searchable: true,
                    sortable: true
                },
            ],
            columns: [
                {data: 'id'},
                {data: 'date'},
                {data: 'time'},
                {data: 'cbid'},
                {data: 'change_text'},
            ],
        });




});