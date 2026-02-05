import os
import django
import sys
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Organization
from projects.models import Project

User = get_user_model()

def verify_journey():
    client = APIClient()
    
    print("1. Creating Users and Orgs...")
    # Create Admin
    admin_user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com', 'role': 'ADMIN'})
    client.force_authenticate(user=admin_user)
    
    # Create Organization
    org = Organization.objects.create(name="Ministry of Works", type="OWNER")
    contractor_org = Organization.objects.create(name="BuildIt Construction", type="CONTRACTOR")
    print(f"   Created Org: {org.name}")

    print("\n2. Creating Project via API...")
    project_data = {
        "name": "Highway 101 Expansion",
        "type": "ROAD",
        "start_date": "2024-01-01",
        "end_date": "2025-01-01",
        "owner_org": org.id,
        "location": {"type": "Point", "coordinates": [28.2, -15.4]}
    }
    response = client.post('/api/v1/projects/', project_data, format='json')
    if response.status_code != 201:
        print(f"FAILED: {response.data}")
        return
    project_id = response.data['id']
    print(f"   Success! Project ID: {project_id}")

    print("\n3. Creating Contract & Milestone...")
    contract_data = {
        "project": project_id,
        "contractor": contractor_org.id,
        "total_value": "1000000.00",
        "start_date": "2024-02-01",
        "end_date": "2025-01-01"
    }
    contract_res = client.post('/api/v1/contracts/', contract_data, format='json')
    contract_id = contract_res.data['id']
    
    milestone_data = {
        "contract": contract_id,
        "title": "Foundation Complete",
        "target_percent": "10.00",
        "value_amount": "100000.00",
        "due_date": "2024-03-01"
    }
    milestone_res = client.post('/api/v1/milestones/', milestone_data, format='json')
    milestone_id = milestone_res.data['id']
    print(f"   Success! Milestone '{milestone_res.data['title']}' created.")

    print("\n4. Submitting Inspection...")
    inspection_data = {
        "milestone": milestone_id,
        "inspector": admin_user.id,
        "inspected_at": "2024-03-02T10:00:00Z",
        "quality_verdict": "PASS",
        "form_data": {"checklist_1": True, "notes": "Looks solid."}
    }
    inspection_res = client.post('/api/v1/inspections/', inspection_data, format='json')
    print(f"   Inspection Result: {inspection_res.status_code}")
    if inspection_res.status_code == 201:
        print("   ✅ Full Flow Verified Successfully!")
    else:
        print(f"   ❌ Inspection Failed: {inspection_res.data}")

if __name__ == "__main__":
    verify_journey()
