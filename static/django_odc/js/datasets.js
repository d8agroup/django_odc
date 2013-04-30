(function( $ ){

    /******************************************************************************************************************/
    /* Static Functions */
    $.django_odc_datasets = {};

    //Reload the list
    $.django_odc_datasets.reload_datasets = function() {

        //Call the dataset list change function
        $('#your-datasets').django_odc_datasets('reload_dataset_list');
    };

    //Add a new dataset to the users dataset list
    $.django_odc_datasets.add_new_dataset = function() {

        //Create the dataset list change data
        var dataset_list_change_data = {
            action: 'new'
        };

        //Call the dataset list change function
        $('#your-datasets').django_odc_datasets('dataset_list_change', dataset_list_change_data);
    };

    //Remove a dataset from the dataset list
    $.django_odc_datasets.remove_dataset = function(dataset_id) {

        //Create the dataset list change data
        var dataset_list_change_data = {
            action: 'remove',
            dataset_id: dataset_id
        };

        //Call the dataset list change function
        $('#your-datasets').django_odc_datasets('dataset_list_change', dataset_list_change_data);
    };

    //Update a dataset
    $.django_odc_datasets.update_dataset = function(dataset_id) {

        //Create the dataset list change data
        var dataset_list_change_data = {
            action: 'update',
            dataset_id: dataset_id
        };

        //Call the dataset list change function
        $('#your-datasets').django_odc_datasets('dataset_list_change', dataset_list_change_data);
    };

    //Hide the no datasets message if its shows
    $.django_odc_datasets.show_or_hide_no_datasets_message = function() {

        var datasets = $('.dataset');

        if (datasets.length > 0)
            //Hide the no datasets message
            $('#no-datasets').hide();

        else
            //Show the no datasets message
            $('#no-datasets').show();
    };

    /******************************************************************************************************************/
    /* Instance Functions */
    var methods = {
        init : function() {

            //Get a handle on the container
            var container = $(this);

            //Attach any event handlers
            container.django_odc_datasets('attach_event_handlers');

            //Reload the dataset list
            container.django_odc_datasets('reload_dataset_list');
        },
        attach_event_handlers: function() {

            //Get a handle on the container
            var container = $(this);

            //Get a handel on the add dataset button
            var add_dataset_button = container.find('#add-dataset-button');

            //Attach the on click handler for the add dataset button
            add_dataset_button.click(function(){

                //Call the static add dataset function
                $.django_odc_datasets.add_new_dataset();
            });
        },
        reload_dataset_list: function(){

            //Get a handle on the container
            var container = $(this);

            //Call the api to load the datasets
            container.find('#datasets-container').load(URL_DATASETS, function(){

                //Datasetify all the datasets
                $('.dataset').each(function(){
                    $(this).django_odc_dataset();
                    $(this).find('.toggle-dataset-button').click();
                });
            });

        },
        dataset_list_change: function(data) {

            //Get a handle on the container
            var container = $(this);

            //If we are adding a new dataset
            if (data.action == 'new') {

                //Get a new dashboard object from the api
                $.get(URL_DATASET_TEMPLATE, function(raw_template){

                    //jQueryify the template
                    var template = $(raw_template);

                    //make the template hidden
                    template.addClass('hide');

                    //Append the template to the container
                    $('#datasets-container').prepend(template);

                    //Datasetify the template
                    template.django_odc_dataset();

                    //Show the template
                    template.slideDown();

                    //Show the no datasets message
                    $.django_odc_datasets.show_or_hide_no_datasets_message();
                });
            }
            else if (data.action == 'remove') {

                //Get the id of the subject dataset
                var dataset_id = data.dataset_id;

                //Get a handle on the subject dataset
                var dataset = $('#dataset_' + dataset_id);

                //Slide it up then remove it
                dataset.slideUp(function(){

                    //Remove it
                    $(this).remove();

                    //Show the no datasets message
                    $.django_odc_datasets.show_or_hide_no_datasets_message();
                });

                // Build the url for the api removal call
                var url = URL_DATASET_DELETE.replace('DATASET_ID', dataset_id);

                //Fire and forget to the api
                $.get(url);
            }
            else if (data.action == 'update') {

                //Get the id of the subject dataset
                var dataset_id = data.dataset_id;

                //Get a handle on the subject dataset
                var dataset = $('#dataset_' + dataset_id);

                //Get a handle on the next sibling
                var next_sibling = dataset.next();

                //Build the url to get the new dataset template
                var url = URL_DATASET.replace('DATASET_ID', dataset_id);

                //Call the api
                $.get(url, function(raw_template){

                    //jQueryify the template
                    var template = $(raw_template);

                    //Remove the original dataset
                    dataset.remove();

                    //Add the new one in place
                    next_sibling.before(template);

                    //Datasetify it
                    template.django_odc_dataset();

                    //Show the no datasets message
                    $.django_odc_datasets.show_or_hide_no_datasets_message();

                });
            }
        }
    };

    /******************************************************************************************************************/
    /* Instance Method Locator */
    $.fn.django_odc_datasets = function( method ) {
        if ( methods[method] ) { return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));}
        else if ( typeof method === 'object' || ! method ) { return methods.init.apply( this, arguments ); }
        else { $.error( 'Method ' +  method + ' does not exist on jQuery.django_odc_site' ); }
    };

})( jQuery );