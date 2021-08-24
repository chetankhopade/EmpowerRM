# Generated by Django 2.1.2 on 2019-05-02 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0009_auto_20190430_1235'),
    ]

    operations = [
        migrations.AddField(
            model_name='directcustomer',
            name='is_big3',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='contract',
            name='eligibility',
            field=models.SmallIntegerField(blank=True, choices=[(0, 'NONE'), (1, 'GPO DRIVEN (BASE)'), (2, 'SUPPLIER DRIVEN'), (3, 'SUPPLIER LOC'), (4, 'INDIVIDUAL'), (5, 'BLANKET')], null=True),
        ),
    ]
