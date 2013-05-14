from copy import deepcopy

# Global variables needed for the nlp service
tokenizer = None
tagger = None


class _BaseService(object):

    @property
    def configuration(self):
        return deepcopy(self._configuration)

    def channel_data_type_is_supported(self, channel_data_type):
        """This should be overwritten in inheriting classes"""
        pass

    def run(self, config, data):
        """This should be overwritten in inheriting classes"""
        return data


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


class NLPV01Service(_BaseService):
    _configuration = {
        'type': 'nlp_v01',
        'images': {
            '16': '/static/django_odc/img/services/nlp_v01/16.png',
            '24': '/static/django_odc/img/services/nlp_v01/24.png',
            '32': '/static/django_odc/img/services/nlp_v01/32.png',
            '48': '/static/django_odc/img/services/nlp_v01/48.png',
            '64': '/static/django_odc/img/services/nlp_v01/64.png',
            '128': '/static/django_odc/img/services/nlp_v01/128.png'
        },
        'display_name_short': 'NLP',
        'display_name_full': 'Natural Language Processing',
        'description_short': 'Extract keywords from the source text.',
        'description_full': 'Use this service to extract the keywords for the source content.',
        'config': {
            'type': 'none'
        }
    }

    def channel_data_type_is_supported(self, channel_data_type):
        # This service only supports content types
        return channel_data_type in 'content_v01'

    def run(self, config, data):
        import nltk
        global tagger, tokenizer
        if not tokenizer:
            tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+|[^\w\s]+')
        if not tagger:
            tagger = nltk.UnigramTagger(nltk.corpus.brown.tagged_sents())
        for item in data:
            item.add_metadata('tags', self._get_tags(config, item, tokenizer, tagger), 'string')
        return data

    def _get_tags(self, config, content_item, tokenizer, tagger):
        text = self._extract_text(config, content_item)
        tokenized = tokenizer.tokenize(text)
        tagged = tagger.tag(tokenized)
        results = [word.replace('#', '') for word in text.split() if word.startswith('#')]
        for pair in tagged:
            if len(pair) > 1:
                if pair[1] and pair[1].startswith('N'):
                    if pair[0].lower() not in results and len(pair[0]) > 3:
                        results.append(pair[0].lower())
        results = sorted(results, key=lambda r: len(r), reverse=True)
        return results

    def _extract_text(self, config, content_item):
        text = content_item.title or ''
        text += ' '.join(content_item.text)
        return text.encode('ascii', 'ignore')

