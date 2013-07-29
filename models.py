import datetime
import inspect
import json
import re
import sys
import uuid
from django.conf import settings

from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.utils.timezone import now

import channels
from django_odc.objects import ContentItem
from django_odc.settingsbridge import access_settings
from django_odc.utils import async, format_error, dynamic_import
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
    def GetForUser(cls, user, include_deleted=False, include_user_group_linked=False, count=None):
        datasets = [d for d in Dataset.objects.filter(user=user)]
        if include_user_group_linked:
            for user_group in UserGroup.GetForUser(user):
                for dataset in user_group.get_datasets():
                    if dataset not in datasets:
                        datasets.append(dataset)
        if not include_deleted:
            datasets = [d for d in datasets if d.status != 'deleted']
        datasets = sorted(datasets, key=lambda d: d.created, reverse=True)
        if count:
            datasets = datasets[:count]
        return datasets

    @classmethod
    def GetAllForInstance(cls, include_deleted=False):
        if not include_deleted:
            datasets = [d for d in Dataset.objects.exclude(status='deleted')]
        else:
            datasets = [d for d in Dataset.objects.all()]
        datasets = sorted(datasets, key=lambda d: d.created, reverse=True)
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
            'id': self.id,  # The id of the dataset
            'display_name': self.display_name,  # The dataset display name
            'status': self.status,  # The status
            'status_messages': self.status_messages,  # Get the un serialized status messages
            'created': self.created.strftime('%c'),  # Format time as local
            'modified': self.modified.strftime('%c  '),  # Format time as local
            'sources': self.sources_configuration()}  # All the dataset sources

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
        # If there are non then just break out
        if not sources:
            return
        # Filter out ones that are not polling
        sources = [s for s in sources if s.channel['aggregation_type'] == 'polling']
        # If there are non then just break out
        if not sources:
            return
        # Call the polling aggregate function on each of the sources
        for source in sources:
            self.send_data_to_datasetore(source, source.aggregate_polling_source())

    def send_data_to_datasetore(self, source, data):
        # Get the current data context
        data_context = self._get_data_context()
        # Call the push data function on the data context
        data_context.push(source, data)

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

    def get_statistics(self, format_for_display=False):
        # Format Mappings
        mappings = {
            'total_items': {
                'display_name': 'Total items',
                'abbr': 'Items'},
            'aggregate_items_per_minute': {
                'display_name': 'New Items Collected Per Minute',
                'abbr': 'IPM'},
            'aggregate_items_per_day': {
                'display_name': 'New Items Collected Per Day',
                'abbr': 'IPD'}}
        # Get the current data context
        data_context = self._get_data_context()
        # Get the raw statistics from the data context
        statistics = data_context.dataset_statistics(self)
        # if not format them then Return them
        if not format_for_display:
            return statistics
        # Build the formatted list
        formatted_stats = []
        # Add the stats to the formatted list
        for key, value in statistics.items():
            formatted_stat = mappings.get(key, {'display_name': key, 'abbr': key})
            formatted_stat['value'] = value
            formatted_stats.append(formatted_stat)
        # Return the formatted array
        return formatted_stats

    def run_query(self, search_data):
        # Get the data context
        data_context = self._get_data_context()
        # Call run query
        results = data_context.run_query(search_data)
        # TODO: May add formatting and extensions here
        # Return the results
        return results

    def user_groups(self):
        return UserGroup.GetForDataset(self, create_if_missing=False)

    def user_is_in_user_groups(self, user):
        for ug in self.user_groups():
            if user in ug.get_users():
                return True
        return False

    def _get_data_context(self):
        # Get the dynamic data context init config
        config = access_settings('ODC_DATACONTEXT_INIT_CONFIG')
        # Get the dynamically configured data context
        data_context_type = access_settings('ODC_DATACONTEXT_TYPE')
        # Loop through all the installed apps looking for services
        for app in settings.INSTALLED_APPS:
            try:
                module = dynamic_import(app + ".datacontext")
                data_context = getattr(module, data_context_type)(config)
                break
            except Exception:
                pass
        return data_context


class UserGroup(models.Model):
    _datasets = models.ManyToManyField(Dataset)
    _users = models.ManyToManyField(User)
    created = models.DateTimeField()
    _name = models.TextField(default='')

    @classmethod
    def Create(cls, dataset):
        #Check if there is an unnamed group for this dataset already
        try:
            return UserGroup.objects.get(_datasets__id=dataset.id, _name='')
        except UserGroup.DoesNotExist:
            pass
        #If not then create one
        user_group = UserGroup(created=now())
        user_group.save()
        user_group._datasets.add(dataset)
        user_group.save()
        return user_group

    @classmethod
    def GetForDataset(cls, dataset, create_if_missing=True):
        user_groups = UserGroup.objects.filter(_datasets__id=dataset.id).all()
        if user_groups or not create_if_missing:
            return user_groups
        return [cls.Create(dataset)]

    @classmethod
    def GetForUser(cls, user):
        return UserGroup.objects.filter(_users__id=user.id).all()

    @property
    def name(self):
        # If there is a name then return it
        if self._name:
            return self._name
        # Else build one from the dataset
        return 'Users assigned to dataset %s' % [d for d in self._datasets.all()][0].display_name

    def add_user(self, user):
        if user not in self._users.all():
            self._users.add(user)
            self.save()

    def remove_user(self, user):
        if user in self._users.all():
            self._users.remove(user)
            self.save()

    def get_users(self):
        return [u for u in self._users.all()]

    def add_dataset(self, dataset, name=None):
        # TODO this should enforce that all user groups with more that one datasets have a name
        raise NotImplementedError

    def remove_dataset(self, dataset):
        # TODO this should reset the name to '' if there is only one dataset left in the set
        raise NotImplementedError

    def get_datasets(self):
        return [d for d in self._datasets.all()]

    def is_unnamed(self):
        return self._name == ''


class Source(models.Model):
    _channel = models.TextField(default='{}')  # The configuration of the underlying channel
    _status_messages = models.TextField(default='')  # Any status messages for the source
    _services = models.TextField(default='[]')  # The json serialized services collection
    display_name = models.TextField(default='')  # A user friendly name provided by the user
    guid = models.TextField(default='')  # An editable id that allows after the fact data context connection
    user = models.ForeignKey(User)  # Relationship to a single user
    datasets = models.ManyToManyField(Dataset)  # Relationship to many datasets
    status = models.TextField(default='unconfigured')  # The status of the data point
    created = models.DateTimeField()  # When it was Created
    modified = models.DateTimeField()  # When it was modified

    is_channel_regex = re.compile(r'^[A-Z]\w+Channel$')  # Regex for extracting only channels from the channels module
    is_service_regex = re.compile(r'^[A-Z]\w+Service$')  # Regex for extracting only services from the services module

    @classmethod
    def Create(cls, user, dataset, channel_type):
        # Create a new source with some defaults
        source = Source(
            user=user,  # Add the parent user
            created=datetime.datetime.now(),  # Created now
            guid='%s' % uuid.uuid4())
        # Add the channel
        source.channel = Source._GetChannelByType(channel_type).configuration
        # Add the status messages template
        source.status_messages = {'errors': [], 'infos': []}
        # Call save override
        source.save()
        # Associate with the dataset
        source.datasets.add(dataset)
        # Call save again skipping any validation
        source.save(skip_validation=True)
        # Return new source
        return source

    @classmethod
    def GetById(cls, source_id):
        try:
            return Source.objects.get(id=source_id)
        except Source.DoesNotExist:
            return None

    @classmethod
    def GetForUser(cls, user):
        return Source.objects.filter(user=user).exclude(status='deleted').all()

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
        # Sort them by the config to show advanced ones at the end
        all_channels = sorted(all_channels, key=lambda s: s.configuration['display_name_short'].startswith('[Advance'))
        return all_channels

    @classmethod
    def _AllAvailableServices(cls, channel_data_type):
        # Build the master list of all possible services
        all_classes = []
        # Loop through all the installed apps looking for services
        for app in settings.INSTALLED_APPS:
            try:
                dynamic_import(app + ".services")
                for c in inspect.getmembers(sys.modules[app + ".services"], inspect.isclass):
                    if not [_c for _c in all_classes if _c[0] == c[0]]:
                        all_classes.append(c)
            except Exception:
                pass
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
                # Check that the display name is unique
            is_unique = len(
                Source.objects.filter(display_name=self.display_name).all()) < 2
            if self.display_name and not is_unique:
                # And f not then add an error saying so
                status_messages['errors'].append('You already have a source with that name in this dataset.')
            # Extract out the channel configuration so it can be amended by the channel validation method
            channel_configuration = self.channel
            # Call the channel to validate the config
            status_messages['errors'] += self._underlying_channel().ValidateAndReturnErrors(channel_configuration)
            # Save back any updated configuration
            self.channel = channel_configuration
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
            # Update the GUID
            self.guid = updated_data.get('guid', self.guid)
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

    def to_dict(self):
        return {
            'id': self.id,
            'guid': self.guid,
            'display_name': self.display_name,
            'services': self.services,
            'status': self.status,
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
        # Call the services for augmentation
        data = self._apply_services_to_data(data, record)
        # Send this data to the dataset
        for dataset in self.datasets.all():
            dataset.send_data_to_datasetore(self, data)
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
        # Force all parent datasets to pick up the running signal
        [d.save() for d in self.datasets.all()]
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
            # Extract out the configuration so it can be saved back with any changes from the run
            channel_configuration = self.channel
            # Call the channel to return any new data
            data = channel.run_polling_aggregation(self, channel_configuration, record)
            # Save back the configuration
            self.channel = channel_configuration
        except Exception, e:
            record.update(
                'error',
                {'errors': [
                    'There was a system error in this run',
                    format_error(e, sys.exc_info())], 'infos': []})
        finally:
            if record.status == 'running':
                record.update('error', {'errors': ['This run did not finish correctly'], 'infos': []})
        # Call the services for augmentation
        data = self._apply_services_to_data(data, record)
        # Set the status back to active
        self.status = 'active'
        # Save yourself
        self.save()
        # Force all parent datasets to pick up the active signal
        [d.save() for d in self.datasets.all()]
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

    def empty(self, reset_since_time=True):
        for dataset in self.datasets.all():
            data_context = dataset._get_data_context()
            data_context.source_empty(self)
            if not reset_since_time:
                continue
            channel = self.channel
            channel.pop('since_time', None)
            self.channel = channel
            self.save(skip_validation=True)

    def _underlying_channel(self):
        channel_type = self.channel['type']
        return Source._GetChannelByType(channel_type)

    def _get_service_by_service_type(self, service_type):
        # Get all the services
        all_services = self._AllAvailableServices(self.channel['data_type'])
        # Extract the service that matches the service type
        candidate_services = [s for s in all_services if s.configuration['type'] == service_type]
        service = candidate_services[0] if candidate_services else None
        # Return the service
        return service

    def _apply_services_to_data(self, data, run_record):
        for service in self.services:
            service_object = self._get_service_by_service_type(service['type'])
            if service_object:
                try:
                    data = service_object.run(service, data)
                except Exception, e:
                    run_record.update(
                        'error',
                        {'errors': [
                            'There was a system error in this run',
                            format_error(e, sys.exc_info())], 'infos': []})
        return data


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
        for error in status_messages.get('errors', []):
            self.status_messages['errors'].append(error)
        for info in status_messages.get('infos', []):
            self.status_messages['infos'].append(info)
        self.modified = now()
        self.save()

    def kill(self, reason):
        self.status = 'killed'
        self.modified = now()
        self.status_messages['errors'].append(
            'Kill signal issues on %s for %s' % (self.modified.strftime('%c'), reason))
        self.save()


class AuthenticationStorage(models.Model):
    type = models.TextField()
    _config = models.TextField(default='{}')

    @classmethod
    def GetByType(cls, type):
        try:
            return AuthenticationStorage.objects.get(type=type)
        except AuthenticationStorage.DoesNotExist:
            return None
        except MultipleObjectsReturned:
            [a.delete() for a in AuthenticationStorage.objects.all()]
            return None

    @classmethod
    def CreateWithTypeAndConfig(cls, type, config):
        storage = cls.GetByType(type)
        if not storage:
            storage = AuthenticationStorage(type=type)
            storage.config = config
            storage.save()
        return storage

    @property
    def config(self):
        return json.loads(self._config)

    @config.setter
    def config(self, value):
        self._config = json.dumps(value or {})
