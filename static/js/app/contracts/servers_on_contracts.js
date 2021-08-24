let tableContractDetailsServers = $("#tableContractDetailsServers");
let dtContractDetailsServers = '';

let SERVERS_ON_CONTRACTS = {

};

$(function () {

    dtContractDetailsServers = tableContractDetailsServers.DataTable({
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
                return 'Servers_on_Contracts_' + n;
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
                return 'Servers_on_Contracts_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },
            }
            ],
            scrollY:        '48vh',
            scrollX:        true,
            processing:     true,
            serverSide:     true,
            responsive:     true,
            deferRender:    true,
            autoWidth:      false,
            infoFiltered:       "",
            order:          [[0, 'desc']],  // default ordered by 1st column
            language : {
                search:             "",
                searchPlaceholder:  "Search ...",
                processing:         SPINNER_LOADER,
            },
            ajax: {
                url:    `/${DB_NAME}/contracts/contract_servers_load_data`,
                type:   'POST',
                data: function ( d ) {
                    return $.extend({}, d, {
                        "contract_id": CONTRACT_ID
                    });
                }
            },
            initComplete: function() {
                let $searchInput = $('#tableContractDetailsServers_filter input');
                $searchInput.unbind();
                $searchInput.bind('keyup', function(e) {
                    if(this.value.length === 0 || this.value.length >= 3) {
                        dtContractDetailsServers.search( this.value ).draw();
                    }
                });
            },
            columnDefs: [
                {
                    type:'date',
                    "targets":[3, 4]
                },
            ],
            columns: [
                {data: 'name'},
                {data: 'cb_amount'},
                {data: 'cb_lines'},
                {data: 'units_sold'},
                {data: 'start_date'},
                {data: 'end_date'},
            ],
        });
});