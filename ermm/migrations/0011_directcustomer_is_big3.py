# Generated by Django 2.1.2 on 2019-05-02 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ermm', '0010_auto_20190430_2250'),
    ]

    operations = [
        migrations.AddField(
            model_name='directcustomer',
            name='is_big3',
            field=models.BooleanField(default=False),
        ),
    ]
