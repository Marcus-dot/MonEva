
import os
import django
import sys
from datetime import date

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from projects.models import Project
from indicators.models import Indicator
from assessments.models import Inspection, Milestone
from django.contrib.auth import get_user_model

User = get_user_model()

def verify_strategy():
    print("🚀 Verifying Strategic Architecture Upgrade...\n")
    try:
        # 1. Project with Moonlight Strategy
        print("1️⃣  Creating Strategic Project (Moonlight)...")
        from core.models import Organization
        org, _ = Organization.objects.get_or_create(name="Strategic Ministry", defaults={'type': 'GOVERNMENT'})
        
        project = Project.objects.create(
            name="KGLCDC Community Borehole",
            type="CSR",
            status="ACTIVE",
            thematic_area="WASH",  # New Field
            primary_kra="SOCIO_ECONOMIC", # New Field
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_org=org # Dynamic
        )
        print(f"   ✅ Project Created: {project.name}")
        print(f"      Theme: {project.thematic_area}")
        print(f"      KRA: {project.primary_kra}\n")

        # 2. Indicator with RBM Level (Daylight)
        print("2️⃣  Creating Outcome Indicator (Daylight)...")
        indicator = Indicator.objects.create(
            name="Reduction in Waterborne Diseases",
            level="OUTCOME", # New Field
            unit_type="PERCENTAGE",
            direction="DECREASING",
            disaggregation=["Gender", "Age Group"] # New Field
        )
        print(f"   ✅ Indicator Created: {indicator.name}")
        print(f"      Level: {indicator.level}")
        print(f"      Disaggregation: {indicator.disaggregation}\n")

        # 3. Inspection with I-CARE Compliance
        print("3️⃣  Logging Inspection with I-CARE Values...")
        # Need a milestone first
        # Hack: just grab first milestone or create dummy
        from projects.models import Contract, Milestone
        # ... assuming Contract/Organisation setup exists from previous runs ...
        # For robustness, let's create a dummy contract/milestone linked to our project
        from core.models import Organization
        org, _ = Organization.objects.get_or_create(name="Strategic Contractor")
        contract = Contract.objects.create(
            project=project,
            contractor=org,
            total_value=1000,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )
        milestone = Milestone.objects.create(
            contract=contract,
            title="Drilling Complete",
            target_percent=100,
            value_amount=1000,
            due_date=date(2026, 6, 1)
        )

        inspection = Inspection.objects.create(
            milestone=milestone,
            inspected_at="2026-06-01T10:00:00Z",
            quality_verdict="PASS",
            icare_compliance={
                "innovation": True,
                "community_centric": True,
                "accountability": True,
                "respect": True,
                "excellence": True
            } # New Field
        )
        print(f"   ✅ Inspection Logged for: {milestone.title}")
        print(f"      I-CARE Compliance: {inspection.icare_compliance}\n")

        print("🎉 STRATEGIC UPGRADE VERIFIED!")

    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_strategy()
