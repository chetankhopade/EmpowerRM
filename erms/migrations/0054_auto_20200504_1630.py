# Generated by Django 2.1.2 on 2020-05-04 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0053_auto_20200504_1622'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classoftrade',
            name='group',
            field=models.SmallIntegerField(blank=True, choices=[(1, 'GOVERNMENT'), (2, 'DISTRIBUTION'), (3, 'PROVIDERS'), (4, 'RESIDENTIAL'), (5, 'NON-RETAIL PHARMACY'), (6, 'RETAIL PHARMACY'), (7, 'OTHER PURCHASERS'), (8, 'PAYERS')], null=True),
        ),
    ]