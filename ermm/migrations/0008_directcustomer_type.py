# Generated by Django 2.1.2 on 2019-04-30 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ermm', '0007_auto_20190430_1014'),
    ]

    operations = [
        migrations.AddField(
            model_name='directcustomer',
            name='type',
            field=models.SmallIntegerField(blank=True, choices=[(1, 'Distributor'), (2, 'GPO'), (3, 'Buying'), (4, 'Group'), (5, 'Parent')], null=True),
        ),
    ]
