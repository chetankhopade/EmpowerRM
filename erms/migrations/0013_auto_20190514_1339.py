# Generated by Django 2.1.2 on 2019-05-14 13:39

from django.db import migrations, models
import django.db.models.deletion
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0012_auto_20190503_1259'),
    ]

    operations = [
        migrations.AddField(
            model_name='indirectcustomer',
            name='address1',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='indirectcustomer',
            name='address2',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='indirectcustomer',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='indirectcustomer',
            name='company_name',
            field=models.CharField(default='N/A', max_length=140),
        ),
        migrations.AddField(
            model_name='indirectcustomer',
            name='location_number',
            field=models.CharField(default='N/A', max_length=100),
        ),
        migrations.AddField(
            model_name='indirectcustomer',
            name='metadata',
            field=django_mysql.models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name='indirectcustomer',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='erms.DirectCustomer'),
        ),
        migrations.AddField(
            model_name='indirectcustomer',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='indirectcustomer',
            name='zip_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='contract',
            name='eligibility',
            field=models.SmallIntegerField(blank=True, choices=[(1, 'GPO DRIVEN (BASE)'), (2, 'SUPPLIER DRIVEN'), (3, 'SUPPLIER LOC'), (4, 'INDIVIDUAL'), (5, 'BLANKET')], null=True),
        ),
    ]
