# Generated by Django 2.1.2 on 2020-07-01 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0071_auto_20200625_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='audittrail',
            name='filename',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
