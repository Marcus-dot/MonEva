
import os
import django
import sys

sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

def setup():
    # 1. Maker (Project Manager)
    maker, created = User.objects.get_or_create(username='e2e_maker', defaults={'email': 'maker@example.com', 'role': 'PROJECT_MANAGER'})
    maker.set_password('password123')
    maker.role = 'PROJECT_MANAGER'
    maker.save()
    print(f"User 'e2e_maker' setup. (Created: {created})")

    # 2. Checker (Finance)
    checker, created = User.objects.get_or_create(username='e2e_checker', defaults={'email': 'checker@example.com', 'role': 'FINANCE'})
    checker.set_password('password123')
    checker.role = 'FINANCE'
    checker.save()
    print(f"User 'e2e_checker' setup. (Created: {created})")

if __name__ == '__main__':
    setup()
