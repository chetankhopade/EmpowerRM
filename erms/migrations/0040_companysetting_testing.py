# Generated by Django 2.1.2 on 2020-01-19 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0039_auto_20200119_1705'),
    ]

    operations = [
        migrations.AddField(
            model_name='companysetting',
            name='testing',
            field=models.BooleanField(default=False),
        ),
    ]
