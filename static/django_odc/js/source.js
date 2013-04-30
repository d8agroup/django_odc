(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_source = {};


    /******************************************************************************************************************/
    /* Instance Functions */
    var methods = {
        init : function() {

            //Get a handle on the container
            var container = $(this);

            //Attach any event handlers
            container.django_odc_source('attach_event_handlers');

        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Live attach to the source object
            container

                .mouseenter(function() {

                    //Show the actions
                    $(this).find('.dataset-source-actions').show();
                })

                .mouseleave(function() {

                    //Hide the actions
                    $(this).find('.dataset-source-actions').hide();
                });

            // Attach to the configure source button
            container.find('.dataset-source-action-configure').click(function() {

                //Get a handel on the button
                var button = $(this);

                //Get a handle on the parent source container
                var source_container = button.parents('.dataset-source:first');

                //Get the source data
                var source = source_container.data('source');

                //Switch on the source channel aggregation_type
                if (source.channel.aggregation_type == 'polling') {

                    //Open the configure polling source modal
                    $.django_odc_modal_configure_polling_source.open(source);
                }
                if (source.channel.aggregation_type == 'post_adapter'){

                    //This is a post adapter type channel so open the right modal
                    $.django_odc_modal_configure_post_adapter_source.open(source);
                }
            });

            // Attach to the delete button
            container.find('.dataset-source-action-delete').click(function(){

                //Get a handel on the button
                var button = $(this);

                //Get a handle on the parent source container
                var source_container = button.parents('.dataset-source:first');

                //Get the source data
                var source = source_container.data('source');

                // Get a handel on the dataset
                var dataset_container = source_container.parents('.dataset:first');

                //Call the api to activate the source
                var callback = function() {

                    // Apply the loading message
                    dataset_container.django_odc_loading('apply', 'Deleting Source');

                    //Delay for usable UI
                    setTimeout(function(){
                        $.get(URL_SOURCE_DELETE.replace('SOURCE_ID', source.id), function(){

                            //Remove the loading mask
                            dataset_container.django_odc_loading('remove');

                            //Update the dataset object
                            $.django_odc_datasets.update_dataset(source.dataset.id);
                        });
                    }, 1000);
                };

                //Build the confirmation modal data
                var confirmation_data = {
                    title: 'Do you really want to do that?',
                    question: 'Are you sure you want to delete this source?',
                    help_message: 'All data associated with this source will be gone for good',
                    confirm_callback: callback
                };

                //Call the confirm modal
                $.django_odc_modal_confirmation.open(confirmation_data);

            });

            //Live attach to the activate source button
            container.find('.dataset-source-action-activate').click(function(){

                //Get a handel on the button
                var button = $(this);

                //Get a handle on the parent source container
                var source_container = button.parents('.dataset-source:first');

                //Get the source data
                var source = source_container.data('source');

                // Get a handel on the dataset
                var dataset_container = source_container.parents('.dataset:first');

                // Apply the loading message
                dataset_container.django_odc_loading('apply', 'Activating and Validating Source');

                //Delay for usable UI
                setTimeout(function(){
                    //Call the api to activate the source
                    $.get(URL_SOURCE_ACTIVATE.replace('SOURCE_ID', source.id), function(){

                        //Remove the loading mask
                        dataset_container.django_odc_loading('remove');

                        //Update the dataset object
                        $.django_odc_datasets.update_dataset(source.dataset.id);
                    });
                }, 1000);
            });

            //Live attach to the deactivate source button
            container.find('.dataset-source-action-deactivate').click(function(){

                //Get a handel on the button
                var button = $(this);

                //Get a handle on the parent source container
                var source_container = button.parents('.dataset-source:first');

                //Get the source data
                var source = source_container.data('source');

                // Get a handel on the dataset
                var dataset_container = source_container.parents('.dataset:first');

                // Apply the loading message
                dataset_container.django_odc_loading('apply', 'Deactivating Source');

                //Delay for usable UI
                setTimeout(function(){
                    //Call the api to deactivate the source
                    $.get(URL_SOURCE_DEACTIVATE.replace('SOURCE_ID', source.id), function(){

                        //Remove the loading mask
                        dataset_container.django_odc_loading('remove');

                        //Update the dataset object
                        $.django_odc_datasets.update_dataset(source.dataset.id);
                    });
                }, 1000);
            })
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_source = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_site' ); }
    };

})( jQuery );