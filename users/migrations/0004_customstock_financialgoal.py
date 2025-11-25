# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_predictedstockdata_currency'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(db_index=True, max_length=20, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('current_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('change_percent', models.DecimalField(decimal_places=2, default=0.0, max_digits=8)),
                ('stock_type', models.CharField(choices=[('penny', 'Penny Stock'), ('volatile', 'Highly Volatile'), ('stable', 'Stable Blue Chip'), ('growth', 'Growth Stock'), ('dividend', 'Dividend Stock'), ('tech', 'Tech Stock'), ('finance', 'Finance Stock'), ('energy', 'Energy Stock')], default='stable', max_length=20)),
                ('sector', models.CharField(default='General', max_length=100)),
                ('category', models.CharField(default='Mid Cap', max_length=50)),
                ('volatility', models.FloatField(default=0.02)),
                ('trend', models.CharField(default='neutral', max_length=10)),
                ('trend_strength', models.FloatField(default=0.0)),
                ('price_history', models.JSONField(blank=True, default=list)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('market_cap', models.CharField(default='N/A', max_length=50)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['symbol'],
            },
        ),
        migrations.AddIndex(
            model_name='customstock',
            index=models.Index(fields=['symbol'], name='users_custo_symbol_idx'),
        ),
        migrations.AddIndex(
            model_name='customstock',
            index=models.Index(fields=['stock_type'], name='users_custo_stock_t_idx'),
        ),
    ]

