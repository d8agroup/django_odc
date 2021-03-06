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
    url(r'dataset_delete/(?P<dataset_id>\w+)$',
        views.dataset_delete, name='dataset_delete'),
    url(r'dataset_sources/(?P<dataset_id>\w+)$',
        views.dataset_sources, name='dataset_sources'),
    url(r'dataset_statistics_summary/(?P<dataset_id>\w+)$',
        views.dataset_statistics_summary, name='dataset_statistics_summary'),

    url(r'dataset_users_configure/(?P<dataset_id>\w+)$',
        views.dataset_users_configure, name='dataset_users_configure'),
    url(r'dataset_users_add/(?P<dataset_id>\w+)/(?P<user_id>\w+)$',
        views.dataset_users_add, name='dataset_users_add'),
    url(r'dataset_users_remove/(?P<dataset_id>\w+)/(?P<user_id>\w+)$',
        views.dataset_users_remove, name='dataset_users_remove'),

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

    url(r'post_adapter_source_create/(?P<dataset_id>\w+)/(?P<channel_type>\w+)$',
        views.post_adapter_source_create, name='post_adapter_source_create'),
    url(r'post_adapter_source_configure/(?P<source_id>\w+)$',
        views.post_adapter_source_configure, name='post_adapter_source_configure'),
    url(r'post_adapter_source_test/(?P<source_id>\w+)$',
        views.post_adapter_source_test, name='post_adapter_source_test'),
    url(r'post_adapter_source_test_check/(?P<source_id>\w+)$',
        views.post_adapter_source_test_check, name='post_adapter_source_test_check'),
    url(r'post_adapter_source_instructions/(?P<source_id>\w+)$',
        views.post_adapter_source_instructions, name='post_adapter_source_instructions'),
    url(r'post_adapter_source_analysis/(?P<source_id>\w+)$',
        views.post_adapter_source_analysis, name='post_adapter_source_analysis'),
    url(r'post_adapter_source_confirm/(?P<source_id>\w+)$',
        views.post_adapter_source_confirm, name='post_adapter_source_confirm'),
    url(r'source/(?P<source_id>\w+)/test/(?P<test_id>\w+)$',
        views.post_adapter_source_test_adapter, name='post_adapter_source_test_adapter'),
    url(r'source/(?P<source_id>\w+)/post$',
        views.post_adapter_source_adapter, name='post_adapter_source_adapter'),

    url(r'source_add_service/(?P<source_id>\w+)/(?P<service_type>\w+)$',
        views.source_add_service, name='source_add_service'),
    url(r'source_remove_service/(?P<source_id>\w+)/(?P<service_type>\w+)$',
        views.source_remove_service, name='source_remove_service'),
    url(r'source_activate/(?P<source_id>\w+)$',
        views.source_activate, name='source_activate'),
    url(r'source_deactivate/(?P<source_id>\w+)$',
        views.source_deactivate, name='source_deactivate'),
    url(r'source_delete/(?P<source_id>\w+)$',
        views.source_delete, name='source_delete'),
    url(r'sources_kill$',
        views.sources_kill, name='sources_kill'),
    url(r'sources_empty$',
        views.sources_empty, name='sources_empty'),

    url(r'statistics_run_records$',
        views.statistics_run_records, name='statistics_run_records'),
    url(r'statistics_authentication_status$',
        views.statistics_authentication_status, name='statistics_authentication_status'),
    url(r'statistics_authentication_twitterv01_configure$',
        views.statistics_authentication_twitterv01_configure, name='statistics_authentication_twitterv01_configure'),
    url(r'statistics_authentication_twitterv01_oauth$',
        views.statistics_authentication_twitterv01_oauth, name='statistics_authentication_twitterv01_oauth'),

    url(r'aggregate_for_user$',
        views.aggregate_datasets_for_current_user, name='aggregate_datasets_for_current_user'),

    url(r'api/aggregate_all/(?P<api_key>\w+)$',
        views.aggregate_all, name='aggregate_all'),

    url(r'(?P<dataset_id>\w*)$', views.home, name='odc_home'))
