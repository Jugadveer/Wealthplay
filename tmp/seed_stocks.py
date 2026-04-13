import os
import django
import sys
from decimal import Decimal
import random
from datetime import datetime, timedelta

# Setup django
sys.path.append('d:\\Bios')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthplay.settings')
django.setup()

from users.models import CustomStock

def seed_custom_stocks():
    new_stocks = [
        {"symbol": "NSYC", "name": "NeuralSync (Custom Stock)", "sector": "Technology", "category": "Mid Cap", "price": 450.50, "type": "tech"},
        {"symbol": "QFUL", "name": "QuantumFuel (Custom Stock)", "sector": "Energy", "category": "Small Cap", "price": 120.25, "type": "energy"},
        {"symbol": "BGNX", "name": "BioGenX (Custom Stock)", "sector": "Healthcare", "category": "Large Cap", "price": 890.00, "type": "growth"},
        {"symbol": "AECB", "name": "AeonCyber (Custom Stock)", "sector": "Cybersecurity", "category": "Mid Cap", "price": 320.75, "type": "tech"},
        {"symbol": "SSTR", "name": "SolarStream (Custom Stock)", "sector": "Renewables", "category": "Small Cap", "price": 85.40, "type": "energy"},
        {"symbol": "NXCR", "name": "NexusCore (Custom Stock)", "sector": "Infrastructure", "category": "Large Cap", "price": 560.10, "type": "stable"},
        {"symbol": "TRFM", "name": "TerraForma (Custom Stock)", "sector": "Environment", "category": "Mid Cap", "price": 210.30, "type": "growth"},
        {"symbol": "AMNG", "name": "AstroMining (Custom Stock)", "sector": "Space", "category": "Small Cap", "price": 750.00, "type": "volatile"},
        {"symbol": "OMVS", "name": "OmniVista (Custom Stock)", "sector": "Media", "category": "Mid Cap", "price": 145.60, "type": "dividend"},
        # Existing ones update
        {"symbol": "GGL", "name": "Giggle (Custom Stock)", "sector": "Technology", "category": "Large Cap", "price": 2800.00, "type": "tech"},
        {"symbol": "MFT", "name": "Macrosoft (Custom Stock)", "sector": "Technology", "category": "Large Cap", "price": 350.00, "type": "tech"},
        {"symbol": "AMZ", "name": "Amazing (Custom Stock)", "sector": "Commerce", "category": "Large Cap", "price": 175.00, "type": "growth"},
    ]

    for data in new_stocks:
        stock, created = CustomStock.objects.update_or_create(
            symbol=data['symbol'],
            defaults={
                'name': data['name'],
                'sector': data['sector'],
                'category': data['category'],
                'base_price': Decimal(str(data['price'])),
                'current_price': Decimal(str(data['price'])),
                'change_percent': Decimal(str(random.uniform(-2, 2))),
                'market_cap': f"₹{random.randint(100, 1000)} Cr",
                'currency': 'INR',
                'stock_type': data['type'],
                'price_history': [
                    {"date": (datetime.now() - timedelta(days=i)).isoformat(), "price": float(data['price']) * (1 + random.uniform(-0.05, 0.05))}
                    for i in range(30, 0, -1)
                ]
            }
        )
        if created:
            print(f"Created {data['symbol']}")
        else:
            print(f"Updated {data['symbol']}")

if __name__ == "__main__":
    seed_custom_stocks()
