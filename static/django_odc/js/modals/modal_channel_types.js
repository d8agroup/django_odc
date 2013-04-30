(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_modal_channel_types = {};

    //Init
    $.django_odc_modal_channel_types.init = function() {

        //Init around the modal container
        $('#modal-channel-types').django_odc_modal_channel_types();
    };

    //Store dataset id
    $.django_odc_modal_channel_types.set_dataset_id = function(dataset_id) {

        $('#modal-channel-types').data('dataset_id', dataset_id);
    };

    //Get dataset id
    $.django_odc_modal_channel_types.get_dataset_id = function() {

        return $('#modal-channel-types').data('dataset_id');
    };

    //Open
    $.django_odc_modal_channel_types.open = function(dataset_id) {

        //Check init has been called
        if ($('#modal-channel-types').data('uiDialog') == null)
            $.django_odc_modal_channel_types.init();

        //Call the open method on the instance
        $('#modal-channel-types').django_odc_modal_channel_types('open_modal', dataset_id);
    };

    //Close
    $.django_odc_modal_channel_types.close = function() {

        //Check init has been called
        if ($('#modal-channel-types').data('uiDialog') == null)
            $.django_odc_modal_channel_types.init();

        //Call the close method on the instance
        $('#modal-channel-types').django_odc_modal_channel_types('close_modal');
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
            container.django_odc_modal_channel_types('attach_event_handlers');

        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Get a handle on the close button
            var modal_close_button = container.find('.modal-close-button');

            //Attach the click handler
            modal_close_button.click(function(){

                //Call the static close method
                $.django_odc_modal_channel_types.close();
            });

            container.find('.available-channel-type')

                //Live attach to the source mouseover
                .livequery('mouseenter', function(){

                    //Get a handle on the source container
                    var container = $(this);

                    //Extract the source data
                    var channel = container.data('channel');

                    //Hide the help message
                    $('#channel-details-instructions').hide();

                    //set the display name
                    $('#channel-details-display-name').html(channel.display_name_short);

                    //Set the description
                    $('#channel-details-description').html(channel.description_full);
                })

                //Live attach to the source mouseout
                .livequery('mouseleave', function(){

                    //Show the help message
                    $('#channel-details-instructions').show();

                    //set the display name to blank
                    $('#channel-details-display-name').html('');

                    //Set the description to blank
                    $('#channel-details-description').html('');
                })

                //Live attach to the click event
                .livequery('click', function(){

                    //Get a handel on the clicked channel
                    var channel_container = $(this);

                    //Get the channel data
                    var channel = channel_container.data('channel');

                    //Build the data to pass to the config modal
                    var channel_data = {
                        channel: channel,
                        dataset_id: $.django_odc_modal_channel_types.get_dataset_id()
                    };

                    //Close this modal
                    $.django_odc_modal_channel_types.close();

                    //Switch on the aggregation type of this channel
                    if (channel.aggregation_type == 'polling'){

                        //This is a polling type channel so open the configure_polling_source modal
                        $.django_odc_modal_configure_polling_source.open_with_channel(channel_data);
                    }
                    if (channel.aggregation_type == 'post_adapter'){

                        //This is a post adapter type channel so open the right modal
                        $.django_odc_modal_configure_post_adapter_source.open_with_channel(channel_data);
                    }
                    //TODO: Add support for more aggregation types
                });
        },
        open_modal: function(dataset_id) {

            //Get a handel on the container
            var container = $(this);

            //set the dataset id
            $.django_odc_modal_channel_types.set_dataset_id(dataset_id);

            //Reload the content
            container.find('#channel-types-list').load(URL_CHANNEL_TYPES);

            //Open the dialog
            container.dialog('open');
        },
        close_modal: function() {

            //Get a handel on the container
            var container = $(this);

            //erase the dataset id
            $.django_odc_modal_channel_types.set_dataset_id(null);

            //Close the dialog
            container.dialog('close');
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_modal_channel_types = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_modal_channel_types' ); }
    };

})( jQuery );