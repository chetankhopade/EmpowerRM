# Generated by Django 2.1.2 on 2019-04-25 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0003_auto_20190425_1336'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargebacklinehistory',
            name='approved_reason_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='chargebacklinehistory',
            name='line_status',
            field=models.SmallIntegerField(blank=True, choices=[(1, 'PENDING'), (2, 'APPROVED'), (3, 'DISPUTED')], null=True),
        ),
    ]
