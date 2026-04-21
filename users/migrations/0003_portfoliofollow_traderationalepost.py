from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_demopportfolio_trade_history'),
    ]

    operations = [
        migrations.CreateModel(
            name='TradeRationalePost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=20)),
                ('action', models.CharField(choices=[('BUY', 'Buy'), ('SELL', 'Sell'), ('HOLD', 'Hold')], max_length=4)),
                ('rationale', models.CharField(max_length=140)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trade_rationale_posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PortfolioFollow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('followed_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio_followers', to=settings.AUTH_USER_MODEL)),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio_following', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='traderationalepost',
            index=models.Index(fields=['author', 'created_at'], name='users_trade_author__edfdd1_idx'),
        ),
        migrations.AddIndex(
            model_name='traderationalepost',
            index=models.Index(fields=['symbol', 'created_at'], name='users_trade_symbol_16fd0f_idx'),
        ),
        migrations.AddIndex(
            model_name='portfoliofollow',
            index=models.Index(fields=['follower', 'followed_user'], name='users_portf_followe_351186_idx'),
        ),
        migrations.AddIndex(
            model_name='portfoliofollow',
            index=models.Index(fields=['followed_user', 'created_at'], name='users_portf_followe_1b37b5_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='portfoliofollow',
            unique_together={('follower', 'followed_user')},
        ),
    ]
