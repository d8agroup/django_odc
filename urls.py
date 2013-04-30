from django.conf.urls import patterns, url
import views

urlpatterns = patterns(
    '',
    url(r'javascript_url_bridge$',
        views.javascript_url_bridge, name='javascript_url_bridge'),
    url(r'datasets$',
        views.datasets, name='datasets'),
    url(r'dataset/(?P<dataset_id>\w+)$',
        views.dataset, name='dataset'),
    url(r'dataset_template$',
        views.dataset_template, name='dataset_template'),
    url(r'dataset_save$',
        views.dataset_save, name='dataset_save'),
    url(r'dataset_sources/(?P<dataset_id>\w+)$',
        views.dataset_delete, name='dataset_delete'),
    url(r'dataset_delete/(?P<dataset_id>\w+)$',
        views.dataset_sources, name='dataset_sources'),
    url(r'dataset_statistics_summary/(?P<dataset_id>\w+)$',
        views.dataset_statistics_summary, name='dataset_statistics_summary'),

    url(r'channel_types$',
        views.channel_types, name='channel_types'),

    url(r'polling_source_create/(?P<dataset_id>\w+)/(?P<channel_type>\w+)$',
        views.polling_source_create, name='polling_source_create'),
    url(r'polling_source_configure/(?P<source_id>\w+)$',
        views.polling_source_configure, name='polling_source_configure'),
    url(r'polling_source_test/(?P<source_id>\w+)$',
        views.polling_source_test, name='polling_source_test'),
    url(r'polling_source_test_check/(?P<source_id>\w+)$',
        views.polling_source_test_check, name='polling_source_test_check'),
    url(r'polling_source_analysis/(?P<source_id>\w+)$',
        views.polling_source_analysis, name='polling_source_analysis'),
    url(r'polling_source_confirm/(?P<source_id>\w+)$',
        views.polling_source_confirm, name='polling_source_confirm'),

    url(r'source_add_service/(?P<source_id>\w+)/(?P<service_type>\w+)$',
        views.source_add_service, name='source_add_service'),
    url(r'source_remove_service/(?P<source_id>\w+)/(?P<service_type>\w+)$',
        views.source_remove_service, name='source_remove_service'),
    url(r'source_activate/(?P<source_id>\w+)$',
        views.source_activate, name='source_activate'),
    url(r'source_deactivate/(?P<source_id>\w+)$',
        views.source_deactivate, name='source_deactivate'),
    url(r'sources_kill$',
        views.sources_kill, name='sources_kill'),
    url(r'source_bridge/(?P<source_type>\w+)$',
        views.source_bridge, name='source_bridge'),

    url(r'statistics_run_records$',
        views.statistics_run_records, name='statistics_run_records'),

    url(r'aggregate_for_user$',
        views.aggregate_datasets_for_current_user, name='aggregate_datasets_for_current_user'),

    url(r'$', views.home, name='odc_home'))
