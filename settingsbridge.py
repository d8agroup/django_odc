from django.conf import settings

_DEFAULT_SETTINGS = {
    'ODC_DATACONTEXT_TYPE': 'Solr4xDataContent',
    'ODC_DATACONTEXT_INIT_CONFIG': {
        # This must be overwritten in your settings file
        #'solr_url': 'THIS MUST BE OVERWRITTEN IN YOUR SETTINGS FILE'
    },
    'ODC_API_KEY': '12345',
    'ODC_AUTHENTICATION_SCOPE': 'application',  # application|user
    'ODC_DEFAULT_SOURCE_LIMIT': 10000,
}


def access_settings(key):
    try:
        return getattr(settings, key)
    except AttributeError:
        return _DEFAULT_SETTINGS[key]
