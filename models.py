import datetime
import inspect
import json
import re
import sys

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

import channels
from django_odc.objects import ContentItem
from django_odc.settingsbridge import access_settings
from django_odc.utils import async, format_error
import services
import datacontext


class Dataset(models.Model):
    display_name = models.TextField()
    user = models.ForeignKey(User)
    status = models.TextField(default='unconfigured')
    _status_messages = models.TextField(default='')
    created = models.DateTimeField()
    modified = models.DateTimeField()

    @classmethod
    def Create(cls, user):
        # Create a new dataset with default values
        dataset = Dataset(
            user=user,  # The current user
            created=now(),  # Created now
            modified=now())  # Modified now
        # Call save to cause validation
        dataset.save()
        # Return the new dataset
        return dataset

    @classmethod
    def GetById(cls, dataset_id):
        # Dataset should always exists, but you never know :D
        try:
            # Get the dataset
            dataset = Dataset.objects.get(id=dataset_id)
            # Save it to force validation
            dataset.save()
            # And then return it
            return dataset
        except Dataset.DoesNotExist:
            return None

    @classmethod
    def GetForUser(cls, user, include_deleted=False, count=None):
        datasets = Dataset.objects.filter(user=user)
        if not include_deleted:
            datasets = [d for d in datasets if d.status != 'deleted']
        if count:
            datasets = datasets[:count]
        return datasets

    @property
    def status_messages(self):
        return json.loads(self._status_messages)

    @status_messages.setter
    def status_messages(self, value):
        self._status_messages = json.dumps(value)

    def validate(self):
        # Default status messages
        status_messages = {'errors': [], 'infos': []}
        # Check for display_name
        if not self.display_name:
            self.status = 'unconfigured'
            status_messages['infos'].append('You need to provide a name for this dataset.')
        else:
            # Get the source configs
            source_configs = self.sources_configuration()
            # Check for the lack of sources
            if not source_configs:
                self.status = 'unconfigured'
                status_messages['infos'].append('There are no sources configured for this dataset.')
            # If any are running
            elif any(s['status'] == 'running' for s in source_configs):
                # Then the dataset should be active
                self.status = 'running'
            # If any are active
            elif any(s['status'] == 'active' for s in source_configs):
                # Then the dataset should be active
                self.status = 'active'
            # Finally if none are active
            else:
                # The the dataset is inactive
                self.status = 'inactive'
                status_messages['infos'].append('None of the sources in this dataset are active.')
            # Serialize the status messages for storage
        self.status_messages = status_messages

    def save(self, updated_data=None, *args, **kwargs):
        # If there are updates to apply
        if updated_data:
            # Apply the display_name
            self.display_name = updated_data.get('display_name')
            # Call validate to update status and status messages if not deleted
        if self.status != "deleted":
            self.validate()
            # Set the last modified time to now
        self.modified = now()
        # Save the object
        super(Dataset, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id, # The id of the dataset
            'display_name': self.display_name, # The dataset display name
            'status': self.status, # The status
            'status_messages': self.status_messages, # Get the un serialized status messages
            'created': self.created.strftime('%X'), # Format time as local
            'modified': self.modified.strftime('%X')}  # Format time as local

    def to_json(self):
        # Json serialize the bits we want in the format we want
        return json.dumps(self.to_dict())

    def sources_configuration(self):
        # Get any source objects associated with this dataset
        sources = self.source_set.exclude(status='deleted').all()
        # Extract and json decode
        configuration = [s.to_dict() for s in sources]
        # Return the configuration array
        return configuration

    def mark_as_deleted(self):
        self.status = "deleted"
        self.save()

    def aggregate_polling_sources(self):
        # if we are not in the ready to run state then just return
        if self.status != 'active':
            return
            # Get all sources that are ready to run
        sources = self.source_set.filter(status='active')
        # Filter out ones that are not polling
        sources = [s for s in sources if s.channel['aggregation_type'] == 'polling']
        # If there are non then just break out
        if not sources:
            return
            # Call the polling aggregate function on each of the sources
        for source in sources:
            self.send_data_to_datasetore(source.aggregate_polling_source())

    def send_data_to_datasetore(self, data):
        # Get the current data context
        data_context = self._get_data_context()
        # Call the push data function on the data context
        data_context.push(data)

    def kill(self):
        # If this is not running then just quit
        if self.status != 'running':
            return
        # Kill any running sources
        for source in self.source_set.filter(status='running').all():
            source.kill()
        # If the top level state is still running
        if self.status == 'running':
            self.status = 'active'
            self.save()

    def get_run_records(self, count=None):
        # A list to hold them in
        run_records = []
        # Loop over sources collecting run records
        for source in self.source_set.all():
            run_records += [r for r in source.sourcerunrecord_set.all()]
        # Return the list
        return run_records

    def get_statistics(self):
        # Get the current data context
        data_context = self._get_data_context()
        # Get the raw statistics from the data context
        statistics = data_context.dataset_statistics(self)
        # Return them
        return statistics

    def _get_data_context(self):
        # Get the dynamic data context init config
        config = access_settings('ODC_DATACONTEXT_INIT_CONFIG')
        # Get the dynamically configured data context
        data_context = getattr(datacontext, access_settings('ODC_DATACONTEXT_TYPE'))(config)
        return data_context


class Source(models.Model):
    _channel = models.TextField(default='{}')  # The configuration of the underlying channel
    _status_messages = models.TextField(default='')  # Any status messages for the source
    _services = models.TextField(default='[]')  # The json serialized services collection
    display_name = models.TextField(default='')  # A user friendly name provided by the user
    dataset = models.ForeignKey(Dataset)  # Link to the parent dataset
    status = models.TextField(default='unconfigured')  # The status of the data point
    created = models.DateTimeField()  # When it was Created
    modified = models.DateTimeField()  # When it was modified

    is_channel_regex = re.compile(r'^[A-Z]\w+Channel$')  # Regex for extracting only channels from the channels module
    is_service_regex = re.compile(r'^[A-Z]\w+Service$')  # Regex for extracting only services from the services module

    @classmethod
    def Create(cls, dataset, channel_type):
        # Create a new source with the args plus some defaults
        source = Source(
            dataset=dataset, # The parent dataset
            created=datetime.datetime.now())  # Created now
        # Add the channel
        source.channel = Source._GetChannelByType(channel_type).configuration
        # Add the status messages template
        source.status_messages = {'errors': [], 'infos': []}
        # Call save override
        source.save()
        # Return new source
        return source

    @classmethod
    def GetById(cls, source_id):
        try:
            return Source.objects.get(id=source_id)
        except Source.DoesNotExist:
            return None

    @classmethod
    def AllAvailableChannelConfigurations(cls):
        # Get all the sources from the sources module
        all_sources = cls._AllAvailableChannels()
        # Get a list of their configuration
        configurations = [s.configuration for s in all_sources]
        # Return the configs
        return configurations

    @classmethod
    def _GetChannelByType(cls, channel_type):
        all_available_channels = cls._AllAvailableChannels()
        candidate_channels = [s for s in all_available_channels if s.configuration['type'] == channel_type]
        if not candidate_channels:
            return None
        return candidate_channels[0]

    @classmethod
    def _AllAvailableChannels(cls):
        # Get a list of the the source classes in the sources module
        all_classes = inspect.getmembers(sys.modules[channels.__name__], inspect.isclass)
        # Filter out any that are not sources
        all_channels = [s[1]() for s in all_classes if cls.is_channel_regex.search(s[0])]
        return all_channels

    @classmethod
    def _AllAvailableServices(cls, channel_data_type):
        # Get a list of the the source classes in the services module
        all_classes = inspect.getmembers(sys.modules[services.__name__], inspect.isclass)
        # Filter out any that are not services
        all_services = [s[1]() for s in all_classes if cls.is_service_regex.search(s[0])]
        # Filter out any that do not support the provided data type
        available_services = [s for s in all_services if s.channel_data_type_is_supported(channel_data_type)]
        # Return the services
        return available_services

    @property
    def channel(self):
        return json.loads(self._channel)

    @channel.setter
    def channel(self, value):
        self._channel = json.dumps(value)

    @property
    def status_messages(self):
        return json.loads(self._status_messages)

    @status_messages.setter
    def status_messages(self, value):
        self._status_messages = json.dumps(value)

    @property
    def services(self):
        return json.loads(self._services)

    @services.setter
    def services(self, value):
        self._services = json.dumps(value)

    def add_service_by_service_type(self, service_type):
        # If the service already exists do nothing
        if [s for s in self.services if s['type'] == service_type]:
            return
            # Get a copy the service config
        service_config = [s for s in self.get_all_available_service() if s['type'] == service_type][0]
        # Enhance the service config
        service_config['active'] = True
        service_config['created'] = now().strftime('%c')
        # Get a handel on the decoded services
        services = self.services
        # Add the new one
        services.append(service_config)
        # Put them back
        self.services = services
        #Save
        self.save()

    def remove_service_by_service_type(self, service_type):
        # If the service does not already exists do nothing
        if not [s for s in self.services if s['type'] == service_type]:
            return
            # Get a handel on the decoded services
        services = self.services
        # Put them back excluding the one to remove
        self.services = [s for s in services if s['type'] != service_type]
        # save
        self.save()

    def activate(self):
        # Set the status
        self.status = 'active'
        # Call save and validate
        self.save()

    def deactivate(self):
        # Set the status
        self.status = 'inactive'
        # Call save and validate
        self.save(skip_validation=True)

    def validate(self, validate_config=True):
        # If we are to validate the underlying channel config
        if validate_config:
            # Json ready object to hold the status messages
            status_messages = {'errors': [], 'infos': []}
            # Check that a display name has been provided
            if not self.display_name:
                status_messages['errors'].append('You need to provide a name for this source.')
                # Check that the display name is unique for this dataset
            is_unique = len(
                Source.objects.filter(dataset=self.dataset).filter(display_name=self.display_name).all()) < 2
            if self.display_name and not is_unique:
                # And f not then add an error saying so
                status_messages['errors'].append('You already have a source with that name in this dataset.')
                # Call the channel to validate the config
            status_messages['errors'] += self._underlying_channel().ValidateAndReturnErrors(self.channel)
            # If there are errors returned from the underlying channel
            if status_messages['errors']:
                # Set the state to unconfigured
                self.status = 'unconfigured'
            # Else if no errors and the current state is unconfigured
            elif self.status == 'unconfigured':
                # Set to active
                self.status = 'inactive'
                # Put in the status messages
            self.status_messages = status_messages

    def save(self, updated_data=None, skip_validation=False, *args, **kwargs):
        # If there is updated data then update the channel config
        if updated_data:
            # Update the display name
            self.display_name = updated_data.get('display_name', '')
            # Extract the config
            configuration = self.channel
            # Get a handle on the elements in the config
            elements = configuration['config']['elements']
            # Loop over the element keys
            for key in [e['name'] for e in elements]:
                # Update the values
                [e for e in elements if e['name'] == key][0]['value'] = updated_data.get(key, '')
                # Reset the config
            self.channel = configuration
        # Call validate to update status and status messages but skip validate config if first save
        if not skip_validation:
            self.validate(validate_config=self.modified)
            # Set the last modified time to now
        self.modified = now()
        # Save the object
        super(Source, self).save(*args, **kwargs)

    def delete(self, force_delete=False, using=None):
        # Intercept the delete signal and mark as deleted
        if force_delete:
            super(Source, self).delete(using)
        else:
            self.status = 'deleted'
            self.save(skip_validation=True)

    def to_dict(self):
        return {
            'id': self.id,
            'display_name': self.display_name,
            'services': self.services,
            'status': self.status,
            'dataset': json.loads(self.dataset.to_json()),
            'channel': self._underlying_channel().configuration}

    def to_json(self):
        return json.dumps(self.to_dict())

    @async
    def begin_get_and_parse_test_data(self):
        # Mark all previous tests as inactive
        for test_result in self.sourcetestresult_set.all():
            test_result.mark_as_inactive()
        # Create a new test results object for this test
        test_result = SourceTestResult.Create(self)
        #yield the test id
        yield test_result.id
        # LONG RUNNING - Call the underlying channel to start a new test
        self._underlying_channel().run_test(self, self.channel, test_result.id)

    def update_with_raw_data(self, raw_data):
        # If this source is not active say so
        if self.status != 'active':
            return {
                'status': 'error',
                'errors': ['The source you are trying to send data to is not currently active.']}
        # Get any currently running run records
        run_records = [r for r in self.sourcerunrecord_set.filter(status='running').all()]
        # If there none or is more then one then kill them all
        if not len(run_records) or len(run_records) > 1:
            [r.kill('Overlapping runs called') for r in run_records]
            # And create a new one
            record = SourceRunRecord.Create(self)
        else:
            record = run_records[0]
        # Call the channel to update the test
        data = self._underlying_channel().receive_post_data(self, self.channel, record, raw_data)
        # Send this data to the dataset
        self.dataset.send_data_to_datasetore(data)
        # Return an ok signal
        return {'status': 'ok'}

    def update_test_with_raw_data(self, test_id, raw_data):
        # Get the current test
        test = self.get_current_test_data_results()
        # If the ids don't match then quit with an error
        if not test or test_id != ('%s' % test.id):
            return {
                'status': 'error',
                'errors': ['No test could be found for the provided test id %s' % test_id]}
        # If the test is not running
        if not test.status == 'running':
            return {
                'status': 'error',
                'errors': [
                    'The test you are trying to add data (with test id: %s) is not currently '
                    'running, please stop sending data to this test.' % test_id]}
        # Call the channel to update the test
        passed = self._underlying_channel().update_test_with_results(self, self.channel, test_id, raw_data)
        if passed:
            return {'status': 'ok'}
        else:
            # re get the test data
            test = self.sourcetestresult_set.get(id=test_id)
            # Return an api error and any errors from the test
            return {'status': 'error', 'errors': test.status_messages['errors']}

    def get_current_test_data_results(self):
        try:
            # Get the current active test
            current_test_results = self.sourcetestresult_set.get(active=True)
            # If the test has passed then mark it as inactive
            if current_test_results.status == 'passed':
                current_test_results.mark_as_inactive()
                # Return it
            return current_test_results
        except SourceTestResult.DoesNotExist:
            # If there are none return none
            return None

    def update_test_data(self, test_result_id, status, status_messages, results=None):
        # Get the current test_results object
        test_results = self.get_current_test_data_results()
        # If none or of the id's don't match just quit
        if not test_results or test_results.id != test_result_id:
            return
            # Call the update method on the test result
        test_results.save(status=status, status_messages=status_messages, results=results)

    def get_all_available_service(self):
        # Get all available services based on the data type of the underlying channel
        services = self._AllAvailableServices(self.channel['data_type'])
        # Extract the configs
        service_configs = [s.configuration for s in services]
        # And return them
        return service_configs

    def aggregate_polling_source(self):
        # If this is not a polling channel then return
        if self.channel['aggregation_type'] != 'polling':
            return
            # Set the status of the source to running
        self.status = 'running'
        # Save this
        self.save(skip_validation=True)
        # Force the parent dataset to pick up the running signal
        self.dataset.save()
        # Get any currently running run records
        run_records = self.sourcerunrecord_set.filter(status='running').all()
        # If there are any ill them and the runs
        [r.kill('Overlapping runs called') for r in run_records]
        # Create a new run record for this this run
        record = SourceRunRecord.Create(self)
        # create the data variable
        data = []
        try:
            # Get a handel on the underlying channel
            channel = self._underlying_channel()
            # Call the channel to return any new data
            data = channel.run_polling_aggregation(self, self.channel, record)
        except Exception, e:
            record.update(
                'error',
                {'errors': [
                    'There was a system error in this run',
                    format_error(e, sys.exc_info())], 'infos': []})
        finally:
            if record.status == 'running':
                record.update('error', {'errors': ['This run did not finish correctly'], 'infos': []})

        # TODO: call the services for augmentation

        # Set the status back to active
        self.status = 'active'
        # Save yourself
        self.save()
        # Force the parent dataset to pick up the active signal
        self.dataset.save()
        # Return the results to the dataset
        return data

    def get_post_adapter_instructions(self):
        # Get the underlying channel
        channel = self._underlying_channel()
        # Return the instruction
        return channel.return_post_configuration_js()

    def kill(self):
        # If this is not running then just quit
        if self.status != 'running':
            return
        # Kill any run records
        [r.kill('User initiated kill') for r in self.sourcerunrecord_set.filter(status='running').all()]
        # Set the status to active
        self.status = 'active'
        # save
        self.save(skip_validation=True)

    def _underlying_channel(self):
        channel_type = self.channel['type']
        return Source._GetChannelByType(channel_type)


class SourceTestResult(models.Model):
    source = models.ForeignKey(Source)  # The parent source
    created = models.DateTimeField()  # When it was started
    modified = models.DateTimeField()  # When it was last checked or updated
    active = models.BooleanField(default=True)  # If this is the active test
    status = models.TextField()  # Used to store the current state of the test run
    _status_messages = models.TextField(default='{}')  # Used to store a JSON version of the status messages
    _results = models.TextField(default='[]')  # Used to store the JSON version of the actual results

    @classmethod
    def Create(cls, source):
        # Create a new Test Result object with defaults
        test_result = SourceTestResult(
            source=source,
            created=now(),
            active=True,
            status='running')
        # Set the status messages
        test_result.status_messages = {'errors': [], 'infos': []}
        # Save the test results
        test_result.save()
        # Return the test result object
        return test_result

    @classmethod
    def DefaultTestErrorReturn(cls):
        return {
            'status': 'error',
            'status_messages': {
                'errors': ['There was a system error with this test. Please try again.'],
                'infos': []}}

    @property
    def status_messages(self):
        return json.loads(self._status_messages)

    @status_messages.setter
    def status_messages(self, value):
        self._status_messages = json.dumps(value)

    @property
    def results(self):
        return json.loads(self._results)

    @results.setter
    def results(self, value):
        results_array = [v.to_dict() for v in value] if value else []
        self._results = json.dumps(results_array)

    def mark_as_inactive(self):
        self.active = False
        self.save()

    def to_json(self):
        return json.dumps({
            'id': self.id, # The object ID
            'status': self.status, # The current state of the test
            'status_messages': self.status_messages, # Any messages for the UI
            'results': self.results})  # Any results of the test

    def save(self, *args, **kwargs):
        # Update the status if provided
        if 'status' in kwargs:
            self.status = kwargs.pop('status')
            # Update the status messages if update
        if 'status_messages' in kwargs:
            self.status_messages = kwargs.pop('status_messages')
            # Update the results if provided
        if 'results' in kwargs:
            results = kwargs.pop('results')
            if results and isinstance(results, list):
                aggregated_results = [ContentItem.FromDict(r) for r in self.results] + results
                self.results = aggregated_results
        # Set the last modified time to now
        self.modified = now()
        # Save the object
        super(SourceTestResult, self).save(*args, **kwargs)


class SourceRunRecord(models.Model):
    source = models.ForeignKey(Source)  # The parent source
    created = models.DateTimeField()  # when the run started
    modified = models.DateTimeField()  # when it was last modified
    status = models.TextField()  # the current state of the run
    _status_messages = models.TextField()  # JSON any status messages
    _statistics = models.TextField()  # JSON the run statistics

    @classmethod
    def Create(cls, source):
        record = SourceRunRecord(
            source=source,
            created=now(),
            modified=now(),
            status='running')
        record.status_messages = {'errors': [], 'infos': []}
        record.record_statistics(prevent_save=True)  # Set up the default statistics
        record.save()
        return record

    @property
    def status_messages(self):
        return json.loads(self._status_messages)

    @status_messages.setter
    def status_messages(self, value):
        self._status_messages = json.dumps(value)

    @property
    def statistics(self):
        return json.loads(self._statistics)

    def record_statistics(self, prevent_save=False, total_item=None, oldest_datetime=None, youngest_datetime=None):
        # Build the default object
        now_datetime = now()
        stats = {
            'started': self.created.strftime('%c'),
            'finished': now_datetime.strftime('%c'),
            'duration_in_seconds': (self.created - now_datetime).seconds,
            'total_items': 0,
            'ipm': 0}  # items per minute
        # If nothing is passed in then just add the default
        if not total_item:
            self._statistics = json.dumps(stats)
        else:
            # Record the total items
            stats['total_items'] = total_item
            # Check if date-times are provided
            if oldest_datetime and isinstance(oldest_datetime, datetime.datetime) and \
                    youngest_datetime and isinstance(youngest_datetime, datetime.datetime):
                # Calculate the imp
                total_time_difference = (oldest_datetime - youngest_datetime).seconds or 1
                seconds_per_item = float(total_time_difference) / total_item
                items_per_minute = 60.0 / seconds_per_item
                stats['ipm'] = items_per_minute
            self._statistics = json.dumps(stats)
        #If we are to save then do so
        if not prevent_save:
            self.save()

    def update(self, status, status_messages):
        self.status = status
        self.status_messages = status_messages
        self.modified = now()
        self.save()

    def kill(self, reason):
        self.status = 'killed'
        self.modified = now()
        self.status_messages['errors'].append(
            'Kill signal issues on %s for %s' % (self.modified.strftime('%c'), reason))
        self.save()
