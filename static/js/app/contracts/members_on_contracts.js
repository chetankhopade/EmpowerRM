// datatable
let tableContractManageMembership = $("#tableContractManageMembership");
let dtContractManageMembership;

// div
let divContractTabOptionsManageMembership = $("#divContractTabOptionsManageMembership");

let MEMBERS_ON_CONTRACTS = {
    name: 'MEMBERS_ON_CONTRACTS',

    load_data: function (elem, query) {
        // css active to filters options
        if (elem){
            divContractTabOptionsManageMembership.find('a').removeClass('active');
            elem.addClass('active');
        }else{
            $("#divContractTabOptionsManageMembership a:first-child").addClass('active');
        }

        if (dtContractManageMembership !== undefined && dtContractManageMembership !== '') {
            dtContractManageMembership.destroy();
        }
        dtContractManageMembership = tableContractManageMembership.DataTable({
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
                return 'Members_on_Contracts_' + n;
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
                return 'Members_on_Contracts_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },

            }
            ],
            scrollY:        '48vh',
            processing:     true,
            serverSide:     true,
            responsive:     true,
            deferRender:    true,
            order:          [[1, 'desc']],  // default ordered by 1st column
            language : {
                search:             "",
                searchPlaceholder:  "Search ...",
                processing:         SPINNER_LOADER,
            },
            // add datepicker dynamically to dt
            fnDrawCallback: function() {
                $('.datepicker').datepicker({
                    autoclose: true,
                    format: "mm/dd/yyyy"
                });
            },
            ajax: {
                url:    `/${DB_NAME}/contracts/${CONTRACT_ID}/tab_manage_membership/load_data`,
                type:   'POST',
                data: { 'q': query }
            },
            initComplete: function() {
                let $searchInput = $('#tableContractManageMembership_filter input');
                $searchInput.unbind();
                $searchInput.bind('keyup', function(e) {
                    if(this.value.length === 0 || this.value.length >= 3) {
                        dtContractManageMembership.search( this.value ).draw();
                    }
                });
            },
            columnDefs: [
                {
                    type: 'date',
                    'targets': [3, 4]
                }

            ],
            columns: [
                {data: 'location_number'},
                {data: 'company_name'},
                {data: 'indirect_customer__address1'},
                {data: 'indirect_customer__city'},
                {data: 'indirect_customer__state'},
                {data: 'indirect_customer__zip_code'},
                {data: 'indirect_customer__cot__trade_class'},
                {
                    data: 'start_date',
                    // render : function(data, type, row) {
                    //     return '<input type="text" class="inputManageMembershipStartDate input-no-border form-control width-80 datepicker" value="'+data+'" disabled />'
                    // }
                },
                {
                    data: 'end_date',
                    // render : function(data, type, row) {
                    //     return '<input type="text" class="inputManageMembershipEndDate input-no-border form-control width-80 datepicker" value="'+data+'" disabled />'
                    // }
                },
                {
                    data: 'status',
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
            ],
        });
    }
};

$(function () {
    MEMBERS_ON_CONTRACTS.load_data();
});