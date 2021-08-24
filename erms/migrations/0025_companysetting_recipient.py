# Generated by Django 2.1.2 on 2019-08-16 18:07

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0024_chargebacklinehistory_submitted_contract_no'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanySetting',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('auto_contact_notifications', models.BooleanField(default=False)),
                ('auto_chargeback_reports_enable', models.BooleanField(default=False)),
                ('enable_daily_report', models.BooleanField(default=False)),
                ('default_wac_enable', models.BooleanField(default=False)),
                ('auto_assign_big_3_as_contract_servers', models.BooleanField(default=False)),
                ('global_customer_list_updates_overrides_local_changes', models.BooleanField(default=False)),
                ('alert_enabled', models.BooleanField(default=False)),
                ('alert_sent_in_single_daily_digest', models.BooleanField(default=False)),
                ('membership_validation_enable', models.BooleanField(default=False)),
                ('proactive_membership_validation', models.BooleanField(default=False)),
                ('auto_contract_notification_enabled', models.BooleanField(default=False)),
                ('class_of_trade_validation_enabled', models.BooleanField(default=False)),
                ('automatic_chargeback_processing', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Company Setting',
                'verbose_name_plural': 'Companies Settings',
                'db_table': 'companies_settings',
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='Recipient',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('first_name', models.CharField(default='Jane', max_length=120)),
                ('last_name', models.CharField(default='Doe', max_length=120)),
                ('email', models.CharField(blank=True, max_length=100, null=True)),
                ('processing_report_alert_recipient', models.BooleanField(default=False)),
                ('alert_recipient', models.BooleanField(default=False)),
                ('company_setting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='erms.CompanySetting')),
            ],
            options={
                'verbose_name': 'Recipient',
                'verbose_name_plural': 'Recipients',
                'db_table': 'recipients',
                'ordering': ('company_setting',),
            },
        ),
    ]
