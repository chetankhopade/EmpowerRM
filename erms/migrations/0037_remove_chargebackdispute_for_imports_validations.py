# Generated by Django 2.1.2 on 2019-11-15 11:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0036_auto_20191115_0054'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chargebackdispute',
            name='for_imports_validations',
        ),
    ]
