# Generated by Django 2.1.2 on 2020-06-24 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0069_auto_20200619_1308'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='status',
            field=models.SmallIntegerField(blank=True, choices=[(3, 'PENDING'), (1, 'ACTIVE'), (2, 'INACTIVE'), (4, 'PROPOSED')], null=True),
        ),
        migrations.AlterField(
            model_name='contractcustomer',
            name='status',
            field=models.SmallIntegerField(blank=True, choices=[(3, 'PENDING'), (1, 'ACTIVE'), (2, 'INACTIVE'), (4, 'PROPOSED')], null=True),
        ),
        migrations.AlterField(
            model_name='contractline',
            name='status',
            field=models.SmallIntegerField(blank=True, choices=[(3, 'PENDING'), (1, 'ACTIVE'), (2, 'INACTIVE'), (4, 'PROPOSED')], null=True),
        ),
        migrations.AlterField(
            model_name='contractmember',
            name='status',
            field=models.SmallIntegerField(blank=True, choices=[(3, 'PENDING'), (1, 'ACTIVE'), (2, 'INACTIVE'), (4, 'PROPOSED')], null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='status',
            field=models.SmallIntegerField(blank=True, choices=[(3, 'PENDING'), (1, 'ACTIVE'), (2, 'INACTIVE'), (4, 'PROPOSED')], default=1, null=True),
        ),
    ]
