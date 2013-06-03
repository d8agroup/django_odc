# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Dataset'
        db.create_table(u'django_odc_dataset', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('display_name', self.gf('django.db.models.fields.TextField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.TextField')(default='unconfigured')),
            ('_status_messages', self.gf('django.db.models.fields.TextField')(default='')),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('modified', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'django_odc', ['Dataset'])

        # Adding model 'UserGroup'
        db.create_table(u'django_odc_usergroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('_name', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal(u'django_odc', ['UserGroup'])

        # Adding M2M table for field _datasets on 'UserGroup'
        m2m_table_name = db.shorten_name(u'django_odc_usergroup__datasets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('usergroup', models.ForeignKey(orm[u'django_odc.usergroup'], null=False)),
            ('dataset', models.ForeignKey(orm[u'django_odc.dataset'], null=False))
        ))
        db.create_unique(m2m_table_name, ['usergroup_id', 'dataset_id'])

        # Adding M2M table for field _users on 'UserGroup'
        m2m_table_name = db.shorten_name(u'django_odc_usergroup__users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('usergroup', models.ForeignKey(orm[u'django_odc.usergroup'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['usergroup_id', 'user_id'])

        # Adding model 'Source'
        db.create_table(u'django_odc_source', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_channel', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('_status_messages', self.gf('django.db.models.fields.TextField')(default='')),
            ('_services', self.gf('django.db.models.fields.TextField')(default='[]')),
            ('display_name', self.gf('django.db.models.fields.TextField')(default='')),
            ('guid', self.gf('django.db.models.fields.TextField')(default='')),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.TextField')(default='unconfigured')),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('modified', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'django_odc', ['Source'])

        # Adding M2M table for field datasets on 'Source'
        m2m_table_name = db.shorten_name(u'django_odc_source_datasets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('source', models.ForeignKey(orm[u'django_odc.source'], null=False)),
            ('dataset', models.ForeignKey(orm[u'django_odc.dataset'], null=False))
        ))
        db.create_unique(m2m_table_name, ['source_id', 'dataset_id'])

        # Adding model 'SourceTestResult'
        db.create_table(u'django_odc_sourcetestresult', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_odc.Source'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('modified', self.gf('django.db.models.fields.DateTimeField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('status', self.gf('django.db.models.fields.TextField')()),
            ('_status_messages', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('_results', self.gf('django.db.models.fields.TextField')(default='[]')),
        ))
        db.send_create_signal(u'django_odc', ['SourceTestResult'])

        # Adding model 'SourceRunRecord'
        db.create_table(u'django_odc_sourcerunrecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_odc.Source'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('modified', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.TextField')()),
            ('_status_messages', self.gf('django.db.models.fields.TextField')()),
            ('_statistics', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'django_odc', ['SourceRunRecord'])

        # Adding model 'AuthenticationStorage'
        db.create_table(u'django_odc_authenticationstorage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.TextField')()),
            ('_config', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal(u'django_odc', ['AuthenticationStorage'])


    def backwards(self, orm):
        # Deleting model 'Dataset'
        db.delete_table(u'django_odc_dataset')

        # Deleting model 'UserGroup'
        db.delete_table(u'django_odc_usergroup')

        # Removing M2M table for field _datasets on 'UserGroup'
        db.delete_table(db.shorten_name(u'django_odc_usergroup__datasets'))

        # Removing M2M table for field _users on 'UserGroup'
        db.delete_table(db.shorten_name(u'django_odc_usergroup__users'))

        # Deleting model 'Source'
        db.delete_table(u'django_odc_source')

        # Removing M2M table for field datasets on 'Source'
        db.delete_table(db.shorten_name(u'django_odc_source_datasets'))

        # Deleting model 'SourceTestResult'
        db.delete_table(u'django_odc_sourcetestresult')

        # Deleting model 'SourceRunRecord'
        db.delete_table(u'django_odc_sourcerunrecord')

        # Deleting model 'AuthenticationStorage'
        db.delete_table(u'django_odc_authenticationstorage')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'django_odc.authenticationstorage': {
            'Meta': {'object_name': 'AuthenticationStorage'},
            '_config': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.TextField', [], {})
        },
        u'django_odc.dataset': {
            'Meta': {'object_name': 'Dataset'},
            '_status_messages': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'display_name': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.TextField', [], {'default': "'unconfigured'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'django_odc.source': {
            'Meta': {'object_name': 'Source'},
            '_channel': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            '_services': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            '_status_messages': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'datasets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['django_odc.Dataset']", 'symmetrical': 'False'}),
            'display_name': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'guid': ('django.db.models.fields.TextField', [], {'default': "''"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.TextField', [], {'default': "'unconfigured'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'django_odc.sourcerunrecord': {
            'Meta': {'object_name': 'SourceRunRecord'},
            '_statistics': ('django.db.models.fields.TextField', [], {}),
            '_status_messages': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_odc.Source']"}),
            'status': ('django.db.models.fields.TextField', [], {})
        },
        u'django_odc.sourcetestresult': {
            'Meta': {'object_name': 'SourceTestResult'},
            '_results': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            '_status_messages': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_odc.Source']"}),
            'status': ('django.db.models.fields.TextField', [], {})
        },
        u'django_odc.usergroup': {
            'Meta': {'object_name': 'UserGroup'},
            '_datasets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['django_odc.Dataset']", 'symmetrical': 'False'}),
            '_name': ('django.db.models.fields.TextField', [], {'default': "''"}),
            '_users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['django_odc']