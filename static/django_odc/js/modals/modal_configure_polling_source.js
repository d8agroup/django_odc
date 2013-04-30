(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_modal_configure_polling_source = {};

    //Init
    $.django_odc_modal_configure_polling_source.init = function() {

        //Init around the modal container
        $('#modal-configure-polling-source').django_odc_modal_configure_polling_source();
    };

    //Store source configuration
    $.django_odc_modal_configure_polling_source.set_source_configuration = function(source_configuration) {

        //Store the config
        $('#modal-configure-polling-source').data('source_configuration', source_configuration);

        //if there is config then set any config driven display elements
        if (source_configuration) {

            //Blank out the channel type indicator image
            $('#configure-polling-source-channel-type-image').attr('src', source_configuration.channel.images['32']);
        }
    };

    //Get source configuration
    $.django_odc_modal_configure_polling_source.get_source_configuration = function() {

        return $('#modal-configure-polling-source').data('source_configuration');
    };

    //Open with channel configuration - when a new source is being built
    $.django_odc_modal_configure_polling_source.open_with_channel = function(channel) {

        //Build the url to create a source from this channel config
        var url = URL_POLLING_SOURCE_CREATE
            .replace('DATASET_ID', channel.dataset_id)
            .replace('CHANNEL_TYPE', channel.channel.type);

        //Call the api to create a new source from this channel config
        $.getJSON(url, function(source){

            //Open this modal with the new source config
            $.django_odc_modal_configure_polling_source.open(source)
        });
    };

    //Open
    $.django_odc_modal_configure_polling_source.open = function(source_configuration) {

        //Get a handel on the modal
        var modal = $('#modal-configure-polling-source');

        //Check init has been called
        if (modal.data('uiDialog') == null)
            $.django_odc_modal_configure_polling_source.init();

        //Blank out any config driven display elements
        $('#configure-polling-source-channel-type-image').attr('src', '');
        $('#configure-polling-source-test-waiting-message').show();

        //Call the open method on the instance
        modal.django_odc_modal_configure_polling_source('open_modal', source_configuration);
    };

    //Close
    $.django_odc_modal_configure_polling_source.close = function(prevent_dataset_update) {

        //Get a handle on the modal
        var modal = $('#modal-configure-polling-source');

        //Check init has been called
        if (modal.data('uiDialog') == null)
            $.django_odc_modal_configure_polling_source.init();

        if (prevent_dataset_update == null || !prevent_dataset_update) {

            //Get the dataset id
            var dataset_id = $.django_odc_modal_configure_polling_source.get_source_configuration().dataset.id;

            //Call the list refresh
            $.django_odc_datasets.update_dataset(dataset_id);
        }

        //Call the close method on the instance
        modal.django_odc_modal_configure_polling_source('close_modal');
    };

    //Poll for testing results
    $.django_odc_modal_configure_polling_source.poll_for_testing_results = function(testing_start_time) {

        //Check if the testing start time is null = first time
        if (testing_start_time == null)
            testing_start_time = new Date();

        //Get the current source configuration
        var source_configuration = $.django_odc_modal_configure_polling_source.get_source_configuration();

        //Build the url for the api call
        var url = URL_POLLING_SOURCE_TEST_CHECK.replace('SOURCE_ID', source_configuration.id);

        //Make the call to the api
        $.getJSON(url, function(test_results){

            //If the test is still running
            if (test_results.status == 'running') {

                //Function to pass to the timeout
                var timeout_function = function() {

                    //if the modal is visible
                    if ($('#modal-configure-polling-source').is(':visible'))
                        //Recall the poll function
                        $.django_odc_modal_configure_polling_source.poll_for_testing_results(testing_start_time);
                };

                //Call the timeout function again
                setTimeout(timeout_function, 1000);
            }
            else {

                //Render the returned template into the container
                $('#config-source-test-results').html(test_results.template);

                //Remove the waiting messages
                $('#configure-polling-source-test-waiting-message').hide();

                // Attach to the confirm button
                $('#config-source-confirm-button').click(function(){

                    //Get the source
                    var source = $.django_odc_modal_configure_polling_source.get_source_configuration();

                    //Build the url
                    var url = URL_POLLING_SOURCE_ANALYSIS.replace('SOURCE_ID', source.id);

                    //Reload the configure html
                    $('#configure-polling-source-container').load(url)
                });

                // Attach to the reconfigure button
                $('#config-source-reconfigure-button').click(function(){

                    //Get the source
                    var source = $.django_odc_modal_configure_polling_source.get_source_configuration();

                    //Build the url
                    var url = URL_POLLING_SOURCE_CONFIGURE.replace('SOURCE_ID', source.id);

                    //Reload the configure html
                    $('#configure-polling-source-container').load(url)
                });
            }
        });
    };


    /******************************************************************************************************************/
    /* Instance Functions */
    var methods = {
        init : function() {

            //Get a handle on the container
            var container = $(this);

            //Create a dialog for later
            container.dialog({
                modal: true,
                resizable: false,
                draggable: false,
                width: 600,
                height: 400,
                autoOpen: false
            });

            //Attach any event handlers
            container.django_odc_modal_configure_polling_source('attach_event_handlers');

        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Get a handle on the close button
            var modal_close_button = container.find('.modal-close-button');

            //Attach the click handler
            modal_close_button.click(function(){

                //Call the static close method
                $.django_odc_modal_configure_polling_source.close();
            });

            //Live attach to the showing of the config form
            $('#configure-polling-source-config').livequery(function(){

                //Unbind all
                $(this).find("*").unbind();

                //Deactivate all the steps
                $('.configure-polling-source-indicator-step').removeClass('active');

                //Activate the config step
                $('#configure-polling-source-indicator-config').addClass('active');

                //Attach to the submit config button
                $('#submit-source-config-button').click(function(){

                    //Unbind all
                    $(this).find("*").andSelf().unbind();

                    //Get a handel on the button
                    var button = $(this);

                    //Get a handle on the form
                    var form = button.parents('form:first');

                    //serialize the form data
                    var post_data = form.serialize();

                    //Show saving
                    $('#configure-polling-source-container').html('<div class="loading"><p><i class="icon-spinner icon-spin"></i> Just checking</p></div>')

                    //Slight delay for usability
                    setTimeout(function(){

                        //Get the source config
                        var source = $.django_odc_modal_configure_polling_source.get_source_configuration();

                        //Build the url
                        var url = URL_POLLING_SOURCE_CONFIGURE.replace('SOURCE_ID', source.id);

                        //post off the form data
                        $.post(url, post_data, function(template){

                            //Render the template
                            $('#configure-polling-source-container').html(template);
                        });
                    }, 500);
                });
            });

            //Live attach to the showing of the testing form
            $('#configure-polling-source-test').livequery(function(){

                //Unbind all
                $(this).find("*").unbind();

                //Deactivate all the steps
                $('.configure-polling-source-indicator-step').removeClass('active');

                //Activate the config step
                $('#configure-polling-source-indicator-test').addClass('active');

                //Begin polling for results
                $.django_odc_modal_configure_polling_source.poll_for_testing_results(null);
            });

            // Live attach to the showing of the analysis form
            $('#configure-polling-source-analysis').livequery(function(){

                //Unbind all
                $(this).find("*").unbind();

                //Deactivate all the steps
                $('.configure-polling-source-indicator-step').removeClass('active');

                //Activate the config step
                $('#configure-polling-source-indicator-analysis').addClass('active');

                //Attach to all the service types
                $(this).find('.available-service-type')

                    //Live attach to the service mouseover
                    .mouseenter(function(){

                        //Get a handle on the source container
                        var container = $(this);

                        //Extract the source data
                        var service = container.data('service');

                        //Hide the help message
                        $('#service-details-instructions').hide();

                        //set the display name
                        $('#service-details-display-name').html(service.display_name_short);

                        //Set the description
                        $('#service-details-description').html(service.description_full);

                        //Set the labels
                        $('#service-status-label-inactive').css('display', (container.is('.active') ? 'none' : 'block'));
                        $('#service-status-label-active').css('display', (container.is('.active') ? 'block' : 'none'));
                    })

                    //Live attach to the service mouseout
                    .mouseleave(function(){

                        //Show the help message
                        $('#service-details-instructions').show();

                        //set the display name to blank
                        $('#service-details-display-name').html('');

                        //Set the description to blank
                        $('#service-details-description').html('');

                        //Set the labels
                        $('#service-status-label-inactive').hide();
                        $('#service-status-label-active').hide();
                    })

                    //Life attach to the click event
                    .click(function(){

                        //get a handel on the service
                        var service_container = $(this);

                        //Get the service data
                        var service = service_container.data('service');

                        //Get the current source
                        var source = $.django_odc_modal_configure_polling_source.get_source_configuration();

                        //Switch on the presence of an active class
                        if (service_container.is('.active')){

                            //Remove the active class
                            service_container.removeClass('active');

                            //build the url for the api call
                            var url = URL_SOURCE_REMOVE_SERVICE
                                .replace('SOURCE_ID', source.id)
                                .replace('SERVICE_TYPE', service.type);

                            //Fire and forget the api call
                            $.get(url);
                        }
                        else {

                            //ADD the active class
                            service_container.addClass('active');

                            //build the url for the api call
                            var url = URL_SOURCE_ADD_SERVICE
                                .replace('SOURCE_ID', source.id)
                                .replace('SERVICE_TYPE', service.type);

                            //Fire and forget the api call
                            $.get(url);
                        }

                        //call the mouseenter event to repaint the display
                        service_container.mouseenter();
                    });

                $('#save-polling-source-analysis-button').click(function(){

                    //Get the source
                    var source = $.django_odc_modal_configure_polling_source.get_source_configuration();

                    //Build the url
                    var url = URL_POLLING_SOURCE_CONFIRM.replace('SOURCE_ID', source.id);

                    //Reload the confirm html
                    $('#configure-polling-source-container').load(url);
                });
            });

            //Live attach to the showing of the confirmation form
            $('#configure-polling-source-confirm').livequery(function(){

                //Unbind all
                $(this).find("*").unbind();

                //Deactivate all the steps
                $('.configure-polling-source-indicator-step').removeClass('active');

                //Activate the config step
                $('#configure-polling-source-indicator-confirm').addClass('active');

                // Attach to the save and activate button
                $('#polling-source-confirm-save-and-activate-button').click(function() {

                    //Get the source
                    var source = $.django_odc_modal_configure_polling_source.get_source_configuration();

                    //Call the api to activate the source
                    $.get(URL_SOURCE_ACTIVATE.replace('SOURCE_ID', source.id), function(){

                        //Close the modal preventing the normal updat
                        $.django_odc_modal_configure_polling_source.close(true);

                        //Update the dataset object
                        $.django_odc_datasets.update_dataset(source.dataset.id);
                    });
                });

                // Attach to the save and activate button
                $('#polling-source-confirm-save-button').click(function() {

                    //Get the source
                    var source = $.django_odc_modal_configure_polling_source.get_source_configuration();

                    //Call the api to activate the source
                    $.get(URL_SOURCE_DEACTIVATE.replace('SOURCE_ID', source.id), function(){

                        //Close the modal prventing the normal dataset update
                        $.django_odc_modal_configure_polling_source.close(true);

                        //Update the dataset object
                        $.django_odc_datasets.update_dataset(source.dataset.id);
                    });
                });

                // Attach to the reconfigure button
                $('#polling-config-source-reconfigure-button').click(function(){

                    //Get the source
                    var source = $.django_odc_modal_configure_polling_source.get_source_configuration();

                    //Build the url
                    var url = URL_POLLING_SOURCE_CONFIGURE.replace('SOURCE_ID', source.id);

                    //Reload the configure html
                    $('#configure-polling-source-container').load(url)
                });
            });
        },
        open_modal: function(source_configuration) {

            //Get a handel on the container
            var container = $(this);

            //set the source config
            $.django_odc_modal_configure_polling_source.set_source_configuration(source_configuration);

            //build the url
            var url = URL_POLLING_SOURCE_CONFIGURE.replace('SOURCE_ID', source_configuration.id);

            //Load the template into the container
            $('#configure-polling-source-container').load(url);

            //Open the dialog
            container.dialog('open');
        },
        close_modal: function() {

            //Get a handel on the container
            var container = $(this);

            //erase the dataset id
            $.django_odc_modal_configure_polling_source.set_source_configuration(null);

            //Close the dialog
            container.dialog('close');
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_modal_configure_polling_source = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_modal_configure_polling_source' ); }
    };

})( jQuery );