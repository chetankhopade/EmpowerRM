# Generated by Django 2.1.2 on 2020-05-26 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0064_import844history_bulk_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chargebackline',
            name='invoice_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='chargebacklinehistory',
            name='invoice_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
