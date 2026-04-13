from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='demoportfolio',
            name='trade_history',
            field=models.JSONField(blank=True, default=list),
        ),
    ]