# Generated by Django 2.1.2 on 2019-08-02 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ermm', '0015_auto_20190628_2350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directcustomer',
            name='type',
            field=models.SmallIntegerField(blank=True, choices=[(1, 'Distributor'), (2, 'GPO'), (3, 'Buying Group'), (4, 'Parent')], null=True),
        ),
    ]
