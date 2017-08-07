/*
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.
*/

function popup_message(title, message) {
    $("#popup-dialog .modal-title").html(title);
    $("#popup-dialog .modal-body").html(message);
    $("#popup-dialog").modal();
}

$(document).ready(function() {

    $('#select-organization').selectize({
        create: true,
        sortField: 'text'
    });

    $("#select-category").selectize({
        sortField: 'value',
        maxItems: null
    });

    $("#select-supplier").selectize({
        sortField: 'text'
    });

    $("#catalog-select-supplier select").selectize({
        sortField: 'text',
        onChange: function(value) {
            if (!(value)) return;
            window.location = "/catalog/supplier/" + value;
        }
    });

    $("#blockchain-chkbox-label").on("click", function() {
        $("#blockchain-chkbox").click();
    });

    $('[data-toggle="popover"]').popover({
        trigger: 'focus'
    });


    $(document).on("click", ".crypto-expand-collapse", function() {
        var file_sha1 = $(this).attr("file-sha1");
        $("#crypto-file-hits-" + file_sha1).animate({height: "toggle"});
        $(this).find(".crypto-down-arrow").toggle();
        $(this).find(".crypto-right-arrow").toggle();
    });

    $("#new-supplier-form").on("submit", function() {
        $.ajax({
            url: "/supplier/new",
            type: "POST",
            contentType: "application/json; charset=utf-8;",
            data: JSON.stringify({
                "supplier_name": $("input[name=name]").val(),
                "password": md5($("input[name=pwd]").val()),
                "blockchain": $("#blockchain-chkbox").is(":checked")
            }),
            dataType: "json",

            beforeSend: function() {

                $(".preload-img").show()
                $("#form-modal").fadeIn();
            },
            success: function(response) {

                if (response.failed) {
                    popup_message("Error", response.error_message);
                } else {
                    $("#supplier-table-container").html(response.supplier_table_html);
                    $("input[name=name]").val("");
                    $("input[name=pwd]").val("");
                }

                $(".preload-img").hide()
                $("#form-modal").stop().fadeOut();


            },
            error: function(jqXHR, textStatus, errorThrown) {
                $(".preload-img").hide()
                $("#form-modal").fadeOut();
                popup_message("Error", "Error [HTTP " + jqXHR.status +
                    "]: " + errorThrown);
            }
        });

        return false;
    });


    $("#new-part-form").on("submit", function() {

        $.ajax({
            url: "/part/create",
            type: "POST",
            contentType: "application/json; charset=utf-8;",
            data: JSON.stringify({
                "categories": $("select[name=category]").val(),
                "supplier_id": $("select[name=supplier]").val(),
                "password": md5($("input[name=pwd]").val()),
                "usku": $("input[name=usku]").val(),
                "supplier_part_id": $(
                    "input[name=supplier_part_id]").val(),
                "name": $("input[name=name]").val(),
                "version": $("input[name=version]").val(),
                "licensing": $("input[name=licensing]").val(),
                "blockchain": $("#blockchain-chkbox").is(":checked"),
                "envelope_id": null,
                "url": $("input[name=url]").val(),
                "status": $("input[name=status]").val(),
                "description": $("textarea[name=description]").val()
            }),
            dataType: "json",

            beforeSend: function() {
                $("input[name=pwd]").parent().removeClass("has-error");
                $("#pwd-input-text").hide()
                $("#form-modal").fadeIn();
                $(".preload-img").show()
            },
            success: function(response) {

                $(".preload-img").hide()
                $("#form-modal").stop().fadeOut();

                if (response.incorrect_password) {
                    // popup_message("Invalid Password", "The supplier password was incorrect.");
                    $("#pwd-input-text").html(
                        "Incorrect supplier password").show();
                    $("input[name=pwd]").parent().addClass("has-error");
                    return;
                }

                if (response.failed) {
                    popup_message("Failed to save data", response.error_message);
                } else {
                    window.location = "/part/view/" + response.part_id;
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                popup_message("Error", "Error [HTTP " + jqXHR.status +
                    "]: " + errorThrown);
                $(".preload-img").hide()
                $("#form-modal").fadeOut();
            }
        });

        return false;
    });

    $("#delete-part-btn").on("click", function() {
        $("#delete-part-dialog").modal();
    });


    $("#category-select-container").on("click", function(evt) {
        evt.stopPropagation();
        evt.preventDefault();
    });

    $("#part-profile-category-select").selectize({
        sortField: 'value',
        maxItems: null
    }).on("change", function() {
        _category_index_strings = $(this).val();
        selected_categories = []
        selected_categories_string = "";
        for (var i = 0; i < _category_index_strings.length; i++) {
            selected_categories.push(parseInt(_category_index_strings[i]))
        }

        for (var i = 0; i < category_list.length; i++) {
            if (selected_categories.includes(category_list[i]["value"])) {
                selected_categories_string += category_list[i]["text"] + ", ";
            }
        }

        // remove last ", "
        selected_categories_string =
            selected_categories_string.substring(0, selected_categories_string.length - 2);

        $("#part-category .editable-input input").val(selected_categories_string);
    });

    $(".field-value").each(function() {

        var editable_options = {
            toggle: "manual",
            mode: "inline",
            unsavedclass: "inline-edit-unsaved",
            emptytext: ""
        }


        if ($(this).hasClass("field-category")) {

            // onblur: ignore makes it so that when user clicks out of the editable,
            // the selectize element doesn't disappear.

            editable_options["onblur"] = "ignore";

            $(this).on("shown", function() {
                $(this).parent().find(".editable-input").hide();
                $("#part-profile-category-select")[0].selectize.setValue(selected_categories);
                $("#category-select-container").show();
            });

            $(this).on("hidden", function(event, reason) {
                $("#category-select-container").hide();
                if (reason == "cancel") {
                    $("#part-profile-category-select")[0].selectize.setValue(lastsaved_categories);
                }
            });

        } else if ($(this).hasClass("field-description")) {
            editable_options["rows"] = "6";
        }

        $(this).editable(editable_options);

        $(this).attr({
            "lastsavedvalue": $(this).editable("getValue", true)
        });
    });

    $("#enable-edit-btn").on("click", function() {
        $(".edit-button").show();
        $("#enable-edit-btn").hide()
        $("#cancel-edit-btn").show();
        $("#save-edit-btn").show();
    });


    $("#save-edit-btn").on("click", function() {
        $(".supplier-pwd-label").hide();
        $("input[name=pwd]").parent().removeClass("has-error");
        $(".supplier-pwd-input").val("");
        $("#edit-dialog").modal();
    })


    $("#cancel-edit-btn").on("click", function() {
        $(".field-value").each(function() {
            $(this).removeClass("inline-edit-unsaved")
            $(this).editable("setValue", $(this).attr("lastsavedvalue"));
        });
        $("#part-category .field-value").editable("hide");
        $("#part-profile-category-select")[0].selectize.setValue(lastsaved_categories);
        $(".edit-button").hide();
        $("#enable-edit-btn").show()
        $("#cancel-edit-btn").hide();
        $("#save-edit-btn").hide();
    })



    $(".edit-button").on("click", function(e) {
        e.stopPropagation();
        $(this).closest("div").find(".field-value").editable('toggle');
        $(".editable-input input, .editable-input select").removeClass("input-sm");
        $(".editable-buttons button").removeClass("btn-sm");
    });


    $("#edit-part-form").on("submit", function() {

        $.ajax({
            url: "/part/edit",
            type: "POST",
            contentType: "application/json; charset=utf-8;",
            dataType: "json",
            data: JSON.stringify({
                "supplier_id": $("#supplier-id").val(),
                "password": md5($(
                    "#edit-dialog .supplier-pwd-input").val()),
                "part_id": $("#part-id").val(),
                "name": $("#part-name .field-value").editable(
                    "getValue", true),
                "version": $("#part-version .field-value").editable(
                    "getValue", true),
                "licensing": $("#part-licensing .field-value").editable(
                    "getValue", true),
                "usku": $("#part-usku .field-value").editable(
                    "getValue", true),
                "supplier_part_id": $(
                    "#part-supplier-part-id .field-value").editable(
                    "getValue", true),
                "status": $("#part-status .field-value").editable(
                    "getValue", true),
                "description": $("#part-description .field-value").editable(
                    "getValue", true),
                "categories": selected_categories,
                "url": $("#part-url .field-value").editable(
                    "getValue", true),
            }),


            beforeSend: function() {
                $(".preload-img").show();
            },
            success: function(response) {

                $(".preload-img").hide();

                if (response.incorrect_password) {
                    $("#edit-dialog .supplier-pwd-label").html(
                        "Incorrect supplier password").show();
                    $("#edit-dialog input[name=pwd]").parent().addClass(
                        "has-error");
                    return;
                }

                if (!(response.part_exists)) {
                    popup_message("Error",
                        "Part was not found in the database");
                    return;
                }

                if (response.failed) {
                    popup_message("Failed to save data", response.error_message);
                } else {

                    $(".field-value").each(function() {
                        $(this).removeClass(
                            "inline-edit-unsaved");
                        $(this).attr("lastsavedvalue", $(this).editable(
                            "getValue", true));
                    });
                    lastsaved_categories = selected_categories.slice();
                    $(".edit-button").hide();
                    $("#enable-edit-btn").show()
                    $("#cancel-edit-btn").hide();
                    $("#save-edit-btn").hide();

                    $("#edit-dialog").modal("hide");
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $(".preload-img").hide();
                popup_message("Error", "Error [HTTP " + jqXHR.status +
                    "]: " + errorThrown);

            }
        });
        return false;
    });


    $("#delete-part-form").on("submit", function() {
        $.ajax({
            url: "/part/delete",
            type: "POST",
            contentType: "application/json; charset=utf-8;",
            dataType: "json",
            data: JSON.stringify({
                "supplier_id": $("#supplier-id").val(),
                "password": md5($(
                    "#delete-part-dialog .supplier-pwd-input"
                ).val()),
                "part_id": $("#part-id").val()
            }),

            beforeSend: function() {
                $(".preload-img").show();
            },
            success: function(response) {

                $(".preload-img").hide();

                if (response.incorrect_password) {
                    $("#delete-part-dialog .supplier-pwd-label").html(
                        "Incorrect supplier password").show();
                    $("#delete-part-dialog input[name=pwd]").parent().addClass(
                        "has-error");
                    return;
                }

                if (!(response.part_exists)) {
                    popup_message("Error",
                        "Part was not found in the database");
                    return;
                }

                if (response.failed) {
                    popup_message("Failed to delete part", response.error_message);
                } else {

                    window.location = "/catalog";
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $(".preload-img").hide();
                popup_message("Error", "Error [HTTP " + jqXHR.status +
                    "]: " + errorThrown);

            }
        });
        return false;
    });


    $(document).on("change", "#env-file", function(evt) {

        evt.stopPropagation();
        evt.preventDefault();

        if (evt.target.files.length != 1) {
            // user canceled the file open dialog
            return;
        }

        var file = evt.target.files[0];

        $.ajax({
            url: "/envelope/upload?part_id=" + $("#part-id").val(),
            type: "POST",
            data: new FormData($("#envelope-form")[0]),
            dataType: "json",
            cache: false,
            contentType: false,
            processData: false,

            xhr: function() {
                var progressXHR = $.ajaxSettings.xhr();
                if (progressXHR.upload) {
                    progressXHR.upload.addEventListener('progress',
                        function(e) {
                            if (e.lengthComputable) {

                                var value = e.loaded;
                                var max = e.total;
                                var percentage = parseInt(value *
                                    100 / max);

                                var progressbar = $(
                                    "#upload-progress-bar .progress-bar"
                                )
                                progressbar.attr("aria-valuenow", percentage);
                                progressbar.css("width", percentage + "%");
                                progressbar.html("Uploading Envelope ... (" + percentage + "%)");

                                if (value === max) {
                                    $("#parse-progress-bar").fadeIn();
                                }
                            }
                        }, false);
                }
                return progressXHR;
            },

            beforeSend: function() {
                $("#upload-progress-bar").fadeIn();
            },

            success: function(response) {

                $("#upload-progress-bar").fadeOut();
                $("#parse-progress-bar").fadeOut();

                if (response.hasOwnProperty("error_message")) {
                    popup_message("Error", response.error_message);
                    return;
                }

                if (response["successfully_uploaded"] == true) {

                    $("#envelope-form").hide();
                    $("#envelope-table").html(response["envelope_html"]);
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $("#upload-progress-bar").hide();
                $("#parse-progress-bar").hide();
                popup_message("Error", "Error [HTTP " + jqXHR.status +
                    "]: " + errorThrown);
            }
        });
    });

    $(document).on("click", ".delete-envelope-btn", function() {
        $("#delete-envelope-dialog .supplier-pwd-label").hide();
        $("#delete-envelope-dialog input[name=pwd]").val("");
        $("#delete-envelope-dialog input[name=pwd]").parent().removeClass(
            "has-error");
        $("#delete-envelope-dialog").modal();
    });

    $(document).on("submit", "#delete-envelope-form", function() {

        $.ajax({
            url: "/envelope/delete/" + $("#envelope-uuid").val(),
            type: "POST",
            contentType: "application/json; charset=utf-8;",
            dataType: "json",
            data: JSON.stringify({
                "supplier_id": $("#supplier-id").val(),
                "password": md5($(
                    "#delete-envelope-dialog .supplier-pwd-input"
                ).val()),
            }),

            beforeSend: function() {
                $("#delete-envelope-dialog .supplier-pwd-label").hide();
                $("#delete-envelope-dialog input[name=pwd]").parent().removeClass("has-error");
                $("#delete-envelope-dialog input[name=pwd]").val("");
                $(".preload-img").show();
            },

            success: function(response) {
                $(".preload-img").hide();

                if (response.failed) {
                    if (response.invalid_password) {
                        $("#delete-envelope-dialog .supplier-pwd-label")
                            .html(
                                "Incorrect supplier password").show();
                        $("#delete-envelope-dialog input[name=pwd]").parent()
                            .addClass("has-error");
                    } else {
                        popup_message("Error", response.error_message);
                    }
                } else {
                    $("#envelope-table").html(response["envelope_html"]);
                    $("#delete-envelope-dialog").modal("hide");
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $("#delete-envelope-dialog").modal("hide");
                $(".preload-img").hide();
                $("#upload-progress-bar").hide();
                $("#parse-progress-bar").hide();
                popup_message("Error", "Error [HTTP " + jqXHR.status +
                    "]: " + errorThrown);

            }
        });

        return false;

    });


    $(".btn-envelope-details").on("click", function() {
        var art_details = $(this).parent().find(".artifact-details").first().html();
        popup_message("Artifact Details", art_details);
    });


    $(".expand-collapse-title").on("click", function() {

        $(this).parent().find(".expand-collapse-content").first().toggle();
        var plusminus = $(this).parent().find(".expand-collapse-icon span").first();

        if (plusminus.hasClass("glyphicon-plus")) {
            plusminus.removeClass("glyphicon-plus").addClass("glyphicon-minus");
        } else {
            plusminus.removeClass("glyphicon-minus").addClass("glyphicon-plus");
        }
    });

});
