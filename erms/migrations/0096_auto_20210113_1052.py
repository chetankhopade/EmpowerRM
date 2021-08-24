# Generated by Django 3.1.2 on 2021-01-13 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0095_auto_20201210_1138'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportfield',
            name='dateformat',
            field=models.CharField(default='%m/%d/%Y', max_length=100),
        ),
        migrations.AddField(
            model_name='reportfield',
            name='field_data_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='reportfield',
            name='is_currency',
            field=models.BooleanField(default=False),
        ),
    ]