(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_dataset = {};

    //Update after a save request
    $.django_odc_dataset.update_with_saved_data = function(dataset_data){

        //Get a handel on the dataset
        var dataset = $('#dataset_' + dataset_data.id);

        //Add the new data
        dataset.data('dataset', dataset_data);

        //Flash the saving icon
        dataset.find('.dataset-saved')
            .fadeIn(1000, function(){
                var dataset_saved = $(this);
                setTimeout(function(){
                    dataset_saved.fadeOut(1000);
                }, 500)
            });

        //Update the status messages
        dataset.django_odc_dataset('update_status_messages');
    };


    /******************************************************************************************************************/
    /* Instance Functions */
    var methods = {
        init : function() {

            //Get a handle on the container
            var container = $(this);

            //Attach any event handlers
            container.django_odc_dataset('attach_event_handlers');

            //Update the status messages
            container.django_odc_dataset('update_status_messages');

            //Load the sources
            container.django_odc_dataset('reload_sources');

            //Load the statistics
            container.django_odc_dataset('reload_statistics');
        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Attach event handler to the remove dataset button
            container.find('.remove-dataset-button')

                //When the button is clicked
                .click(function(){

                    //Get the id of this dataset
                    var dataset_id = $(this).parents('.dataset:first').data('dataset').id;

                    //Build the confirmation modal data
                    var confirmation_data = {
                        title: 'Do you really want to do that?',
                        question: 'Are you sure you want to delete this dataset?',
                        help_message: 'All data associated with this dataset will be gone for good',
                        confirm_callback: function() {

                            //Call the dataset list change event
                            $.django_odc_datasets.remove_dataset(dataset_id);
                        }
                    };

                    //Call the confirm modal
                    $.django_odc_modal_confirmation.open(confirmation_data);
                });

            //Attach the expand and collapse handler
            container.find('.toggle-dataset-button')

                //When the button is clicked
                .click(function(){

                    //Get a handel on the container
                    var container = $(this).parents('.dataset:first');

                    //If the dataset is expanded
                    if (container.is('.expanded')) {

                        container

                            //Remove the expanded class
                            .removeClass('expanded')

                            //Add the collapsed class
                            .addClass('collapsed')

                            //Slide up the content
                            .find('.dataset-content').slideUp();

                        //Round off the bottom of the header
                        container.find('.dataset-header').addClass('ui-corner-bottom');
                    }
                    else {

                        container

                            //Add the expanded class
                            .addClass('expanded')

                            //Remove the collapsed class
                            .removeClass('collapsed')

                            //Slide down the content
                            .find('.dataset-content').slideDown();

                        //Un round the bottom of the header
                        container.find('.dataset-header').removeClass('ui-corner-bottom');
                    }
                });

            //Attach even handler to the dataset name textbox
            container.find('.dataset-name')

                //When focus is called
                .focus(function(){
                    $(this).addClass('in-focus');
                })

                //When looses focus
                .blur(function(){
                    $(this)
                        .removeClass('in-focus')
                        .mouseleave();
                })

                //When the mouse is over it
                .mouseenter(function() {
                    $(this)
                        .addClass('active')
                        .removeClass('as-label');
                })

                //When the mouse leaves it
                .mouseleave(function() {
                    if ($(this).is('.in-focus'))
                        return;
                    $(this)
                        .removeClass('active')
                        .addClass('as-label');
                })

                //When the users has paused typing
                .bindWithDelay('keyup', function(e){

                    //If its the tab key then ignore it
                    var code = e.keyCode || e.which;
                    if (code == '9')
                        return;

                    //Get a handel on the input box
                    var input = $(this);

                    //Get a handel on the container
                    var container = input.parents('.dataset:first');

                    //Set the display name on the dataset
                    container.data('dataset').display_name = input.val();

                    //Call the save function
                    container.django_odc_dataset('save');
                }, 1500);

            //Attach the add sources event
            container.find('.add-source-button')

                .click(function(){

                    //Get a handel on the container
                    var container = $(this).parents('.dataset:first');

                    //Get the dataset id
                    var dataset_id = container.data('dataset').id;

                    //Open the add source modal
                    $.django_odc_modal_channel_types.open(dataset_id);
                });
        },
        save: function() {

            //Get a handle on the container
            var container = $(this);

            //Get the dataset data
            var dataset = container.data('dataset');

            //build the post data
            var post_data = {
                dataset: JSON.stringify(dataset)
            };

            //Make the save request to the api
            $.post(URL_DATASET_SAVE, post_data, function(updated_dataset){

                //Update the dataset
                $.django_odc_dataset.update_with_saved_data(updated_dataset);
            });
        },
        update_status_messages: function() {

            //Get a handle on the container
            var container = $(this);

            //Get the dataset data
            var dataset = container.data('dataset');

            //Hide all the status messages
            container.find('.dataset-status .label').hide();

            //Get the class of the one to show
            var class_name = "status-" + dataset.status;

            //Show the active one
            container.find('.' + class_name).show();

            //hide and remove all messages
            container.find('.dataset-messages > div').each(function(index, item){

                //Hide and remove content
                $(item).hide().html('');
            });
            
            //Get the new status messages
            var status_messages = dataset.status_messages;
            
            //If there are errors
            if (status_messages.errors != null && status_messages.errors.length > 0) {
                
                //Get a handel on the error container
                var error_container = container.find('.dataset-error-messages');
                
                //Loop through the messages
                $.each(status_messages.errors, function(index, item){
                    
                    //Format the message
                    var message = '<p><i class="icon-warning-sign"></i> ' + item + '</p>';
                    
                    //Append it to the error container
                    error_container.append(message);
                });
                
                //Show the error messages
                error_container.show();
            }

            //If there are infos
            if (status_messages.infos != null && status_messages.infos.length > 0) {
                
                //Get a handel on the info container
                var info_container = container.find('.dataset-info-messages');
                
                //Loop through the messages
                $.each(status_messages.infos, function(index, item){
                    
                    //Format the message
                    var message = '<p><i class="icon-star"></i> ' + item + '</p>';
                    
                    //Append it to the info container
                    info_container.append(message);
                });
                
                //Show the info messages
                info_container.show();
            }
        },
        reload_sources: function() {

            //Get a handel on the container
            var container = $(this);

            //Get a handel on the dataset sources list
            var dataset_sources_list = container.find('.dataset-sources-list');

            //Build the url for the sources call
            var url = URL_DATASET_SOURCES.replace('DATASET_ID', container.data('dataset').id);

            //Load the sources into the container
            dataset_sources_list.load(url, function(){

                //Sourceify all the source
                dataset_sources_list.find('.dataset-source').each(function(){
                    $(this).django_odc_source();
                })
            });
        },
        reload_statistics: function() {

            //Get a handel on the container
            var container = $(this);

            // Get a handel on the statistic summary
            var stats_summary_container = container.find('.dataset-statistics-summary');

            //Apply loading
            stats_summary_container.django_odc_loading('apply', 'Loading Statistics');

            //Get the dataset id
            var dataset_id = container.data('dataset').id;

            //Build the url
            var url = URL_DATASET_STATISTICS_SUMMARY.replace('DATASET_ID', dataset_id);

            //Load the stats summery template into the container
            $.get(url, function(template){

                stats_summary_container
                    .django_odc_loading('remove')
                    .html(template);
            });
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_dataset = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_site' ); }
    };

})( jQuery );