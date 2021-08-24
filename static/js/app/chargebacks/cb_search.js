// vars
let fmChargebackSearch = $("#fmChargebackSearch");
let inputSearchFiltersCBId = $("#inputSearchFiltersCBId");
let selectSearchFiltersCustomer = $("#selectSearchFiltersCustomer");
let inputSearchFiltersCBNumber = $("#inputSearchFiltersCBNumber");
let selectSearchFiltersDistributor = $("#selectSearchFiltersDistributor");
let inputSearchFiltersCBCreditMemo = $("#inputSearchFiltersCBCreditMemo");
let inputSearchFiltersStartDate = $("#inputSearchFiltersStartDate");
let inputSearchFiltersUniqueLine = $("#inputSearchFiltersUniqueLine");
let inputSearchFiltersEndDate = $("#inputSearchFiltersEndDate");

// table and Datatable
let tableChargebacksSearch = $("#tableChargebacksSearch");
let dtChargebacksSearch;

let inputChargebacksSearchSelectedFilters = $("#inputChargebacksSearchSelectedFilters");

// global var for selected cbids
let selected_chargebacks_ids = '';

// vars for 849
let modalGenerate849Results = $("#modalGenerate849Results");
let btnDownloadAllFilesGenerate849 = $("#btnDownloadAllFilesGenerate849");


let CB_SEARCH = {

    name: 'CB_SEARCH',

    clear: function () {
        fmChargebackSearch.find('input').val('');
        fmChargebackSearch.find('select').val('').trigger('change');
        inputChargebacksSearchSelectedFilters.val('');
        // reload data based on filters
        dtChargebacksSearch.ajax.reload();

    },

    search: function () {

        //validate cbid field
        isValidNumber(inputSearchFiltersCBId, 0, 999999999, 0);
        let cbid = inputSearchFiltersCBId.val();

        // update input based on chosen filters
        let payload = {
            'cbid': cbid,
            'customer_id': selectSearchFiltersCustomer.val(),
            'cbnumber': inputSearchFiltersCBNumber.val(),
            'distributor_id':  selectSearchFiltersDistributor.val(),
            'credit_memo': inputSearchFiltersCBCreditMemo.val(),
            'start_date': inputSearchFiltersStartDate.val(),
            'unique_line': inputSearchFiltersUniqueLine.val(),
            'end_date': inputSearchFiltersEndDate.val()
        };
        inputChargebacksSearchSelectedFilters.val(JSON.stringify(payload));

        // reload data based on filters
        dtChargebacksSearch.ajax.reload();

    },

    select_all_lines: function() {
        let button_val = $("#btnSelectAllRows").val();
        $("#tableChargebacksSearch tr").each(function () {
            let elem = $(this);
            if(button_val === 'select_all'){
                elem.addClass('selected');
            }else{
                elem.removeClass('selected');
            }
        });
        if(button_val === 'select_all'){
            $("#btnSelectAllRows").val('deselect_all').text('Deselect All');
        }else{
            $("#btnSelectAllRows").val('select_all').text('Select All');
        }
    },

    regenerate_849: function (elem) {
        let selected_chargebacks_ids_to_submit = [];
        $("#tableChargebacksSearch tr").each(function () {
            let elem = $(this);
            let id = $(this).attr('id');
            if (typeof id != "undefined" && elem.hasClass('selected')){
                selected_chargebacks_ids_to_submit.push(id);
            }
        });
        selected_chargebacks_ids = selected_chargebacks_ids_to_submit.join('|');

        if (selected_chargebacks_ids.length > 0) {
            let loadingText = "<span class='font-11'><i class='fa fa-circle-o-notch fa-spin mr-1'></i> ReGenerating 849 ...</span>";
            let originalText = elem.html();

            $.ajax({
                type: "POST",
                url: `/${DB_NAME}/chargebacks/generate_849`,
                data: {
                    'chargebacks_ids': selected_chargebacks_ids
                },
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                    elem.addClass('disabled').html(loadingText);
                },
                success: function (response) {
                    if (response.result === 'ok'){
                        // chargebacks which could not be deleted for some reason
                        let html = '';
                        if (response.invalid_cbs_to_process.length > 0){
                            btnDownloadAllFilesGenerate849.hide();
                            html += "<div class='row'>" +
                                        "<div class='col-1'>" +
                                            "<i class='empower-color-yellow fas fa-info-circle fa-3x mr-1'></i> " +
                                        "</div>" +
                                        "<div class='col'>" +
                                            "<p class='text-justify ml-1'>" +
                                                "Some chargebacks are missing their Credit Memo information or " +
                                                "have lines with Pending status. Please check the following " +
                                                "Chargebacks were properly Posted to Accounting before " +
                                                "attempting to add them to an 849." +
                                            "</p>" +
                                        "</div>" +
                                    "</div>";

                            html += "<table class='table table-condensed table-striped table-borderless mt-2'>" +
                                        "<thead>" +
                                            "<tr class='font-11'>" +
                                                "<th style='width: 60px'>CBID</th>" +
                                                "<th style='width: 120px'>Number</th>" +
                                                "<th>Reason</th>" +
                                            "</tr>" +
                                        "</thead>" +
                                    "<tbody>";
                                    for (let i=0; i < response.invalid_cbs_to_process.length; i++){
                                        let elem = response.invalid_cbs_to_process[i];
                                        html += "<tr class='font-11'>" +
                                                    "<td style='width: 50px'>"+elem[0]+"</td>" +
                                                    "<td>"+elem[1]+"</td>" +
                                                    "<td>"+elem[2]+"</td>" +
                                                "</tr>";
                                    }
                                    html += "</tbody></table>";

                        }else{
                            btnDownloadAllFilesGenerate849.show();
                            html = "<h6 class='text-center _700'>" +
                                        "The following files were generated:" +
                                    "</h6>" +
                                    "<table class='table table-condensed table-striped table-borderless mt-1'>" +
                                        "<thead>" +
                                            "<tr class='font-11'>" +
                                                "<th></th>" +
                                                "<th style='width: 250px'></th>" +
                                                "<th style='width: 100px'></th>" +
                                            "</tr>" +
                                        "</thead>" +
                                        "<tbody>";
                                        for (let i=0; i < response.results.length; i++){
                                            let elem = response.results[i];
                                            html += "<tr class='font-11'>" +
                                                        "<td>"+elem.customer+"</td>" +
                                                        "<td>"+elem.text+"</td>" +
                                                    "<td>";

                                            if (elem.show_download_btn){
                                                html += "<a href='/"+DB_NAME+"/chargebacks/generate_849/"+elem.filename+"/download' class='btnGenerate849ResultsFile tt' title='"+elem.filename+"'>" +
                                                            "<i class='fa fa-download'></i> Download" +
                                                        "</a>";
                                            }
                                        html+= "</td></tr>";
                            }
                            html += "</tbody></table>";
                        }

                        // show modal dialog with results generate 849
                        modalGenerate849Results.find('.modal-body').html(html);
                        modalGenerate849Results.fadeIn(500, function(){
                            modalGenerate849Results.modal({'backdrop':'static'}).modal("show");
                        });

                    }else{
                        show_toast_error_message(response.message, 'bottomRight');
                    }
                },
                complete: function() {
                    setTimeout(function () {
                        elem.removeClass('disabled').html(originalText);
                    }, 500);
                },
                error: function () {
                    elem.removeClass('disabled').html(originalText);
                    show_toast_error_message('Internal Error', 'bottomRight');
                }
            });
        }else{
            show_toast_warning_message("Select at least 1 Chargeback to continue", 'bottomRight');
        }
    },

    download_849_files: function () {
        $(".btnGenerate849ResultsFile").each(function () {
            window.open($(this).attr('href'), '_blank');
        });
    },

};


$(function () {

    // Distributor Dropdown populated with DC Names of the Customer selected above
    selectSearchFiltersCustomer.change(function () {
        selectSearchFiltersDistributor.html('');
        let cid = $(this).val();
        if (cid) {
            $.ajax({
                type: "POST",
                url: `/${DB_NAME}/customers/direct/${cid}/distribution_centers/json`,
                data: {},
                dataType: 'json',
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                },
                success: function (response) {
                    let options = '<option value="">-----</option>';
                    for (let i = 0; i < response.length; i++) {
                        let elem = response[i];
                        options += '<option value="' + elem.pk + '">' + elem.fields['name'] + '</option>';
                    }
                    selectSearchFiltersDistributor.html(options).trigger('change');
                },
                error: function () {
                    show_toast_error_message('Internal Error');
                }
            });
        }else{
            selectSearchFiltersDistributor.html('').trigger('change');
        }
        $(this).attr('selected', 'selected');
    });

    // selected customers
    selectSearchFiltersCustomer.trigger('change');

    // DataTable
    if (dtChargebacksSearch !== undefined && dtChargebacksSearch !== '') {
        $(dtChargebacksSearch).DataTable().clear();
        dtChargebacksSearch.destroy();
    }
    dtChargebacksSearch = tableChargebacksSearch.DataTable({
        lengthMenu:     [[50, 100, 150, -1], [50, 100, 150, "All"]],
        scrollY:        '35vh',
        scrollX:        true,
        dom: "<'row'<'col-4'l><'col-4'i><'col-4 text-right buttons_container'f>>" + "<'row'<'col-12'tr>>" + "<'row dt_footer'<'col-sm-5' B><'col-sm-7'p>>",
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
                return 'Chargebacks_Search_' + n;
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
                return 'Chargebacks_Search_' + n;
                },
                exportOptions: {
                    columns: ':not(.notexport)',
                },
            }
            ],

        processing:     true,
        serverSide:     true,
        responsive:     true,
        info:           true,
        order:          [1, "desc"],
        language : {
            search:             "",
            searchPlaceholder:  "Search ...",
            processing:         SPINNER_LOADER,
        },
        select: true,
        ajax: {
            url:    `/${DB_NAME}/chargebacks/search/load_data`,
            type:   'POST',
            data: function ( d ) {
                return $.extend({}, d, {
                    "payload": inputChargebacksSearchSelectedFilters.val()
                });
            }
        },
        initComplete: function() {
            let $searchInput = $('#tableChargebacksSearch_filter input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dtChargebacksSearch.search( this.value ).draw();
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
            },
            {
                "targets": [0, 12],
                "sortable": false,
                "searchable": false,
            },
            {
                type:'date',
                "targets": [5, 11]
            }
        ],
        columns: [
            {data: 'id'},
            {
                data: 'cbid',
                render : function(data, type, row) {
                    return '<span db="'+DB_NAME+'" target="/chargebacks/'+row["id"]+'/details">' +
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
                    if (row['request'] === row['issued']){
                        html  = '<span class="font-11" style="color: #228b22">' + data + '</span>';
                    }else{
                        html  = '<span class="font-11">' + data + '</span>';
                    }
                    return html
                }
            },
            {data: 'issued'},
            {
                data: 'stage',
                render : function(data, type, row) {
                    let html = '';
                    if (row['substage'] === SUBSTAGE_TYPE_NO_ERRORS_DISPLAY){
                        html  = '<span class="text-success">' + data + '</span>';
                    }else{
                        html  = '<span class="text-danger">' + data + '</span>';
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
                    }else{
                        html  = '<span class="text-danger">' + data + '</span>';
                    }
                    return html
                }
            },
            {data: 'imported'},
            {
                data: 'status',
                render : function(data, type, row) {
                    let html = '';
                    if (row['substage'] === SUBSTAGE_TYPE_NO_ERRORS_DISPLAY){
                        html  = '<i class="fas fa-check text-success"></i>';
                    }else{
                        html  = '<i class="fa fa-exclamation-triangle text-warning"></i>';
                    }
                    return html
                }
            },
        ],
    });
    // hide paging cause dt doesnt allow to do this in runtime
    // $('#tableChargebacksSearch_paginate').css("display", "none");
    // $('#tableChargebacksSearch_length').css("display", "none");
    $('#tableChargebacksSearch_filter').css("display", "none");
    $('<button id="btnSelectAllRows" value="select_all" type="button" onclick="CB_SEARCH.select_all_lines();" class="btn btn-primary btn-sm">Select All</button>').appendTo("#tableChargebacksSearch_wrapper .buttons_container");
    if(!is_read_only_user) {
        $('<button type="button" onclick="CB_SEARCH.regenerate_849($(this));" class="btn btn-warning btn-sm ml-1">Re-Generate 849</button>').appendTo("#tableChargebacksSearch_wrapper .buttons_container");
    }else{
        $('<button type="button" onclick="APP.get_read_only_user_error();" class="btn btn-warning btn-sm ml-1">Re-Generate 849</button>').appendTo("#tableChargebacksSearch_wrapper .buttons_container");
    }
});
