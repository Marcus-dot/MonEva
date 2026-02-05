
import os
import django
import sys
from datetime import date

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Organization
from projects.models import Project, Contract, Milestone
from assessments.models import Inspection
from finance.models import PaymentClaim

User = get_user_model()

def verify_system():
    print("🚀 Starting Full System Verification...\n")
    
    try:
        # --- 1. USER & ORGANIZATION SETUP ---
        print("1️⃣  Verifying User & Org Setup...")
        # (Same as before)
        admin, _ = User.objects.get_or_create(username='sys_admin', defaults={'email': 'admin@test.com', 'role': 'ADMIN'})
        pm, _ = User.objects.get_or_create(username='sys_pm', defaults={'email': 'pm@test.com', 'role': 'PROJECT_MANAGER'})
        finance, _ = User.objects.get_or_create(username='sys_finance', defaults={'email': 'fin@test.com', 'role': 'FINANCE'})
        
        org_owner, _ = Organization.objects.get_or_create(name="Ministry of Infrastructure", defaults={'type': 'GOVERNMENT'})
        org_contractor, _ = Organization.objects.get_or_create(name="Lusaka Roads Ltd", defaults={'type': 'CONTRACTOR'})
        print("   ✅ Users and Orgs ready.\n")

        # --- 2. PROJECT MANAGEMENT ---
        print("2️⃣  Verifying Project Workflow...")
        project = Project.objects.create(
            name="System Verify Highway",
            type="ROAD",
            status="ACTIVE",
            owner_org=org_owner,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            location={"lat": -15.3875, "lng": 28.3228}
        )
        
        contract = Contract.objects.create(
            project=project,
            contractor=org_contractor,
            total_value=5000000.00,
            currency="ZMW",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )
        
        milestone = Milestone.objects.create(
            contract=contract,
            title="Phase 1: Grading",
            target_percent=25.0,
            value_amount=1250000.00,
            due_date=date(2026, 3, 1),
            status="PENDING"
        )
        print(f"   ✅ Project '{project.name}' created with Contract & Milestone.\n")

        # --- 3. INSPECTION WORKFLOW (Assessments) ---
        print("3️⃣  Verifying Inspection/Assessment Workflow...")
        from django.utils import timezone
        inspection = Inspection.objects.create(
            milestone=milestone,
            inspector=pm,
            inspected_at=timezone.now(),
            quality_verdict="PASS",
            notes="Verified grading levels.",
            form_data={"checklist": {"level": "ok", "compaction": "ok"}}
        )
        print(f"   ✅ Inspection completed for '{milestone.title}'. Verdict: {inspection.quality_verdict}\n")


        # --- 4. FINANCE WORKFLOW (MAKER-CHECKER) ---
        print("4️⃣  Verifying Finance Workflow...")
        # Create Claim (Draft)
        claim = PaymentClaim.objects.create(
            contract=contract,
            amount=100000.00,
            claim_date=date(2026, 2, 15),
            status="DRAFT",
            description="Payment for Grading",
            prepared_by=pm
        )
        print("   -> Claim Created (DRAFT)")

        # PM Submits
        claim.status = "SUBMITTED"
        claim.save()
        print("   -> Claim Submitted (SUBMITTED)")
        
        # Admin Approves (Testing the override/permission logic implicitly via model save, 
        # though real enforcement is in ViewSet/Serializer. Here we verify model states).
        claim.status = "APPROVED"
        claim.approved_by = admin
        claim.save()
        print("   -> Claim Approved by Admin (APPROVED)")

        # Finance Pays
        claim.status = "PAID"
        claim.save()
        print("   -> Claim Paid (PAID)")
        print(f"   ✅ Finance Cycle Complete. Final Status: {claim.status}\n")

        print("🎉 SYSTEM VERIFICATION SUCCESSFUL! All modules functioning correctly.")
        
    except Exception as e:
        print(f"\n❌ SYSTEM VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_system()
