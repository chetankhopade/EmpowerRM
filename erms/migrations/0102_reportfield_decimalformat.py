# Generated by Django 3.1.1 on 2021-02-04 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0101_auto_20210129_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportfield',
            name='decimalformat',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]