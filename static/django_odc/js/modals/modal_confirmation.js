(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_modal_confirmation = {};

    //Init
    $.django_odc_modal_confirmation.init = function() {

        //Init around the modal container
        $('#modal-confirmation').django_odc_modal_confirmation();
    };

    //Open
    $.django_odc_modal_confirmation.open = function(confirmation_data) {

        //Get a handle on the modal
        var modal = $('#modal-confirmation');

        //Check init has been called
        if (modal.data('uiDialog') == null)
            $.django_odc_modal_confirmation.init();

        //set the ui
        $('#confirmation-title').html(confirmation_data.title || '');
        $('#confirmation-question').html(confirmation_data.question || '');
        $('#confirmation-help-message').html(confirmation_data.help_message || '');

        //Set the callback
        modal.data('confirm_callback', confirmation_data.confirm_callback);

        //Open
        modal.dialog('open');
    };

    //Close
    $.django_odc_modal_confirmation.close = function(run_callback) {

        //Get a handle on the modal
        var modal = $('#modal-confirmation');

        //Check init has been called
        if (modal.data('uiDialog') == null)
            $.django_odc_modal_confirmation.init();

        //If confirm, run the callback
        if (run_callback != null && run_callback)
            modal.data('confirm_callback')();

        //Close
        modal.dialog('close');
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
                width: 400,
                autoOpen: false
            });

            //Attach any event handlers
            container.django_odc_modal_confirmation('attach_event_handlers');

            //Return the container
            return container;
        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Attach the confirm action
            container.find('#confirmation-confirm-button').click(function(){

                $.django_odc_modal_confirmation.close(true);
            });

            //Attach the cancel button
            container.find('#confirmation-cancel').click(function(){

                $.django_odc_modal_confirmation.close(false);
            });
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_modal_confirmation = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_site' ); }
    };

})( jQuery );