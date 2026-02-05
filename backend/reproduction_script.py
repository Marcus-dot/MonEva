
import os
import django
import sys
import datetime
from decimal import Decimal

# Setup Django
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from django.contrib.auth import get_user_model
from finance.serializers import PaymentClaimSerializer
from finance.models import PaymentClaim
from projects.models import Contract, Project, Milestone
from core.models import Organization

User = get_user_model()

def run():
    # 1. Get or Create User
    user, _ = User.objects.get_or_create(username='test_pm', defaults={'role': 'PROJECT_MANAGER', 'email': 'pm@example.com'})
    
    # 2. Get Data or Create
    org, _ = Organization.objects.get_or_create(name="Test Org", defaults={"type": "GOVERNMENT"})
    contractor_org, _ = Organization.objects.get_or_create(name="Test Contractor Org", defaults={"type": "CONTRACTOR"})

    project = Project.objects.first()
    if not project:
         project = Project.objects.create(
             name="Test Project", 
             status="ACTIVE", 
             location={"lat": 0, "lng": 0},
             owner_org=org,
             start_date="2026-01-01",
             end_date="2026-12-31",
             type="ROAD"
         )
    
    contract = Contract.objects.filter(project=project).first()
    if not contract:
        contract = Contract.objects.create(
            project=project, 
            contractor=contractor_org, 
            total_value=100000, 
            start_date="2026-01-01", 
            end_date="2026-12-31"
        )

    milestone = Milestone.objects.filter(contract=contract).first()
    if not milestone:
        milestone = Milestone.objects.create(
            contract=contract,
            title="Test Milestone",
            description="Test",
            target_percent=10,
            value_amount=1000,
            due_date="2026-06-01",
            status="PENDING"
        )
    
    print(f"Testing with Contract: {contract.id}, Milestone: {milestone.id}")
    
    # 3. Simulate Payload
    payload = {
        "contract": str(contract.id),
        "milestones": [str(milestone.id)],
        "amount": "1234.56",
        "claim_date": "2026-02-01",
        "description": "Test Claim from Script",
        "status": "DRAFT"
    }
    
    # 4. Serialize
    print("\n--- Testing Serializer ---")
    from rest_framework.test import APIRequestFactory
    factory = APIRequestFactory()
    request = factory.post('/api/v1/claims/')
    request.user = user
    
    serializer = PaymentClaimSerializer(data=payload, context={'request': request})
    
    if serializer.is_valid():
        print("Serializer IS VALID.")
        # Verify save (M2M handling)
        try:
             # Just like ViewSet perform_create
             claim = serializer.save(prepared_by=user, status="DRAFT")
             print(f"Claim created: {claim.id}")
             print(f"Claim Milestones: {claim.milestones.all()}")
        except Exception as e:
             import traceback
             traceback.print_exc()
             print(f"Save Failed: {e}")
    else:
        print("Serializer INVALID.")
        print(serializer.errors)

if __name__ == '__main__':
    run()
