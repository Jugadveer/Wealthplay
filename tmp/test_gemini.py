import os
import django
from django.conf import settings

# Setup Django if needed, but for simple test we might just import client
import os
import sys

# Add project root to sys.path
sys.path.append(r'd:\Bios')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthplay.settings')
# django.setup() # Might be slow, let's try direct import

os.environ['GEMINI_MODEL'] = 'gemini-2.0-flash-lite'
from mentor_engine.gemini_client import gemini_chat

try:
    print("Testing Gemini connection...")
    resp = gemini_chat("Hello, say 'WealthPlay is online'")
    print(f"RESPONSE: {resp}")
except Exception as e:
    print(f"TEST FAILED: {e}")
