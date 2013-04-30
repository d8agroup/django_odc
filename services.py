from copy import deepcopy


class _BaseService(object):

    @property
    def configuration(self):
        return deepcopy(self._configuration)

    def channel_data_type_is_supported(self, channel_data_type):
        """This should be overwritten in inheriting classes"""
        pass


class SentimentAnalysisV01Service(_BaseService):
    _configuration = {
        'type': 'sentiment_analysis_v01',
        'images': {
            '16': '/static/django_odc/img/services/sentiment_analysis_v01/16.png',
            '24': '/static/django_odc/img/services/sentiment_analysis_v01/24.png',
            '32': '/static/django_odc/img/services/sentiment_analysis_v01/32.png',
            '48': '/static/django_odc/img/services/sentiment_analysis_v01/48.png',
            '64': '/static/django_odc/img/services/sentiment_analysis_v01/64.png',
            '128': '/static/django_odc/img/services/sentiment_analysis_v01/128.png'
        },
        'display_name_short': 'Sentiment',
        'display_name_full': 'Sentiment Analysis',
        'description_short': 'Extract the tone of a piece of content.',
        'description_full': 'Use this service to extract the sentiment (tone) from items of content.',
        'config': {
            'type': 'none'
        }
    }

    def channel_data_type_is_supported(self, channel_data_type):
        # This service only supports content types
        return channel_data_type in 'content_v01'