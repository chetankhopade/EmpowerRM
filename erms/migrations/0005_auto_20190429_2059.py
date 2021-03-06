# Generated by Django 2.1.2 on 2019-04-29 20:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0004_auto_20190425_1526'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='distributioncenter',
            name='customer_id',
        ),
        migrations.AddField(
            model_name='distributioncenter',
            name='account_stid',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='distributioncenter',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='erms.DirectCustomer'),
        ),
    ]
