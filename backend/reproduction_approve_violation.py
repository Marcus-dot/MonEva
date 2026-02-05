
import os
import django
import sys

# Setup Django
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from django.contrib.auth import get_user_model
from finance.serializers import PaymentClaimSerializer
from finance.models import PaymentClaim
from projects.models import Contract, Project, Milestone
from core.models import Organization
from rest_framework.request import Request
from rest_framework.exceptions import PermissionDenied, ValidationError

User = get_user_model()

def run():
    print("--- Simulating Maker-Checker Violation ---")
    
    # 1. Setup Maker User
    maker, _ = User.objects.get_or_create(username='violation_maker', defaults={'role': 'PROJECT_MANAGER'})
    maker.role = 'PROJECT_MANAGER' # Ensure role
    maker.save()
    
    # 2. Setup Data
    org, _ = Organization.objects.get_or_create(name="Test Org Vi", defaults={"type": "GOVERNMENT"})
    project, _ = Project.objects.get_or_create(name="Violation Project", defaults={"start_date": "2026-01-01", "end_date": "2026-12-31", "owner_org": org, "type": "ROAD"})
    contract, _ = Contract.objects.get_or_create(project=project, defaults={"total_value": 10000, "start_date": "2026-01-01", "end_date": "2026-12-31", "contractor": org})
    
    # 3. Create Claim (Prepared by Maker)
    claim = PaymentClaim.objects.create(
        contract=contract, 
        amount=500, 
        claim_date="2026-02-01", 
        status="SUBMITTED",
        prepared_by=maker
    )
    print(f"Claim {claim.id} prepared by {maker.username}. Status: {claim.status}")

    # 4. Attempt Approve by SAME Maker
    from rest_framework.test import APIRequestFactory
    factory = APIRequestFactory()
    request = factory.patch(f'/api/v1/claims/{claim.id}/')
    request.user = maker # <--- SAME USER
    
    # Mocking ViewSet logic which calls perform_update
    # We need to simulate the ViewSet because validation logic for Maker-Checker is in perform_update or serializer? 
    # Let's check serializer first.
    # Logic: "validate_status" checks roles. 
    # But "perform_update" in ViewSet checks the specific "Maker != Checker" constraint.
    
    print(f"\nAttempting Approval by {maker.username}...")
    
    try:
        serializer = PaymentClaimSerializer(claim, data={"status": "APPROVED"}, partial=True, context={'request': request})
        if serializer.is_valid():
            # Mimic ViewSet.perform_update logic
            instance = serializer.instance
            new_status = serializer.validated_data.get('status')
            
            if new_status == 'APPROVED' and instance.status != 'APPROVED':
                 if instance.prepared_by == request.user:
                     print("!!! CAUGHT ERROR !!!")
                     print("PermissionDenied: Maker-Checker Violation: You cannot approve a claim you prepared.")
                     return

            serializer.save()
            print("ERROR: Approval Succeeded (Should have failed!)")
        else:
            print("Serializer Invalid:")
            print(serializer.errors)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == '__main__':
    run()
