let tableContractDetailsHistory = $("#tableContractDetailsHistory");
let dtContractDetailsHistory = '';

let HISTORY = {
    name: 'HISTORY',
    width: '',

    load_data:function (){
        if (dtContractDetailsHistory !== undefined && dtContractDetailsHistory !== '') {
            dtContractDetailsHistory.destroy();
        }
        dtContractDetailsHistory = tableContractDetailsHistory.DataTable({
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
                return 'Contracts_History_' + n;
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
                return 'Contracts_History_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },

            }
            ],
            scrollY:        '45vh',
            scrollX:        true,
            autoWidth:      false,
            processing:     true,
            serverSide:     true,
            // info: false,
            language : {
                search:             "",
                searchPlaceholder:  "Search...",
                processing:         SPINNER_LOADER,
                lengthMenu: "Show _MENU_",
                infoFiltered: "",
            },
            // add datepicker dynamically to dt
            fnDrawCallback: function() {
                $('.datepicker').datepicker({
                    autoclose: true,
                    format: "mm/dd/yyyy"
                });
            },
            ajax: {
                url:    `/${DB_NAME}/contracts/${CONTRACT_ID}/contract_audit_trails/load_data`,
                type:   'POST',
            },
            initComplete: function() {
                let $searchInput = $('#tableContractDetailsHistory input');
                $searchInput.unbind();
                $searchInput.bind('keyup', function(e) {
                    if(this.value.length === 0 || this.value.length >= 3) {
                        dtContractDetailsHistory.search( this.value ).draw();
                    }
                });
            },
            columnDefs: [

                {
                    "targets": "_all",
                    "class": "no_wrap",
                    "width": 110,
                }

            ],
            columns: [
                {data: 'date'},
                {data: 'time'},
                {data: 'user_email'},
                {data: 'change_type'},
                {data: 'field_name'},
                {data: 'product__ndc'},
                {data: 'change_text'},
            ],
        });
        HISTORY.width = get_datatable_wrapper_width_based_on_screen_size();
        // wrap the table to keep using bootstrap grid and scroll in dt
        $("#tableContractDetailsHistory_wrapper").css('width', HISTORY.width).css('margin', '0 auto');
        dtContractDetailsHistory.columns.adjust().draw();
        dtContractDetailsHistory.responsive.recalc();
    },
}



$(function () {
    HISTORY.load_data();
});