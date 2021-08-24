# Generated by Django 2.1.2 on 2019-04-25 10:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ermm', '0002_auto_20190422_1138'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanySetting',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('auto_contact_notifications', models.BooleanField(default=False)),
                ('auto_chargeback_reports_enable', models.BooleanField(default=False)),
                ('enable_daily_report', models.BooleanField(default=False)),
                ('default_wac_enable', models.BooleanField(default=False)),
                ('auto_assign_big_3_as_contract_servers', models.BooleanField(default=False)),
                ('global_customer_list_updates_overrides_local_changes', models.BooleanField(default=False)),
                ('alert_enabled', models.BooleanField(default=False)),
                ('alert_sent_in_single_daily_digest', models.BooleanField(default=False)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ermm.Company')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='companysetting_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='companysetting_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Company Setting',
                'verbose_name_plural': 'Companies Settings',
                'db_table': 'companies_settings',
                'ordering': ('company',),
            },
        ),
        migrations.AlterUniqueTogether(
            name='companysetting',
            unique_together={('company',)},
        ),
    ]
