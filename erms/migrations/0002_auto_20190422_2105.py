# Generated by Django 2.1.2 on 2019-04-22 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chargebackdispute',
            name='dispute_code',
            field=models.CharField(blank=True, max_length=2, null=True),
        ),
    ]