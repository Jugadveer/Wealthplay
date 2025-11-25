# Generated manually to fix missing timeline, streak, and last_activity_date columns
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_add_risk_tolerance_to_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='timeline',
            field=models.CharField(blank=True, choices=[('less_than_1', 'Less than 1 year'), ('1_to_5', '1-5 years'), ('5_plus', '5+ years')], max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='streak',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='last_activity_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]

