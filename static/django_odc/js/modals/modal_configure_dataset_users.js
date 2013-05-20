(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_modal_configure_dataset_users = {};

    //Init
    $.django_odc_modal_configure_dataset_users.init = function() {

        //Init around the modal container
        $('#modal-configure-dataset-users').django_odc_modal_configure_dataset_users();
    };

    //Store dataset id
    $.django_odc_modal_configure_dataset_users.set_dataset_id = function(dataset_id) {

        $('#modal-configure-dataset-users').data('dataset_id', dataset_id);
    };

    //Get dataset id
    $.django_odc_modal_configure_dataset_users.get_dataset_id = function() {

        return $('#modal-configure-dataset-users').data('dataset_id');
    };

    //Open
    $.django_odc_modal_configure_dataset_users.open = function(dataset_id) {

        //Check init has been called
        if ($('#modal-configure-dataset-users').data('uiDialog') == null)
            $.django_odc_modal_configure_dataset_users.init();

        //Call the open method on the instance
        $('#modal-configure-dataset-users').django_odc_modal_configure_dataset_users('open_modal', dataset_id);
    };

    //Close
    $.django_odc_modal_configure_dataset_users.close = function() {

        //Check init has been called
        if ($('#modal-configure-dataset-users').data('uiDialog') == null)
            $.django_odc_modal_configure_dataset_users.init();

        //Call the close method on the instance
        $('#modal-configure-dataset-users').django_odc_modal_configure_dataset_users('close_modal');
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
            container.django_odc_modal_configure_dataset_users('attach_event_handlers');

        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Get a handle on the close button
            var modal_close_button = container.find('.modal-close-button');

            //Attach the click handler
            modal_close_button.click(function(){

                //Call the static close method
                $.django_odc_modal_configure_dataset_users.close();
            });
        },
        open_modal: function(dataset_id) {

            //Get a handel on the container
            var container = $(this);

            //set the dataset id
            $.django_odc_modal_configure_dataset_users.set_dataset_id(dataset_id);

            //Show loading
            container.find('#configure-dataset-users-user-list').ml_themes_loading('Loading Users');

            //Build the url
            var url = URL_DATASET_USERS_CONFIGURE.replace('DATASET_ID', dataset_id);

            //Reload the content
            container.find('#configure-dataset-users-user-list').load(url, function(){

                container.find('.add-this-user-to-dataset-button').click(function(){

                    //Get a handel on the button
                    var button = $(this);

                    //show loading indicator
                    button.addClass('disabled').find('i').attr('class', 'icon-spin icon-spinner');

                    //Get the user id
                    var user_id = button.data('user_id');

                    //Get the dataset id
                    var dataset_id = $.django_odc_modal_configure_dataset_users.get_dataset_id();

                    //Build the url
                    var url = URL_DATASET_USERS_ADD.replace('DATASET_ID', dataset_id).replace('USER_ID', user_id);

                    //Call the url
                    $.get(url, function(){

                        //Call thr dataset lists to update the dataset
                        $.django_odc_datasets.update_dataset(dataset_id);

                        //Close this modal
                        $.django_odc_modal_configure_dataset_users.close()
                    })
                })
            });

            //Open the dialog
            container.dialog('open');
        },
        close_modal: function() {

            //Get a handel on the container
            var container = $(this);

            //get the dataset id
            var dataset_id = $.django_odc_modal_configure_dataset_users.get_dataset_id();

            //Reload the dataset
            $.django_odc_datasets.update_dataset(dataset_id);

            //erase the dataset id
            $.django_odc_modal_configure_dataset_users.set_dataset_id(null);

            //Close the dialog
            container.dialog('close');
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_modal_configure_dataset_users = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_modal_configure_dataset_users' ); }
    };

})( jQuery );