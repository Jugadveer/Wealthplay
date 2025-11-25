# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_fix_challengeleaderboard_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='challengeleaderboard',
            name='stock_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='challengeleaderboard',
            name='scenario_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='challengeleaderboard',
            name='scenario_attempts',
            field=models.IntegerField(default=0),
        ),
    ]
