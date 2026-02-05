import requests
import json
import os

import sys
import django

# Setup Django
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from django.contrib.auth import get_user_model

BASE_URL = 'http://127.0.0.1:8000/api/v1'

def run():
    print("🚀 simulating Mobile I-CARE Submission...")

    # 0. Ensure User Exists
    User = get_user_model()
    username = 'mobile_tester@example.com'
    password = 'password123'
    if not User.objects.filter(email=username).exists():
        print(f"👤 Creating test user: {username}")
        User.objects.create_user(email=username, username=username, password=password, role='INSPECTOR')
    else:
        print(f"👤 Test user exists: {username}")

    # 1. Login (Get Token)
    print("🔑 Logging in...")
    auth_resp = requests.post(f"{BASE_URL}/auth/token/", json={
        'username': username, 
        'password': password
    })
    
    if auth_resp.status_code != 200:
        print(f"❌ Login failed: {auth_resp.text}")
        # Try creating user if fails? No, assume setup is done.
        return 

    token = auth_resp.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Logged in.")

    # 2. Get a Milestone to inspect
    print("🔍 Fetching Milestones...")
    # First get a project
    proj_resp = requests.get(f"{BASE_URL}/projects/", headers=headers)
    projects = proj_resp.json()
    if not projects:
        print("❌ No projects found.")
        return
    
    project_id = projects[0]['id']
    
    milestone_resp = requests.get(f"{BASE_URL}/milestones/?project={project_id}", headers=headers)
    milestones = milestone_resp.json()
    
    if not milestones:
        print("❌ No milestones found.")
        # Create one?
        return

    milestone_id = milestones[0]['id']
    print(f"✅ Found Milestone: {milestones[0]['title']}")

    # 3. Submit Inspection with I-CARE data
    print("📝 Submitting Inspection with I-CARE Payload...")
    
    icare_data = {
        "integrity": True,
        "community": True,
        "accountability": True,
        "respect": True,
        "excellence": False # Intentionally false to verify
    }

    payload = {
        'milestone': milestone_id,
        'quality_verdict': 'PASS',
        'notes': 'Simulated Mobile Inspection from Python Script',
        'inspected_at': '2026-02-01T12:00:00Z',
        'icare_compliance': json.dumps(icare_data) # Send as JSON string as per Mobile Logic
    }

    # Multipart request
    resp = requests.post(f"{BASE_URL}/inspections/", headers=headers, data=payload)
    
    if resp.status_code == 201:
        print("✅ Inspection Created Successfully!")
        data = resp.json()
        print(f"🆔 Inspection ID: {data['id']}")
        print(f"❤️ I-CARE Compliance Saved: {data.get('icare_compliance')}")
        
        # Verify persistence
        if data.get('icare_compliance', {}).get('excellence') is False:
             print("✅ I-CARE Data Verified Correctly.")
        else:
             print("⚠️ Warning: I-CARE Data mismatch.")
    else:
        print(f"❌ Failed to create inspection: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    run()
