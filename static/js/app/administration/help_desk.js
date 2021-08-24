// vars
let btnZohoGrantAccess = $("#btnZohoGrantAccess");
let tableZohoTickets = $("#tableZohoTickets");
let modalZohoTicketAddComment = $("#modalZohoTicketAddComment");
let modalZohoCloseTicket = $("#modalZohoCloseTicket");
let inputZohoTicketId = $("#inputZohoTicketId");
let inputZohoTicketIdCloseTicket = $("#inputZohoTicketIdCloseTicket");
let textareaZohoTicketAddComment = $("#textareaZohoTicketAddComment");

let dataTable = undefined;

let HELPDESK = {

    name: 'HELPDESK',

    show_loader_in_table: function () {
        tableZohoTickets.html("<tr>" +
            "<td colspan='10' class='text-center justify-content-center'>" +
            "<img src='/static/images/loading2.gif' width='70' height='70' alt='zoho_loader'/>" +
            "</td>" +
            "</tr>");
    },

    loadDataTable: function (dataset_tickets) {
        tableZohoTickets.html('');
        dataTable = tableZohoTickets.DataTable({
            "lengthMenu": [[10, 20, 50, 100, -1], [10, 20, 50, 100, "All"]],
            "scrollY":        "50vh",
            "scrollCollapse": true,
            "order": [[ 2, "desc" ]],
            data: dataset_tickets,
            language : {
                search: "",
                searchPlaceholder: "Search ..."
            },
            columns: [
                { title: "Ticket No." },
                { title: "Created At" },
                { title: "Email" },
                { title: "Subject" },
                { title: "Status" },
                { title: "Actions" },
            ]
        });
    },

    getDirJSONResponse: function(){
        if (dataTable !== undefined) {
            dataTable.destroy();
        }

        let dataset_tickets = [];
        $.ajax({
            url: "/default/administration/helpdesk/tickets",
            type: "POST",
            data: {
                "access_token": sessionStorage.getItem('access_token'),
                "org_id": sessionStorage.getItem('org_id'),
            },
            dataType: "json",
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
                HELPDESK.show_loader_in_table();
            },
            success: function(response){
                if (response.result === 'ok'){
                    response.tickets.forEach(function (item) {
                        let ticket_id = item["id"];
                        let ticket_no = item["ticketNumber"];
                        let created_at = item["createdTime"];
                        let email = item["email"];
                        let subject = item["subject"];
                        let status = item["status"];
                        let rows = [
                            ticket_no,
                            created_at,
                            email,
                            subject,
                            (status === 'Open'?"<span class='badge badge-success font-9 p-04'>"+status+"</span>":"<span class='badge badge-danger font-9 p-04'>"+status+"</span>"),
                            "<a class='btn btn-xs btn-primary' onclick='HELPDESK.showModalTicketComment($(this));' tid='"+ticket_id+"' tno='"+ticket_no+"' data-toggle='tooltip' data-placement='top' title='Add Comment'>" +
                                "<i class='fa fa-comment'></i>" +
                            "</a>" +
                            (status === 'Open'?"<a class='btn btn-xs btn-danger ml-2 text-white' onclick='HELPDESK.showModalCloseTicket($(this));' tid='"+ticket_id+"' tno='"+ticket_no+"' data-toggle='tooltip' data-placement='top' title='Close Ticket'>" +
                                "<i class='fa fa-close'></i>" +
                            "</a>":"")
                        ];
                        dataset_tickets.push(rows);
                    });
                }else{
                    if (response.message === '401'){
                        window.sessionStorage.clear();
                        APP.show_app_loader();
                        setTimeout(function () {
                            location.reload();
                        });

                    }
                }

            },
            complete: function () {
                if (dataset_tickets){
                    HELPDESK.loadDataTable(dataset_tickets);
                }
            }
        });


    },

    // modal Add Comment to Ticket
    showModalTicketComment: function (elem) {
        let ticket_id = elem.attr('tid');
        let ticket_no = elem.attr('tno');
        inputZohoTicketId.val(ticket_id);
        textareaZohoTicketAddComment.val('');
        modalZohoTicketAddComment.find('.modal-title').html('Add Comment to Ticket: #'+ticket_no);
        modalZohoTicketAddComment.modal('show');
    },

    // Add Comment API
    addTicketComment: function (elem) {
        let loadingText = "<span class='font-11'><i class='fa fa-circle-o-notch fa-spin'></i> Submitting...</span>";
        let originalText = elem.html();
        let ticket_id = inputZohoTicketId.val();
        let comments = textareaZohoTicketAddComment.val();

        // send comment (ajax)
        if (ticket_id && comments){
            $.ajax({
                url: "/default/administration/helpdesk/tickets/"+ticket_id+"/comments",
                type: "POST",
                data: {
                    "access_token": sessionStorage.getItem('access_token'),
                    "org_id": sessionStorage.getItem('org_id'),
                    "comments": comments,
                },
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                    elem.addClass('disabled').html(loadingText);
                },
                success: function(response){
                    if (response.result === 'ok'){

                        // show success message
                        show_toast_success_message(response.message, 'topRight');

                        // close modal
                        modalZohoTicketAddComment.modal('hide');

                        // refresh data again in table
                        HELPDESK.getDirJSONResponse();

                    }else{
                        show_toast_warning_message(response.message, 'bottomRight');
                    }

                },
                complete: function () {
                    elem.removeClass('disabled').html(originalText);
                },
                error: function () {
                    show_toast_error_message('Ajax Error')
                }
            });
        }else {
            show_toast_warning_message('Comments is required.', 'bottomRight')
        }
    },

    // show modal Close Ticket
    showModalCloseTicket: function (elem) {
        let ticket_id = elem.attr('tid');
        let ticket_no = elem.attr('tno');
        inputZohoTicketIdCloseTicket.val(ticket_id);
        modalZohoCloseTicket.find('.modal-title').html('Close Ticket: #'+ticket_no);
        modalZohoCloseTicket.modal('show');
    },

    // Close Ticket API
    closeTicket: function (elem) {
        let loadingText = "<span class='font-11'><i class='fa fa-circle-o-notch fa-spin'></i> Submitting...</span>";
        let originalText = elem.html();
        let ticket_id = inputZohoTicketIdCloseTicket.val();

        // send to server (ajax)
        if (ticket_id){
            $.ajax({
                url: "/default/administration/helpdesk/tickets/"+ticket_id+"/close",
                type: "POST",
                data: {
                    "access_token": sessionStorage.getItem('access_token'),
                    "org_id": sessionStorage.getItem('org_id'),
                },
                dataType: "json",
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                    elem.addClass('disabled').html(loadingText);
                },
                success: function(response){
                    if (response.result === 'ok'){

                        // show success message
                        show_toast_success_message(response.message, 'topRight');

                        // close modal
                        modalZohoCloseTicket.modal('hide');

                        // refresh data again in table
                        HELPDESK.getDirJSONResponse();

                    }else{
                        show_toast_warning_message(response.message, 'bottomRight');
                    }

                },
                complete: function () {
                    elem.removeClass('disabled').html(originalText);
                },
                error: function () {
                    show_toast_error_message('Ajax Error')
                }
            });
        }else {
            show_toast_warning_message('Comments is required.', 'bottomRight')
        }
    },

    persistAuthInfo: function () {
        if (ACCESS_TOKEN) {
            sessionStorage.setItem('access_token', ACCESS_TOKEN);
        }
        sessionStorage.setItem('org_id', ORG_ID);
    },

    tokenAdquired: function () {
        let access_token = sessionStorage.getItem('access_token');
        return (access_token !== undefined && access_token !== 'None' && access_token != null)
    },

};


$(function () {

    let init_auth_status = function () {
        HELPDESK.persistAuthInfo();

        if (!HELPDESK.tokenAdquired()){
            // redirect to zoho page to get grant access
            btnZohoGrantAccess[0].click();
        }else{
            // load table making api calls with access token
            HELPDESK.getDirJSONResponse();
        }
    };

    init_auth_status();

});
