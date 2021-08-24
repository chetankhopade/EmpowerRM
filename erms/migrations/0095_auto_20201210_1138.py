# Generated by Django 3.1.2 on 2020-12-10 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0094_auto_20201210_0911'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduledreport',
            name='data_range',
            field=models.CharField(blank=True, choices=[('TD', 'Today'), ('YD', 'Yesterday'), ('LM', 'Last Month'), ('WTD', 'Week to Date'), ('MTD', 'Month to Date'), ('YTD', 'Year to Date'), ('TW', 'This Week'), ('LW', 'Last Week'), ('LY', 'Last Year'), ('LQ', 'Last Quarter'), ('QTD', 'Quarter To Date')], max_length=5, null=True),
        ),
    ]
