# Generated by Django 4.2.17 on 2024-12-07 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('policy_analysis', '0012_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='trackedsite',
            name='privacy_policy_history',
            field=models.JSONField(default=list),
        ),
    ]
