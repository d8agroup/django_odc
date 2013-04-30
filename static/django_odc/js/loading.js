(function( $ ){

    /******************************************************************************************************************/
    /* Instance Functions */
    var methods = {
        apply : function(message) {

            //Get a handle on the container
            var container = $(this);

            //ensure position = relative
            container.css('position', 'relative');

            // Build the template
            var template = $('<div class="loading-mask ui-corner-all"><p class="ui-corner-all"><i class="icon-spin icon-spinner"></i> ' + message + '</p></div>');

            //set the height and width
            template.css('height', container.height() + "px");
            template.css('width', container.width() + "px");
            if (container.height() < 50) {
                template.find('p').css('font-size', "12px");
                template.find('p').css('margin-top', "5px");
                template.find('p').css('padding', "0");
            }
            else {
                template.find('p').css('margin-top', parseInt(container.height() / 3) + "px");
                template.find('p').css('font-size', (container.height() < 50) ? "12px" : "24px");
            }

            //Add the template to the container
            container.append(template);

            //Return the container
            return container;
        },
        remove: function() {

            //Get a handle on the container
            var container = $(this);

            // Remove the template
            container.find('> div.loading-mask').remove();

            //Return the container
            return container;
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_loading = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_loading' ); }
    };

})( jQuery );