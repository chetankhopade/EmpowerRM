# Generated by Django 2.1.2 on 2020-07-02 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0072_audittrail_filename'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargebackhistory',
            name='processed_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
