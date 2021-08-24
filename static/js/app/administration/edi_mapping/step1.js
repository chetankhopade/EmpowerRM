// span
let spanFileName = $("#spanFileName");
let spanEDIMappingImportFile = $("#spanEDIMappingImportFile");


// Dropzone EDI Mapping
Dropzone.options.formDropzoneEDIMapping = {
    url: "/default/administration/edi_mapping/s1/upload_file",
    maxFilesize: 20, // MB
    uploadMultiple: false,
    acceptedFiles: '.txt, .edi',
    init: function() {
        this.on("success", function(file, response) {
            if (response.result === 'ok'){
                // update filename in the ui span tag
                EDIMAPPING_STEP1.filename = file.name;
                spanFileName.html(EDIMAPPING_STEP1.filename);
                spanEDIMappingImportFile.attr('target', '/administration/edi_mapping/s2?fn='+EDIMAPPING_STEP1.filename);
            }else{
               spanEDIMappingImportFile.attr('target', '');
               show_toast_error_message(response.message);
            }
            this.removeAllFiles();
        });
        this.on("error", function (file) {
            alert('Error')
        })
    }
};


let EDIMAPPING_STEP1 = {

    name: 'EDIMAPPING_STEP1',
    filename: '',
    mapID: '',

    // cancel button -> remove the imported file
    cancel: function () {
        $.ajax({
            url: "/default/administration/edi_mapping/s1/delete_file",
            data: {
                'fn': EDIMAPPING_STEP1.filename
            },
            type: "POST",
            dataType: "json",
            success: function (response) {
                if (response.result === 'ok'){
                    show_toast_success_message(response.message, 'bottomRight');
                    spanFileName.html('');
                }else{
                    show_toast_error_message(response.message);
                }
            },
            error: function () {
                show_toast_error_message('AJAX Error');
            }
        });
    },

    // Actions handler
    execute_action: function (e, a) {
        let tdParent = e.parent();
        this.mapID = tdParent.attr('mapid');

        switch (a) {
            case 'view':
                this.view();
                break;
            case 'active':
                this.active();
                break;
            case 'disable':
                this.disable();
                break;
            case 'edit':
                this.edit();
                break;
            case 'clone':
                this.clone();
                break;
            case 'delete':
                this.delete();
                break;
        }
    },

    // Actions functions
    view: function () {
        alert('View: ' + this.mapID);
    },

    active: function () {
        alert('Active: ' + this.mapID);
    },

    disable: function () {
        alert('Disable: ' + this.mapID);
    },

    edit: function () {
        alert('Edit: ' + this.mapID);
    },

    clone: function () {
        alert('Clone: ' + this.mapID);
    },

    delete: function () {
        alert('Delete: ' + this.mapID);
    },

};




