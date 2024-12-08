# Generated by Django 2.1.5 on 2024-11-10 18:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('policy_analysis', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='privacypolicyhistory',
            options={},
        ),
        migrations.RenameField(
            model_name='trackedsite',
            old_name='created_at',
            new_name='date_added',
        ),
        migrations.RemoveField(
            model_name='trackedsite',
            name='last_scraped',
        ),
        migrations.AlterField(
            model_name='privacypolicyhistory',
            name='tracked_site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='policy_analysis.TrackedSite'),
        ),
    ]
