# Generated by Django 2.1.15 on 2020-05-05 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0054_auto_20200504_1630'),
    ]

    operations = [
        migrations.AddField(
            model_name='import844',
            name='bulk_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
