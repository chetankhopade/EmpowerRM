# Generated by Django 2.1.2 on 2019-09-10 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0029_auto_20190909_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='companysetting',
            name='generate_transaction_number',
            field=models.BooleanField(default=False),
        ),
    ]
