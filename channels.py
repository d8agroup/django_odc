import datetime
import json
import re
import time
import sys
from random import randint
from copy import deepcopy
from hashlib import md5

import feedparser
import facepy
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django_odc.objects import ContentItemAuthor, ContentItem
from django_odc.utils import format_error

access_token = 'CAAESCkX9loYBAL0cxgiDUAADSYniLG2bTPxdnPPgdEhJkpmvcNZCW9L8v2h9SgwcxeB8ruxpbXzaTPCCBy9YZBpGZA76XXvJZCkZA6PwsxwmDakb9Iy2zaEoJyuZBBkOmF9AYZCZC9ZAeVw38GuUL6RlcfZAZCcDu3DGKEhMeBZA8n7ZCCzvZAZBcTIORxZB66J6UURG4lEZD'


class _BaseChannel(object):

    @classmethod
    def ValidateAndReturnErrors(cls, configuration):
        """This is designed to be overwritten by subclasses if there is configuration to validate

        Optionally, the channel can also make changes to the configuration - such as setting variables
        based on configuration values that will then be persisted along with the calling channel
        """
        return []

    @property
    def configuration(self):
        return deepcopy(self._configuration)

    def run_test(self, source, configuration, test_result_id):
        # This is designed to be overwritten by subclasses
        pass

    def run_polling_aggregation(self, source, configuration, run_record_id):
        # This is designed to be overwritten by subclasses that have an aggregation type of 'polling'
        pass

    def return_post_configuration_js(self):
        # This is designed to be overwritten by subclasses that have an aggregation type of 'polling'
        post_adapter_configuration_js_name = self._configuration['type'] + ".js"
        return render_to_string('django_odc/post_adapter_configuration_js/%s' % post_adapter_configuration_js_name)

    def update_test_with_results(self, source, configuration, test_result_id, raw_data):
        """This is designed to be overwritten by subclasses

        This method must return a boolean indicating if the results were parsed and added to the test results
        without error.
        """
        return True

    def receive_post_data(self, source, configuration, run_record, raw_data):
        """This is designed to be overwritten by subclasses that have aggregation_type=post_adapter

        This method must return an array of objects based on the data type of the channel
        """
        return []


class TwitterStreamPostChannel(_BaseChannel):
    _base_image_url = 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks'
    _configuration = {
        'type': 'twitter_post_v01',
        'data_type': 'content_v01',
        'aggregation_type': 'post_adapter',
        'images': {
            '16': _base_image_url + '/16/social_twitter_box_blue.png',
            '24': _base_image_url + '/24/social_twitter_box_blue.png',
            '32': _base_image_url + '/32/social_twitter_box_blue.png',
            '48': _base_image_url + '/48/social_twitter_box_blue.png',
            '64': _base_image_url + '/64/social_twitter_box_blue.png',
            '128': _base_image_url + '/128/social_twitter_box_blue.png'
        },
        'display_name_short': '[Advanced] Tweet Stream',
        'display_name_full': '[Advanced] Twitter Streaming Adapter',
        'description_short': 'Set up a Streaming POST Adapter for tweets from Twitter',
        'description_full': 'Use this source to create a POST adapter that you can use to push a stream of tweets to.',
        'config': {
            'elements': [
                {
                    'name': 'limit',
                    'display_name': 'Total Limit',
                    'type': 'select',
                    'help_message': 'Please choose the total number of content items that can be held for this '
                                    'data source. Once this limit is reached, old items will drop off the bottom to '
                                    'make way for new items.',
                    'values': ['1000', '10000', '100000', '1000000'],
                    'value': '10000',
                }
            ]
        }
    }

    def _parse_incoming_tweet(self, raw_tweet, source):
        author = ContentItemAuthor()
        author.display_name = raw_tweet['user']['screen_name']
        author.id = raw_tweet['user']['id_str']
        author.profile_image_url = raw_tweet['user']['profile_image_url']
        content = ContentItem()
        content.author = author
        content.id = md5(raw_tweet['id_str']).hexdigest()
        content.source = source.to_dict()
        content.title = raw_tweet['text']
        content.link = 'https://twitter.com/#!/%s/status/%s' % (author.display_name, raw_tweet['id_str'])
        content.language = raw_tweet['lang']
        content.created = datetime.datetime.strptime(raw_tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        content.add_popularity_metadata(raw_tweet['favorite_count'] + raw_tweet['retweet_count'])
        return content

    def update_test_with_results(self, source, configuration, test_result_id, raw_data):
        test = source.sourcetestresult_set.get(id=test_result_id)
        try:
            tweets = json.loads(raw_data)
        except Exception, e:
            error = format_error(e, sys.exc_info())
            test.save(status='error', status_messages={'errors': ['The json was malformed', error], 'infos': []})
            return False
        if not tweets or not isinstance(tweets, list):
            test.save(status='error', status_messages={'errors': ['The tweets array was empty'], 'infos': []})
            return False
        parsed_data = []
        for tweet in tweets:
            try:
                parsed_data.append(self._parse_incoming_tweet(tweet, source))
            except Exception, e:
                error = format_error(e, sys.exc_info())
                test.save(
                    status='error',
                    status_messages={
                        'errors': ['At least one of the tweets could not be parsed', error], 'infos': []})
                return False
        test.save(results=parsed_data)
        # If the limit has been reached
        limit = 2
        number_or_results = len(test.results)
        if number_or_results >= limit:
            # Set the test to passed with a nice info message
            test.save(
                status='passed',
                status_messages={
                    'errors': [],
                    'infos': ['This test passed as %i tweets were parsed without error.' % number_or_results]})
        return True

    def run_test(self, source, configuration, test_result_id):
        # If there is no content after seconds
        seconds = 60
        time.sleep(seconds)
        # Check if the test is not working and quit with an error if this is the case
        current_test = source.get_current_test_data_results()
        if current_test.status == 'running' and not current_test.results:
            source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['This test ran for %i seconds without receiving and content' % seconds], 'infos': []})

    def receive_post_data(self, source, configuration, run_record, raw_data):
        try:
            tweets = json.loads(raw_data)
        except Exception, e:
            error = format_error(e, sys.exc_info())
            run_record.update('error', {'errors': ['The json was malformed', error], 'infos': []})
            return []
        if not tweets or not isinstance(tweets, list):
            run_record.update('error', {'errors': ['The tweets array was empty'], 'infos': []})
            return []
        parsed_data = []
        for tweet in tweets:
            try:
                parsed_data.append(self._parse_incoming_tweet(tweet, source))
            except Exception, e:
                error = format_error(e, sys.exc_info())
                run_record.update(
                    'error',
                    {'errors': ['At least one of the tweets could not be parsed', error], 'infos': []})
                return []
        # calculate oldest and youngest
        oldest = None
        youngest = None
        for r in parsed_data:
            if r.created:
                if not oldest or r.created < oldest:
                    oldest = r.created
                if not youngest or r.created > youngest:
                    youngest = r.created
        # Update the stats on the run record
        run_record.record_statistics(total_item=len(parsed_data), oldest_datetime=oldest, youngest_datetime=youngest)
        run_record.update('finished', {'errors': [], 'infos': ['%i items collected' % len(parsed_data)]})
        return parsed_data


class FacebookStreamPostChannel(_BaseChannel):
    _image_url_base = 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks'
    _configuration = {
        'type': 'facebook_post_v01',
        'data_type': 'content_v01',
        'aggregation_type': 'post_adapter',
        'images': {
            '16': _image_url_base + '/16/social_facebook_box_blue.png',
            '24': _image_url_base + '/24/social_facebook_box_blue.png',
            '32': _image_url_base + '/32/social_facebook_box_blue.png',
            '48': _image_url_base + '/48/social_facebook_box_blue.png',
            '64': _image_url_base + '/64/social_facebook_box_blue.png',
            '128': _image_url_base + '/128/social_facebook_box_blue.png'
        },
        'display_name_short': '[Advanced] Facebook Stream',
        'display_name_full': '[Advanced] Facebook Bulk Upload Adapter',
        'description_short': 'Set up a Streaming POST Adapter for posts from Facebook',
        'description_full': 'Use this source to create a POST adapter that you can use to push a stream of facebook'
                            ' posts to.',
        'config': {
            'elements': [
                {
                    'name': 'limit',
                    'display_name': 'Total Limit',
                    'type': 'select',
                    'help_message': 'Please choose the total number of content items that can be held for this '
                                    'data source. Once this limit is reached, old items will drop off the bottom to '
                                    'make way for new items.',
                    'values': ['1000', '10000', '100000', '1000000'],
                    'value': '10000',
                }
            ]
        }
    }

    def _parse_incoming_post(self, raw_post, source):
        author = ContentItemAuthor()
        author.display_name = raw_post['user_name']
        author.id = raw_post['user_id']
        content = ContentItem()
        content.author = author
        content.id = md5(raw_post['id']).hexdigest()
        content.source = source.to_dict()
        content.title = raw_post['message']
        content.link = raw_post['link']
        content.created = datetime.datetime.strptime(raw_post['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
        return content

    def update_test_with_results(self, source, configuration, test_result_id, raw_data):
        test = source.sourcetestresult_set.get(id=test_result_id)
        try:
            posts = json.loads(raw_data)
        except Exception, e:
            error = format_error(e, sys.exc_info())
            test.save(status='error', status_messages={'errors': ['The json was malformed', error], 'infos': []})
            return False
        if not posts or not isinstance(posts, list):
            test.save(status='error', status_messages={'errors': ['The posts array was empty'], 'infos': []})
            return False
        parsed_data = []
        for post in posts:
            try:
                parsed_data.append(self._parse_incoming_post(post, source))
            except Exception, e:
                error = format_error(e, sys.exc_info())
                test.save(
                    status='error',
                    status_messages={
                        'errors': ['At least one of the posts could not be parsed', error], 'infos': []})
                return False
        test.save(results=parsed_data)
        # If the limit has been reached
        limit = 2
        number_or_results = len(test.results)
        if number_or_results >= limit:
            # Set the test to passed with a nice info message
            test.save(
                status='passed',
                status_messages={
                    'errors': [],
                    'infos': ['This test passed as %i posts were parsed without error.' % number_or_results]})
        return True

    def run_test(self, source, configuration, test_result_id):
        # If there is no content after seconds
        seconds = 60
        time.sleep(seconds)
        # Check if the test is not working and quit with an error if this is the case
        current_test = source.get_current_test_data_results()
        if current_test.status == 'running' and not current_test.results:
            source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['This test ran for %i seconds without receiving and content' % seconds], 'infos': []})

    def receive_post_data(self, source, configuration, run_record, raw_data):
        try:
            posts = json.loads(raw_data)
        except Exception, e:
            error = format_error(e, sys.exc_info())
            run_record.update('error', {'errors': ['The json was malformed', error], 'infos': []})
            return []
        if not posts or not isinstance(posts, list):
            run_record.update('error', {'errors': ['The posts array was empty'], 'infos': []})
            return []
        parsed_data = []
        for post in posts:
            try:
                parsed_data.append(self._parse_incoming_post(post, source))
            except Exception, e:
                error = format_error(e, sys.exc_info())
                run_record.update(
                    'error',
                    {'errors': ['At least one of the posts could not be parsed', error], 'infos': []})
                return []
        # calculate oldest and youngest
        oldest = None
        youngest = None
        for r in parsed_data:
            if r.created:
                if not oldest or r.created < oldest:
                    oldest = r.created
                if not youngest or r.created > youngest:
                    youngest = r.created
        # Update the stats on the run record
        run_record.record_statistics(total_item=len(parsed_data), oldest_datetime=oldest, youngest_datetime=youngest)
        run_record.update('finished', {'errors': [], 'infos': ['%i items collected' % len(parsed_data)]})
        return parsed_data


class FeedChannel(_BaseChannel):
    _configuration = {
        'type': 'feed_v01',
        'data_type': 'content_v01',
        'aggregation_type': 'polling',
        'images': {
            '16': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/16/social_rss_box_orange.png',
            '24': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/24/social_rss_box_orange.png',
            '32': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/32/social_rss_box_orange.png',
            '48': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/48/social_rss_box_orange.png',
            '64': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/64/social_rss_box_orange.png',
            '128': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/128/social_rss_box_orange.png'
        },
        'display_name_short': 'Feeds',
        'display_name_full': 'Web Feeds (RSS/ATOM)',
        'description_short': 'Collect content from blogs and news sites.',
        'description_full': 'Use this source to connect to blogs and news sites that publish content via RSS '
                            'or ATOM',
        'config': {
            'elements': [
                {
                    'name': 'feed_url',
                    'display_name': 'The address of the feed',
                    'type': 'text',
                    'help_message': 'This must be the url of the actual feed (the rss or atom items).',
                    'value': ''
                },
                {
                    'name': 'limit',
                    'display_name': 'Total Limit',
                    'type': 'select',
                    'help_message': 'Please choose the total number of content items that can be held for this '
                                    'data source. Once this limit is reached, old items will drop off the bottom to '
                                    'make way for new items.',
                    'values': ['1000', '10000', '100000', '1000000'],
                    'value': '10000',
                }
            ]
        }
    }

    @classmethod
    def ValidateAndReturnErrors(cls, configuration):
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the feed url for checking
        feed_url = [e for e in elements if e['name'] == 'feed_url'][0]['value']
        # If there is no feed url
        if not feed_url:
            # Return an error saying so
            return ['You must enter an address for this source.']
        try:
            # Use django to validate the url for format
            url_validator = URLValidator()
            url_validator(feed_url)
        except ValidationError:
            # Return a error is format does not pass
            return ['The address you entered does not look like a url.']
        try:
            # Use feedparser to check there is a feed at the end of the url
            feed = feedparser.parse(feed_url)
            # If there is no feed then throw an error
            if not feed['feed'] or not feed['entries']:
                raise Exception()
        except Exception:
            # return an error saying that a feed does not exist at that url
            return ['The address you provided seems to be for a web page, not a feed (have you tried copying '
                    'it from your browsers address bar?). ']
        # No errors = pass
        return []

    def run_test(self, source, configuration, test_result_id):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = FeedChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the test via the source object
            return source.update_test_data(test_result_id, 'error', status_messages)
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the feed url for checking
        feed_url = [e for e in elements if e['name'] == 'feed_url'][0]['value']
        # Begin collecting content from the channel
        try:
            # Create a new feed from the url
            feed = feedparser.parse(feed_url)
        except Exception:
            # If there is a feed level error
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['This source is not correctly configured.'], 'infos': []})
        # Check for bozo errors and store them to return them to the UI if they exists
        bozo_errors = []
        if feed.get('bozo'):
            bozo_errors += ['The feed at this address is not well formatted xml.']
            bozo_errors += ['%s' % feed.get('bozo_exception')]
        # Extract the items from the feed
        items = feed.get('items', None)
        # If there are no items
        if not items:
            # Update the source with the error
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['No items could be collected from this address.'] + bozo_errors, 'infos': []})
        # Set up the results variable
        results = []
        # Count the number of content items with no dates
        number_of_items_with_no_date = 0
        # Loop over the items
        for item in feed.get('items'):
            content = self._parse_feed_item(item, source)
            if not content.created:
                number_of_items_with_no_date += 1
            results.append(content)
        # Work out if there are any info messages to show
        info_messages = bozo_errors
        if number_of_items_with_no_date:
            info_messages += ['Some of the items did not have a published date, this can lead to content duplication.']
        # Update the source with the results and include any bozo errors as info messages
        return source.update_test_data(
            test_result_id,
            'passed',
            {'errors': [], 'infos': info_messages},
            results)
    
    def run_polling_aggregation(self, source, configuration, run_record):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = FeedChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the run record
            run_record.update('error', status_messages)
            return None
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the feed url for checking
        feed_url = [e for e in elements if e['name'] == 'feed_url'][0]['value']
        # Begin collecting content from the channel
        try:
            # Create a new feed from the url
            feed = feedparser.parse(feed_url)
        except Exception:
            # If there is a feed level error update the run record and quit
            run_record.update('error', {'errors': ['This source is not correctly configured.'], 'infos': []})
            return None
        # Check for bozo errors and store them to return them to the UI if they exists
        bozo_errors = []
        if feed.get('bozo'):
            bozo_errors += ['The feed at this address is not well formatted xml.']
            bozo_errors += ['%s' % feed.get('bozo_exception')]
        # Extract the items from the feed
        items = feed.get('items', None)
        # If there are no items
        if not items:
            # update the run and quit
            run_record.update(
                'error',
                {'errors': ['No items could be collected from this address.'] + bozo_errors, 'infos': []})
            return None
        # Set up the results variable
        results = []
        # Loop over the items
        for item in feed.get('items'):
            content = self._parse_feed_item(item, source)
            results.append(content)
        # If there is a since time in the config
        if 'since_time' in configuration:
            try:
                # Parse the since time as a datetime
                since_time = datetime.datetime.fromtimestamp(configuration['since_time'])
                # filter out all duplicates based on time created
                results = [r for r in results if not r.created or r.created > since_time]
            except:
                pass
        # Work out if there are any info messages to show
        info_messages = bozo_errors
        # calculate oldest and youngest
        oldest = None
        youngest = None
        for r in results:
            if r.created:
                if not oldest or r.created < oldest:
                    oldest = r.created
                if not youngest or r.created > youngest:
                    youngest = r.created
        # Update the stats on the run record
        run_record.record_statistics(total_item=len(results), oldest_datetime=oldest, youngest_datetime=youngest)
        # update the run record
        run_record.update('finished', {'errors': [], 'infos': info_messages})
        # Update the configuration with the new since_time
        youngest_is_time = (youngest and isinstance(youngest, datetime.datetime))
        configuration['since_time'] = time.mktime(youngest.timetuple()) if youngest_is_time else time.time()
        # Return the results
        return results

    def _parse_feed_item(self, item, source):
        created = None
        try:
            timestamp = time.mktime(item.get('published_parsed'))
            created = datetime.datetime.fromtimestamp(timestamp)
        except Exception:
            pass
        author = ContentItemAuthor()
        author.display_name = item.get('author', '')
        content = ContentItem()
        content.id = md5(item.get('link', ('%s' % (time.time() + randint(0, 1000))))).hexdigest()
        content.source = source.to_dict()
        content.author = author
        content.title = Truncator(strip_tags(item.get('title', ''))).words(20, truncate=' ...')
        content.link = item.get('link', '')
        content.text = [Truncator(strip_tags(item.get('description', ''))).words(10000, truncate=' ...')]
        content.created = created
        return content


class FeedInToSentenceChannel(_BaseChannel):
    _configuration = {
        'type': 'feedtosentence_v01',
        'data_type': 'content_v01',
        'aggregation_type': 'polling',
        'images': {
            '16': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/16/social_rss_box_orange.png',
            '24': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/24/social_rss_box_orange.png',
            '32': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/32/social_rss_box_orange.png',
            '48': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/48/social_rss_box_orange.png',
            '64': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/64/social_rss_box_orange.png',
            '128': 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks/128/social_rss_box_orange.png'
        },
        'display_name_short': 'Feed Sentences',
        'display_name_full': 'Web Feeds Sentences (RSS/ATOM)',
        'description_short': 'Sentences content from blogs and news sites.',
        'description_full': 'Use this source to connect to blogs and news sites that publish content via RSS '
                            'or ATOM and break the content down by sentence',
        'config': {
            'elements': [
                {
                    'name': 'feed_url',
                    'display_name': 'The address of the feed',
                    'type': 'text',
                    'help_message': 'This must be the url of the actual feed (the rss or atom items).',
                    'value': ''
                },
                {
                    'name': 'limit',
                    'display_name': 'Total Limit',
                    'type': 'select',
                    'help_message': 'Please choose the total number of content items that can be held for this '
                                    'data source. Once this limit is reached, old items will drop off the bottom to '
                                    'make way for new items.',
                    'values': ['1000', '10000', '100000', '1000000'],
                    'value': '10000',
                }
            ]
        }
    }

    @classmethod
    def ValidateAndReturnErrors(cls, configuration):
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the feed url for checking
        feed_url = [e for e in elements if e['name'] == 'feed_url'][0]['value']
        # If there is no feed url
        if not feed_url:
            # Return an error saying so
            return ['You must enter an address for this source.']
        try:
            # Use django to validate the url for format
            url_validator = URLValidator()
            url_validator(feed_url)
        except ValidationError:
            # Return a error is format does not pass
            return ['The address you entered does not look like a url.']
        try:
            # Use feedparser to check there is a feed at the end of the url
            feed = feedparser.parse(feed_url)
            # If there is no feed then throw an error
            if not feed['feed'] or not feed['entries']:
                raise Exception()
        except Exception:
            # return an error saying that a feed does not exist at that url
            return ['The address you provided seems to be for a web page, not a feed (have you tried copying '
                    'it from your browsers address bar?). ']
        # No errors = pass
        return []

    def run_test(self, source, configuration, test_result_id):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = FeedChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the test via the source object
            return source.update_test_data(test_result_id, 'error', status_messages)
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the feed url for checking
        feed_url = [e for e in elements if e['name'] == 'feed_url'][0]['value']
        # Begin collecting content from the channel
        try:
            # Create a new feed from the url
            feed = feedparser.parse(feed_url)
        except Exception:
            # If there is a feed level error
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['This source is not correctly configured.'], 'infos': []})
        # Check for bozo errors and store them to return them to the UI if they exists
        bozo_errors = []
        if feed.get('bozo'):
            bozo_errors += ['The feed at this address is not well formatted xml.']
            bozo_errors += ['%s' % feed.get('bozo_exception')]
        # Extract the items from the feed
        items = feed.get('items', None)
        # If there are no items
        if not items:
            # Update the source with the error
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['No items could be collected from this address.'] + bozo_errors, 'infos': []})
        # Set up the results variable
        results = []
        # Count the number of content items with no dates
        number_of_items_with_no_date = 0
        # Loop over the items
        for item in feed.get('items'):
            for content in self._parse_feed_item(item, source):
                if not content.created:
                    number_of_items_with_no_date += 1
                results.append(content)
        # Work out if there are any info messages to show
        info_messages = bozo_errors
        if number_of_items_with_no_date:
            info_messages += ['Some of the items did not have a published date, this can lead to content duplication.']
        # Update the source with the results and include any bozo errors as info messages
        return source.update_test_data(
            test_result_id,
            'passed',
            {'errors': [], 'infos': info_messages},
            results)

    def run_polling_aggregation(self, source, configuration, run_record):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = FeedChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the run record
            run_record.update('error', status_messages)
            return None
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the feed url for checking
        feed_url = [e for e in elements if e['name'] == 'feed_url'][0]['value']
        # Begin collecting content from the channel
        try:
            # Create a new feed from the url
            feed = feedparser.parse(feed_url)
        except Exception:
            # If there is a feed level error update the run record and quit
            run_record.update('error', {'errors': ['This source is not correctly configured.'], 'infos': []})
            return None
        # Check for bozo errors and store them to return them to the UI if they exists
        bozo_errors = []
        if feed.get('bozo'):
            bozo_errors += ['The feed at this address is not well formatted xml.']
            bozo_errors += ['%s' % feed.get('bozo_exception')]
        # Extract the items from the feed
        items = feed.get('items', None)
        # If there are no items
        if not items:
            # update the run and quit
            run_record.update(
                'error',
                {'errors': ['No items could be collected from this address.'] + bozo_errors, 'infos': []})
            return None
        # Set up the results variable
        results = []
        # Loop over the items
        for item in feed.get('items'):
            for content in self._parse_feed_item(item, source):
                results.append(content)
        # If there is a since time in the config
        if 'since_time' in configuration:
            try:
                # Parse the since time as a datetime
                since_time = datetime.datetime.fromtimestamp(configuration['since_time'])
                # filter out all duplicates based on time created
                results = [r for r in results if not r.created or r.created > since_time]
            except:
                pass
        # Work out if there are any info messages to show
        info_messages = bozo_errors
        # calculate oldest and youngest
        oldest = None
        youngest = None
        for r in results:
            if r.created:
                if not oldest or r.created < oldest:
                    oldest = r.created
                if not youngest or r.created > youngest:
                    youngest = r.created
        # Update the stats on the run record
        run_record.record_statistics(total_item=len(results), oldest_datetime=oldest, youngest_datetime=youngest)
        # update the run record
        run_record.update('finished', {'errors': [], 'infos': info_messages})
        # Update the configuration with the new since_time
        youngest_is_time = (youngest and isinstance(youngest, datetime.datetime))
        configuration['since_time'] = time.mktime(youngest.timetuple()) if youngest_is_time else time.time()
        # Return the results
        return results

    def _parse_feed_item(self, item, source):
        created = None
        try:
            timestamp = time.mktime(item.get('published_parsed'))
            created = datetime.datetime.fromtimestamp(timestamp)
        except Exception:
            pass
        author = ContentItemAuthor()
        author.display_name = item.get('author', '')
        text = item.get('title', '') + '. ' + strip_tags(item.get('description', ''))
        sentences = re.split(r' *[\.\?!][\'"\)\]]* *', text)
        content_items = []
        for sentence in sentences:
            if sentence:
                content = ContentItem()
                content.id = md5('%s' % (time.time() + randint(0, 1000))).hexdigest()
                content.source = source.to_dict()
                content.author = author
                content.title = sentence
                content.link = item.get('link', '')
                content.created = created
                content_items.append(content)
        return content_items


class FacebookPublicSearchIntoSentenceChannel(_BaseChannel):
    _image_url_base = 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks'
    _configuration = {
        'type': 'facebook_public_search_into_sentence_v01',
        'data_type': 'content_v01',
        'aggregation_type': 'polling',
        'images': {
            '16': _image_url_base + '/16/social_facebook_box_blue.png',
            '24': _image_url_base + '/24/social_facebook_box_blue.png',
            '32': _image_url_base + '/32/social_facebook_box_blue.png',
            '48': _image_url_base + '/48/social_facebook_box_blue.png',
            '64': _image_url_base + '/64/social_facebook_box_blue.png',
            '128': _image_url_base + '/128/social_facebook_box_blue.png'
        },
        'display_name_short': 'Facebook In Sentences',
        'display_name_full': 'Public Facebook Posts Into Sentences',
        'description_short': 'Collect public posts from Facebook in Sentences.',
        'description_full': 'Use this source to search the public posts stream of Facebook',
        'config': {
            'elements': [
                {
                    'name': 'search',
                    'display_name': 'Search Term(s)',
                    'type': 'text',
                    'help_message': 'Only numbers and characters separated by spaces (Note that all terms use '
                                    'a logical AND).',
                    'value': ''
                },
                {
                    'name': 'limit',
                    'display_name': 'Total Limit',
                    'type': 'select',
                    'help_message': 'Please choose the total number of content items that can be held for this '
                                    'data source. Once this limit is reached, old items will drop off the bottom to '
                                    'make way for new items.',
                    'values': ['1000', '10000', '100000', '1000000'],
                    'value': '10000',
                }
            ]
        }
    }

    @classmethod
    def ValidateAndReturnErrors(cls, configuration):
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the search terms for checking
        search_terms = [e for e in elements if e['name'] == 'search'][0]['value']
        # If there are no search terms or they are not valid
        if not search_terms or [c for c in search_terms if not c.isalnum() and c != ' ']:
            # Return an error saying so
            return ['The search term(s) you entered are not valid.']
        # No errors = pass
        return []

    def run_test(self, source, configuration, test_result_id):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = FacebookPublicSearchChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the test via the source object
            return source.update_test_data(test_result_id, 'error', status_messages)
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the search terms
        search_terms = [e for e in elements if e['name'] == 'search'][0]['value']
        # Get the fb items
        try:
            fb = facepy.GraphAPI(access_token)
            results = fb.search(term=search_terms, type='post', limit=5)
        except Exception, e:
            # Format the error
            error = format_error(e, sys.exc_info())
            # If there is an error even getting the results
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['There was an error getting data from facebook.', error], 'infos': []})
        # check that there are results
        if not results or 'data' not in results or not results.get('data', None):
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['There were no results returned from facebook.'], 'infos': []})
        # Array to hold the parsed content
        parsed_results = []
        for r in results.get('data', []):
            try:
                for parsed_item in self._parse_fb_item(r, source):
                    if parsed_item.title:
                        parsed_results.append(parsed_item)
            except Exception, e:
                # Format the error
                error = format_error(e, sys.exc_info())
                # If there is an error even getting the results
                return source.update_test_data(
                    test_result_id,
                    'error',
                    {'errors': ['Not all of the posts could be parsed.', error], 'infos': []})
        # Update the source with the results and include any bozo errors as info messages
        return source.update_test_data(
            test_result_id,
            'passed',
            {'errors': [], 'infos': []},
            parsed_results)

    def run_polling_aggregation(self, source, configuration, run_record):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = FacebookPublicSearchChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the test via the source object
            return run_record.update('error', status_messages)
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the search terms
        search_terms = [e for e in elements if e['name'] == 'search'][0]['value']
        # Get the fb items
        try:
            fb = facepy.GraphAPI(access_token)
            raw_results = fb.search(term=search_terms, type='post', limit=100)
        except Exception, e:
            # Format the error
            error = format_error(e, sys.exc_info())
            # If there is an error even getting the results
            return run_record.update(
                'error',
                {'errors': ['There was an error getting data from facebook.', error], 'infos': []})
        # check that there are results
        if not raw_results or 'data' not in raw_results or not raw_results.get('data', None):
            return run_record.update(
                'error',
                {'errors': ['There were no results returned from facebook.'], 'infos': []})
        # Array to hold the parsed content
        results = []
        for r in raw_results.get('data', []):
            try:
                for parsed_item in self._parse_fb_item(r, source):
                    if parsed_item.title:
                        results.append(parsed_item)
            except Exception, e:
                # Format the error
                error = format_error(e, sys.exc_info())
                # If there is an error even getting the results
                return run_record.update(
                    run_record.status,
                    {'errors': ['Not all of the posts could be parsed.', error], 'infos': []})
        # If there is a since time in the config
        if 'since_time' in configuration:
            try:
                # Parse the since time as a datetime
                since_time = datetime.datetime.fromtimestamp(configuration['since_time'])
                # filter out all duplicates based on time created
                results = [r for r in results if not r.created or r.created > since_time]
            except:
                pass
        # calculate oldest and youngest
        oldest = None
        youngest = None
        for r in results:
            if r.created:
                if not oldest or r.created < oldest:
                    oldest = r.created
                if not youngest or r.created > youngest:
                    youngest = r.created
        # Update the stats on the run record
        run_record.record_statistics(total_item=len(results), oldest_datetime=oldest, youngest_datetime=youngest)
        # update the run record
        run_record.update('finished', {'errors': [], 'infos': []})
        # Update the configuration with the new since_time
        youngest_is_time = (youngest and isinstance(youngest, datetime.datetime))
        configuration['since_time'] = time.mktime(youngest.timetuple()) if youngest_is_time else time.time()
        # Return the results
        return results

    def _parse_fb_item(self, item, source):
        created = None
        item_id = item.get('id', None)
        link_format = 'http://www.facebook.com/%s'
        try:
            timestamp = item.get('created_time')
            created = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S+0000')
        except Exception:
            pass
        author = ContentItemAuthor()
        author.display_name = item.get('from', {}).get('name', None)
        author.id = item.get('from', {}).get('id', None)
        text = item.get('message', '')
        sentences = re.split(r' *[\.\?!][\'"\)\]]* *', text)
        content_items = []
        for sentence in sentences:
            content = ContentItem()
            content.id = md5(item_id or ('%s' % (time.time() + randint(0, 1000)))).hexdigest()
            content.source = source.to_dict()
            content.author = author
            content.title = sentence
            if item_id:
                content.link = link_format % (item_id.split('_')[1])
            content.created = created
            content_items.append(content)
        return content_items


class FacebookPublicSearchChannel(_BaseChannel):
    _image_url_base = 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks'
    _configuration = {
        'type': 'facebook_public_search_v01',
        'data_type': 'content_v01',
        'aggregation_type': 'polling',
        'images': {
            '16': _image_url_base + '/16/social_facebook_box_blue.png',
            '24': _image_url_base + '/24/social_facebook_box_blue.png',
            '32': _image_url_base + '/32/social_facebook_box_blue.png',
            '48': _image_url_base + '/48/social_facebook_box_blue.png',
            '64': _image_url_base + '/64/social_facebook_box_blue.png',
            '128': _image_url_base + '/128/social_facebook_box_blue.png'
        },
        'display_name_short': 'Facebook Posts',
        'display_name_full': 'Public Facebook Posts',
        'description_short': 'Collect public posts from Facebook.',
        'description_full': 'Use this source to search the public posts stream of Facebook',
        'config': {
            'elements': [
                {
                    'name': 'search',
                    'display_name': 'Search Term(s)',
                    'type': 'text',
                    'help_message': 'Only numbers and characters separated by spaces (Note that all terms use '
                                    'a logical AND).',
                    'value': ''
                },
                {
                    'name': 'limit',
                    'display_name': 'Total Limit',
                    'type': 'select',
                    'help_message': 'Please choose the total number of content items that can be held for this '
                                    'data source. Once this limit is reached, old items will drop off the bottom to '
                                    'make way for new items.',
                    'values': ['1000', '10000', '100000', '1000000'],
                    'value': '10000',
                }
            ]
        }
    }

    @classmethod
    def ValidateAndReturnErrors(cls, configuration):
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the search terms for checking
        search_terms = [e for e in elements if e['name'] == 'search'][0]['value']
        # If there are no search terms or they are not valid
        if not search_terms or [c for c in search_terms if not c.isalnum() and c != ' ']:
            # Return an error saying so
            return ['The search term(s) you entered are not valid.']
        # No errors = pass
        return []

    def run_test(self, source, configuration, test_result_id):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = FacebookPublicSearchChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the test via the source object
            return source.update_test_data(test_result_id, 'error', status_messages)
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the search terms
        search_terms = [e for e in elements if e['name'] == 'search'][0]['value']
        # Get the fb items
        try:
            fb = facepy.GraphAPI(access_token)
            results = fb.search(term=search_terms, type='post', limit=5)
        except Exception, e:
            # Format the error
            error = format_error(e, sys.exc_info())
            # If there is an error even getting the results
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['There was an error getting data from facebook.', error], 'infos': []})
        # check that there are results
        if not results or 'data' not in results or not results.get('data', None):
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['There were no results returned from facebook.'], 'infos': []})
        # Array to hold the parsed content
        parsed_results = []
        for r in results.get('data', []):
            try:
                parsed_item = self._parse_fb_item(r, source)
                if parsed_item.title:
                    parsed_results.append(parsed_item)
            except Exception, e:
                # Format the error
                error = format_error(e, sys.exc_info())
                # If there is an error even getting the results
                return source.update_test_data(
                    test_result_id,
                    'error',
                    {'errors': ['Not all of the posts could be parsed.', error], 'infos': []})
        # Update the source with the results and include any bozo errors as info messages
        return source.update_test_data(
            test_result_id,
            'passed',
            {'errors': [], 'infos': []},
            parsed_results)

    def run_polling_aggregation(self, source, configuration, run_record):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = FacebookPublicSearchChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the test via the source object
            return run_record.update('error', status_messages)
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the search terms
        search_terms = [e for e in elements if e['name'] == 'search'][0]['value']
        # Get the fb items
        try:
            fb = facepy.GraphAPI(access_token)
            raw_results = fb.search(term=search_terms, type='post', limit=100)
        except Exception, e:
            # Format the error
            error = format_error(e, sys.exc_info())
            # If there is an error even getting the results
            return run_record.update(
                'error',
                {'errors': ['There was an error getting data from facebook.', error], 'infos': []})
        # check that there are results
        if not raw_results or 'data' not in raw_results or not raw_results.get('data', None):
            return run_record.update(
                'error',
                {'errors': ['There were no results returned from facebook.'], 'infos': []})
        # Array to hold the parsed content
        results = []
        for r in raw_results.get('data', []):
            try:
                parsed_item = self._parse_fb_item(r, source)
                if parsed_item.title:
                    results.append(parsed_item)
            except Exception, e:
                # Format the error
                error = format_error(e, sys.exc_info())
                # If there is an error even getting the results
                return run_record.update(
                    run_record.status,
                    {'errors': ['Not all of the posts could be parsed.', error], 'infos': []})
        # If there is a since time in the config
        if 'since_time' in configuration:
            try:
                # Parse the since time as a datetime
                since_time = datetime.datetime.fromtimestamp(configuration['since_time'])
                # filter out all duplicates based on time created
                results = [r for r in results if not r.created or r.created > since_time]
            except:
                pass
        # calculate oldest and youngest
        oldest = None
        youngest = None
        for r in results:
            if r.created:
                if not oldest or r.created < oldest:
                    oldest = r.created
                if not youngest or r.created > youngest:
                    youngest = r.created
        # Update the stats on the run record
        run_record.record_statistics(total_item=len(results), oldest_datetime=oldest, youngest_datetime=youngest)
        # update the run record
        run_record.update('finished', {'errors': [], 'infos': []})
        # Update the configuration with the new since_time
        youngest_is_time = (youngest and isinstance(youngest, datetime.datetime))
        configuration['since_time'] = time.mktime(youngest.timetuple()) if youngest_is_time else time.time()
        # Return the results
        return results

    def _parse_fb_item(self, item, source):
        created = None
        message = Truncator(strip_tags(item.get('message', ''))).words(50, truncate=' ...')
        item_id = item.get('id', None)
        link_format = 'http://www.facebook.com/%s'
        try:
            timestamp = item.get('created_time')
            created = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S+0000')
        except Exception:
            pass
        author = ContentItemAuthor()
        author.display_name = item.get('from', {}).get('name', None)
        author.id = item.get('from', {}).get('id', None)
        content = ContentItem()
        content.id = md5(item_id or ('%s' % (time.time() + randint(0, 1000)))).hexdigest()
        content.source = source.to_dict()
        content.author = author
        content.title = Truncator(message).words(10, truncate=' ...')
        if item_id:
            content.link = link_format % (item_id.split('_')[1])
        content.text = [message]
        content.created = created
        return content


class TwitterPublicSearchChannel(_BaseChannel):
    _base_image_url = 'http://cdn1.iconfinder.com/data/icons/yooicons_set01_socialbookmarks'
    _configuration = {
        'type': 'twitter_public_search_v01',
        'data_type': 'content_v01',
        'aggregation_type': 'polling',
        'images': {
            '16': _base_image_url + '/16/social_twitter_box_blue.png',
            '24': _base_image_url + '/24/social_twitter_box_blue.png',
            '32': _base_image_url + '/32/social_twitter_box_blue.png',
            '48': _base_image_url + '/48/social_twitter_box_blue.png',
            '64': _base_image_url + '/64/social_twitter_box_blue.png',
            '128': _base_image_url + '/128/social_twitter_box_blue.png'
        },
        'display_name_short': 'Twitter Search',
        'display_name_full': 'Twitter Search',
        'description_short': 'Search public tweets.',
        'description_full': 'Use this source to search the public tweet stream of Twitter',
        'config': {
            'elements': [
                {
                    'name': 'search',
                    'display_name': 'Search Term(s)',
                    'type': 'text',
                    'help_message': 'Only numbers and characters separated by spaces (Note that all terms use '
                                    'a logical AND).',
                    'value': ''
                },
                {
                    'name': 'limit',
                    'display_name': 'Total Limit',
                    'type': 'select',
                    'help_message': 'Please choose the total number of content items that can be held for this '
                                    'data source. Once this limit is reached, old items will drop off the bottom to '
                                    'make way for new items.',
                    'values': ['1000', '10000', '100000', '1000000'],
                    'value': '10000',
                }
            ]
        }
    }

    @classmethod
    def ValidateAndReturnErrors(cls, configuration):
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the search terms for checking
        search_terms = [e for e in elements if e['name'] == 'search'][0]['value']
        # If there are no search terms or they are not valid
        if not search_terms or [c for c in search_terms if not c.isalnum() and c != ' ' and c != ':']:
            # Return an error saying so
            return ['The search term(s) you entered are not valid.']
        # Check that there is a valid oauth store entry
        from django_odc.authentication import TwitterV01AuthenticationController
        auth_controller = TwitterV01AuthenticationController.GetOrCreate()
        if auth_controller.status() != 'active':
            return ['The OAuth authentication for this channel is not set up.']
        # No errors = pass
        return []

    def run_test(self, source, configuration, test_result_id):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = TwitterPublicSearchChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the test via the source object
            return source.update_test_data(test_result_id, 'error', status_messages)
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the search terms
        search_terms = [e for e in elements if e['name'] == 'search'][0]['value']
        # Get the items
        try:
            from django_odc.authentication import TwitterV01AuthenticationController
            twitter_api = TwitterV01AuthenticationController.GetOrCreate().return_authorized_wrapper()
            # results = twitter_api.search(q=search_terms, lang='en', results_type='recent', rpp=10)
            results = twitter_api.search(q=search_terms, lang='en', results_type='recent', count=10)
        except Exception, e:
            # Format the error
            error = format_error(e, sys.exc_info())
            # If there is an error even getting the results
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['There was an error getting data from twitter.', error], 'infos': []})
        # check that there are results
        if not results or not results.get('statuses', []):
            return source.update_test_data(
                test_result_id,
                'error',
                {'errors': ['There were no results returned from Twitter.'], 'infos': []})
        # Array to hold the parsed content
        parsed_results = []
        for r in results['statuses']:
            try:
                parsed_item = self._parse_incoming_tweet(r, source)
                if parsed_item.title:
                    parsed_results.append(parsed_item)
            except Exception, e:
                # Format the error
                error = format_error(e, sys.exc_info())
                # If there is an error even getting the results
                return source.update_test_data(
                    test_result_id,
                    'error',
                    {'errors': ['Not all of the tweets could be parsed.', error], 'infos': []})
        # Update the source with the results and include any bozo errors as info messages
        return source.update_test_data(
            test_result_id,
            'passed',
            {'errors': [], 'infos': []},
            parsed_results)

    def run_polling_aggregation(self, source, configuration, run_record):
        # Validate the config to ensure its ok - it should be but who knows :)
        errors = TwitterPublicSearchChannel.ValidateAndReturnErrors(configuration)
        #If these are any errors then set the test in error state
        if errors:
            # Build the status messages
            status_messages = {'errors': ['This source is not correctly configured.'], 'infos': []}
            # Update the test via the source object
            return run_record.update('error', status_messages)
        # Extract the elements from the config
        elements = configuration['config']['elements']
        # Get the search terms
        search_terms = [e for e in elements if e['name'] == 'search'][0]['value']
        # Get the items
        try:
            from django_odc.authentication import TwitterV01AuthenticationController
            twitter_api = TwitterV01AuthenticationController.GetOrCreate().return_authorized_wrapper()
            # results = twitter_api.search(q=search_terms, lang='en', results_type='recent', rpp=10)
            raw_results = twitter_api.search(q=search_terms, lang='en', results_type='recent', count=100)
        except Exception, e:
            # Format the error
            error = format_error(e, sys.exc_info())
            # If there is an error even getting the results
            return run_record.update(
                'error',
                {'errors': ['There was an error getting data from Twitter.', error], 'infos': []})
        # check that there are results
        if not raw_results or not raw_results.get('statuses', []):
            return run_record.update(
                'error',
                {'errors': ['There were no results returned from Twitter.'], 'infos': []})
        # Array to hold the parsed content
        results = []
        for r in raw_results['statuses']:
            try:
                parsed_item = self._parse_incoming_tweet(r, source)
                if parsed_item.title:
                    results.append(parsed_item)
            except Exception, e:
                # Format the error
                error = format_error(e, sys.exc_info())
                # If there is an error even getting the results
                return run_record.update(
                    run_record.status,
                    {'errors': ['Not all of the posts could be parsed.', error], 'infos': []})
        # If there is a since time in the config
        if 'since_time' in configuration:
            try:
                # Parse the since time as a datetime
                since_time = datetime.datetime.fromtimestamp(configuration['since_time'])
                # filter out all duplicates based on time created
                results = [r for r in results if not r.created or r.created > since_time]
            except:
                pass
        # calculate oldest and youngest
        oldest = None
        youngest = None
        for r in results:
            if r.created:
                if not oldest or r.created < oldest:
                    oldest = r.created
                if not youngest or r.created > youngest:
                    youngest = r.created
        # Update the stats on the run record
        run_record.record_statistics(total_item=len(results), oldest_datetime=oldest, youngest_datetime=youngest)
        # update the run record
        run_record.update('finished', {'errors': [], 'infos': []})
        # Update the configuration with the new since_time
        youngest_is_time = (youngest and isinstance(youngest, datetime.datetime))
        configuration['since_time'] = time.mktime(youngest.timetuple()) if youngest_is_time else time.time()
        # Return the results
        return results

    def _parse_incoming_tweet(self, raw_tweet, source):
        author = ContentItemAuthor()
        author.display_name = raw_tweet.get('user', {}).get('screen_name', None)
        author.id = raw_tweet.get('user', {}).get('id_str', None)
        author.profile_image_url = raw_tweet.get('user', {}).get('profile_image_url', None)
        content = ContentItem()
        content.author = author
        content.id = md5(raw_tweet.get('id_str')).hexdigest()
        content.source = source.to_dict()
        content.title = raw_tweet.get('text')
        content.link = 'https://twitter.com/#!/%s/status/%s' % (author.display_name, raw_tweet.get('id_str'))
        content.language = raw_tweet.get('lang', None)
        content.created = datetime.datetime.strptime(raw_tweet.get('created_at'), '%a %b %d %H:%M:%S +0000 %Y')
        return content
