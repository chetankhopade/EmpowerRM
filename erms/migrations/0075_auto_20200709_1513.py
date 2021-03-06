# Generated by Django 2.1.2 on 2020-07-09 15:13

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0074_auto_20200707_2351'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChargeBackDisputeHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('chargeback_id', models.CharField(blank=True, max_length=100, null=True)),
                ('chargebackline_id', models.CharField(blank=True, max_length=100, null=True)),
                ('dispute_code', models.CharField(blank=True, max_length=2, null=True)),
                ('dispute_note', models.TextField(blank=True, null=True)),
                ('field_name', models.CharField(blank=True, max_length=100, null=True)),
                ('field_value', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('chargeback_ref', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='erms.ChargeBackHistory')),
                ('chargebackline_ref', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='erms.ChargeBackLineHistory')),
            ],
            options={
                'verbose_name': 'ChargeBackDispute - History',
                'verbose_name_plural': 'ChargeBacksDisputes - History',
                'db_table': 'chargeback_disputes_history',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AlterModelOptions(
            name='chargebackdispute',
            options={'ordering': ('-created_at',), 'verbose_name': 'ChargeBackDispute - Open', 'verbose_name_plural': 'ChargeBacksDisputes - Open'},
        ),
    ]
