(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_statistics_and_administration = {};


    /******************************************************************************************************************/
    /* Instance Functions */
    var methods = {
        init : function() {

            //Get a handle on the container
            var container = $(this);

            //Attach any event handlers
            container.django_odc_statistics_and_administration('attach_event_handlers');

            // Reload the run records
            container.django_odc_statistics_and_administration('reload_run_records');
        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Attach to the kill all button
            $('#kill-all-source-button').click(function(){

                //Build the confirmation modal data
                var confirmation_data = {
                    title: 'Do you really want to do that?',
                    question: 'This will stop all running sources.',
                    help_message: 'This is a good idea if you think something has broken but use it wisely!',
                    confirm_callback: function() {

                        // Call the api
                        $.get(URL_SOURCES_KILL, function(){

                            //Reload all the datasets
                            $.django_odc_datasets.reload_datasets();
                        });
                    }
                };

                //Call the confirm modal
                $.django_odc_modal_confirmation.open(confirmation_data);
            });

            //Attach to the clear all data button
            $('#clear-all-data-button').click(function(){

                //Build the confirmation modal data
                var confirmation_data = {
                    title: 'Do you really want to do that?',
                    question: 'This will delete all data for all sources.',
                    help_message: 'This will bank out this app to no data state.',
                    confirm_callback: function() {

                        // Call the api
                        $.get(URL_SOURCES_EMPTY, function(){

                            //Set some ui stuff on the button
                            $('#clear-all-data-button')
                                .removeClass('disabled')
                                .html('<i class="icon-trash"></i>');

                            //Reload all the datasets
                            $.django_odc_datasets.reload_datasets();
                        });
                    },
                    cancel_callback: function() {

                        //Reset some ui stuff on the button
                        $('#clear-all-data-button')
                            .removeClass('disabled')
                            .html('<i class="icon-trash"></i>');
                    }
                };

                //Set the button state
                $('#clear-all-data-button')
                    .addClass('disabled')
                    .html('<i class="icon-spin icon-spinner"></i>');

                //Call the confirm modal
                $.django_odc_modal_confirmation.open(confirmation_data);
            });

            // The aggregate polling sources now button
            $('#aggregator-poll-now-button').click(function(){

                $('#aggregator-poll-now-label-inactive').hide();
                $('#aggregator-poll-now-label-running').show();

                //Call the api
                $.get('aggregate_for_user', function(){

                    $('#aggregator-poll-now-label-running').hide();
                    $('#aggregator-poll-now-label-inactive').show();

                    //Reload the run records
                    container.django_odc_statistics_and_administration('reload_run_records');

                    $.django_odc_datasets.reload_datasets()
                });
            });
        },
        reload_run_records: function(){

            // Get a handle on the container
            var container = $(this);

            // Get a handle on the list container
            var list_container = container.find('#run-records-list');

            //Apply loading to the list container
            list_container.django_odc_loading('apply', 'Loading');

            //Ui delay
            setTimeout(function(){

                //Call the api
                $.get(URL_STATISTICS_RUN_RECORDS, function(template){

                    //Remove loading and apply this new template
                    list_container
                        .django_odc_loading('remove')
                        .html(template);

                    //Attach mouseover and leave to all the errors
                    list_container.find('.run-record.error').click(function(){

                            //Get a handel on the errors
                            var errors = $(this).find('.errors');

                            //If they are visible, hide them
                            if (errors.is(':visible'))
                                errors.slideUp();
                            else
                                errors.slideDown();
                        });
                });
            }, 1000);
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_statistics_and_administration = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_site' ); }
    };

})( jQuery );