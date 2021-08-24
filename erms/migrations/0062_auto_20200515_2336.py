# Generated by Django 2.1.2 on 2020-05-15 23:36

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0061_auto_20200515_2325'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContractCoT',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=100, null=True)),
                ('contract_id', models.CharField(blank=True, max_length=50, null=True)),
                ('cot_id', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Contract - CoT',
                'verbose_name_plural': 'Contracts - CoTs',
                'db_table': 'contracts_cots',
                'ordering': ('contract_id',),
            },
        ),
        migrations.AlterUniqueTogether(
            name='contractcot',
            unique_together={('contract_id', 'cot_id')},
        ),
    ]
