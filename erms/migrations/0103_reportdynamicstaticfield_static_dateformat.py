# Generated by Django 3.1.1 on 2021-02-18 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0102_reportfield_decimalformat'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportdynamicstaticfield',
            name='static_dateformat',
            field=models.CharField(default='%m/%d/%Y', max_length=100),
        ),
    ]
