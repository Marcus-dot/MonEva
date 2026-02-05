import random
import uuid
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from core.models import Organization, Role
from projects.models import Project, Contract, Milestone
from indicators.models import Indicator, IndicatorTarget, IndicatorResult
from finance.models import PaymentClaim
from grievances.models import Grievance
from investigations.models import Investigation
from assessments.models import Inspection, Evidence

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds 5 years of historical data for Zambia (2021-2026)'

    def handle(self, *args, **options):
        self.stdout.write("Starting data seed for Zambia (2021-2026)...")
        
        try:
            with transaction.atomic():
                self.seed_data()
            self.stdout.write(self.style.SUCCESS("Successfully seeded 5 years of data!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Seed failed: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())

    def seed_data(self):
        # 1. Setup Provinces and Towns for Zambia
        provinces = {
            'Lusaka': [(-15.4167, 28.2833), (-15.7667, 28.5167), (-15.4000, 28.1667)],
            'Copperbelt': [(-12.9667, 28.6333), (-12.8000, 28.2000), (-13.1167, 28.1167)],
            'Central': [(-14.4500, 28.4500), (-14.2833, 28.0000), (-14.9833, 28.1833)],
            'Southern': [(-17.8500, 25.8667), (-16.3000, 27.0000), (-16.1167, 27.7000)],
            'Eastern': [(-13.6333, 32.6500), (-14.1333, 31.3333), (-13.0000, 32.1333)],
            'Northern': [(-10.2167, 31.1833), (-9.3333, 30.4167), (-8.8333, 30.5000)],
            'Muchinga': [(-11.8333, 31.4167), (-10.1333, 32.3333), (-11.5167, 32.3333)],
            'North-Western': [(-12.1833, 26.4000), (-12.4333, 25.0167), (-11.7167, 24.4333)],
            'Western': [(-15.2833, 23.1500), (-16.1167, 23.2500), (-17.4833, 24.3000)],
            'Luapula': [(-11.0833, 28.8833), (-10.2167, 29.0000), (-9.4833, 29.3333)]
        }

        # 2. Get/Create Organization
        org, _ = Organization.objects.get_or_create(
            name="Zambia Development Agency",
            defaults={'type': Organization.Types.OWNER}
        )
        partner_org, _ = Organization.objects.get_or_create(
            name="Construction Partner Ltd",
            defaults={'type': Organization.Types.CONTRACTOR}
        )

        # 3. Setup Roles
        maker_role, _ = Role.objects.get_or_create(name="Maker", defaults={'is_system_role': True})
        checker_role, _ = Role.objects.get_or_create(name="Checker", defaults={'is_system_role': True})

        # 4. Get/Create Users
        maker, _ = User.objects.get_or_create(
            username="e2e_maker",
            defaults={'email': 'maker@example.com', 'role': maker_role, 'legacy_role': 'PM'}
        )
        if _: maker.set_password("password123"); maker.save()
        else: maker.role = maker_role; maker.save()
        
        checker, _ = User.objects.get_or_create(
            username="e2e_checker",
            defaults={'email': 'checker@example.com', 'role': checker_role, 'legacy_role': 'ADMIN'}
        )
        if _: checker.set_password("password123"); checker.save()
        else: checker.role = checker_role; checker.save()

        # 4. Standard Indicators
        indicators = []
        indicator_data = [
            ("Beneficiaries Reached", "Number of people directly benefiting", Indicator.UnitType.NUMBER),
            ("Project Completion", "Percentage of work finished", Indicator.UnitType.PERCENTAGE),
            ("Budget Utilization", "Funds spent vs allocated", Indicator.UnitType.CURRENCY),
            ("Compliance Score", "Adherence to regulations", Indicator.UnitType.PERCENTAGE),
            ("Local Jobs Created", "Number of local hires", Indicator.UnitType.NUMBER)
        ]
        for name, definition, utype in indicator_data:
            ind, _ = Indicator.objects.get_or_create(
                name=name,
                defaults={
                    'definition': definition,
                    'unit_type': utype,
                    'category': Indicator.Category.STANDARD,
                    'level': Indicator.Level.OUTPUT
                }
            )
            indicators.append(ind)

        # 5. Generate Projects over 5 years
        years = range(2021, 2027)
        for year in years:
            self.stdout.write(f"  Generating data for {year}...")
            for i in range(10):
                province = random.choice(list(provinces.keys()))
                lat, lon = random.choice(provinces[province])
                
                start_dt = date(year, random.randint(1, 6), random.randint(1, 28))
                end_dt = start_dt + timedelta(days=random.randint(180, 500))
                
                # Dynamic Status based on year
                current_date = date.today()
                if end_dt < current_date:
                    status = Project.Status.COMPLETED
                elif start_dt <= current_date <= end_dt:
                    status = Project.Status.ACTIVE
                else:
                    status = Project.Status.PLANNING

                project = Project.objects.create(
                    name=f"{province} {random.choice(['Infrastructure', 'Health', 'Link', 'Hub', 'Care'])} {year}-{i+1}",
                    type=random.choice(Project.Types.choices)[0],
                    thematic_area=random.choice(Project.StrategicTheme.choices)[0],
                    primary_kra=random.choice(Project.KeyResultArea.choices)[0],
                    description=f"A strategic development project in {province} province.",
                    latitude=lat,
                    longitude=lon,
                    start_date=start_dt,
                    end_date=end_dt,
                    status=status,
                    owner_org=org
                )

                # 6. Create Contract
                contract_val = random.randint(500000, 5000000)
                contract = Contract.objects.create(
                    project=project,
                    contractor=partner_org,
                    total_value=contract_val,
                    start_date=start_dt,
                    end_date=end_dt
                )

                # 7. Create Milestones (3 per project)
                milestones = []
                for j in range(3):
                    m_status = Milestone.Status.PENDING
                    if status == Project.Status.COMPLETED:
                        m_status = Milestone.Status.COMPLETED
                    elif status == Project.Status.ACTIVE and j == 0:
                        m_status = Milestone.Status.COMPLETED
                    elif status == Project.Status.ACTIVE and j == 1:
                        m_status = Milestone.Status.IN_PROGRESS

                    m = Milestone.objects.create(
                        contract=contract,
                        title=f"Phase {j+1}: {random.choice(['Mobilization', 'Construction', 'Finishing', 'Quality Check'])}",
                        target_percent=(j+1)*33.33,
                        value_amount=contract_val / 3,
                        due_date=start_dt + timedelta(days=(j+1)*60),
                        status=m_status
                    )
                    milestones.append(m)

                # 8. Indicator Targets and Results
                for ind in indicators:
                    target = IndicatorTarget.objects.create(
                        indicator=ind,
                        project=project,
                        baseline_value=0,
                        target_value=random.randint(100, 1000) if ind.unit_type == Indicator.UnitType.NUMBER else 100
                    )
                    
                    # Create results if project is active or completed
                    if status in [Project.Status.ACTIVE, Project.Status.COMPLETED]:
                        num_results = 2 if status == Project.Status.ACTIVE else 3
                        for r in range(num_results):
                            result_val = (r+1) * (target.target_value / 3)
                            IndicatorResult.objects.create(
                                target=target,
                                date=start_dt + timedelta(days=(r+1)*60),
                                value=result_val,
                                recorded_by=maker
                            )

                # 9. Payment Claims
                if status in [Project.Status.ACTIVE, Project.Status.COMPLETED]:
                    num_claims = 1 if status == Project.Status.ACTIVE else 2
                    for c in range(num_claims):
                        pc = PaymentClaim.objects.create(
                            contract=contract,
                            amount=contract_val / 4,
                            claim_date=start_dt + timedelta(days=(c+1)*90),
                            status=PaymentClaim.Status.PAID if status == Project.Status.COMPLETED else PaymentClaim.Status.APPROVED,
                            prepared_by=maker,
                            approved_by=checker
                        )
                        pc.milestones.add(milestones[c])

                # 10. Grievances and Investigations
                if random.random() > 0.6: # 40% chance of grievance
                    g = Grievance.objects.create(
                        project=project,
                        reporter_contact=f"citizen_{random.randint(1,100)}@zambia.zm",
                        description=f"Issue reported in {province}: {random.choice(['Noise', 'Dust', 'Access', 'Employment concerns'])}",
                        status=Grievance.Status.CLOSED if status == Project.Status.COMPLETED else Grievance.Status.OPEN,
                        priority=random.choice(Grievance.Priority.choices)[0]
                    )
                    
                    if g.status == Grievance.Status.CLOSED:
                        Investigation.objects.create(
                            title=f"Investigation: Grievance #{g.id}",
                            description=g.description,
                            status=Investigation.Status.CLOSED,
                            severity=random.choice(Investigation.Severity.choices)[0],
                            category=Investigation.Category.GRIEVANCE,
                            project=project,
                            related_grievance=g,
                            assigned_to=checker,
                            created_by=maker,
                            resolution_summary="Resolved through community engagement.",
                            resolved_at=timezone.now(),
                            closed_at=timezone.now()
                        )

                # 11. Assessments (Inspections)
                for m in milestones:
                  if m.status == Milestone.Status.COMPLETED:
                      Inspection.objects.create(
                          milestone=m,
                          inspector=checker,
                          inspected_at=timezone.now() if m.due_date > date.today() else timezone.make_aware(datetime.combine(m.due_date, datetime.min.time())),
                          quality_verdict=Inspection.QualityVerdict.PASS,
                          notes="Standard quality check passed.",
                          form_data={"structural_integrity": "OK", "safety_gear": "YES"},
                          icare_compliance={"integrity": True, "professionalism": True}
                      )

