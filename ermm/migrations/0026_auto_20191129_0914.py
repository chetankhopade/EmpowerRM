# Generated by Django 2.1.2 on 2019-11-29 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ermm', '0025_auto_20191124_1543'),
    ]

    operations = [
        migrations.AddField(
            model_name='view',
            name='icon',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='view',
            name='link',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='view',
            name='option',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]