# Generated by Django 2.1.2 on 2019-04-30 10:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0006_auto_20190429_2102'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='distributioncenter',
            name='account_stid',
        ),
    ]
