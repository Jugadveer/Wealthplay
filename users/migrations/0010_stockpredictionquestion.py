# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_add_timeline_streak_to_userprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockPredictionQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stock_name', models.CharField(max_length=200)),
                ('stock_symbol', models.CharField(max_length=20, unique=True)),
                ('question', models.TextField()),
                ('chart_data', models.JSONField(default=list)),
                ('expected_direction', models.CharField(choices=[('up', 'Upward Trend'), ('down', 'Downward Trend'), ('neutral', 'Neutral/Flat')], default='neutral', max_length=10)),
                ('expected_keywords', models.JSONField(default=list)),
                ('explanation', models.TextField()),
                ('base_score', models.IntegerField(default=10)),
                ('max_score', models.IntegerField(default=20)),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], default='medium', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

