# Generated by Django 2.1.2 on 2019-12-18 18:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ermm', '0027_auto_20191129_0935'),
    ]

    operations = [
        migrations.CreateModel(
            name='EDIMappingTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('name', models.CharField(max_length=300)),
                ('document_type', models.SmallIntegerField(blank=True, choices=[(1, '844'), (2, '849'), (3, '850')], null=True)),
                ('format', models.SmallIntegerField(blank=True, choices=[(1, 'text'), (2, 'csv'), (3, 'xml')], null=True)),
                ('type', models.SmallIntegerField(blank=True, choices=[(1, 'Delimited'), (2, 'Fixed Width')], null=True)),
                ('delimiter', models.CharField(blank=True, max_length=2, null=True)),
                ('show_header', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='edimappingtemplate_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='edimappingtemplate_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'EDI Mapping Template',
                'verbose_name_plural': 'EDI Mappings Templates',
                'db_table': 'edi_mapping_templates',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='EDIMappingTemplateDetail',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('segment', models.CharField(max_length=100)),
                ('fixed_width_row', models.CharField(blank=True, max_length=100, null=True)),
                ('fixed_width_char', models.CharField(blank=True, max_length=100, null=True)),
                ('fixed_width_length', models.CharField(blank=True, max_length=100, null=True)),
                ('enable', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='edimappingtemplatedetail_created_by', to=settings.AUTH_USER_MODEL)),
                ('edi_mapping_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ermm.EDIMappingTemplate')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='edimappingtemplatedetail_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'EDI Mapping Template - Detail',
                'verbose_name_plural': 'EDI Mappings Templates - Details',
                'db_table': 'edi_mapping_templates_details',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AlterUniqueTogether(
            name='edimappingtemplatedetail',
            unique_together={('edi_mapping_template', 'name', 'segment')},
        ),
        migrations.AlterUniqueTogether(
            name='edimappingtemplate',
            unique_together={('name', 'document_type')},
        ),
    ]
