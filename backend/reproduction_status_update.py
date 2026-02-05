
import os
import django
import sys
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
    # 1. Setup Data
    user, _ = User.objects.get_or_create(username='test_pm', defaults={'role': 'PROJECT_MANAGER', 'email': 'pm@example.com'})
    # Ensure role is PM
    user.role = 'PROJECT_MANAGER'
    user.save()

    # Create dummy claim if needed
    org, _ = Organization.objects.get_or_create(name="Test Org", defaults={"type": "GOVERNMENT"})
    contractor, _ = Organization.objects.get_or_create(name="Test Contractor", defaults={"type": "CONTRACTOR"})
    
    project, _ = Project.objects.get_or_create(name="Test Project", defaults={"start_date": "2026-01-01", "end_date": "2026-12-31", "owner_org": org, "type": "ROAD"})
    contract, _ = Contract.objects.get_or_create(project=project, defaults={"total_value": 10000, "start_date": "2026-01-01", "end_date": "2026-12-31", "contractor": contractor})
    claim = PaymentClaim.objects.create(
        contract=contract, 
        amount=500, 
        claim_date="2026-02-01", 
        status="DRAFT",
        prepared_by=user
    )

    print(f"Testing Update for Claim {claim.id} (Status: {claim.status})")

    # 2. Simulate Payload: Submit for Approval
    payload = {"status": "SUBMITTED"}
    
    # 3. Serialize Update
    print("\n--- Testing Serializer Update ---")
    from rest_framework.test import APIRequestFactory
    factory = APIRequestFactory()
    request = factory.patch(f'/api/v1/claims/{claim.id}/')
    request.user = user
    
    # Partial update
    serializer = PaymentClaimSerializer(claim, data=payload, partial=True, context={'request': request})
    
    if serializer.is_valid():
        print("Serializer IS VALID.")
        updated_claim = serializer.save()
        print(f"New Status: {updated_claim.status}")
    else:
        print("Serializer INVALID.")
        print(serializer.errors)

if __name__ == '__main__':
    run()
