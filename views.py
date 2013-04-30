import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from django_odc.models import Dataset, Source, SourceTestResult
from django_odc.utils import async


@login_required(login_url='/admin')
def home(request):
    return render_to_response('django_odc/home.html', context_instance=RequestContext(request))


def aggregate_datasets_for_current_user(request):
    user = request.user
    datasets = Dataset.GetForUser(user)
    for d in datasets:
        d.aggregate_polling_sources()
    return HttpResponse('')


@login_required(login_url='/admin')
def loading(request):
    return render_to_response('django_odc/loading.html')


@login_required(login_url='/admin')
def javascript_url_bridge(request):
    template_data = {
        'urls': [
            {
                'name': 'DATASETS',
                'url': reverse('datasets')
            },
            {
                'name': 'DATASET',
                'url': reverse('dataset', args=('DATASET_ID',))
            },
            {
                'name': 'DATASET_TEMPLATE',
                'url': reverse('dataset_template')
            },
            {
                'name': 'DATASET_SAVE',
                'url': reverse('dataset_save')
            },
            {
                'name': 'DATASET_DELETE',
                'url': reverse('dataset_delete', args=('DATASET_ID',))
            },
            {
                'name': 'DATASET_SOURCES',
                'url': reverse('dataset_sources', args=('DATASET_ID',))
            },
            {
                'name': 'DATASET_STATISTICS_SUMMARY',
                'url': reverse('dataset_statistics_summary', args=('DATASET_ID',))
            },
            {
                'name': 'CHANNEL_TYPES',
                'url': reverse('channel_types')
            },
            {
                'name': 'POLLING_SOURCE_CREATE',
                'url': reverse('polling_source_create', args=('DATASET_ID', 'CHANNEL_TYPE',))
            },
            {
                'name': 'POLLING_SOURCE_CONFIGURE',
                'url': reverse('polling_source_configure', args=('SOURCE_ID',))
            },
            {
                'name': 'POLLING_SOURCE_TEST',
                'url': reverse('polling_source_test', args=('SOURCE_ID',))
            },
            {
                'name': 'POLLING_SOURCE_TEST_CHECK',
                'url': reverse('polling_source_test_check', args=('SOURCE_ID',))
            },
            {
                'name': 'POLLING_SOURCE_ANALYSIS',
                'url': reverse('polling_source_analysis', args=('SOURCE_ID', ))
            },
            {
                'name': 'POLLING_SOURCE_CONFIRM',
                'url': reverse('polling_source_confirm', args=('SOURCE_ID', ))
            },
            {
                'name': 'POST_ADAPTER_SOURCE_CREATE',
                'url': reverse('post_adapter_source_create', args=('DATASET_ID', 'CHANNEL_TYPE',))
            },
            {
                'name': 'POST_ADAPTER_SOURCE_CONFIGURE',
                'url': reverse('post_adapter_source_configure', args=('SOURCE_ID', ))
            },
            {
                'name': 'POST_ADAPTER_SOURCE_TEST_CHECK',
                'url': reverse('post_adapter_source_test_check', args=('SOURCE_ID', ))
            },
            {
                'name': 'POST_ADAPTER_SOURCE_ANALYSIS',
                'url': reverse('post_adapter_source_analysis', args=('SOURCE_ID', ))
            },
            {
                'name': 'POST_ADAPTER_SOURCE_CONFIRM',
                'url': reverse('post_adapter_source_confirm', args=('SOURCE_ID', ))
            },
            {
                'name': 'POST_ADAPTER_SOURCE_TEST',
                'url': reverse('post_adapter_source_test', args=('SOURCE_ID', ))
            },
            {
                'name': 'SOURCE_ADD_SERVICE',
                'url': reverse('source_add_service', args=('SOURCE_ID', 'SERVICE_TYPE'))
            },
            {
                'name': 'SOURCE_REMOVE_SERVICE',
                'url': reverse('source_remove_service', args=('SOURCE_ID', 'SERVICE_TYPE'))
            },
            {
                'name': 'SOURCE_ACTIVATE',
                'url': reverse('source_activate', args=('SOURCE_ID',))
            },
            {
                'name': 'SOURCE_DEACTIVATE',
                'url': reverse('source_deactivate', args=('SOURCE_ID',))
            },
            {
                'name': 'SOURCE_DELETE',
                'url': reverse('source_delete', args=('SOURCE_ID',))
            },
            {
                'name': 'SOURCES_KILL',
                'url': reverse('sources_kill')
            },
            {
                'name': 'STATISTICS_RUN_RECORDS',
                'url': reverse('statistics_run_records')
            }]}
    return render_to_response(
        'django_odc/javascript_url_bridge', template_data, content_type='text/javascript')


@login_required(login_url='/admin')
def datasets(request):
    # Get the current user
    user = request.user
    # Get all the datasets for this user
    datasets = Dataset.GetForUser(user)
    # Render these to the template
    return render_to_response('django_odc/datasets.html', {'datasets': datasets})


@login_required(login_url='/admin')
def dataset(request, dataset_id):
    # Get the dataset for this id
    dataset = Dataset.GetById(dataset_id)
    # Build the template data for the template
    template_data = {
        'dataset': dataset,  # The raw dataset object
        'dataset_as_json': dataset.to_json()}  # A json copy for the data element
    # Render the template to the response
    return render_to_response('django_odc/dataset.html', template_data)


@login_required(login_url='/admin')
def dataset_template(request):
    # Create a new dataset for this user
    dataset = Dataset.Create(request.user)
    # Build the template data for the template
    template_data = {
        'dataset': dataset,  # The raw dataset object
        'dataset_as_json': dataset.to_json()}  # A json copy for the data element
    # Render the template to the response
    return render_to_response('django_odc/dataset.html', template_data)


@login_required(login_url='/admin')
@csrf_exempt
def dataset_save(request):
    # Get the updated json from the POST variable
    updated_json = request.POST.get('dataset')
    # Check we have it
    if updated_json:
        # JSON Parse it into an object
        updated_data = json.loads(updated_json)
        # Extract the dataset id
        dataset_id = updated_data.get('id')
        # Get the dataset by this id
        dataset = Dataset.GetById(dataset_id)
        # Check we have it
        if dataset:
            # Call the save overload passing in the updated data
            dataset.save(updated_data=updated_data)
            # Return the new dataset serialized to json
            return HttpResponse(dataset.to_json(), content_type='application/json')
    # Else just return what was sent
    return HttpResponse(updated_json, content_type='application/json')


@login_required(login_url='/admin')
def dataset_delete(request, dataset_id):
    # Get the dataset in question
    dataset = Dataset.GetById(dataset_id)
    # Delete it
    dataset.mark_as_deleted()
    # Return none
    return HttpResponse('')


@login_required(login_url='/admin')
def dataset_statistics_summary(request, dataset_id):
    # Get the dataset by its id
    dataset = Dataset.GetById(dataset_id)
    # Get the dataset statistics
    statistics = dataset.get_statistics()
    # render the template
    return render_to_response('django_odc/dataset_statistics_summary.html', {'statistics': statistics})


@login_required(login_url='/admin')
def dataset_sources(request, dataset_id):
    # Get the dataset for this id
    dataset = Dataset.GetById(dataset_id)
    # Get the sources configuration for this dataset
    sources = dataset.sources_configuration()
    # If there is no
    if not sources:
        # Return the empty template
        return render_to_response('django_odc/dataset_no_sources.html')
    # Else render the sources and return t he template
    return render_to_response('django_odc/dataset_sources.html', {'sources': sources})


@login_required(login_url='/admin')
def channel_types(request):
    # Get all the currently available channel types
    available_channels = Source.AllAvailableChannelConfigurations()
    # Render the template and return it
    return render_to_response('django_odc/modal_channel_types_list.html', {'channels': available_channels})


@login_required(login_url='/admin')
@csrf_exempt
def polling_source_create(request, dataset_id, channel_type):
    # Get the dataset that matches the id
    dataset = Dataset.GetById(dataset_id)
    # Create a new source
    source = Source.Create(dataset, channel_type)
    # Render the template with the config
    return HttpResponse(source.to_json(), content_type='application/json')


@login_required(login_url='/admin')
@csrf_exempt
def polling_source_configure(request, source_id):
    # Get the source from by the id
    source = Source.GetById(source_id)
    #If this is an update via POST
    if request.method == 'POST':
        # Update based on the post vars
        source.save(updated_data=request.POST)
        # If there were no config errors
        if source.status != 'unconfigured':
            # Redirect to the test view
            return redirect('polling_source_test', source_id=source_id)
    # Return the configure source template
    return render_to_response(
        'django_odc/modals/configure_polling_source/configure_polling_source_config.html',
        {'source': source})


@login_required(login_url='/admin')
@async
def polling_source_test(request, source_id):
    # Get the source from by the id
    source = Source.GetById(source_id)
    # If the source is unconfigured
    if source.status == 'unconfigured':
        # Redirect to the configure view
        yield redirect('polling_source_configure', source_id=source_id)
        return
    # yield the testing html - async
    yield render_to_response(
        'django_odc/modals/configure_polling_source/configure_polling_source_test.html',
        {'source': source})
    # Init the get test data routine
    source.begin_get_and_parse_test_data()
    return


@login_required(login_url='/admin')
def polling_source_test_check(request, source_id):
    # Get the source from by the id
    source = Source.GetById(source_id)
    # Get the results of the current test
    current_results = source.get_current_test_data_results()
    # If the results are none or the results are in error state
    if not current_results or current_results.status == 'error':
        # Build the error template out of the current results or the default test errors
        error_template = render_to_string(
            'django_odc/modals/configure_polling_source/configure_polling_source_test_error.html',
            {'test_results': current_results or SourceTestResult.DefaultTestErrorReturn()})
        # Json encode it and return it along with status = error
        return HttpResponse(
            json.dumps({'status': 'error', 'template': error_template}),
            content_type='application/json')
    # If the test is still running then return the data
    if current_results.status == 'running':
        return HttpResponse(current_results.to_json(), content_type='application/json')
    # Choose the template based on the status of the test
    template_name_format = 'django_odc/modals/configure_polling_source/configure_polling_source_test_%s.html'
    template_name = template_name_format % current_results.status
    # Render the template
    template = render_to_string(template_name, {'test_results': current_results})
    # Build the return data
    return_data = {
        'status': current_results.status,
        'template': template}
    # Return the template
    return HttpResponse(json.dumps(return_data), content_type='application/json')


@login_required(login_url='/admin')
def polling_source_confirm(request, source_id):
    # Get the source from by the id
    source = Source.GetById(source_id)
    # Render the source confirm template
    return render_to_response(
        'django_odc/modals/configure_polling_source/configure_polling_source_confirm.html',
        {'source': source})


@login_required(login_url='/admin')
def polling_source_analysis(request, source_id):
    # Get the source from by the id
    source = Source.GetById(source_id)
    # Get the services configured for this source
    source_services = source.services
    # Get all the available analysis services
    analysis_services_configs = source.get_all_available_service()
    # Create an array to merge the two lists into
    all_services_including_configured_services = [s for s in source_services]
    # Add any services that are not currently applied to the source
    for service in analysis_services_configs:
        if not [s for s in all_services_including_configured_services if s['type'] == service['type']]:
            all_services_including_configured_services.append(service)
    # Get the results of the current test
    return render_to_response(
        'django_odc/modals/configure_polling_source/configure_polling_source_analysis.html',
        {'source': source, 'services': all_services_including_configured_services})


@login_required(login_url='/admin')
@csrf_exempt
def post_adapter_source_create(request, dataset_id, channel_type):
    # Get the dataset that matches the id
    dataset = Dataset.GetById(dataset_id)
    # Create a new source
    source = Source.Create(dataset, channel_type)
    # Render the template with the config
    return HttpResponse(source.to_json(), content_type='application/json')


@login_required(login_url='/admin')
@csrf_exempt
def post_adapter_source_configure(request, source_id):
    # Get the source from by the id
    source = Source.GetById(source_id)
    #If this is an update via POST
    if request.method == 'POST':
        # Update based on the post vars
        source.save(updated_data=request.POST)
        # If there were no config errors
        if source.status != 'unconfigured':
            # Redirect to the test view
            return redirect('post_adapter_source_test', source_id=source_id)
    # Return the configure source template
    return render_to_response(
        'django_odc/modals/configure_post_adapter_source/configure_post_adapter_source_config.html',
        {'source': source})


@login_required(login_url='/admin')
def post_adapter_source_test(request, source_id):
    # Get the source by the id
    source = Source.GetById(source_id)
    # If the source is unconfigured
    if source.status == 'unconfigured':
        # Redirect to the configure view
        return redirect('post_adapter_source_configure', source_id=source_id)
    # Init the get test data routine
    test_id = source.begin_get_and_parse_test_data()
    # Build the relative url
    relative_adapter_url = reverse('post_adapter_source_test_adapter', args=(source_id, test_id, ))
    #Build the full url
    full_adapter_url = request.build_absolute_uri(relative_adapter_url)
    # return the testing html - async
    return render_to_response(
        'django_odc/modals/configure_post_adapter_source/configure_post_adapter_source_test.html',
        {'source': source, 'test_id': test_id, 'full_adapter_url': full_adapter_url})


@login_required(login_url='/admin')
def post_adapter_source_instructions(request, source_id):
    # Get the source by the id
    source = Source.GetById(source_id)
    # Get the instructions as a string
    instructions = source.get_post_adapter_instructions()
    # Build and return the response
    return HttpResponse(instructions, content_type='text/javascript')


@csrf_exempt
def post_adapter_source_test_adapter(request, source_id, test_id):
    # Get the source by the id
    source = Source.GetById(source_id)
    # Extract the raw request data
    raw_data = request.body
    # Tell the source to update the test
    results = source.update_test_with_raw_data(test_id, raw_data)
    # Return the ok status
    return HttpResponse(json.dumps(results), content_type='application/json')


@login_required(login_url='/admin')
def post_adapter_source_test_check(request, source_id):
    # Get the source from by the id
    source = Source.GetById(source_id)
    # Get the results of the current test
    current_results = source.get_current_test_data_results()
    # If the results are none or the results are in error state
    if not current_results or current_results.status == 'error':
        # Build the error template out of the current results or the default test errors
        error_template = render_to_string(
            'django_odc/modals/configure_post_adapter_source/configure_post_adapter_source_test_error.html',
            {'test_results': current_results or SourceTestResult.DefaultTestErrorReturn()})
        # Json encode it and return it along with status = error
        return HttpResponse(
            json.dumps({'status': 'error', 'template': error_template}),
            content_type='application/json')
    # If the test is still running then return the data
    if current_results.status == 'running':
        return HttpResponse(current_results.to_json(), content_type='application/json')
    # Render the passed template and return it
    template = render_to_string(
        'django_odc/modals/configure_post_adapter_source/configure_post_adapter_source_test_passed.html',
        {'test_results': current_results})
    return HttpResponse(
        json.dumps({'status': 'passed', 'template': template, 'results': current_results.results}),
        content_type='application/json')


@login_required(login_url='/admin')
def post_adapter_source_confirm(request, source_id):
    # Get the source from by the id
    source = Source.GetById(source_id)
    # Build the relative url
    relative_adapter_url = reverse('post_adapter_source_adapter', args=(source_id, ))
    #Build the full url
    full_adapter_url = request.build_absolute_uri(relative_adapter_url)
    # Render the source confirm template
    return render_to_response(
        'django_odc/modals/configure_post_adapter_source/configure_post_adapter_source_confirm.html',
        {'source': source, 'full_adapter_url': full_adapter_url})


@login_required(login_url='/admin')
def post_adapter_source_analysis(request, source_id):
    # Get the source from by the id
    source = Source.GetById(source_id)
    # Get the services configured for this source
    source_services = source.services
    # Get all the available analysis services
    analysis_services_configs = source.get_all_available_service()
    # Create an array to merge the two lists into
    all_services_including_configured_services = [s for s in source_services]
    # Add any services that are not currently applied to the source
    for service in analysis_services_configs:
        if not [s for s in all_services_including_configured_services if s['type'] == service['type']]:
            all_services_including_configured_services.append(service)
    # Get the results of the current test
    return render_to_response(
        'django_odc/modals/configure_post_adapter_source/configure_post_adapter_source_analysis.html',
        {'source': source, 'services': all_services_including_configured_services})


@csrf_exempt
def post_adapter_source_adapter(request, source_id):
    # Get the source by the id
    source = Source.GetById(source_id)
    # Extract the raw request data
    raw_data = request.body
    # Tell the source to update the test
    results = source.update_with_raw_data(raw_data)
    # Return the ok status
    return HttpResponse(json.dumps(results), content_type='application/json')


@login_required(login_url='/admin')
def source_add_service(request, source_id, service_type):
    # Get the source from by the id
    source = Source.GetById(source_id)
    # Add the service to the source
    source.add_service_by_service_type(service_type)
    # Return ok
    return HttpResponse()


@login_required(login_url='/admin')
def source_remove_service(request, source_id, service_type):
    # Get the source from by the id
    source = Source.GetById(source_id)
    # Remove the services by its type
    source.remove_service_by_service_type(service_type)
    # Return ok
    return HttpResponse()


@login_required(login_url='/admin')
def source_activate(request, source_id):
    # Get the source by its id
    source = Source.GetById(source_id)
    # Activate it
    source.activate()
    # return
    return HttpResponse()


@login_required(login_url='/admin')
def source_deactivate(request, source_id):
    # Get the source by its id
    source = Source.GetById(source_id)
    # deactivate it
    source.deactivate()
    # return
    return HttpResponse()


@login_required(login_url='/admin')
def source_delete(request, source_id):
    # Get the source by its id
    source = Source.GetById(source_id)
    # deactivate it
    source.delete()
    # return
    return HttpResponse()


@login_required(login_url='/admin')
def sources_kill(request):
    # Get all the datasets for this user
    datasets = Dataset.GetForUser(request.user)
    # Issue the kill signal
    [d.kill() for d in datasets]
    # return nothing
    return HttpResponse('')


@login_required(login_url='/admin')
def statistics_run_records(request):
    # Get all datasets for this user
    datasets = Dataset.GetForUser(request.user)
    # List for all the run records
    run_records = []
    # Loop over the datasets adding run records
    for dataset in datasets:
        run_records += dataset.get_run_records()
    # Sort them by date desc
    run_records = sorted(run_records, key=lambda r: r.created, reverse=True)
    # Render them to the template
    return render_to_response('django_odc/run_records.html', {'run_records': run_records})