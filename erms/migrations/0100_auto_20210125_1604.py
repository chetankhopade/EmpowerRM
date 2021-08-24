# Generated by Django 3.1.1 on 2021-01-25 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erms', '0099_auto_20210125_1243'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='auditchargeback',
            name='cb_audit_user_email',
        ),
        migrations.RenameField(
            model_name='auditchargeback',
            old_name='user_mail',
            new_name='user_email',
        ),
        migrations.AddIndex(
            model_name='auditchargeback',
            index=models.Index(fields=['user_email'], name='cb_audit_user_email'),
        ),
    ]