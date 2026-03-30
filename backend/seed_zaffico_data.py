#!/usr/bin/env python
"""
Seed ZAFFICO-specific data for demo
Run with: python seed_zaffico_data.py
"""
import os
import sys
import django
from datetime import date, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Organization
from projects.models import Project, Contract, Milestone, SDG

User = get_user_model()


def seed_data():
    print("=" * 60)
    print("Seeding ZAFFICO Demo Data")
    print("=" * 60)

    # 1. Create ZAFFICO Organization
    zaffico, created = Organization.objects.get_or_create(
        name='ZAFFICO',
        defaults={'type': 'OWNER'}
    )
    if created:
        print(f"[CREATED] Organization: ZAFFICO")
    else:
        print(f"[EXISTS] Organization: ZAFFICO")

    # 2. Get users
    users = {
        'ankandela': User.objects.filter(username='ankandela').first(),  # GM
        'kkashimbaya': User.objects.filter(username='kkashimbaya').first(),  # Manager HCD
        'dhibajene': User.objects.filter(username='dhibajene').first(),  # Manager Tech
        'mmatale': User.objects.filter(username='mmatale').first(),  # Manager Finance
        'skilaka': User.objects.filter(username='skilaka').first(),  # Procurement
        'nmumba': User.objects.filter(username='nmumba').first(),  # Finance
        'nsitenge': User.objects.filter(username='nsitenge').first(),  # PA
        'smufishi': User.objects.filter(username='smufishi').first(),  # Project Engineer
        'skunda': User.objects.filter(username='skunda').first(),  # Project Engineer
    }

    # 3. Get some SDGs relevant to forestry
    sdg13 = SDG.objects.filter(code='SDG13').first()  # Climate Action
    sdg15 = SDG.objects.filter(code='SDG15').first()  # Life on Land
    sdg8 = SDG.objects.filter(code='SDG8').first()  # Decent Work

    # 4. Define ZAFFICO-relevant projects
    zaffico_projects = [
        {
            'name': 'Chati Forest Plantation Expansion',
            'type': 'CSR',
            'csr_focus': 'ENVIRONMENT',
            'thematic_area': 'ENVIRONMENT',
            'description': 'Expansion of Chati Forest plantation with indigenous tree species to increase forest cover and carbon sequestration capacity.',
            'status': 'ACTIVE',
            'start_date': date(2024, 1, 15),
            'end_date': date(2025, 12, 31),
            'latitude': -15.4067,
            'longitude': 28.2871,
        },
        {
            'name': 'Kabompo River Basin Reforestation',
            'type': 'CSR',
            'csr_focus': 'ENVIRONMENT',
            'thematic_area': 'ENVIRONMENT',
            'description': 'Community-based reforestation project along the Kabompo River Basin to prevent soil erosion and protect water sources.',
            'status': 'ACTIVE',
            'start_date': date(2024, 3, 1),
            'end_date': date(2026, 2, 28),
            'latitude': -14.4000,
            'longitude': 24.2000,
        },
        {
            'name': 'Copperbelt Schools Tree Planting Initiative',
            'type': 'CSR',
            'csr_focus': 'EDUCATION',
            'thematic_area': 'EDUCATION',
            'description': 'Partnership with schools in the Copperbelt to establish tree nurseries and environmental education programs.',
            'status': 'ACTIVE',
            'start_date': date(2024, 2, 1),
            'end_date': date(2025, 11, 30),
            'latitude': -12.8123,
            'longitude': 28.2136,
        },
        {
            'name': 'Sustainable Timber Processing Facility',
            'type': 'BUILDING',
            'csr_focus': 'INFRASTRUCTURE',
            'thematic_area': 'ENERGY',
            'description': 'Construction of modern timber processing facility with solar power integration and waste-to-energy systems.',
            'status': 'PLANNING',
            'start_date': date(2025, 1, 1),
            'end_date': date(2026, 6, 30),
            'latitude': -15.2500,
            'longitude': 28.3000,
        },
        {
            'name': 'Forest Guard Housing Project',
            'type': 'BUILDING',
            'csr_focus': 'INFRASTRUCTURE',
            'thematic_area': 'OTHER',
            'description': 'Construction of housing units for forest guards in remote plantation areas to improve security and response times.',
            'status': 'ACTIVE',
            'start_date': date(2024, 4, 1),
            'end_date': date(2025, 3, 31),
            'latitude': -15.3500,
            'longitude': 28.1500,
        },
        {
            'name': 'Community Beekeeping & Agroforestry',
            'type': 'CSR',
            'csr_focus': 'OTHER',
            'thematic_area': 'AGRICULTURE',
            'description': 'Training local communities in beekeeping and agroforestry practices to provide alternative livelihoods while supporting forest conservation.',
            'status': 'COMPLETED',
            'start_date': date(2023, 1, 1),
            'end_date': date(2024, 6, 30),
            'latitude': -14.8000,
            'longitude': 25.5000,
        },
    ]

    # Get or create contractor
    contractor, _ = Organization.objects.get_or_create(
        name='Green Works Construction',
        defaults={'type': 'CONTRACTOR'}
    )

    project_engineers = [users['smufishi'], users['skunda']]
    managers = [users['kkashimbaya'], users['dhibajene'], users['mmatale']]

    for proj_data in zaffico_projects:
        project, created = Project.objects.get_or_create(
            name=proj_data['name'],
            owner_org=zaffico,
            defaults={
                'type': proj_data['type'],
                'csr_focus': proj_data.get('csr_focus'),
                'thematic_area': proj_data['thematic_area'],
                'description': proj_data['description'],
                'status': proj_data['status'],
                'start_date': proj_data['start_date'],
                'end_date': proj_data['end_date'],
                'latitude': proj_data['latitude'],
                'longitude': proj_data['longitude'],
            }
        )

        if created:
            print(f"[CREATED] Project: {project.name}")

            # Add SDGs
            if sdg15:
                project.sdgs.add(sdg15)
            if sdg13:
                project.sdgs.add(sdg13)
            if sdg8:
                project.sdgs.add(sdg8)

            # Assign team members
            for eng in project_engineers:
                if eng:
                    project.assigned_team.add(eng)

            # Assign a manager
            manager = random.choice([m for m in managers if m])
            if manager:
                project.assigned_team.add(manager)

            # Create contract if not CSR
            if proj_data['type'] != 'CSR':
                contract_value = random.randint(500000, 5000000)
                contract = Contract.objects.create(
                    project=project,
                    contractor=contractor,
                    total_value=contract_value,
                    currency='ZMW',
                    start_date=proj_data['start_date'],
                    end_date=proj_data['end_date'],
                )
                print(f"  [CREATED] Contract: ZMW {contract_value:,}")

                # Create milestones
                milestones = [
                    ('Site Preparation', 20, 0.2),
                    ('Foundation Work', 30, 0.3),
                    ('Main Construction', 40, 0.35),
                    ('Finishing & Handover', 10, 0.15),
                ]

                for i, (title, percent, value_pct) in enumerate(milestones):
                    due_offset = (proj_data['end_date'] - proj_data['start_date']).days * (i + 1) / len(milestones)
                    due_date = proj_data['start_date'] + timedelta(days=int(due_offset))

                    status = 'PENDING'
                    if proj_data['status'] == 'COMPLETED':
                        status = 'COMPLETED'
                    elif proj_data['status'] == 'ACTIVE' and i == 0:
                        status = 'COMPLETED'
                    elif proj_data['status'] == 'ACTIVE' and i == 1:
                        status = 'IN_PROGRESS'

                    Milestone.objects.create(
                        contract=contract,
                        title=title,
                        description=f'{title} for {project.name}',
                        target_percent=percent,
                        value_amount=contract_value * value_pct,
                        due_date=due_date,
                        status=status,
                    )
                print(f"  [CREATED] 4 Milestones")
        else:
            print(f"[EXISTS] Project: {project.name}")

    # 5. Assign existing projects to new users
    print("\n--- Assigning users to existing projects ---")

    # Get some active projects to assign
    active_projects = Project.objects.filter(status='ACTIVE')[:10]

    for project in active_projects:
        # Add all engineers to the project
        for eng in project_engineers:
            if eng and eng not in project.assigned_team.all():
                project.assigned_team.add(eng)

        # Add a random manager
        manager = random.choice([m for m in managers if m])
        if manager and manager not in project.assigned_team.all():
            project.assigned_team.add(manager)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for username, user in users.items():
        if user:
            count = user.assigned_projects.count()
            print(f"{user.first_name} {user.last_name}: {count} assigned projects")

    print("\nZAFFICO Projects:")
    for proj in Project.objects.filter(owner_org=zaffico):
        print(f"  - {proj.name} ({proj.status})")


if __name__ == '__main__':
    seed_data()
