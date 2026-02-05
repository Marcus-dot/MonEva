
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from core.models import User

try:
    u = User.objects.get(username='admin_verify')
    u.role = 'ADMIN'
    u.save()
    print(f"Updated {u.username} role to {u.role}")
except User.DoesNotExist:
    print("User admin_verify not found")
