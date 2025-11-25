# Generated manually to fix missing risk_tolerance column
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_customstock_financialgoal'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='risk_tolerance',
            field=models.CharField(blank=True, choices=[('safe', 'Play it safe'), ('balanced', 'Balanced approach'), ('aggressive', 'Higher returns, higher risk')], max_length=20),
        ),
    ]

