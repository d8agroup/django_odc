import datetime
from django.utils.timezone import make_aware, get_current_timezone
import solr
from solr.core import utc_from_string


class _BaseDataContext(object):
    def push(self, data):
        """This is designed to be overwritten in inheriting classes"""
        pass

    def dataset_statistics(self, dataset):
        """This is designed to be overwritten in inheriting classes"""
        pass


class Solr4xDataContent(_BaseDataContext):
    solr_url = ''

    def __init__(self, config):
        self.solr_url = config['solr_url'].rstrip('/')

    def push(self, data):
        connection = solr.SolrConnection(self.solr_url)
        for d in data:
            try:
                parsed_data = self._parse_data(d)
                connection.add_many([parsed_data])
            except Exception, e:
                # TODO need to record this
                pass
        connection.commit()

    def dataset_statistics(self, dataset):
        connection = solr.SolrConnection(self.solr_url)
        stats = {
            'total_items': 0,
            'aggregate_items_per_minute': 0}
        items_per_minute = []
        sources = dataset.source_set.all()
        for source in sources:
            try:
                results = connection.query(q='source_id_s:%s' % source.id, stats='on', stats_field='created_dt')
                stats['total_items'] += results._numFound
                created_max = results.stats['stats_fields']['created_dt']['max']
                created_min = results.stats['stats_fields']['created_dt']['min']
                total_minutes = (float((created_max - created_min).seconds) / 60) or 1
                items_per_minute.append(float(stats['total_items']) / total_minutes)
            except Exception, e:
                pass
        stats['aggregate_items_per_minute'] = sum(items_per_minute) / len(sources)

        return stats

    def _parse_data(self, d):
        data_type = d.source['channel']['data_type']
        if data_type == 'content_v01':
            created = make_aware(d.created, get_current_timezone())
            parsed_data = {
                'data_type_s': data_type,
                'source_id_s': d.source['id'],
                'id': d.id,
                'title_txt': d.title,
                'text_txt': d.text,
                'link_s': d.link,
                'created_dt': created
            }
            if d.author:
                parsed_data['author_display_name_s'] = d.author.display_name
            return parsed_data

