
import os
import django
import sys
import json
import base64
from datetime import datetime

# Setup Django environment
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    user = User.objects.get(username='admin')
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    print(f"\nAccess Token Generated")
    
    # manual decode to verify exp
    payload_part = access_token.split('.')[1]
    # padding
    payload_part += '=' * (-len(payload_part) % 4)
    payload = json.loads(base64.b64decode(payload_part))
    
    exp_timestamp = payload.get('exp')
    exp_dt = datetime.fromtimestamp(exp_timestamp)
    now_dt = datetime.now()
    
    diff = exp_dt - now_dt
    print(f"Token Expiry: {exp_dt}")
    print(f"Current Time: {now_dt}")
    print(f"Duration (approx): {diff}")
    
    if diff.total_seconds() > 3000: # greater than 50 minutes
        print("PASS: Token duration > 50 minutes")
    else:
        print(f"FAIL: Token duration is {diff.total_seconds()} seconds")

except Exception as e:
    print(f"Error: {e}")
