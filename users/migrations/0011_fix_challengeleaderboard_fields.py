# Generated manually to fix ChallengeLeaderboard fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_stockpredictionquestion'),
    ]

    operations = [
        # Add created_at field
        migrations.AddField(
            model_name='challengeleaderboard',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        # Rename last_updated to updated_at
        migrations.RenameField(
            model_name='challengeleaderboard',
            old_name='last_updated',
            new_name='updated_at',
        ),
        # Make created_at non-nullable (after data migration if needed)
        migrations.AlterField(
            model_name='challengeleaderboard',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

