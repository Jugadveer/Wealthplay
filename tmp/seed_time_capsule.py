import os
import django
import sys
from datetime import date
from decimal import Decimal

# Setup django
sys.path.append('d:\\Bios')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthplay.settings')
django.setup()

from users.models import HistoricalCrisis, HistoricalNews

def seed_time_capsule():
    HistoricalCrisis.objects.all().delete()
    
    # 2008 Crisis
    subprime = HistoricalCrisis.objects.create(
        name="The 2008 Subprime Collapse",
        slug="subprime-2008",
        description="Witness the collapse of Lehman Brothers and the global financial meltdown.",
        start_date=date(2008, 9, 1),
        end_date=date(2009, 3, 31),
        initial_balance=Decimal("50000.00"),
        difficulty="Insane",
        icon="flame",
        narrative_intro="The housing bubble has burst. Banks are freezing. The world economy is on the brink of total collapse.",
        recovery_period_months=24
    )
    
    HistoricalNews.objects.create(
        crisis=subprime,
        relative_day=14,
        headline="Lehman Brothers Files for Bankruptcy",
        impact_description="The 158-year-old firm collapses. Panic spreads through Wall Street.",
        sentiment="panic"
    )
    HistoricalNews.objects.create(
        crisis=subprime,
        relative_day=30,
        headline="AIG Receives $85 Billion Bailout",
        impact_description="The government steps in to prevent systemic failure, but markets continue to slide.",
        sentiment="bearish"
    )
    HistoricalNews.objects.create(
        crisis=subprime,
        relative_day=180,
        headline="Market Hits 'Generational Bottom'",
        impact_description="Indices are down 50% from highs. Fear is at an all-time high, but the tide may be turning.",
        sentiment="bullish"
    )

    # 2020 Pivot
    covid = HistoricalCrisis.objects.create(
        name="The 2020 Pandemic Pivot",
        slug="covid-2020",
        description="A black swan event like no other. Trade through the fastest crash in history.",
        start_date=date(2020, 2, 14),
        end_date=date(2020, 6, 1),
        initial_balance=Decimal("50000.00"),
        difficulty="Hard",
        icon="alert-circle",
        narrative_intro="A global pandemic has shut down the world. Supply chains are broken. Humans are in lockdown.",
        recovery_period_months=6
    )
    
    HistoricalNews.objects.create(
        crisis=covid,
        relative_day=10,
        headline="Italy Declares National Lockdown",
        impact_description="Europe becomes the epicenter. Travel stocks begin a vertical descent.",
        sentiment="panic"
    )
    HistoricalNews.objects.create(
        crisis=covid,
        relative_day=26,
        headline="WHO Declares Global Pandemic",
        impact_description="The S&P 500 triggers multiple circuit breakers. Limit down across the board.",
        sentiment="panic"
    )
    HistoricalNews.objects.create(
        crisis=covid,
        relative_day=45,
        headline="Fed Announces 'Unlimited' QE",
        impact_description="The Federal Reserve pledges to print whatever it takes. Tech starts to rally.",
        sentiment="bullish"
    )

    # Dot Com
    dotcom = HistoricalCrisis.objects.create(
        name="The 2000 Dot-Com Bust",
        slug="dotcom-2000",
        description="The internet euphoria ends. Watch 'Paper Millionaires' turn into paupers.",
        start_date=date(2000, 3, 1),
        end_date=date(2002, 10, 1),
        initial_balance=Decimal("50000.00"),
        difficulty="Moderate",
        icon="zap",
        narrative_intro="Pets.com was worth millions yesterday. Today, internet stocks are being valued at zero.",
        recovery_period_months=60
    )
    
    print(f"Seeded {HistoricalCrisis.objects.count()} crises and {HistoricalNews.objects.count()} news events.")

if __name__ == "__main__":
    seed_time_capsule()
