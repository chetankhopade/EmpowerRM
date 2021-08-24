// span
let spanTitleParserActivity = $(".spanTitleParserActivity");

// select
let selectParserActivityRangeTableDetails = $("#selectParserActivityRangeTableDetails");
let selectParserActivityChartTimeframe = $("#selectParserActivityChartTimeframe");
let selectParserActivityChartMetrics = $("#selectParserActivityChartMetrics");

//modal
let modalParserActivityChartDetails = $("#modalParserActivityChartDetails");

// Chart canvas
let canvasParserActivityChart = $("#canvasParserActivityChart");
let divParserActivityChartLoader = $("#divParserActivityChartLoader");

// table and datatable
let tableServiceStatus = $("#tableServiceStatus");
let dtServiceStatus;


let SERVICE_STATUS = {

    name: 'SERVICE_STATUS',
    cid: '',
    accno: '',
    company_id: '',

    // API to get data (CBs count) from edi api and show in modal
    get_count_of_cbs_data: function (target, timeframe) {

        if (target) {

            let tdTarget = $("#td"+target);

            let url = `${EDI_API_URL}/parser_activity/${SERVICE_STATUS.cid}/${target}?token=${EDI_API_TOKEN}&timeframe=${timeframe}`;

            if (target === 'AtERM'){
                url = `/default/administration/service_status/get_count_of_open_cbs_by_partner?cid=${SERVICE_STATUS.company_id}&accno=${SERVICE_STATUS.accno}`;
            }

            $.ajax({
                url: url,
                type: "GET",
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    tdTarget.html(SPINNER_LOADER_XS);
                },
                success: function (response) {
                    tdTarget.html(response.data)
                },
                error: function (response) {
                    alert(response.message);
                }
            });
        }
    },

    // reload ajax when dropdown timeframe changes
    load_data: function () {
        // reload data table ajax
        dtServiceStatus.ajax.reload();
    },

    // CHART Section
    update_parser_activity_data: function () {
        let timeframe = selectParserActivityChartTimeframe.val();
        let metric = selectParserActivityChartMetrics.val();
        spanTitleParserActivity.html(timeframe);

        // Update Counters
        // get 844Vin data
        SERVICE_STATUS.get_count_of_cbs_data('844Vin', timeframe);
        // get 997Vout data
        SERVICE_STATUS.get_count_of_cbs_data('997Vout', timeframe);
        // get AtERM data
        SERVICE_STATUS.get_count_of_cbs_data('AtERM', '');

        // Update Chart
        SERVICE_STATUS.drawChart_ParserActivity(timeframe, metric);
    },

    // draw Chart
    drawChart_ParserActivity: function (timeframe, metric) {

        // chart config
        let chartConfig = {
            type: 'line',
            data: {},
            options: {
                responsive: true,
                scales: {
                    xAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Dates'
                        }
                    }],
                    yAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Values'
                        }
                    }]
                }
            }
        };

        // init chart
        let chartParserActivity = new Chart(canvasParserActivityChart, chartConfig);

        $.ajax({
            url: `${EDI_API_URL}/parser_activity/${SERVICE_STATUS.cid}/chart?token=${EDI_API_TOKEN}&timeframe=${timeframe}&metric=${metric}`,
            beforeSend: function(){
                canvasParserActivityChart.hide();
                divParserActivityChartLoader.show();
            },
            type: 'GET',
            dataType: 'json'
        }).done(function(response){
            divParserActivityChartLoader.hide();
            chartParserActivity.data.labels = response.labels;
            chartParserActivity.data.datasets = response.datasets;
            chartParserActivity.update();
            canvasParserActivityChart.show();
        });

    },

};


$(function () {

    // Main DataTable
    dtServiceStatus = tableServiceStatus.DataTable({
        lengthMenu:     [[-1], ["All"]],
        scrollY:        '40vh',
        processing:     true,
        responsive:     true,
        info:           true,
        order:          [[1, 'asc']],
        language : {
            search:             "",
            searchPlaceholder:  "Search ...",
            loadingRecords:     "",
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
            });
            $(".btnShowModalChartDetail").click(function () {
                SERVICE_STATUS.cid = $(this).attr('cid');
                SERVICE_STATUS.accno = $(this).attr('partner_acctno');
                SERVICE_STATUS.company_id = $(this).attr('customer_ermid');

                let customer_isa = $(this).attr('customer_isa');
                let partner_isa = $(this).attr('partner_isa');

                modalParserActivityChartDetails.find('.modal-header').html("<h5 class='modal-title'>Parser Activity - Details</h5> <span>("+customer_isa+" - "+partner_isa+")</span>");
                modalParserActivityChartDetails.modal({backdrop: 'static', keyboard: false});
                modalParserActivityChartDetails.modal('show');
            });
        },
        ajax: {
            url:    `${EDI_API_URL}/parser_activity/?token=${EDI_API_TOKEN}`,
            type:   'GET',
            data: function ( d ) {
                return $.extend({}, d, {
                    "timeframe": selectParserActivityRangeTableDetails.val(),
                });
            }
        },
        initComplete: function() {
            let $searchInput = $('#tableServiceStatus_filter input');
            $searchInput.unbind();
            $searchInput.bind('keyup', function(e) {
                if(this.value.length === 0 || this.value.length >= 3) {
                    dtServiceStatus.search( this.value ).draw();
                }
            });
        },
        columnDefs: [
            {
                "targets": [0],
                // "visible": false,
                "searchable": false,
                "orderable": false,
            }
        ],
        columns: [
            {
                data: '',
                render : function(data, type, row) {
                    return  '<a class="btnShowModalChartDetail tt" cid="'+row["id"]+'" customer_ermid="'+row["customer_ermid"]+'" customer_isa="'+row["customer_isa"]+'" partner_isa="'+row["partner_isa"]+'" partner_acctno="'+row["partner_acctno"]+'" title="Show Details">' +
                        '<i class="fa fa-line-chart"></i>' +
                        '</a>'
                }
            },
            {data: 'customer_isa'},
            {data: 'partner_isa'},
            {
                data: 'state',
                class: 'text-center',
                render : function(data, type, row) {
                    if (data === 'T'){
                        return '<span class="badge badge-pill badge-secondary tt" title="Test">'+data+'</span>'
                    }else{
                        return '<span class="badge badge-pill badge-success tt" title="Production">'+data+'</span>'
                    }
                }
            },
            {
                data: 'count_of_errors_total',
                class: 'text-center',
                render : function(data, type, row) {
                    return '<span>' + data + '</span> (<span>'+row["count_of_errors_unack"]+'</span>/<span>'+row["count_of_errors_ack"]+'</span>)'
                }
            },
            {
                data: 'count_of_transactions_total',
                class: 'text-center',
            },
            {
                data: 'p_stat',
                class: 'text-center',
                render : function(data, type, row) {
                    let html = '';
                    if (data === 'ACTIVE'){
                        html = '<span class="text-success _700">' + data + '</span>';
                    } else if (data === 'IDLE') {
                        html = '<span class="text-primary _700">' + data + '</span>';
                    } else if (data === 'DUSTY') {
                        html = '<span class="text-warning _700">' + data + '</span>';
                    } else {
                        html = '<span class="text-danger _700">' + data + '</span>';
                    }
                    return html
                }
            },
            {
                data: 'last_timestamp_inbound_str',
                class: 'text-center',
            },
            {
                data: 'last_timestamp_outbound_str',
                class: 'text-center',
            },
            {
                data: 'last_timestamp_sftp_str',
                class: 'text-center',
            },
            {
                data: 'count_of_unique_cbs_by_timeframe',
                class: 'text-center',
            },
            {
                data: 'sum_of_kchars_by_timeframe',
                class: 'text-center',
            },
            {
                data: 'count_of_unique_files_by_timeframe',
                class: 'text-center',
            },
            {
                data: 'sum_of_lines_by_timeframe',
                class: 'text-center',
            },
            {
                data: '',
                class: 'text-center',
                render : function(data, type, row) {
                    return  '<i class="fa fa-play-circle text-success font-17 tt" title="Run"></i>' +
                        '<i class="fa fa-stop-circle font-17 ml-1 tt" title="Stop"></i>' +
                        '<i class="fa fa-refresh font-17 ml-1 tt" title="Refresh"></i>' +
                        '<i class="fa fa-eye font-17 ml-1 tt" title="View"></i>'
                }
            },
        ],
    });

    // hide paging cause dt doesnt allow to do this in runtime
    // $('#tableServiceStatus_paginate').css("display", "none");
    // $('#tableServiceStatus_length').css("display", "none");

    // Modal Opens (API calls and Chart drawn)
    modalParserActivityChartDetails.on('shown.bs.modal', function (e) {
        // chart (call it first time)
        SERVICE_STATUS.update_parser_activity_data();

    });

    // Selects2 (remove searchbox)
    selectParserActivityRangeTableDetails.select2({
        minimumResultsForSearch: -1
    });

    selectParserActivityChartTimeframe.select2({
        minimumResultsForSearch: -1
    });

    selectParserActivityChartMetrics.select2({
        minimumResultsForSearch: -1
    });


    // // TODO: Check later after changes in main DataTable
    // let get_last_inbound_transaction = function (){
    //     let elem_last_file_received = $("#tdEDILastFileReceived");
    //     $.ajax({
    //         type: "GET",
    //         url: "/"+DB_NAME+"/administration/service_status/get_last_inbound_transaction_from_edi_api",
    //         data: {},
    //         dataType: 'json',
    //         beforeSend: function () {
    //             elem_last_file_received.removeClass('text-danger').html('<img src="/static/images/loading2.gif" width="24" height="24" />');
    //         },
    //         success: function (response) {
    //             if (response.result === 'ok'){
    //                 elem_last_file_received.html(response.last_file_received_timestamp);
    //                 if (response.last_file_received_timestamp_older_than_4hrs){
    //                     elem_last_file_received.addClass('text-danger');
    //                 }
    //             }else{
    //                 elem_last_file_received.html(response.message).addClass('text-danger');
    //             }
    //         },
    //         error: function (response) {
    //             show_toast_error_message(response.message);
    //         }
    //     });
    // };
    // get_last_inbound_transaction();
    //
    // let get_last_outbound_transaction = function (){
    //     let elem_last_file_sent = $("#tdEDILastFileSent");
    //     $.ajax({
    //         type: "GET",
    //         url: "/"+DB_NAME+"/administration/service_status/get_last_outbound_transaction_from_edi_api",
    //         data: {},
    //         dataType: 'json',
    //         beforeSend: function () {
    //             elem_last_file_sent.removeClass('text-danger').html('<img src="/static/images/loading2.gif" width="24" height="24" />');
    //         },
    //         success: function (response) {
    //             if (response.result === 'ok'){
    //                 elem_last_file_sent.html(response.last_file_sent_timestamp);
    //                 if (response.last_file_sent_timestamp_older_than_4hrs){
    //                     elem_last_file_sent.addClass('text-danger');
    //                 }
    //             }else{
    //                 elem_last_file_sent.html(response.message).addClass('text-danger');
    //             }
    //         },
    //         error: function (response) {
    //             show_toast_error_message(response.message);
    //         }
    //     });
    // };
    // get_last_outbound_transaction();
    //
    // let get_parser_activity_data = function () {
    //     let tbodyParserActivityData = $("#tbodyParserActivityData");
    //     $.ajax({
    //         type: "GET",
    //         url: "/"+DB_NAME+"/administration/service_status/get_parser_activity_from_edi_api",
    //         data: {},
    //         dataType: 'json',
    //         beforeSend: function () {
    //             tbodyParserActivityData.html('<tr>' +
    //                 '<td colspan="10" class="text-center justify-content-center">' +
    //                 '<img src="/static/images/loading2.gif" width="36" height="36" />' +
    //             '</td>' +
    //             '</tr>');
    //         },
    //         success: function (response) {
    //             tbodyParserActivityData.html('');
    //             if (response.result === 'ok'){
    //                 for (let i = 0; i < response.items.length; i++){
    //                     let elem = response.items[i];
    //                     tbodyParserActivityData.append(
    //                         '<tr class="font-11">' +
    //                         '<td>'+elem.company+'</td>' +
    //                         '<td>'+elem.wholesaler+'</td>' +
    //                         '<td>'+elem.token+'</td>' +
    //                         '<td class="text-center">'+elem.kchars+'</td>' +
    //                         '<td>'+elem.files+'</td>' +
    //                         '<td>'+elem.lines+'</td>' +
    //                         '<td>'+elem.errors+'</td>' +
    //                         '<td>'+elem.last_received_timestamp+'</td>' +
    //                         '<td class="text-center">' +
    //                         '<i class="fa fa-play-circle text-success font-17"></i>' +
    //                         '<i class="fa fa-stop-circle font-17"></i>' +
    //                         '<i class="fa fa-refresh font-17"></i>' +
    //                         '<i class="fa fa-eye font-17"></i>' +
    //                         '</td>' +
    //                         '</tr>');
    //                 }
    //             }else{
    //                 tbodyParserActivityData.html('<tr><td colspan="10" class="text-center justify-content-center text-danger">'+response.message+'</td></tr>');
    //             }
    //         },
    //         error: function (response) {
    //             show_toast_error_message(response.message);
    //         }
    //     });
    // };
    // get_parser_activity_data();

});