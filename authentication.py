from copy import deepcopy
import tweepy
from twython import Twython
from django_odc.models import AuthenticationStorage


class _BaseAuthenticationController(object):
    pass


class TwitterV01AuthenticationController(_BaseAuthenticationController):

    display_name = 'Twitter OAuth'
    type = 'TwitterV01'
    _config = {
        'elements': [
            {
                'name': 'app_key',
                'display_name': 'Application Key',
                'type': 'text',
                'help_message': '',
                'value': ''
            },
            {
                'name': 'app_secret',
                'display_name': 'Application Secret',
                'type': 'text',
                'help_message': '',
                'value': ''
            },
            {
                'name': 'oauth_token',
                'display_name': 'OAuth Token',
                'type': 'hidden',
                'help_message': '',
                'value': ''
            },
            {
                'name': 'oauth_secret',
                'display_name': 'OAuth Secret',
                'type': 'hidden',
                'help_message': '',
                'value': ''
            }]}

    @classmethod
    def GetOrCreate(cls):
        controller = TwitterV01AuthenticationController()
        storage = AuthenticationStorage.GetByType(cls.type)
        if storage:
            controller.config = storage.config
        else:
            controller.config = AuthenticationStorage.CreateWithTypeAndConfig(cls.type, deepcopy(cls._config)).config
        return controller

    def __init__(self):
        self.config = {}

    def save(self):
        storage = AuthenticationStorage.GetByType(self.type)
        if storage:
            storage.config = self.config
        else:
            storage = AuthenticationStorage.CreateWithTypeAndConfig(self.type, self.config)
        storage.save()

    def status(self):
        if not self.config or not self.config.get('elements', None):
            return 'unconfigured'
        oauth_token = [e for e in self.config['elements'] if e['name'] == 'oauth_token'][0]['value']
        oauth_secret = [e for e in self.config['elements'] if e['name'] == 'oauth_secret'][0]['value']
        if not oauth_secret or not oauth_token:
            return 'unconfigured'
        return 'active'

    def to_dict(self):
        return {
            'type': self.type,
            'display_name': self.display_name,
            'config': self.config,
            'status': self.status()}

    def return_authorized_wrapper(self):
        app_key = [e for e in self.config['elements'] if e['name'] == 'app_key'][0]['value']
        app_secret = [e for e in self.config['elements'] if e['name'] == 'app_secret'][0]['value']
        oauth_token = [e for e in self.config['elements'] if e['name'] == 'oauth_token'][0]['value']
        oauth_secret = [e for e in self.config['elements'] if e['name'] == 'oauth_secret'][0]['value']
        # auth = tweepy.OAuthHandler(app_key, app_secret)
        # auth.set_access_token(oauth_token, oauth_secret)
        return Twython(app_key, app_secret, oauth_token, oauth_secret)
        # return tweepy.API(auth_handler=auth)


