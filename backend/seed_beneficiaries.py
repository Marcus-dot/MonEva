#!/usr/bin/env python
"""
Seed beneficiary data for Impact & Equity Analytics dashboard
Run with: python seed_beneficiaries.py
"""
import os
import sys
import django
import random
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from projects.models import Beneficiary, Project, BeneficiaryFeedback

# Zambian names for realistic data
MALE_FIRST_NAMES = [
    'Mwamba', 'Chanda', 'Bwalya', 'Mutale', 'Mulenga', 'Kabwe', 'Chipili',
    'Musonda', 'Kalumba', 'Tembo', 'Phiri', 'Banda', 'Zulu', 'Daka', 'Sakala',
    'Mumba', 'Chilufya', 'Kapembwa', 'Mwape', 'Chisanga', 'Lungu', 'Mwansa',
    'Kasonde', 'Kapata', 'Chola', 'Besa', 'Chomba', 'Kaunda', 'Sata', 'Mwila'
]

FEMALE_FIRST_NAMES = [
    'Mutinta', 'Naomi', 'Grace', 'Charity', 'Faith', 'Hope', 'Mwila', 'Chilufya',
    'Bwalya', 'Mulenga', 'Chanda', 'Musonda', 'Natasha', 'Patricia', 'Mary',
    'Agnes', 'Esther', 'Ruth', 'Martha', 'Priscilla', 'Theresa', 'Monica',
    'Josephine', 'Catherine', 'Elizabeth', 'Margaret', 'Dorothy', 'Sylvia',
    'Beatrice', 'Christine'
]

LAST_NAMES = [
    'Mwamba', 'Banda', 'Phiri', 'Tembo', 'Zulu', 'Mulenga', 'Chanda', 'Bwalya',
    'Musonda', 'Daka', 'Sakala', 'Mumba', 'Lungu', 'Mwansa', 'Kasonde', 'Chola',
    'Besa', 'Chomba', 'Kaunda', 'Sata', 'Mwila', 'Chilufya', 'Kalumba', 'Chipili',
    'Kabwe', 'Mutale', 'Kapembwa', 'Mwape', 'Chisanga', 'Kapata'
]

LOCATIONS = [
    # Rural areas (64% target)
    ('Chongwe', 'RURAL'), ('Kafue', 'RURAL'), ('Chisamba', 'RURAL'),
    ('Mumbwa', 'RURAL'), ('Chibombo', 'RURAL'), ('Mazabuka', 'RURAL'),
    ('Monze', 'RURAL'), ('Choma', 'RURAL'), ('Kalomo', 'RURAL'),
    ('Livingstone', 'PERI_URBAN'), ('Kasama', 'RURAL'), ('Mansa', 'RURAL'),
    ('Samfya', 'RURAL'), ('Kawambwa', 'RURAL'), ('Nchelenge', 'RURAL'),
    ('Kapiri Mposhi', 'RURAL'), ('Mkushi', 'RURAL'), ('Serenje', 'RURAL'),
    ('Chipata', 'PERI_URBAN'), ('Petauke', 'RURAL'), ('Katete', 'RURAL'),
    ('Lundazi', 'RURAL'), ('Solwezi', 'PERI_URBAN'), ('Kasempa', 'RURAL'),
    ('Mufumbwe', 'RURAL'), ('Kabompo', 'RURAL'), ('Zambezi', 'RURAL'),
    ('Chavuma', 'RURAL'), ('Mongu', 'PERI_URBAN'), ('Senanga', 'RURAL'),
    # Urban areas (36%)
    ('Lusaka', 'URBAN'), ('Ndola', 'URBAN'), ('Kitwe', 'URBAN'),
    ('Kabwe', 'URBAN'), ('Chingola', 'URBAN'), ('Mufulira', 'URBAN'),
    ('Luanshya', 'URBAN'), ('Kalulushi', 'URBAN')
]

# Age distribution weights (to create realistic demographics)
AGE_WEIGHTS = {
    '0-14': 0.20,   # Children
    '15-24': 0.25,  # Youth
    '25-64': 0.45,  # Working age adults
    '65+': 0.10    # Elderly
}

# Vulnerability weights
VULNERABILITY_WEIGHTS = {
    'LOW_INCOME': 0.35,
    'ELDERLY': 0.15,
    'DISABLED': 0.10,
    'ORPHAN': 0.08,
    'OTHER': 0.05,
    None: 0.27  # Not vulnerable
}


def get_year_of_birth(age_group):
    """Calculate year of birth based on age group"""
    current_year = date.today().year
    if age_group == '0-14':
        return current_year - random.randint(1, 14)
    elif age_group == '15-24':
        return current_year - random.randint(15, 24)
    elif age_group == '25-64':
        return current_year - random.randint(25, 64)
    else:  # 65+
        return current_year - random.randint(65, 85)


def weighted_choice(weights_dict):
    """Select a random item based on weights"""
    items = list(weights_dict.keys())
    weights = list(weights_dict.values())
    return random.choices(items, weights=weights, k=1)[0]


def seed_beneficiaries():
    print("=" * 60)
    print("Seeding Beneficiary Data for Impact Dashboard")
    print("=" * 60)

    # Get all active projects
    projects = list(Project.objects.filter(status__in=['ACTIVE', 'COMPLETED']))

    if not projects:
        print("ERROR: No active or completed projects found!")
        return

    print(f"Found {len(projects)} projects to distribute beneficiaries across")

    # Target: ~500 beneficiaries with good demographic spread
    total_to_create = 500
    created_count = 0

    # Gender distribution: aim for 48% female, 50% male, 2% other
    gender_weights = {'FEMALE': 0.48, 'MALE': 0.50, 'OTHER': 0.02}

    # Location weights: 64% rural
    rural_locations = [loc for loc in LOCATIONS if loc[1] == 'RURAL']
    urban_locations = [loc for loc in LOCATIONS if loc[1] == 'URBAN']
    peri_urban_locations = [loc for loc in LOCATIONS if loc[1] == 'PERI_URBAN']

    print(f"\nCreating {total_to_create} beneficiaries...")

    for i in range(total_to_create):
        # Select gender
        gender = weighted_choice(gender_weights)

        # Select name based on gender
        if gender == 'MALE':
            first_name = random.choice(MALE_FIRST_NAMES)
        elif gender == 'FEMALE':
            first_name = random.choice(FEMALE_FIRST_NAMES)
        else:
            first_name = random.choice(MALE_FIRST_NAMES + FEMALE_FIRST_NAMES)

        last_name = random.choice(LAST_NAMES)

        # Select age group and calculate year of birth
        age_group = weighted_choice(AGE_WEIGHTS)
        year_of_birth = get_year_of_birth(age_group)

        # Select location (64% rural target)
        location_type_weights = {'rural': 0.64, 'peri_urban': 0.16, 'urban': 0.20}
        location_type = weighted_choice(location_type_weights)

        if location_type == 'rural':
            location, residence = random.choice(rural_locations)
        elif location_type == 'peri_urban':
            location, residence = random.choice(peri_urban_locations)
        else:
            location, residence = random.choice(urban_locations)

        # Select vulnerability category
        vulnerability = weighted_choice(VULNERABILITY_WEIGHTS)
        is_vulnerable = vulnerability is not None
        disability_status = vulnerability == 'DISABLED'

        # If elderly age group, more likely to be marked as elderly vulnerability
        if age_group == '65+' and vulnerability is None:
            vulnerability = 'ELDERLY'
            is_vulnerable = True

        # Assign to a random project
        project = random.choice(projects)

        # Generate contact info
        phone = f"+260 9{random.randint(10, 99)} {random.randint(100, 999)} {random.randint(1000, 9999)}"

        beneficiary = Beneficiary.objects.create(
            project=project,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            year_of_birth=year_of_birth,
            contact_info=phone,
            location=location,
            disability_status=disability_status,
            vulnerability_category=vulnerability or '',
            residence_type=residence,
            is_vulnerable=is_vulnerable
        )

        created_count += 1

        # Progress indicator
        if created_count % 100 == 0:
            print(f"  Created {created_count}/{total_to_create} beneficiaries...")

    print(f"\n[DONE] Created {created_count} beneficiaries")

    # Now let's add some feedback from beneficiaries
    print("\n--- Adding Beneficiary Feedback ---")

    feedback_templates = [
        ("The water project has changed our lives. We no longer walk 5km to fetch water.", "POSITIVE"),
        ("The school construction is good but we need more teachers.", "NEUTRAL"),
        ("Very happy with the health clinic. My children can now get treatment nearby.", "POSITIVE"),
        ("The road improvement has made it easier to transport goods to market.", "POSITIVE"),
        ("We are grateful for the agricultural training program.", "POSITIVE"),
        ("The borehole sometimes runs dry during peak hours.", "NEUTRAL"),
        ("Forest conservation efforts are protecting our environment.", "POSITIVE"),
        ("The tree planting initiative has improved our air quality.", "POSITIVE"),
        ("We need more involvement in project decisions.", "NEUTRAL"),
        ("The skills training helped me start a small business.", "POSITIVE"),
        ("Delays in project completion have affected our plans.", "NEGATIVE"),
        ("Community engagement could be improved.", "NEUTRAL"),
        ("The irrigation system has doubled our crop yield.", "POSITIVE"),
        ("We appreciate the employment opportunities for local youth.", "POSITIVE"),
        ("More female participation would benefit the community.", "NEUTRAL"),
    ]

    # Select random beneficiaries to give feedback
    all_beneficiaries = list(Beneficiary.objects.all())
    feedback_givers = random.sample(all_beneficiaries, min(150, len(all_beneficiaries)))

    feedback_count = 0
    for ben in feedback_givers:
        content, sentiment = random.choice(feedback_templates)

        # Create feedback
        BeneficiaryFeedback.objects.create(
            project=ben.project,
            content=content,
            sentiment=sentiment,
            gender=ben.gender,
            age_group=get_age_group_from_year(ben.year_of_birth) if ben.year_of_birth else '',
            beneficiary_profile=ben,
            beneficiary_id=f"BEN-{str(ben.id)[:8]}"
        )
        feedback_count += 1

    print(f"[DONE] Created {feedback_count} feedback entries")

    # Print summary statistics
    print_summary()


def get_age_group_from_year(year_of_birth):
    """Convert year of birth to age group"""
    if not year_of_birth:
        return ''
    age = date.today().year - year_of_birth
    if age <= 14:
        return '0-14'
    elif age <= 24:
        return '15-24'
    elif age <= 64:
        return '25-64'
    else:
        return '65+'


def print_summary():
    """Print summary statistics"""
    print("\n" + "=" * 60)
    print("BENEFICIARY DATA SUMMARY")
    print("=" * 60)

    total = Beneficiary.objects.count()
    print(f"\nTotal Beneficiaries: {total}")

    print("\n--- Gender Distribution ---")
    for gender, label in Beneficiary.Gender.choices:
        count = Beneficiary.objects.filter(gender=gender).count()
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {label}: {count} ({pct:.1f}%)")

    print("\n--- Age Group Distribution ---")
    current_year = date.today().year
    age_groups = {
        '0-14': Beneficiary.objects.filter(year_of_birth__gt=current_year-15).count(),
        '15-24': Beneficiary.objects.filter(year_of_birth__lte=current_year-15, year_of_birth__gt=current_year-25).count(),
        '25-64': Beneficiary.objects.filter(year_of_birth__lte=current_year-25, year_of_birth__gt=current_year-65).count(),
        '65+': Beneficiary.objects.filter(year_of_birth__lte=current_year-65).count(),
    }
    for group, count in age_groups.items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {group}: {count} ({pct:.1f}%)")

    print("\n--- Residence Type ---")
    for res_type in ['RURAL', 'URBAN', 'PERI_URBAN']:
        count = Beneficiary.objects.filter(residence_type=res_type).count()
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {res_type}: {count} ({pct:.1f}%)")

    print("\n--- Vulnerability Categories ---")
    vulnerable = Beneficiary.objects.filter(is_vulnerable=True).count()
    pct = (vulnerable / total * 100) if total > 0 else 0
    print(f"  Total Vulnerable: {vulnerable} ({pct:.1f}%)")

    for cat in ['LOW_INCOME', 'ELDERLY', 'DISABLED', 'ORPHAN', 'OTHER']:
        count = Beneficiary.objects.filter(vulnerability_category=cat).count()
        print(f"    - {cat}: {count}")

    print("\n--- Feedback Summary ---")
    from projects.models import BeneficiaryFeedback
    for sentiment, label in BeneficiaryFeedback.Sentiment.choices:
        count = BeneficiaryFeedback.objects.filter(sentiment=sentiment).count()
        print(f"  {label}: {count}")


if __name__ == '__main__':
    seed_beneficiaries()
