(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_dataset = {};


    /******************************************************************************************************************/
    /* Instance Functions */
    var methods = {
        init : function() {

            //Get a handle on the container
            var container = $(this);

            //Attach any event handlers
            container.django_odc_dataset('attach_event_handlers');

        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Get a handel on the add dataset button
            var add_dataset_button = container.find('#add-dataset-button');

            //Attach the on click handler for the add dataset button
            add_dataset_button.click(function(){

                //Call the static add dataset function
                $.django_odc_dataset.add_new_dataset();
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