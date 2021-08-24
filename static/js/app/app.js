
function csrfSafeMethod (method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function getCookie (name) {
    let value = "; " + document.cookie;
    let parts = value.split("; " + name + "=");
    if (parts.length === 2) return parts.pop().split(";").shift();
}

function compareStrings (str1, str2) {
    return str1 === str2;
}

function isValidEmailAddress (emailAddress) {
    let pattern = /^([a-z\d!#$%&'*+\-\/=?^_`{|}~\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]+(\.[a-z\d!#$%&'*+\-\/=?^_`{|}~\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]+)*|"((([ \t]*\r\n)?[ \t]+)?([\x01-\x08\x0b\x0c\x0e-\x1f\x7f\x21\x23-\x5b\x5d-\x7e\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]|\\[\x01-\x09\x0b\x0c\x0d-\x7f\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))*(([ \t]*\r\n)?[ \t]+)?")@(([a-z\d\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]|[a-z\d\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF][a-z\d\-._~\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]*[a-z\d\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])\.)+([a-z\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]|[a-z\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF][a-z\d\-._~\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]*[a-z\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])\.?$/i;
    return pattern.test(emailAddress);
}

function isValidNumber (elem, min, max, decimals) {
    let nvalue;
    let value = elem.val();
    // remove comma from float string
    // EA-1450 - 1.8 Unable to edit a manual chargeback because comma in submitted amount
    if (value){
        value = value.replace(/,/g, '');
    }
    // check if is emty
    if (value === ''){
        // value = parseFloat(min).toFixed(decimals);
        elem.val(value);
        return;
    }
    // check if is NaN
    if (isNaN(value)){
        // nvalue = parseFloat(min).toFixed(decimals);
        elem.val('');
        return;
    }
    // check if value less than min
    if (value < min) {
        nvalue = parseFloat(min).toFixed(decimals);
        elem.val(nvalue);
        return;
    }
    // check if is greater than max
    if (max > 0 && value > max){
        nvalue = parseFloat(max).toFixed(decimals);
        elem.val(nvalue);
        return;
    }
    // add decimals to value
    nvalue = parseFloat(value).toFixed(decimals);
    elem.val(nvalue);
}

function show_toast_error_message (msg, position='topCenter') {

    iziToast.error({
        title: 'Error',
        message: msg,
        position: position,    // bottomRight, bottomLeft, topRight, topLeft, topCenter, bottomCenter
    });

}
function preview_warning_error(){
    show_toast_warning_message("To preview or run a report, the report must contain at least one field of type Date.  Please add a field that contains dates to your report and then retry")
}
function show_toast_success_message (msg, position='topCenter') {

    iziToast.success({
        title: 'Success',
        message: msg,
        position: position
    });
}


function show_toast_warning_message (msg, position='topCenter') {

    iziToast.warning({
        title: 'Warning',
        message: msg,
        position: position,
    });

}

function validate_dates_with_year_first(start_date, end_date){
    // dates with format YYYY-MM-DD or YYYY/MM/DD
    // new Date(year, month, day, hours, minutes, seconds, milliseconds)

    let fmtStartDate = '';
    let fmtEndDate = '';
    if (start_date.val().search('/') === -1){
        fmtStartDate = start_date.val().split("-");
        fmtEndDate= end_date.val().split("-");
    }else{
        fmtStartDate = start_date.val().split("/");
        fmtEndDate= end_date.val().split("/");
    }
    let startDate = new Date(fmtStartDate[0], fmtStartDate[1] - 1, fmtStartDate[2]);
    let endDate = new Date(fmtEndDate[0], fmtEndDate[1] - 1, fmtEndDate[2]);
    return startDate <= endDate;
}

function validate_dates_with_month_first(start_date, end_date, show_helper_text){
    // dates with format MM-DD-YYYY or MM/DD/YYYY
    // new Date(year, month, day, hours, minutes, seconds, milliseconds)
    let fmtStartDate = '';
    let fmtEndDate = '';
    if (start_date.val().search('/') === -1){
        fmtStartDate = start_date.val().split("-");
        fmtEndDate= end_date.val().split("-");
    }else{
        fmtStartDate = start_date.val().split("/");
        fmtEndDate= end_date.val().split("/");
    }
    let startDate = new Date(fmtStartDate[2], fmtStartDate[0] - 1, fmtStartDate[1]);
    let endDate = new Date(fmtEndDate[2], fmtEndDate[0] - 1, fmtEndDate[1]);

    if (show_helper_text){
        end_date.parent().find('span').remove();
    }

    if (startDate <= endDate){
        start_date.removeClass('border-red');
        end_date.removeClass('border-red');
        return true;
    }else{
        start_date.addClass('border-red');
        end_date.addClass('border-red');
        if (show_helper_text){
            end_date.parent().append('<span class="text-danger font-10 font-italic">End date cannot be earlier than start date</span>');
        }
        return false;
    }
}

function validate_required_input(elem) {
    elem.parent().find('span').remove();
    if (!elem.val() || elem.val() === ''){
        elem.addClass('border-red');
        elem.parent().append('<span class="text-danger font-10 font-italic">Field is required</span>');
        return false;
    }else{
        elem.removeClass('border-red');
        return true;
    }
}

// EA-1191 No Phone No. validation on profile. Allow to take only special characters and numbers
function isValidPhoneNumber (phoneNumber) {
    let pattern = /^[0-9-+()]*$/;
    return pattern.test(phoneNumber);
}

function get_datatable_wrapper_width_based_on_screen_size() {
    let width = $( window ).width();
    let value = '170vh';
    if (width >= 1900) {
        value = '178vh';
    }
    return value;
}

function derive_status_based_on_date_ranges_with_month_first(start_date, end_date){
    // dates with format MM-DD-YYYY or MM/DD/YYYY
    // new Date(year, month, day, hours, minutes, seconds, milliseconds)
    let fmtStartDate = '';
    let fmtEndDate = '';
    if (start_date.val().search('/') === -1){
        fmtStartDate = start_date.val().split("-");
        fmtEndDate= end_date.val().split("-");
    }else{
        fmtStartDate = start_date.val().split("/");
        fmtEndDate= end_date.val().split("/");
    }
    let today = new Date(); //Current date
    let startDate = new Date(fmtStartDate[2], fmtStartDate[0] - 1, fmtStartDate[1]);
    let endDate = new Date(fmtEndDate[2], fmtEndDate[0] - 1, fmtEndDate[1]);

    let status = '-';
    let cls = 'text-dark';
    if (startDate > today){
        status = 'Pending';
        cls = 'text-warning'
    } else if (endDate < today) {
        status = 'Inactive';
        cls = 'text-danger';
    } else {
        status = 'Active';
        cls = 'text-success';
    }
    return {
        status: status,
        cls: cls
    };
}


function validateDateFormat(dateSTring)
{
    // dates with format MM-DD-YYYY or MM/DD/YYYY are valid
    var dateformat = /^(0?[1-9]|1[012])[\/\-](0?[1-9]|[12][0-9]|3[01])[\/\-]\d{4}$/;
    // Match the date format through regular expression
    if(dateSTring.match(dateformat))
    {
        var opera1 = dateSTring.split('/');
        var opera2 = dateSTring.split('-');
        lopera1 = opera1.length;
        lopera2 = opera2.length;
        // Extract the string into month, date and year
        if (lopera1>1)
        {
            var pdate = dateSTring.split('/');
        }
        else if (lopera2>1)
        {
            var pdate = dateSTring.split('-');
        }
        var mm  = parseInt(pdate[0]);
        var dd = parseInt(pdate[1]);
        var yy = parseInt(pdate[2]);
        // Create list of days of a month [assume there is no leap year by default]
        var ListofDays = [31,28,31,30,31,30,31,31,30,31,30,31];
        if (mm==1 || mm>2)
        {
            if (dd>ListofDays[mm-1])
            {
                alert('Invalid date format!');
                return false;
            }
        }
        if (mm==2)
        {
            var lyear = false;
            if ( (!(yy % 4) && yy % 100) || !(yy % 400))
            {
                lyear = true;
            }
            if ((lyear==false) && (dd>=29))
            {
                return false;
            }
            if ((lyear==true) && (dd>29))
            {
                return false;
            }
        }

        return true;
    }
    else
    {
        return false;
    }
}

function get_start_end_date_for_report(){
    // get Today's date in mm/dd/yyyy format
    let today = new Date();
    let dd = today.getDate();
    let dateObj = new Date();
    dateObj.setDate(dateObj.getDate()-730);


    let mm = today.getMonth()+1;
    let yyyy = today.getFullYear();
    if(dd<10)
    {
        dd='0'+dd;
    }

    if(mm<10)
    {
        mm='0'+mm;
    }
    let end_date = mm+'/'+dd+'/'+yyyy;

    let sd = dateObj.getDate();
    mm = dateObj.getMonth()+1;
    yyyy = dateObj.getFullYear();
    if(sd<10)
    {
        sd='0'+sd;
    }

    if(mm<10)
    {
        mm='0'+mm;
    }

    let start_date = mm+'/'+sd+'/'+yyyy;
    return [{'end_date': end_date, 'start_date': start_date}]
}

function isDate(_date) {
    // dateStr will be ISO or date string , returns true or false
    // Required in reports
    // EA-1541 Static field Value shows incorrectly when running report
    const _regExp  = new RegExp('^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(.[0-9]+)?(Z)?$');
    return _regExp.test(_date);
    // return !isNaN(new Date(dateStr).getDate());
}

function get_date_from_string(dateStr) {

    let day = new Date(dateStr);
    let dd = day.getDate();

    let mm = day.getMonth()+1;
    let yyyy = day.getFullYear();
    if(dd<10)
    {
        dd='0'+dd;
    }

    if(mm<10)
    {
        mm='0'+mm;
    }
    return  mm+'/'+dd+'/'+yyyy;
}

function isNumericData(n) {
  return !isNaN(parseFloat(n)) && isFinite(n);
}

function isFutureDate(idate){
var today = new Date().getTime(),
    idate = idate.split("/");

idate = new Date(idate[2], idate[1] - 1, idate[0]).getTime();
return (today - idate) < 0 ? true : false;
}

function isNumberKey(txt, evt) {
      var charCode = (evt.which) ? evt.which : evt.keyCode;
      if (charCode == 46) {
        //Check if the text already contains the . character
        if (txt.value.indexOf('.') === -1) {
          return true;
        } else {
          return false;
        }
      } else {
        if (charCode > 31 &&
          (charCode < 48 || charCode > 57))
          return false;
      }
      return true;
    }

function newexportaction(e, dt, button, config) {
    var self = this;
    var oldStart = dt.settings()[0]._iDisplayStart;
    dt.one('preXhr', function (e, s, data) {
        // Just this once, load all data from the server...
        data.start = 0;
        data.length = 2147483647;
        dt.one('preDraw', function (e, settings) {
            // Call the original action function
            if (button[0].className.indexOf('buttons-copy') >= 0) {
                $.fn.dataTable.ext.buttons.copyHtml5.action.call(self, e, dt, button, config);
            } else if (button[0].className.indexOf('buttons-excel') >= 0) {
                $.fn.dataTable.ext.buttons.excelHtml5.available(dt, config) ?
                    $.fn.dataTable.ext.buttons.excelHtml5.action.call(self, e, dt, button, config) :
                    $.fn.dataTable.ext.buttons.excelFlash.action.call(self, e, dt, button, config);
            } else if (button[0].className.indexOf('buttons-csv') >= 0) {
                $.fn.dataTable.ext.buttons.csvHtml5.available(dt, config) ?
                    $.fn.dataTable.ext.buttons.csvHtml5.action.call(self, e, dt, button, config) :
                    $.fn.dataTable.ext.buttons.csvFlash.action.call(self, e, dt, button, config);
            } else if (button[0].className.indexOf('buttons-pdf') >= 0) {
                $.fn.dataTable.ext.buttons.pdfHtml5.available(dt, config) ?
                    $.fn.dataTable.ext.buttons.pdfHtml5.action.call(self, e, dt, button, config) :
                    $.fn.dataTable.ext.buttons.pdfFlash.action.call(self, e, dt, button, config);
            } else if (button[0].className.indexOf('buttons-print') >= 0) {
                $.fn.dataTable.ext.buttons.print.action(e, dt, button, config);
            }
            dt.one('preXhr', function (e, s, data) {
                // DataTables thinks the first item displayed is index 0, but we're not drawing that.
                // Set the property to what it was before exporting.
                settings._iDisplayStart = oldStart;
                data.start = oldStart;
            });
            // Reload the grid with the original page. Otherwise, API functions like table.cell(this) don't work properly.
            setTimeout(dt.ajax.reload, 0);
            // Prevent rendering of the full data to the DOM
            return false;
        });
    });
    // Requery the server with the new one-time export settings
    dt.ajax.reload();
};
const capitalize = (s) => {
  if (typeof s !== 'string') return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
}

// Get current date with YMDHMS for export
// year-month-date-hour-minutes-seconds
// EA-1094 - Add CSV export to all grids
function get_current_date_in_ymdhms_for_export(){
    let d = new Date();
    let year = d.getFullYear();
    let month = d.getMonth()+1;
    let day = d.getDate();
    let hour = d.getHours();
    let minute = d.getMinutes();
    let second = d.getSeconds();

    if (month < 10){
        month = "0"+month;
    }
    if (day < 10){
        day = "0"+day;
    }
    if (hour < 10){
        hour = "0"+hour;
    }
    if (minute < 10){
        minute = "0"+minute;
    }
    if (second < 10){
        second = "0"+second;
    }

    return year+month+day+hour+minute+second;
}


// modal Notifications
let modalNotifications = $("#modalNotifications");

// model read only user
let mdlreadonlyUser = $("#mdlreadonlyUser");

let APP = {

    name: 'APP',

    show_app_loader: function(){
        $.blockUI({
            message: $('#app_loader'),
            css: { 'left': '46%', 'width':'150px', 'height': '150', 'padding': '15px',  '-webkit-border-radius': '10px', '-moz-border-radius': '10px',  opacity: .8}
        });
    },

    hide_app_loader: function(){
        $.unblockUI();
    },
    preview_execute_url: function (elem,report_id,is_target=false) {
        let target_blank = false;
        if(is_target){
            target_blank = is_target;
        }
        let dbName = elem.parent().attr('db');
        let target = elem.parent().attr('target');
        let url = '/' + dbName + target;
        $.ajax({
                type: "GET",
                url: `/${DB_NAME}/report_builder/is_preveiw_data/${report_id}`,
                data: {},
                beforeSend: function () {},
                success: function (response) {
                    if(response.data.fields_to_fetch == false){
                        show_toast_warning_message("To preview or run a report, the report must contain at least one field of type Date.  Please add a field that contains dates to your report and then retry","bottomRight")
                        return false
                    }else{

                        if(target_blank == true) {
                            window.open(url, '_blank');
                        }else{
                            $.blockUI({
                            message: $('#app_loader'),
                            css: { 'left': '46%', 'width':'150px', 'height': '150', 'padding': '15px',  '-webkit-border-radius': '10px', '-moz-border-radius': '10px',  opacity: .8}
                            });
                            location.href = url;
                        }


                    }
                },
                error: function () {
                    show_toast_error_message('Internal Error', 'bottomRight');
                }
            });
        },
    // main function for redirections and links
    execute_url: function (elem, url_is_default=false, params='') {

        let dbName = elem.parent().attr('db');
        let target = elem.parent().attr('target');

        // if the db is the master and is not a default url then redirect it based on the select component
        if (dbName === 'default' && !url_is_default){
            dbName = $("#selectCompany").val();
        }

        let url = '/' + dbName + target;
        if (params){
            url += '?' + params;
        }

        this.show_app_loader();
        location.href = url;

    },
    home_execute_url: function(elem){
        let dbName = $("#selectCompany").val();
        let target = $('#'+dbName).attr('target');
        let url = '/' + dbName + target;
        this.show_app_loader();
        location.href = url;

    },
    ajax_redirect_url: function (url) {
        this.show_app_loader();
        location.href = url;

    },

    search: function(e) {

        let elem = $("#input-search");

        let value = elem.val();
        let dbName = elem.attr('db');

        if (dbName === 'default'){
            dbName = $("#select_company").val();
        }

        if (e.which === 13) {
            if (value) {
                this.show_app_loader();
                location.href = '/' + dbName + '/search?s=' + value;
            }
        }
    },

    show_notifications: function (entity) {

        if (entity){

            $.ajax({
                type: "POST",
                url: `/${DB_NAME}/notifications/load_data`,
                data: {
                    'entity': entity,
                },
                beforeSend: function () {
                    modalNotifications.find('.modal-body').html('<div class="mt-5 text-center">'+SPINNER_LOADER+'</div>');
                    modalNotifications.modal('show');
                },
                success: function (response) {
                    // add content html
                    modalNotifications.find('.modal-body').html(response);
                },
                error: function () {
                    show_toast_error_message('Internal Error', 'bottomRight');
                }
            });
        }
    },
    get_read_only_user_error: function (){
      mdlreadonlyUser.modal('show')
    },

};

$(function () {

    $(".tt").tooltip({placement:"top"});
    $(".tr").tooltip({placement:"right"});
    $(".tl").tooltip({placement:"left"});
    $(".tb").tooltip({placement:"bottom"});

    $('.myselect2').select2({
        width: '100%'
    });

    $(".myselect2_nosearch").select2({
        minimumResultsForSearch: -1
    });

    $("#fmLogin").find('input').val('');

    // Collapse elements (module and views)
    $(".btnCollapse").click(function () {
        $(".collapse").removeClass('show');
        let mid = $(this).attr('mid');
        $("#divCollapse_"+mid).collapse('show');
    });

    let collapse_module_based_on_active_view = function () {
        $("li.menu_options.is_active").parent().addClass('show');
    };

    collapse_module_based_on_active_view();

});
