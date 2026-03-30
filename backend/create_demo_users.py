#!/usr/bin/env python
"""
Create demo user accounts for ZAFFICO team
Run with: python create_demo_users.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Role

User = get_user_model()

# User data: (first_name, last_name, position, role_name)
USERS = [
    ('Adern', 'Nkandela', 'General Manager', 'Administrator'),
    ('Kalobwe', 'Kashimbaya', 'Manager - HCD', 'Project Manager'),
    ('David', 'Hibajene', 'Manager - Technical Services', 'Project Manager'),
    ('Mulima', 'Matale', 'Manager - Finance', 'Project Manager'),
    ('Simon', 'Kilaka', 'Procurement', 'Project Manager'),
    ('Nawakwi', 'Mumba', 'Finance', 'Project Manager'),
    ('Naomi', 'Sitenge', 'PA', 'Viewer'),
    ('Steven', 'Mufishi', 'Project Engineer', 'Evaluator'),
    ('Samuel', 'Kunda', 'Project Engineer', 'Evaluator'),
]

DEFAULT_PASSWORD = 'MonEva2024!'  # Temporary password - users should change on first login


def generate_username(first_name, last_name):
    """Generate username from first initial + last name, lowercase"""
    return f"{first_name[0].lower()}{last_name.lower()}"


def generate_email(first_name, last_name):
    """Generate email using first.last@zaffico.co.zm pattern"""
    return f"{first_name.lower()}.{last_name.lower()}@zaffico.co.zm"


def create_users():
    print("=" * 60)
    print("Creating ZAFFICO Demo Users")
    print("=" * 60)

    # Fetch all roles
    roles = {role.name: role for role in Role.objects.all()}

    if not roles:
        print("ERROR: No roles found. Please run migrations first.")
        return

    print(f"\nAvailable roles: {list(roles.keys())}")
    print()

    created_users = []

    for first_name, last_name, position, role_name in USERS:
        username = generate_username(first_name, last_name)
        email = generate_email(first_name, last_name)

        role = roles.get(role_name)
        if not role:
            print(f"WARNING: Role '{role_name}' not found, skipping {first_name} {last_name}")
            continue

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'is_active': True,
            }
        )

        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            status = "CREATED"
        else:
            # Update existing user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.role = role
            user.save()
            status = "UPDATED"

        created_users.append({
            'name': f"{first_name} {last_name}",
            'username': username,
            'email': email,
            'position': position,
            'role': role_name,
            'status': status,
        })

        print(f"[{status}] {first_name} {last_name}")
        print(f"         Username: {username}")
        print(f"         Email: {email}")
        print(f"         Role: {role_name}")
        print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nTotal users processed: {len(created_users)}")
    print(f"Default password: {DEFAULT_PASSWORD}")
    print("\n⚠️  Users should change their password on first login!")
    print()

    # Print table for sharing
    print("-" * 60)
    print("USER CREDENTIALS TABLE (for sharing)")
    print("-" * 60)
    print(f"{'Name':<25} {'Username':<15} {'Role':<15}")
    print("-" * 60)
    for u in created_users:
        print(f"{u['name']:<25} {u['username']:<15} {u['role']:<15}")
    print("-" * 60)
    print(f"\nEmail domain: @zaffico.co.zm")
    print(f"Password: {DEFAULT_PASSWORD}")


if __name__ == '__main__':
    create_users()
