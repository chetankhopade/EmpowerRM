# Generated by Django 2.1.2 on 2019-04-29 21:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0005_auto_20190429_2059'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributioncenter',
            name='dea_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
