import datetime
from django.utils.timezone import make_aware, get_current_timezone
import solr
from solr.core import utc_from_string
from django_odc.objects import ContentItemAuthor, ContentItem


class _BaseDataContext(object):
    def push(self, source, data):
        """This is designed to be overwritten in inheriting classes"""
        pass

    def dataset_statistics(self, dataset):
        """This is designed to be overwritten in inheriting classes"""
        pass

    def run_query(self, search_data):
        """This should be overwritten by the inheriting class"""
        return None


class Solr4xDataContent(_BaseDataContext):
    solr_url = ''

    def __init__(self, config):
        self.solr_url = config['solr_url'].rstrip('/')

    def push(self, source, data):
        connection = solr.SolrConnection(self.solr_url)
        for d in data:
            try:
                parsed_data = self._parse_data_to_solr(d)
                connection.add_many([parsed_data])
            except Exception, e:
                # TODO need to record this
                pass
        connection.commit()
        self._run_delete_if_needed(source, connection)

    def dataset_statistics(self, dataset):
        connection = solr.SolrConnection(self.solr_url)
        stats = {
            'total_items': 0,
            'aggregate_items_per_minute': 0,
            'aggregate_items_per_day': 0}
        items_per_minute = []
        sources = dataset.source_set.all()
        for source in sources:
            if source.status != 'active':
                continue
            try:
                results = connection.query(q='source_id:%s' % source.guid, stats='on', stats_field='created')
                stats['total_items'] += results._numFound
                created_max = results.stats['stats_fields']['created']['max']
                created_min = results.stats['stats_fields']['created']['min']
                total_minutes = (float((created_max - created_min).seconds) / 60) or 1
                items_per_minute.append(float(stats['total_items']) / total_minutes)
            except Exception, e:
                pass
        stats['aggregate_items_per_minute'] = sum(items_per_minute) / (len(sources) or 1)
        stats['aggregate_items_per_day'] = round(stats['aggregate_items_per_minute'] * 86400, 2)

        return stats

    def run_query(self, search_data):
        connection = solr.SolrConnection(self.solr_url)
        q = "*:*"
        fq = [" OR ".join('source_id:%s' % s['guid'] for s in search_data.get('sources', []))]
        fq += search_data.get('filters', [])
        rows = search_data.get('pagination', {}).get('rows', 10)
        pivot = [','.join(p['fields']) for p in search_data.get('pivots', [])]
        raw_results = connection.query(q=q, facet='on', fq=fq, rows=rows, facet_pivot=pivot)
        results = {
            'items': [self._parse_data_from_solr(r) for r in raw_results.results],
            'pivots': self._parse_pivots_from_solr(raw_results.facet_counts.get('facet_pivot', {}))
        }

        return results

    def _parse_pivots_from_solr(self, facet_pivots):
        parsed_pivots = []
        for key, value in facet_pivots.items():
            parsed_pivots.append({
                'fields': key.split(','),
                'values': value})
        return parsed_pivots

    def _parse_data_from_solr(self, i):
        a = ContentItemAuthor()
        a.display_name = i.get('author_display_name', None)
        a.id = i.get('author_id', None)
        a.profile_image_url = i.get('author_profile_image_url', '')
        c = ContentItem(source_guid=i.get('source_id'))
        c.author = a
        c.id = i.get('id')
        c.title = i.get('title', None)
        c.text = i.get('text', [])
        c.link = i.get('link', '')
        c.created = i.get('created')
        for key, val in i.items():
            if key.startswith('metadata'):
                c.metadata.append({'key': key, 'value': val})
        return c

    def _parse_data_to_solr(self, i):
        data_type = i.source['channel']['data_type']
        if data_type == 'content_v01':
            created = make_aware(i.created, get_current_timezone())
            parsed_data = {
                'data_type': data_type,
                'source_id': i.source['guid'],
                'id': i.id,
                'title': i.title,
                'text': i.text,
                'link': i.link,
                'created': created}
            if i.author:
                parsed_data['author_display_name'] = i.author.display_name
                parsed_data['author_id'] = i.author.id
                parsed_data['author_profile_image_url'] = i.author.profile_image_url
            for metadata in i.metadata:
                parsed_data[metadata['key']] = metadata['value']
            return parsed_data

    def _run_delete_if_needed(self, source, connection):
        # TODO: PER SOURCE LIMIT - this is hard coded for now
        per_source_limit = 10000
        results = connection.query('source_id:%s' % source.guid, fl=['id'], sort='created_dt asc', rows=1000)
        number_over_limit = results._numFound - per_source_limit
        if number_over_limit <= 0:
            return
        items_to_delete = []
        for i in results.results:
            if len(items_to_delete) >= number_over_limit:
                break
            items_to_delete.append(i['id'])
        if items_to_delete:
            connection.delete(queries=['id:%s' % id for id in items_to_delete], commit=True)
