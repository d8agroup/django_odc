(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_modal_twitterv01_authentication = {};

    //Init
    $.django_odc_modal_twitterv01_authentication.init = function() {

        //Init around the modal container
        $('#modal-twitterv01-authentication').django_odc_modal_twitterv01_authentication();
    };

    //Open
    $.django_odc_modal_twitterv01_authentication.open = function(on_close_callback) {

        //Get a handle on the modal
        var modal = $('#modal-twitterv01-authentication');

        //Check init has been called
        if (modal.data('uiDialog') == null)
            $.django_odc_modal_twitterv01_authentication.init();

        //Store the callback
        modal.data('on_close_callback', on_close_callback);

        //Call the open method on the instance
        modal.django_odc_modal_twitterv01_authentication('open_modal');
    };

    //Close
    $.django_odc_modal_twitterv01_authentication.close = function() {

        //Get a handle on the modal
        var modal = $('#modal-twitterv01-authentication');

        //Check init has been called
        if (modal.data('uiDialog') == null)
            $.django_odc_modal_twitterv01_authentication.init();

        //Call the close method on the instance
        modal.django_odc_modal_twitterv01_authentication('close_modal');

        //If there is a callback then call it
        var callback = modal.data('on_close_callback');
        if (callback != null)
            callback();
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
            container.django_odc_modal_twitterv01_authentication('attach_event_handlers');

        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Get a handle on the close button
            var modal_close_button = container.find('.modal-close-button');

            //Attach the click handler
            modal_close_button.click(function(){

                //Call the static close method
                $.django_odc_modal_twitterv01_authentication.close();
            });
        },
        open_modal: function() {

            //Get a handel on the container
            var container = $(this);

            //Apply loading
            container.find('.modal-content > .inner').django_odc_loading('apply', 'Loading');

            //Make the api request to load up the config
            $.get(URL_STATISTICS_AUTHENTICATION_TWITTERV01_CONFIGURE, function(return_data){

                //Load the config ui
                container.django_odc_modal_twitterv01_authentication('reload_config', return_data.template);
            });

            //Open the dialog
            container.dialog('open');
        },
        reload_config: function(raw_template){

            //sort out the indicator steps
            $('.twitterv01-authentication-step').removeClass('active');
            $('#twitterv01-authentication-step-1').addClass('active');

            //Get a handel on the container
            var container = $(this);

            //Get a handle on the modal content inner
            var content = container.find('#twitterv01-authentication-content');

            container.find('.modal-content > .inner').django_odc_loading('apply', 'Loading');

            //jQueryify the template
            var template = $(raw_template);

            //Remove loading
            container.find('.modal-content > .inner').django_odc_loading('remove');
            
            //Load the template into the inner container
            content.html(template);

            //Get a handel on the form
            var form = template.find('form');

            //Prevent the form load
            form.submit(function(e){ e.preventDefault(); return false; });

            //Attach to the form submit button
            $('#twitterv01-authentication-config-submit-button').click(function(e){

                //serialize the form
                var post_data = form.serializeArray();

                //Apply loading
                container.find('.modal-content > .inner').django_odc_loading('apply', 'Just checking');

                $.post(URL_STATISTICS_AUTHENTICATION_TWITTERV01_CONFIGURE, post_data, function(return_data){

                    if (return_data.status == 'error') {

                        //reload the config ui
                        container.django_odc_modal_twitterv01_authentication('reload_config', return_data.template);
                    }
                    else {

                        //Load the oauth ui
                        container.django_odc_modal_twitterv01_authentication('load_oauth', return_data.template);
                    }
                });
            });

        },
        load_oauth: function(raw_template) {

            //sort out the indicator steps
            $('.twitterv01-authentication-step').removeClass('active');
            $('#twitterv01-authentication-step-2').addClass('active');

            //Get a handel on the container
            var container = $(this);

            //Get a handle on the modal content inner
            var content = container.find('#twitterv01-authentication-content');

            //jQueryify the template
            var template = $(raw_template);

            //Remove loading
            container.find('.modal-content > .inner').django_odc_loading('remove');
            
            //Load the template into the inner container
            content.html(template);

            //Get a handel on the form
            var form = template.find('form');

            //Prevent the form load
            form.submit(function(e){ e.preventDefault(); return false; });

            //Attach to the form submit button
            $('#twitterv01-authentication-oauth-submit-button').click(function(e){

                //serialize the form
                var post_data = form.serializeArray();

                //Apply loading
                container.find('.modal-content > .inner').django_odc_loading('apply', 'Just checking');

                $.post(URL_STATISTICS_AUTHENTICATION_TWITTERV01_OAUTH, post_data, function(return_data){

                    if (return_data.status == 'error') {

                        //reload the config ui
                        container.django_odc_modal_twitterv01_authentication('load_oauth', return_data.template);
                    }
                    else {

                        //Load the oauth ui
                        container.django_odc_modal_twitterv01_authentication('load_confirmation', return_data.template);
                    }
                });
            });
        },
        load_confirmation: function(raw_template){

            //sort out the indicator steps
            $('.twitterv01-authentication-step').removeClass('active');
            $('#twitterv01-authentication-step-3').addClass('active');

            //Get a handel on the container
            var container = $(this);

            //Get a handle on the modal content inner
            var content = container.find('#twitterv01-authentication-content');

            content.django_odc_loading('apply', 'Loading');

            //jQueryify the template
            var template = $(raw_template);

            //Load the template into the inner container
            content
                .django_odc_loading('remove')
                .html(template);

        },
        close_modal: function() {

            //Get a handel on the container
            var container = $(this);

//            //erase the dataset id
//            $.django_odc_modal_twitterv01_authentication.set_dataset_id(null);

            //Close the dialog
            container.dialog('close');
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_modal_twitterv01_authentication = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_modal_twitterv01_authentication' ); }
    };

})( jQuery );