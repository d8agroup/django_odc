(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_site = {};

    //Main function to init the site wide ui framework
    $.django_odc_site.init = function() {

        //Instance the site around the current body element
        $('body').django_odc_site();

        //Set up any side wide live attach
        $('.tipped').livequery(function(){
            $(this).tooltip();
        })
    };

    /******************************************************************************************************************/
    /* Instance Functions */
    var methods = {
        init : function() {

            //Init the your datasets section
            $('#your-datasets').django_odc_datasets();

            //Init the admin functions
            $('#statistics').django_odc_statistics_and_administration();
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_site = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_site' ); }
    };

})( jQuery );