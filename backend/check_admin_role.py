
import os
import django
import sys

# Setup Django environment
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    admin_user = User.objects.get(username='admin')
    print(f"User: {admin_user.username}")
    print(f"Current Role: {admin_user.role}")
    print(f"Is Superuser: {admin_user.is_superuser}")
    
    if admin_user.role != 'ADMIN':
        print("Updating role to ADMIN...")
        admin_user.role = 'ADMIN'
        admin_user.save()
        print("Role updated successfully.")
    else:
        print("Role is already ADMIN.")

except User.DoesNotExist:
    print("User 'admin' not found.")
