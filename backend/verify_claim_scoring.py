import os
import sys
import django

# Setup Django Environment
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from core.models import User, Organization
from projects.models import Project, Contract, Milestone
from finance.models import PaymentClaim
from django.utils import timezone

def run_test():
    print("--- Starting Claim Risk Scoring Test ---")
    
    # Setup Data
    user, _ = User.objects.get_or_create(username='test_ml_finance', defaults={'role': 'PROJECT_MANAGER'})
    org, _ = Organization.objects.get_or_create(name="ML Finance Org", defaults={'type': 'CONTRACTOR'})
    
    project, _ = Project.objects.get_or_create(
        name="ML Finance Project", 
        defaults={
            'owner_org': org, 
            'start_date': timezone.now(), 
            'end_date': timezone.now(),
            'type': 'ROAD'
        }
    )

    contract, _ = Contract.objects.get_or_create(
        project=project, 
        contractor=org, 
        defaults={
            'total_value': 100000, 
            'start_date': timezone.now(), 
            'end_date': timezone.now()
        }
    )

    # 1. Create a High Risk Claim (Draft)
    # Amount > 50% of contract (Ratio Check)
    # Amount large (Heuristic)
    print("\n1. creating High Risk Claim (Draft)...")
    claim = PaymentClaim.objects.create(
        contract=contract,
        amount=60000, # 60% of contract
        claim_date=timezone.now(),
        prepared_by=user,
        description="High risk test claim",
        status='DRAFT'
    )
    
    print(f"   Created Claim {claim.id}. Current Risk Score: {claim.risk_score}")
    assert claim.risk_score is None

    # 2. Submit Claim (Trigger Signal)
    print("\n2. Submitting Claim (Triggering ML)...")
    claim.status = 'SUBMITTED'
    claim.save()
    
    # 3. reload
    claim.refresh_from_db()
    print(f"   Claim Status: {claim.status}")
    print(f"   Risk Score: {claim.risk_score}")
    print(f"   Risk Factors: {claim.risk_factors}")

    if claim.risk_score and claim.risk_score > 0:
        print("   PASSED: Risk Score calculated.")
    else:
        print("   FAILED: Risk Score missing or zero.")

if __name__ == "__main__":
    run_test()
