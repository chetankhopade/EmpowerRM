# Generated by Django 2.1.2 on 2020-04-09 12:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0050_auto_20200315_2359'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='import844history',
            name='import844_id',
        ),
    ]