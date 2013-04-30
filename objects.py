import uuid
import datetime
from django.utils.timezone import now

class ContentItemAuthor(object):
    display_name = ''
    id = ''
    profile_image_url = ''

    @classmethod
    def FromDict(cls, values):
        a = ContentItemAuthor()
        for k, v in values.items():
            setattr(a, k, v)
        return a

    def to_dict(self):
        return {
            'display_name': self.display_name,
            'id': self.id,
            'profile_image_url': self.profile_image_url}


class ContentItem(object):
    id = '%s' % uuid.uuid4()
    source = {}
    author = ContentItemAuthor()
    title = ''
    text = []
    link = ''
    language = ''  # 2 character ISO language code
    created = now()
    metadata = []

    @classmethod
    def FromDict(cls, values):
        c = ContentItem()
        for k, v in values.items():
            if k == 'author':
                c.author = ContentItemAuthor.FromDict(v)
            elif k == 'created':
                c.created = datetime.datetime.strptime(v, '%c')
            else:
                setattr(c, k, v)
        return c

    def add_metadata(self, key, value, value_type):
        def format_key(k):
            return ''.join(_k for _k in key.lower() if _k.isalpha())

        if value_type == 'string':
            self.metadata.append({'key': 'metadata_%s_s' % format_key(key), 'value': value})
        if value_type == 'int':
            self.metadata.append({'key': 'metadata_%s_i' % format_key(key), 'value': value})

    def add_popularity_metadata(self, value):
        self.add_metadata('popularity', value, 'int')

    def _map_language(self, lang):
        if lang == 'en':
            return 'english'
        return lang

    def to_dict(self):
        return {
            'id': '%s' % self.id,
            'source': self.source,
            'author': self.author.to_dict(),
            'title': self.title,
            'text': self.text,
            'link': self.link,
            'language': self._map_language(self.language),
            'metadata': self.metadata,
            'created': self.created.strftime('%c') if self.created else None}