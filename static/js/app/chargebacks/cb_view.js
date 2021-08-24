// vars
let selected_chargebacks_ids_to_submit = [];
// filters buttons
let divChargebackFilters = $(".divChargebackFilters");
let spanFiltersButtons = $(".spanFiltersButtons");
let spanFilterButtonTotalOpenCount = $("#spanFilterButtonTotalOpenCount");
let spanFilterButtonTotalOpenIssued = $("#spanFilterButtonTotalOpenIssued");
let spanFilterButtonResubmissionsCount = $("#spanFilterButtonResubmissionsCount");
let spanFilterButtonResubmissionsIssued = $("#spanFilterButtonResubmissionsIssued");
let spanFilterButtonDuplicatesCount = $("#spanFilterButtonDuplicatesCount");
let spanFilterButtonDuplicatesIssued = $("#spanFilterButtonDuplicatesIssued");
let spanFilterButtonInvalidsCount = $("#spanFilterButtonInvalidsCount");
let spanFilterButtonInvalidsIssued = $("#spanFilterButtonInvalidsIssued");
let spanFilterButtonIssuesCount = $("#spanFilterButtonIssuesCount");
let spanFilterButtonIssuesIssued = $("#spanFilterButtonIssuesIssued");
let spanFilterButtonFailedValidationsCount = $("#spanFilterButtonFailedValidationsCount");
let spanFilterButtonFailedValidationsIssued = $("#spanFilterButtonFailedValidationsIssued");
let spanFilterButtonReadyToPostCount = $("#spanFilterButtonReadyToPostCount");
let spanFilterButtonReadyToPostIssued = $("#spanFilterButtonReadyToPostIssued");
let spanFilterButtonGenerate849Count = $("#spanFilterButtonGenerate849Count");
let spanFilterButtonGenerate849Issued = $("#spanFilterButtonGenerate849Issued");
let spanFilterButtonArchiveCount = $("#spanFilterButtonArchiveCount");
let spanFilterButtonArchiveIssued = $("#spanFilterButtonArchiveIssued");

// buttons
let btnCBViewButtons = $(".btnCBViewButtons");
let btnCBImport844 = $("#btnCBImport844");
let btnCBRerunValidations = $("#btnCBRerunValidations");
let btnCBPostToAccounting = $("#btnCBPostToAccounting");
let btnCBGenerate849 = $("#btnCBGenerate849");
let btnCBArchive = $("#btnCBArchive");
let btnCBPurge = $("#btnCBPurge");

// table
let tableChargebacks = $("#tableChargebacks");
let dtChargeback;
let inputChargebackFilterSelected = $("#inputChargebackFilterSelected");


let CB_VIEW = {

    name: 'CB_VIEW',

    load_cbs_counters_data: function () {
        // Create our number formatter.
        let formatter = new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        });

        $.ajax({
            url: `/${DB_NAME}/chargebacks/view/load_cbs_counters_data`,
            type: "POST",
            data: {},
            beforeSend: function(xhr, settings) {
                spanFiltersButtons.html(SPINNER_LOADER_XS);
            },
            success: function (response) {
                // Bucket - Totals 
                let total = response.total;
                let total_count = total['count'].toLocaleString();
                let total_subtotal = formatter.format(total['subtotal']);
                let total_issued = formatter.format(total['issued']);
                let total_tooltip = "<p class='font-10 text-left'>Submitted Claim Amount: "+total_subtotal+"</p><p class='font-10 text-left line-height-1px'>Issued Claim Amount: "+total_issued+"</p>";
                spanFilterButtonTotalOpenCount.html(total_count);
                spanFilterButtonTotalOpenIssued.attr('title', total_tooltip).html(total_issued);
        
                // Bucket - Resubmissions 
                let resub = response.resubmissions;
                let resub_count = resub['count'].toLocaleString();
                let resub_subtotal = formatter.format(resub['subtotal']);
                let resub_issued = formatter.format(resub['issued']);
                let resub_tooltip = "<p class='font-10 text-left'>Submitted Claim Amount: "+resub_subtotal+"</p><p class='font-10 text-left line-height-1px'>Issued Claim Amount: "+resub_issued+"</p>";
                spanFilterButtonResubmissionsCount.html(resub_count);
                spanFilterButtonResubmissionsIssued.attr('title', resub_tooltip).html(resub_issued);

                // Bucket - Duplicates 
                let duplicates = response.duplicates;
                let duplicates_count = duplicates['count'].toLocaleString();
                let duplicates_subtotal = formatter.format(duplicates['subtotal']);
                let duplicates_issued = formatter.format(duplicates['issued']);
                let duplicates_tooltip = "<p class='font-10 text-left'>Submitted Claim Amount: "+duplicates_subtotal+"</p><p class='font-10 text-left line-height-1px'>Issued Claim Amount: "+duplicates_issued+"</p>";
                spanFilterButtonDuplicatesCount.html(duplicates_count);
                spanFilterButtonDuplicatesIssued.attr('title', duplicates_tooltip).html(duplicates_issued);
                
                // Bucket - Invalids 
                let invalids = response.invalids;
                let invalids_count = invalids['count'].toLocaleString();
                let invalids_subtotal = formatter.format(invalids['subtotal']);
                let invalids_issued = formatter.format(invalids['issued']);
                let invalids_tooltip = "<p class='font-10 text-left'>Submitted Claim Amount: "+invalids_subtotal+"</p><p class='font-10 text-left line-height-1px'>Issued Claim Amount: "+invalids_issued+"</p>";
                spanFilterButtonInvalidsCount.html(invalids_count);
                spanFilterButtonInvalidsIssued.attr('title', invalids_tooltip).html(invalids_issued);
                
                // Bucket - Issues 
                let issues = response.issues;
                let issues_count = issues['count'].toLocaleString();
                let issues_subtotal = formatter.format(issues['subtotal']);
                let issues_issued = formatter.format(issues['issued']);
                let issues_tooltip = "<p class='font-10 text-left'>Submitted Claim Amount: "+issues_subtotal+"</p><p class='font-10 text-left line-height-1px'>Issued Claim Amount: "+issues_issued+"</p>";
                spanFilterButtonIssuesCount.html(issues_count);
                spanFilterButtonIssuesIssued.attr('title', issues_tooltip).html(issues_issued);
                
                // Bucket - Failed Validations 
                let failed = response.failed_validations;
                let failed_count = failed['count'].toLocaleString();
                let failed_subtotal = formatter.format(failed['subtotal']);
                let failed_issued = formatter.format(failed['issued']);
                let failed_tooltip = "<p class='font-10 text-left'>Submitted Claim Amount: "+failed_subtotal+"</p><p class='font-10 text-left line-height-1px'>Issued Claim Amount: "+failed_issued+"</p>";
                spanFilterButtonFailedValidationsCount.html(failed_count);
                spanFilterButtonFailedValidationsIssued.attr('title', failed_tooltip).html(failed_issued);
                
                // Bucket - Post to Accounting
                let post = response.ready_to_post;
                let post_count = post['count'].toLocaleString();
                let post_subtotal = formatter.format(post['subtotal']);
                let post_issued = formatter.format(post['issued']);
                let post_tooltip = "<p class='font-10 text-left'>Submitted Claim Amount: "+post_subtotal+"</p><p class='font-10 text-left line-height-1px'>Issued Claim Amount: "+post_issued+"</p>";
                spanFilterButtonReadyToPostCount.html(post_count);
                spanFilterButtonReadyToPostIssued.attr('title', post_tooltip).html(post_issued);
                
                // Bucket - Generate 849
                let generate849 = response.generate_849;
                let generate849_count = generate849['count'].toLocaleString();
                let generate849_subtotal = formatter.format(generate849['subtotal']);
                let generate849_issued = formatter.format(generate849['issued']);
                let generate849_tooltip = "<p class='font-10 text-left'>Submitted Claim Amount: "+generate849_subtotal+"</p><p class='font-10 text-left line-height-1px'>Issued Claim Amount: "+generate849_issued+"</p>";
                spanFilterButtonGenerate849Count.html(generate849_count);
                spanFilterButtonGenerate849Issued.attr('title', generate849_tooltip).html(generate849_issued);
                
                // Bucket - Archive
                let archive = response.archive;
                let archive_count = archive['count'].toLocaleString();
                let archive_subtotal = formatter.format(archive['subtotal']);
                let archive_issued = formatter.format(archive['issued']);
                let archive_tooltip = "<p class='font-10 text-left'>Submitted Claim Amount: "+archive_subtotal+"</p><p class='font-10 text-left line-height-1px'>Issued Claim Amount: "+archive_issued+"</p>";
                spanFilterButtonArchiveCount.html(archive_count);
                spanFilterButtonArchiveIssued.attr('title', archive_tooltip).html(archive_issued);
                
            },
            complete: function () {
                // tooltip for buckets
                $('.ttBuckets').tooltip({
                    placement: "top",
                    html: true,
                });
            },
            error: function () {
                show_toast_error_message('Error getting counters');
            }
        });
    },

    show_hide_buttons: function (key){
        // hide all buttons by default
        btnCBViewButtons.addClass('hide');
        switch (key) {
            case '':
                // show Import, Create Chargeback
                btnCBImport844.removeClass('hide');
                btnCBCreateChargeback.removeClass('hide');
                btnCBPurge.removeClass('hide');
                break;
            case 'resubmissions':
                // show Import, Rerun Validation, Purge, Create Chargeback
                // btnCBImport844.removeClass('hide');
                btnCBRerunValidations.removeClass('hide');
                btnCBPurge.removeClass('hide');
                // btnCBCreateChargeback.removeClass('hide');
                break;
            case 'duplicates':
                // show Import, Purge, Create Chargeback
                // btnCBImport844.removeClass('hide');
                btnCBPurge.removeClass('hide');
                // btnCBCreateChargeback.removeClass('hide');
                break;
            case 'invalids':
                // show Import, Purge, Create Chargeback
                // btnCBImport844.removeClass('hide');
                btnCBPurge.removeClass('hide');
                // btnCBCreateChargeback.removeClass('hide');
                break;
            case 'issues':
                // show Import, Rerun Validations, Purge, Create Chargeback
                // btnCBImport844.removeClass('hide');
                btnCBRerunValidations.removeClass('hide');
                btnCBPurge.removeClass('hide');
                // btnCBCreateChargeback.removeClass('hide');
                break;
            case 'failed_validations':
                // show Import, Rerun Validations, Purge, Create Chargeback
                // btnCBImport844.removeClass('hide');
                btnCBRerunValidations.removeClass('hide');
                btnCBPurge.removeClass('hide');
                // btnCBCreateChargeback.removeClass('hide');
                break;
            case 'ready_to_post':
                // show Import, Post to Accounting, Purge, Create Chargeback
                // btnCBImport844.removeClass('hide');
                btnCBPostToAccounting.removeClass('hide');
                btnCBPurge.removeClass('hide');
                // btnCBCreateChargeback.removeClass('hide');
                break;
            case 'generate_849':
                // show Import, Generate 849, Create Chargeback
                btnCBImport844.removeClass('hide');
                btnCBGenerate849.removeClass('hide');
                btnCBCreateChargeback.removeClass('hide');
                break;
            case 'archive':
                // show Import, Archive, Create Chargeback
                btnCBGenerate849.removeClass('hide');
                btnCBArchive.removeClass('hide');
                break;
        }
    },

    load_cb_data: function (elem) {

        let key = elem.attr('action');

        // css active class
        divChargebackFilters.find('.card-body').removeClass('active');
        if (elem){
            elem.find('.card-body').addClass('active');
        }else{
            spanFilterButtonTotalOpenCount.parent().addClass('active');
        }

        // update filter input to pass it to the ajax
        inputChargebackFilterSelected.val(key);

        // show or hide buttons: ticket 1039
        CB_VIEW.show_hide_buttons(key);

        // reload data table ajax
        dtChargeback.ajax.reload();

    },

    select_all_lines: function() {
        let button_val = $('#selectAllRows').val();
        $("#tableChargebacks tr").each(function () {
            let elem = $(this);
            let id = $(this).attr('id');
            if (typeof id != "undefined"){
                if(button_val === 'select_all'){
                    elem.addClass('selected');
                    selected_chargebacks_ids_to_submit.push(id);
                }else{
                    elem.removeClass('selected');
                    selected_chargebacks_ids_to_submit = selected_chargebacks_ids_to_submit.filter(function(itm){ return itm !== id; });
                }
                selected_chargebacks_ids = selected_chargebacks_ids_to_submit.join('|');
            }
        });
        if(button_val === 'select_all'){
            $('#selectAllRows').val('deselect_all');
            $('#selectAllRows').text('Deselect All');
        }
        else{
            $('#selectAllRows').val('select_all');
            $('#selectAllRows').text('Select All');
        }
    },

    get_all_selected_lines: function (callfrom=""){
        if(callfrom !== "page_change"){
            selected_chargebacks_ids_to_submit = [];
        }
        $("#tableChargebacks tr").each(function () {
            let elem = $(this);
            let id = $(this).attr('id');
            if (typeof id != "undefined" && elem.hasClass('selected')){
                selected_chargebacks_ids_to_submit.push(id);
            }
        });
        selected_chargebacks_ids = selected_chargebacks_ids_to_submit.join('|');
    },

};


$(function () {

    // load counters for buttons filters
    CB_VIEW.load_cbs_counters_data();

    // show hide button first time
    CB_VIEW.show_hide_buttons('');

    // Main DataTable
    if (dtChargeback !== undefined && dtChargeback !== '') {
        $(dtChargeback).DataTable().clear();
        dtChargeback.destroy();
    }
    dtChargeback = tableChargebacks.DataTable({
        lengthMenu:     [[50, 100, 150, -1], [50, 100, 150, "All"]],
        scrollY:        '45vh',
        scrollX:        true,
        dom: "<'row'<'col-sm-1 selectAll'><'col-sm-3'l><'col-sm-4'i><'col-sm-4'f>>" + "<'row'<'col-sm-12'tr>>" + "<'row dt_footer'<'col-sm-5' B><'col-sm-7'p>>",
        buttons: [
            {
                extend:    'excelHtml5',
                text:     '<i class="fa fa-file-excel-o">',
                titleAttr: 'Download Excel',
                className: 'btn btn-sm btn-default tt excel_dt_footer',
				title: '',
                filename: function(){
                var d = new Date();
                // var n = d.getTime();
                var n = get_current_date_in_ymdhms_for_export();
                return 'Chargebacks_Processing_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',

                },
                // action: function ( e, dt, node, config ) {
                //     $.fn.dataTable.ext.buttons.excelHtml5.action.call(this, e, dt, node, config);
                // }

            },
            {
                extend:    'csvHtml5',
                text:      '<i class="fa fa-file-text-o"></i>',
                titleAttr: 'Download CSV',
				className: 'btn btn-sm btn-default tt csv_dt_footer',
				title: '',

                filename: function(){
                var d = new Date();
                // var n = d.getTime();
                var n = get_current_date_in_ymdhms_for_export();
                return 'Chargebacks_Processing_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },
                // action: function ( e, dt, node, config ) {
                //     $.fn.dataTable.ext.buttons.excelHtml5.action.call(this, e, dt, node, config);
                // }
            }
            ],
        processing:     true,
        serverSide:     true,
        responsive:     true,
        info:           true,
        order:          [[1, 'desc']],  // default ordered by cbid column
        language : {
            search:             "",
            searchPlaceholder:  "Search ...",
            processing:         SPINNER_LOADER,
        },
        select: true,
        ajax: {
            url:    `/${DB_NAME}/chargebacks/view/load_data`,
            type:   'POST',
            data: function ( d ) {
                return $.extend({}, d, {
                    "k": inputChargebackFilterSelected.val(),
                });
            }
        },
        fnDrawCallback: function() {
            $('.tt').tooltip({
                placement: 'top'
            })
        },
        initComplete: function() {
            let $searchInput = $('#tableChargebacks_filter input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dtChargeback.search( this.value ).draw();
                }
            });
        },
        createdRow: function (row, data, index) {
            let res;
            if (selected_chargebacks_ids.length > 0) {
                res = selected_chargebacks_ids.split("|");
                for (let i = 0; i < res.length; i++) {
                    if (res[i] === row["id"]) {
                        $(row).addClass("selected");
                    }
                }
            }
        },
        columnDefs: [
            {
                "targets": [0],
                "visible": false,
                "searchable": false,
            },
            {
                "targets": [12],
                "sortable": false,
            },
            {
                type: 'date',
                'targets': [5, 11]
            }
        ],
        columns: [
            {data: 'id'},
            {
                data: 'cbid',
                render : function(data, type, row) {
                    return '<span db="'+DB_NAME+'" target="/chargebacks/'+row["id"]+'/details" cbid="'+row["cbid"]+'" cbno="'+row["cbnumber"]+'">' +
                        '<a onclick="APP.execute_url($(this))" class="empower-color-blue">' + data + '</a>' +
                        '</span>'
                }
            },
            {data: 'customer'},
            {data: 'distributor'},
            {data: 'type'},
            {data: 'date'},
            {data: 'cbnumber'},
            {
                data: 'request',
                render : function(data, type, row) {
                    let html = '';
                    if (data){
                        if (row['request'] === row['issued']){
                            html  = '<span class="font-11" style="color: #228b22">' + data.toFixed(2) + '</span>';
                        }else{
                            html  = '<span class="font-11">' + data.toFixed(2) + '</span>';
                        }
                    }else{  //EA-1472 When the chargeback requested amount = 0.00 the amount shows as blank on the main CB page.
                        html  = '<span class="font-11">0.00</span>';
                    }
                    return html
                }
            },
            {
                data: 'issued',
                render : function(data, type, row) {
                    let html = '';
                    if (data){
                        if (row['request'] === row['issued']){
                            html  = '<span class="font-11" style="color: #228b22">' + data.toFixed(2) + '</span>';
                        }else{
                            html  = '<span class="font-11" style="color: red">' + data.toFixed(2) + '</span>';
                        }
                    }else{
                        html  = '<span class="font-11">0.00</span>';
                    }
                    return html
                }
            },
            {
                data: 'stage',
                render : function(data, type, row) {
                    let html = '';
                    if (data){
                        if (row['stage'] === STAGE_TYPE_IN_PROCESS_DISPLAY){
                            html = '<span class="badge badge-warning font-8 p-1">' + data + '</span>';
                        }else {
                            if (row['substage'] === SUBSTAGE_TYPE_NO_ERRORS_DISPLAY){
                                html  = '<span class="text-success">' + data + '</span>';
                            }else{
                                html  = '<span class="text-danger">' + data + '</span>';
                            }
                        }
                    }
                    return html
                }
            },
            {
                data: 'substage',
                render : function(data, type, row) {
                    let html = '';
                    if (row['substage'] === SUBSTAGE_TYPE_NO_ERRORS_DISPLAY){
                        html  = '<span class="text-success">' + data + '</span>';
                    } else{
                        if (row['stage'] === STAGE_TYPE_POSTED_DISPLAY){
                            // html  = '<span class="text-danger tt" title="'+row['accounting_error']+'">' + data + '</span>';
                            // EA-1694 - Posted w/ errors not showing full detail with item not found in Quickbooks
                            html  = "<span class='text-danger tt' title='"+ decodeURI(escape(row['accounting_error'])) +"'>" + data + "</span>";
                        } else{
                            html  = '<span class="text-danger">' + data + '</span>';
                        }
                    }
                    return html
                }
            },
            {data: 'imported'},
            {
                data: 'status',
                class: 'text-center',
                render : function(data, type, row) {
                    let html = '';
                    if (row['stage'] === STAGE_TYPE_IN_PROCESS_DISPLAY){
                        html  = '<i class="fa fa-exclamation-triangle text-warning font-12"></i>';
                    }else {
                        if (row['substage'] === SUBSTAGE_TYPE_NO_ERRORS_DISPLAY){
                            html  = '<i class="fas fa-check text-success"></i>';
                        }else{
                            html  = '<i class="fa fa-exclamation-triangle text-warning font-12"></i>';
                        }
                    }

                    return html
                }
            },
        ],
    });
    // hide paging cause dt doesnt allow to do this in runtime
    // $('#tableChargebacks_paginate').css("display", "none");
    // $('#tableChargebacks_length').css("display", "none");
    $('<button type="button" onclick="CB_VIEW.select_all_lines();" class="btn btn-primary btn-sm" id="selectAllRows" value="select_all">Select All</button>').appendTo("#tableChargebacks_wrapper .selectAll");

    $("#tableChargebacks_paginate").on("click", "a", function() {
        // Just keeping Default to select all per page
        $('#selectAllRows').val('select_all');
        $('#selectAllRows').text('Select All');
    });

    $('#tableChargebacks').on('page.dt', function() {
        CB_VIEW.get_all_selected_lines("page_change");
    });

});
