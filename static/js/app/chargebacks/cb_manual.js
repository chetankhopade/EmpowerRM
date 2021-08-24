// Manual CB variables and steppers
let step1Container = $("#step1Container");                      // div step 1 container
let step2Container = $("#step2Container");                      // div step 2 container
let step1Content = $("#step1Content");                          // div step 1 wrapper
let step2Content = $("#step2Content");                          // div step 2 wrapper
let stepsLoader = $(".stepsLoader");                            // div loader
let modalCreateChargeback = $("#modalCreateChargeback");

let modalCreateChargebackCancel = $("#modalCreateChargebackCancel");
let btnCBCreateChargeback = $("#btnCBCreateChargeback");
let btnCancelCreateManualCB = $(".btnCancelCreateManualCB");
let btnFinishCreateManualCB = $(".btnFinishCreateManualCB");

// Manual CB fields
let selectCBTypeCreateCB = $("#selectCBTypeCreateCB");
let tdCBIDCreateCB = $("#tdCBIDCreateCB");
let inputCBDateCreateCB = $("#inputCBDateCreateCB");
let inputCBNumberCreateCB = $("#inputCBNumberCreateCB");
let selectCustomerCreateCB = $("#selectCustomerCreateCB");
let selectDistributorCreateCB = $("#selectDistributorCreateCB");
let tdAddressCreateCB = $("#tdAddressCreateCB");
let tdCityStateZipCreateCB = $("#tdCityStateZipCreateCB");
let tdDEANumberCreateCB = $("#tdDEANumberCreateCB");

let inputResubmissionNoCreateCB = $("#inputResubmissionNoCreateCB");
let inputResubmissionDescriptionCreateCB = $("#inputResubmissionDescriptionCreateCB");
let inputResubmissionOriginalCBCreateCB = $("#inputResubmissionOriginalCBCreateCB");

let inputSubmittedCreateCB = $("#inputSubmittedCreateCB");
let inputTotalLinesCreateCB = $("#inputTotalLinesCreateCB");
let inputCalculatedCreateCB = $("#inputCalculatedCreateCB");
let inputCMNumberCreateCB = $("#inputCMNumberCreateCB");
let inputAdjustmentCreateCB = $("#inputAdjustmentCreateCB");
let inputCMDateCreateCB = $("#inputCMDateCreateCB");
let inputIssuedCreateCB = $("#inputIssuedCreateCB");
let inputCMAmountCreateCB = $("#inputCMAmountCreateCB");


// Manual Add Line fields
let tbodyManualCBLines = $("#tbodyManualCBLines");
let h6FormTitle = $("#h6FormTitle");
let selectContractAddLine = $("#selectContractAddLine");
let tdContractDescriptionAddLine = $("#tdContractDescriptionAddLine");

let inputItemWACSubmittedAddLine = $("#inputItemWACSubmittedAddLine");
let inputItemContractPriceSubmittedAddLine = $("#inputItemContractPriceSubmittedAddLine");
let inputItemClaimAddLine = $("#inputItemClaimAddLine");

let inputPurchaserDEANumberAddLine = $("#inputPurchaserDEANumberAddLine");
let inputPurchaserNameAddLine = $("#inputPurchaserNameAddLine");
let inputPurchaserAddress1AddLine = $("#inputPurchaserAddress1AddLine");
let inputPurchaserAddress2AddLine = $("#inputPurchaserAddress2AddLine");
let inputPurchaserCityAddLine = $("#inputPurchaserCityAddLine");
let inputPurchaserStateAddLine = $("#inputPurchaserStateAddLine");
let inputPurchaserZipAddLine = $("#inputPurchaserZipAddLine");

let inputInvoiceNumberAddLine = $("#inputInvoiceNumberAddLine");
let inputInvoiceDateAddLine = $("#inputInvoiceDateAddLine");
let inputInvoiceLineNoAddLine = $("#inputInvoiceLineNoAddLine");
let textareaInvoiceNotesAddLine = $("#textareaInvoiceNotesAddLine");

let selectItemNDCAddLine = $("#selectItemNDCAddLine");
let textareaItemDescriptionAddLine = $("#textareaItemDescriptionAddLine");
let inputItemQtyAddLine = $("#inputItemQtyAddLine");
let inputItemUOMAddLine = $("#inputItemUOMAddLine");


let CB_MANUAL = {

    name: 'CB_MANUAL',

    validate_chargeback_data: function (payload, exclude=[]) {
        let isValid = true;
        $.each(payload, function(key, value) {
            if (!exclude.includes(key) && !value){
                isValid = false;
            }
        });
        return isValid;
    },

    validate_total_lines_count: function () {
        let total_count = parseInt(inputTotalLinesCreateCB.val());
        let lines_count = parseInt(inputTotalLinesCreateCB.attr('lines_count'));
        return total_count >= lines_count;
    },

    // show Create Manual CB modal
    show_modal: function (source) {
        // update cancel and finish buttons to have the view source for future logic to close, cancel and redirect
        btnCancelCreateManualCB.attr('source', source);
        btnFinishCreateManualCB.attr('source', source);
        // Finis.attr('source', source);
        modalCreateChargeback.modal({backdrop: 'static', keyboard: false}).modal('show');
    },

    // Cancel Creation action (close or show confirmation delete modal)
    cancel_creation: function (elem){
        let source = elem.attr('source');
        let cbid = btnCBCreateChargeback.attr('cbid');
        if (source === 'cb_detail'){
            modalCreateChargeback.modal('hide');
            location.reload();
        }else{
            if (cbid){
                modalCreateChargebackCancel.css('top', '30%').modal({backdrop: 'static', keyboard: false}).modal('show');
            }else{
                modalCreateChargeback.modal('hide');
            }
        }
    },

    // ticket EA-1217 cancel manual creation (purge cb and its lines)
    cancel_creation_submit: function () {
        let cbid = parseInt(tdCBIDCreateCB.html());
        $.ajax({
            type: "POST",
            url: `/${DB_NAME}/chargebacks/manual/${cbid}/delete`,
            data: {},
            success: function (response) {
                // hide modals
                modalCreateChargebackCancel.modal('hide');
                modalCreateChargeback.modal('hide');
                // show message
                show_toast_success_message(response.message, 'bottomRight');
                // reload to refresh all form elements and recalculate
                APP.show_app_loader();
                setTimeout(function () {
                    location.href = response.redirect_url;
                }, 100)

            },
            error: function () {
                show_toast_error_message('Internal Error');
            }
        });
    },

    // Claim amount autopopulate based on wac and sys
    // ticket 1141 Jeremy's feedback, this claim amount field is calculated (WAC - CP) * QTY.
    recalculate_claim_submitted: function () {
        // EA-EA-1461 Remove automatic calculation on manual chargeback line's Claim Amount field
        if(selectCBTypeCreateCB.val() ==15) {
            inputItemClaimAddLine.removeAttr('disabled');
        }else{
            let qty = 0;
            if (inputItemQtyAddLine.val()) {
                qty = parseFloat(inputItemQtyAddLine.val());
            }
            let wac = 0;
            if (inputItemWACSubmittedAddLine.val()) {
                wac = parseFloat(inputItemWACSubmittedAddLine.val());
            }
            let cp = 0;
            if (inputItemContractPriceSubmittedAddLine.val()) {
                cp = parseFloat(inputItemContractPriceSubmittedAddLine.val());
            }

            if (qty && wac >= 0 && cp >= 0) {
                let claim = (wac - cp) * qty;
                inputItemClaimAddLine.val(claim.toFixed(2));
            } else {
                inputItemClaimAddLine.val('');
            }
        }
    },

    // step 1 - CB General Info
    step1_submit: function () {
        let cb_id = '0';
        if (tdCBIDCreateCB.html() !== ''){
            cb_id = parseInt(tdCBIDCreateCB.html());
        }
        let cb_number = inputCBNumberCreateCB.val();
        let cb_type = selectCBTypeCreateCB.val();
        let cb_date = inputCBDateCreateCB.val();
        let cb_customer_id = selectCustomerCreateCB.val();
        let cb_distributor_id = selectDistributorCreateCB.val();
        let cb_resub_number = inputResubmissionNoCreateCB.val();
        let cb_resub_description = inputResubmissionDescriptionCreateCB.val();
        let cb_original_chargeback_id = inputResubmissionOriginalCBCreateCB.val();
        let cb_claim_subtotal = inputSubmittedCreateCB.val();

        let cb_total_line_count = 0;
        let cb_lines_count = 0;
        if (inputTotalLinesCreateCB.val()){
            cb_total_line_count = parseInt(inputTotalLinesCreateCB.val());
            cb_lines_count = parseInt(inputTotalLinesCreateCB.attr('lines_count'));
        }

        // initialization of values when cbtype is original
        if (cb_type != '15'){
            cb_resub_number = '0';
            cb_resub_description = '0';
            cb_original_chargeback_id = '0';
        }

        let payload = {
            'cb_id': cb_id,
            'cb_number': cb_number,
            'cb_type': cb_type,
            'cb_date': cb_date,
            'cb_customer_id': cb_customer_id,
            'cb_distributor_id': cb_distributor_id,
            'cb_resub_number': cb_resub_number,
            'cb_resub_description': cb_resub_description,
            'cb_original_chargeback_id': cb_original_chargeback_id,
            'cb_total_line_count': cb_total_line_count,
            'cb_claim_subtotal': cb_claim_subtotal,
        };

        // Validations
        let isValid = CB_MANUAL.validate_chargeback_data(payload, ['cb_id', 'cb_resub_number', 'cb_resub_description', 'cb_original_chargeback_id', 'cb_total_line_count']);
        if (!isValid){
            show_toast_warning_message('All enabled fields are required');
        }
        // EA-1325 - Add validation to all date fields when creating a manual chargeback.
        // Validate if CB date is entered in format MM/DD/YYYY
        else if(!validateDateFormat(cb_date)){
            show_toast_warning_message('Date should be entered in format as MM/DD/YYYY');
        }
        // Validate is total lines > 0
        else if (cb_total_line_count <= 0) {
            show_toast_warning_message('Total Lines can not be zero');
        }
        else if (!CB_MANUAL.validate_total_lines_count()){
            show_toast_warning_message('Total Lines <b>(' + cb_total_line_count + ')</b> can not be lower than count of existing lines <b>(' + cb_lines_count + ')</b>');
        }
        else{
            let url = `/${DB_NAME}/chargebacks/manual/create`;
            if (cb_id !== '0') {
                url = `/${DB_NAME}/chargebacks/manual/${cb_id}/update`;
            }

            // Send CB to Server
            $.ajax({
                type: "POST",
                url: url,
                data: {
                    'payload': JSON.stringify(payload),
                },
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                    // opacity and show loader
                    step1Content.css('opacity', '0.1');
                    stepsLoader.show();
                },
                success: function (response) {
                    let cb = response['chargeback'];
                    tdCBIDCreateCB.html(cb.cbid);
                    selectCBTypeCreateCB.val(cb.type);
                    inputCBDateCreateCB.val(cb.date);
                    selectCustomerCreateCB.val(cb.customer_id);
                    selectDistributorCreateCB.val(cb.distribution_center_id).trigger('change');
                    inputResubmissionNoCreateCB.val(cb.resubmit_number);
                    inputResubmissionDescriptionCreateCB.val(cb.resubmit_description);
                    inputResubmissionOriginalCBCreateCB.val(cb.original_chargeback_id);
                    inputSubmittedCreateCB.val(cb.claim_subtotal);
                    inputCalculatedCreateCB.val(cb.claim_calculate);
                    inputAdjustmentCreateCB.val(cb.claim_adjustment);
                    inputIssuedCreateCB.val(cb.claim_issue);
                    inputTotalLinesCreateCB.val(cb.total_line_count);
                    inputCMNumberCreateCB.val(cb.accounting_credit_memo_number);
                    inputCMDateCreateCB.val(cb.accounting_credit_memo_date);
                    inputCMAmountCreateCB.val(cb.accounting_credit_memo_amount);
                    btnCBCreateChargeback.attr('cbid', cb.cbid);
                    // EA-EA-1461 Remove automatic calculation on manual chargeback line's Claim Amount field
                    if(cb.type == 15) {
                        inputItemClaimAddLine.removeAttr('disabled');
                    }else{
                        inputItemClaimAddLine.attr('disabled','disabled');
                    }

                },
                complete: function() {
                    step1Content.css('opacity', '1');
                    stepsLoader.hide();
                    step1Container.hide();
                    step2Container.fadeIn(500);
                },
                error: function () {
                    show_toast_error_message('Internal Error');
                }
            });
        }
    },

    // function to clean Add Line Form (step 2)
    clean_addline_form: function () {
        h6FormTitle.html('ADD LINE <span id="spanCBLNIDEditLine" class="text-dark _600 font-12"></span>');
        selectContractAddLine.val('0').trigger('change');
        inputItemWACSubmittedAddLine.val('');
        inputItemContractPriceSubmittedAddLine.val('');
        inputItemClaimAddLine.val('');
        inputPurchaserDEANumberAddLine.val('');
        inputPurchaserNameAddLine.val('');
        inputPurchaserAddress1AddLine.val('');
        inputPurchaserAddress2AddLine.val('');
        inputPurchaserCityAddLine.val('');
        inputPurchaserStateAddLine.val('');
        inputPurchaserZipAddLine.val('');

        inputInvoiceNumberAddLine.val('');
        inputInvoiceDateAddLine.val('');
        inputInvoiceLineNoAddLine.val('');
        textareaInvoiceNotesAddLine.val('');

        selectItemNDCAddLine.val('0').trigger('change');
        inputItemQtyAddLine.val('1');
        inputItemUOMAddLine.val('EA');

        tdContractDescriptionAddLine.html('');
        textareaItemDescriptionAddLine.val('');
    },

    // Function to update list of CBLines in table
    update_cblines_table: function (cblines){
        tbodyManualCBLines.html('');

        if (cblines.length > 0){
            // update the attr in total lines for later validations
            inputTotalLinesCreateCB.attr('lines_count', cblines.length);
            // loop over all the lines
            for (let i = 0; i < cblines.length; i++){
                let cbline = cblines[i];
                tbodyManualCBLines.append('<tr class="trCBLines font-9">' +
                    '<td>'+cbline.cblnid+'</td>' +
                    '<td class="tdContract" cont_id="'+cbline.contract_id+'">'+cbline.contract_no+'</td>' +
                    '<td class="tdPurcharser" ' +
                        'purch_id="'+cbline.purchaser_id+'"' +
                        'purch_dea="'+cbline.purchaser_dea+'"' +
                        'purch_name="'+cbline.purchaser_name+'"' +
                        'purch_address1="'+cbline.purchaser_address1+'"' +
                        'purch_address2="'+cbline.purchaser_address2+'"' +
                        'purch_city="'+cbline.purchaser_city +'"' +
                        'purch_state="'+cbline.purchaser_state +'"' +
                        'purch_zipcode="'+cbline.purchaser_zipcode +'"' +
                    '>'+cbline.purchaser_name+'</td>' +
                    '<td class="tdInvoice" ' +
                        'inv_no="'+cbline.invoice_number+'"' +
                        'inv_date="'+cbline.invoice_date+'"' +
                        'inv_lineno="'+cbline.invoice_line_no+'"' +
                        'inv_notes="'+cbline.invoice_note+'"' +
                    '>'+cbline.invoice_number+'</td>' +
                    '<td class="text-center">'+cbline.invoice_date+'</td>' +
                    '<td class="tdItem" ' +
                        'item_id="'+cbline.item_id+'"' +
                        'item_qty="'+cbline.item_qty+'"' +
                        'item_uom="'+cbline.item_uom+'"' +
                    '>'+cbline.item_ndc+'</td>' +
                    '<td>'+cbline.item_description+'</td>' +
                    '<td class="text-center">'+cbline.item_qty.toFixed(0)+'</td>' +
                    '<td class="text-center">'+cbline.item_uom+'</td>' +
                    '<td class="tdWACSubmitted text-center">'+cbline.wac_submitted.toFixed(2)+'</td>' +
                    '<td class="tdCPSubmitted text-center">'+cbline.contract_price_submitted.toFixed(2)+'</td>' +
                    '<td class="tdClaimSubmitted text-center">'+cbline.claim_amount_submitted.toFixed(2)+'</td>' +
                    '<td class="text-center">' +
                        '<a onclick="CB_MANUAL.edit_manual_chargebackline($(this));" cblnid="'+cbline.cblnid+'">' +
                            '<i class="fa fa-pencil text-dark font-12"></i>' +
                        '</a>' +
                        '<a onclick="CB_MANUAL.delete_manual_chargebackline($(this));"  cblnid="'+cbline.cblnid+'" class="ml-2">' +
                            '<i class="fa fa-times text-danger font-12"></i>' +
                        '</a>' +
                    '</td>' +
                    '</tr>');
            }
        }else{
            tbodyManualCBLines.html('<tr><td colspan="17" class="alert alert-warning text-center font-11">No Lines</td></tr>');
        }
    },

    // Function to remove cbline from cb
    delete_manual_chargebackline: function (elem) {
        let cblnid = elem.attr('cblnid');
        let cbid = parseInt(tdCBIDCreateCB.html());
        $.ajax({
            type: "POST",
            url: `/${DB_NAME}/chargebacks/manual/${cbid}/lines/${cblnid}/delete`,
            data: {},
            success: function (response) {
                CB_MANUAL.update_cblines_table(response['cblines'])
            },
            error: function () {
                show_toast_error_message('Internal Error');
            }
        });
    },

    // Function to edit cbline from cb
    edit_manual_chargebackline: function (elem) {
        let cblnid = elem.attr('cblnid');
        let tr = elem.parent().parent();
        $('.trCBLines').removeClass('empower_background_yellow');
        tr.addClass('empower_background_yellow');

        // contract
        let contract_id = tr.find('.tdContract').attr('cont_id'); // with this id we derive cnumber triggering select2
        // purchaser
        let purchaser = tr.find('.tdPurcharser');
        let purchaser_dea = purchaser.attr('purch_dea');
        let purchaser_name = purchaser.attr('purch_name');
        let purchaser_address1 = purchaser.attr('purch_address1');
        let purchaser_address2 = purchaser.attr('purch_address2');
        let purchaser_city = purchaser.attr('purch_city');
        let purchaser_state = purchaser.attr('purch_state');
        let purchaser_pzipcode = purchaser.attr('purch_zipcode');
        // invoice
        let invoice = tr.find('.tdInvoice');
        let invoice_no = invoice.attr('inv_no');
        let invoice_date = invoice.attr('inv_date');
        let invoice_lineno = invoice.attr('inv_lineno');
        let invoice_notes = invoice.attr('inv_notes');
        // item
        let item = tr.find('.tdItem');
        let item_id = item.attr('item_id');  // with this id we derive ndc and description triggering select2
        let item_qty = item.attr('item_qty');
        let item_uom = item.attr('item_uom');
        // amounts
        let wac_submitted = tr.find('.tdWACSubmitted').html();
        let cp_submitted = tr.find('.tdCPSubmitted').html();
        let claim_submitted = tr.find('.tdClaimSubmitted').html();

        // set values to forms elements
        // title
        h6FormTitle.html('EDIT LINE: <span id="spanCBLNIDEditLine" class="text-dark _600 font-12">'+cblnid+'</span>');
        // contract
        selectContractAddLine.val(contract_id).trigger('change');
        // purcharser
        inputPurchaserDEANumberAddLine.val(purchaser_dea);
        inputPurchaserNameAddLine.val(purchaser_name);
        inputPurchaserAddress1AddLine.val(purchaser_address1);
        inputPurchaserAddress2AddLine.val(purchaser_address2);
        inputPurchaserCityAddLine.val(purchaser_city);
        inputPurchaserStateAddLine.val(purchaser_state);
        inputPurchaserZipAddLine.val(purchaser_pzipcode);
        // invoice
        inputInvoiceNumberAddLine.val(invoice_no);
        inputInvoiceDateAddLine.val(invoice_date);
        inputInvoiceLineNoAddLine.val(invoice_lineno);
        textareaInvoiceNotesAddLine.val(invoice_notes);
        // item
        selectItemNDCAddLine.val(item_id).trigger('change');
        inputItemQtyAddLine.val(item_qty);
        inputItemUOMAddLine.val(item_uom);
        // amounts
        inputItemWACSubmittedAddLine.val(wac_submitted);
        inputItemContractPriceSubmittedAddLine.val(cp_submitted);
        // EA-EA-1461 Remove automatic calculation on manual chargeback line's Claim Amount field
        if(selectCBTypeCreateCB.val()==15) {
            inputItemClaimAddLine.removeAttr('disabled');
            inputItemClaimAddLine.val(claim_submitted);
        }else{
            inputItemClaimAddLine.val(claim_submitted);
        }

    },

    // Step 2 Previous btn click event
    step2_previous_click: function () {
        // hide step 2 and show step 1
        step2Container.hide();
        step1Container.fadeIn(500);
    },

    // Step 2 Save and Continue click event
    step2_save_click: function () {
        let cb_id = parseInt(tdCBIDCreateCB.html());

        let total_lines = parseInt(inputTotalLinesCreateCB.val());
        let lines_count = parseInt(inputTotalLinesCreateCB.attr('lines_count')) + 1;

        let cbln_id = $("#spanCBLNIDEditLine").html();
        let cbline_contract_id = selectContractAddLine.val();
        let cbline_wac_submitted = inputItemWACSubmittedAddLine.val();
        let cbline_contract_price_submitted = inputItemContractPriceSubmittedAddLine.val();
        let cbline_claim_submitted = inputItemClaimAddLine.val();
        let cbline_purchaser_dea_number = inputPurchaserDEANumberAddLine.val();
        let cbline_purchaser_name = inputPurchaserNameAddLine.val();
        let cbline_purchaser_address1 = inputPurchaserAddress1AddLine.val();
        let cbline_purchaser_address2 = inputPurchaserAddress2AddLine.val();
        let cbline_purchaser_city = inputPurchaserCityAddLine.val();
        let cbline_purchaser_state = inputPurchaserStateAddLine.val();
        let cbline_purchaser_zip = inputPurchaserZipAddLine.val();

        let cbline_invoice_number = inputInvoiceNumberAddLine.val();
        let cbline_invoice_date = inputInvoiceDateAddLine.val();
        let cbline_invoice_line_number = inputInvoiceLineNoAddLine.val();
        let cbline_invoice_notes = textareaInvoiceNotesAddLine.val();

        let cbline_item_id = selectItemNDCAddLine.val();
        let cbline_item_qty = inputItemQtyAddLine.val();
        let cbline_item_uom = inputItemUOMAddLine.val();

        let payload = {
            'cbline_contract_id': cbline_contract_id,
            'cbline_wac_submitted': cbline_wac_submitted,
            'cbline_contract_price_submitted': cbline_contract_price_submitted,
            'cbline_claim_submitted': cbline_claim_submitted,
            'cbline_purchaser_dea_number': cbline_purchaser_dea_number,
            'cbline_purchaser_name': cbline_purchaser_name,
            'cbline_purchaser_address1': cbline_purchaser_address1,
            'cbline_purchaser_address2': cbline_purchaser_address2,
            'cbline_purchaser_city': cbline_purchaser_city,
            'cbline_purchaser_state': cbline_purchaser_state,
            'cbline_purchaser_zip': cbline_purchaser_zip,
            'cbline_invoice_number': cbline_invoice_number,
            'cbline_invoice_date': cbline_invoice_date,
            'cbline_invoice_line_number': cbline_invoice_line_number,
            'cbline_invoice_notes': cbline_invoice_notes,
            'cbline_item_id': cbline_item_id,
            'cbline_item_qty': cbline_item_qty,
            'cbline_item_uom': cbline_item_uom,
        };

        // Validation (excluding some fields)
        let isValid = CB_MANUAL.validate_chargeback_data(
            payload,
            [
                'cbline_purchaser_address2',
                'cbline_invoice_notes',
                'cbline_item_uom',
                'cbline_invoice_line_number'
            ]);

        if (!isValid){
            show_toast_warning_message('All fields are required')
        }
        // EA-1325 - Add validation to all date fields when creating a manual chargeback.
        // Validate if CB date is entered in format MM/DD/YYYY
        else if(!validateDateFormat(cbline_invoice_date)){
            show_toast_warning_message('Invoice Date should be entered in format as MM/DD/YYYY');
        }
        // validate lines_count and total_lines
        else if (lines_count > total_lines){
            show_toast_warning_message('You defined a total of lines: <b>' + total_lines + '</b> in the header, and will have: <b>' + lines_count + '</b> lines. Change the total lines count in the header if need to add more lines');
        }
        // validate lines count
        else{

            let url = `/${DB_NAME}/chargebacks/manual/${cb_id}/lines/create`;
            if (cbln_id) {
                url = `/${DB_NAME}/chargebacks/manual/${cb_id}/lines/${cbln_id}/update`;
            }
            // Send CBLine to Server
            $.ajax({
                type: "POST",
                url: url,
                data: {
                    'payload': JSON.stringify(payload),
                },
                beforeSend: function(xhr, settings) {
                    // opacity and show loader
                    step2Content.css('opacity', '0.1');
                    stepsLoader.show();
                },
                success: function (response) {
                    // update table with new line
                    CB_MANUAL.update_cblines_table(response['cblines']);

                    // clean add line form
                    CB_MANUAL.clean_addline_form();
                },
                complete: function() {
                    step2Content.css('opacity', '1');
                    stepsLoader.hide();
                },
                error: function () {
                    show_toast_error_message('Internal Error');
                }
            });
        }
    },

    // Step 2 Finish click event
    step2_finish_click: function () {
        let cbid = parseInt(tdCBIDCreateCB.html());
        let total_lines = parseInt(inputTotalLinesCreateCB.val());
        let added_lines = parseInt(tbodyManualCBLines.find('tr').length);
        if (tbodyManualCBLines.find('tr').hasClass('trNoLines')){
            added_lines = added_lines - 1;
        }

        // validate lines count
        if (total_lines !== added_lines){
            show_toast_warning_message('You have defined: <b>' + total_lines + '</b> lines in chargeback header,' +
                ' but added: <b>' + added_lines + '</b>. ' +
                'You need to have the same count of lines defined in the header');
        }else {
            // Run Validations for the CB
            $.ajax({
                type: "POST",
                url: `/${DB_NAME}/chargebacks/manual/${cbid}/run_validations`,
                data: {
                    'source': btnFinishCreateManualCB.attr('source')
                },
                beforeSend: function(xhr, settings) {
                    // opacity and show loader
                    step2Content.css('opacity', '0.1');
                    stepsLoader.show();
                },
                success: function (response) {
                    if (response.result === 'ok'){
                        // close modal and components
                        stepsLoader.hide();
                        modalCreateChargeback.modal('hide');
                        step2Content.css('opacity', '1');
                        // show message
                        show_toast_success_message(response.message, 'topRight');
                        // reload to refresh all form elements and recalculate
                        APP.show_app_loader();
                        setTimeout(function () {
                            location.href = response.redirect_url;
                        }, 200)
                    }else{
                        show_toast_warning_message(response.message);
                    }
                },
                error: function () {
                    show_toast_error_message('Internal Error');
                }
            });
        }
    },
};


$(function () {

    // Ticket 1141
    //  You should prevent the user from typing a claim amount into this field and
    //  auto calculate the amount once the WAC, Contract Price, and QTY are all filled in by the user
    inputItemQtyAddLine.blur(function () {
        CB_MANUAL.recalculate_claim_submitted();
    });
    inputItemWACSubmittedAddLine.blur(function () {
        CB_MANUAL.recalculate_claim_submitted();
    });
    inputItemContractPriceSubmittedAddLine.blur(function () {
        CB_MANUAL.recalculate_claim_submitted();
    });

    // Typeahead
    inputPurchaserDEANumberAddLine.typeahead({
        minLength: 2,
        items: 50,
        source: function (query, result) {
            $.ajax({
                url: `/${DB_NAME}/chargebacks/manual/purchaser_data`,
                data: 'query=' + query,
                dataType: "json",
                type: "POST",
                success: function (response) {
                    if (jQuery.isEmptyObject(response.results)){
                        inputPurchaserNameAddLine.val('');
                        inputPurchaserAddress1AddLine.val('');
                        inputPurchaserAddress2AddLine.val('');
                        inputPurchaserCityAddLine.val('');
                        inputPurchaserStateAddLine.val('');
                        inputPurchaserZipAddLine.val('');
                        return ''
                    }else{
                        result($.map(response, function (item) {
                            return item;
                        }));
                    }
                }
            });
        },
        updater: function(item){
            inputPurchaserNameAddLine.val(item.company_name);
            inputPurchaserAddress1AddLine.val(item.address1);
            inputPurchaserAddress2AddLine.val(item.address2);
            inputPurchaserCityAddLine.val(item.city);
            inputPurchaserStateAddLine.val(item.state);
            inputPurchaserZipAddLine.val(item.zip_code);
            return item.name;
        }
    });

    // Resubmission fields are disabled if CBType selected is Original (00)
    let check_resubmission_fields_based_on_cbtype = function(){
        if (selectCBTypeCreateCB.val() === '15'){
            inputResubmissionNoCreateCB.attr('disabled', false);
            inputResubmissionDescriptionCreateCB.attr('disabled', false);
            inputResubmissionOriginalCBCreateCB.attr('disabled', false);

        }else{
            inputResubmissionNoCreateCB.attr('disabled', true);
            inputResubmissionDescriptionCreateCB.attr('disabled', true);
            inputResubmissionOriginalCBCreateCB.attr('disabled', true);
        }
    };
    check_resubmission_fields_based_on_cbtype();
    selectCBTypeCreateCB.change(check_resubmission_fields_based_on_cbtype);

    // Selects Changes events
    // Distributor Dropdown populated with DC Names of the Customer selected above
    selectCustomerCreateCB.change(function () {
        selectDistributorCreateCB.html('');
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
                        options +='<option value="' + elem.pk + '" ' +
                                    'dea_number="' + elem.fields['dea_number'] + '" ' +
                                    'address1="' + elem.fields['address1'] + '" ' +
                                    'city="' + elem.fields['city'] + '" ' +
                                    'state="' + elem.fields['state'] + '" ' +
                                    'zip_code="' + elem.fields['zip_code'] + '" >' +
                                        elem.fields['name'] +
                                   '</option>';
                    }
                    selectDistributorCreateCB.html(options).trigger('change');
                },
                error: function () {
                    show_toast_error_message('Internal Error');
                },
            });
        }else{
            selectDistributorCreateCB.html('').trigger('change');
        }
        $(this).attr('selected', 'selected');
    });

    // Address info and DEA is auto populated based on the choice
    selectDistributorCreateCB.change(function () {
        let option_selected = $('option:selected', this);
        let dea_number = option_selected.attr("dea_number");
        let address1 = option_selected.attr("address1");
        let city = option_selected.attr("city");
        let state = option_selected.attr("state");
        let zip_code = option_selected.attr("zip_code");

        if ($(this).val()){
            tdDEANumberCreateCB.html(dea_number);
            tdAddressCreateCB.html(address1);
            tdCityStateZipCreateCB.html(city + ', ' + state + ', ' + zip_code);
        }else{
            tdDEANumberCreateCB.html('');
            tdAddressCreateCB.html('');
            tdCityStateZipCreateCB.html('');
        }
    });

    // Contract Dropdown populates tdDescription contract
    selectContractAddLine.change(function () {
        if ($(this).val()){
            let option_selected = $('option:selected', this);
            let description = option_selected.attr("desc");
            tdContractDescriptionAddLine.html(description);
        }else{
            tdContractDescriptionAddLine.html('');
        }
    });
    selectContractAddLine.trigger('change');

    // select NDC in CBLine Create CB manual
    selectItemNDCAddLine.change(function () {
        let option_selected = $('option:selected', this);
        let description = option_selected.attr("desc");
        textareaItemDescriptionAddLine.val(description);
    });

    // This Fix the issue of writing in select2 dropwdown inside modal
    selectCustomerCreateCB.select2({
        dropdownParent: modalCreateChargeback,
        width: '100%'
    });

    selectDistributorCreateCB.select2({
        dropdownParent: modalCreateChargeback,
        width: '100%'
    });

    selectContractAddLine.select2({
        dropdownParent: modalCreateChargeback,
        width: '100%'
    });

    selectItemNDCAddLine.select2({
        dropdownParent: modalCreateChargeback,
        width: '100%'
    });

});
