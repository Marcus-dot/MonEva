import os
import django
import sys
from datetime import date

# Setup Django
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from projects.models import Project, Beneficiary
from indicators.models import IndicatorResult, Indicator, IndicatorTarget
from core.models import User
from rest_framework.test import APIClient

def verify_granular_api():
    print("--- Phase 6 Granular API Verification Start ---")
    
    # 1. Setup Data
    client = APIClient()
    admin = User.objects.filter(is_superuser=True).first()
    client.force_authenticate(user=admin)
    
    project = Project.objects.first()
    
    # 2. Test Beneficiary Gender Filter
    # Ensure mixed gender
    current_year = date.today().year
    Beneficiary.objects.create(project=project, first_name="ApiTest", last_name="Male", gender="MALE", year_of_birth=current_year-20)
    Beneficiary.objects.create(project=project, first_name="ApiTest", last_name="Female", gender="FEMALE", year_of_birth=current_year-20)
    
    response = client.get(f'/api/v1/beneficiaries/?project={project.id}&gender=MALE')
    if response.status_code != 200:
        print(f"Error: Failed to fetch beneficiaries. Status: {response.status_code}")
        return
    
    data = response.json()
    # Check if all returned are MALE
    incorrect = [b for b in data if b['gender'] != 'MALE']
    if incorrect:
        print(f"FAIL: Gender filter returned incorrect data: {incorrect}")
    else:
        print("PASS: Beneficiary Gender Filter works")

    # 3. Test Age Calculation Filter
    # Create a 10 year old
    Beneficiary.objects.create(project=project, first_name="ApiTest", last_name="Kid", gender="MALE", year_of_birth=current_year-10)
    
    # Filter age_max=12 (Should include the 10yo, exclude the 20yo)
    response = client.get(f'/api/v1/beneficiaries/?project={project.id}&age_max=12')
    data = response.json()
    
    kids = [b for b in data if b['last_name'] == 'Kid']
    adults = [b for b in data if b['last_name'] == 'Male'] # 20yo
    
    if len(kids) > 0 and len(adults) == 0:
         print("PASS: Beneficiary Age Filter (age_max) works")
    else:
         print(f"FAIL: Age filter logic error. Kids: {len(kids)}, Adults: {len(adults)}")
         
    # 4. Test Indicator Result Filter
    # Create simple structure
    ind = Indicator.objects.create(name="ApiTestIndicator", definition="Test", unit_type="NUMBER")
    target = IndicatorTarget.objects.create(project=project, indicator=ind, target_value=100)
    IndicatorResult.objects.create(target=target, value=50, date=date.today(), status='VERIFIED')
    
    response = client.get(f'/api/v1/indicator-results/?project={project.id}&indicator_name=ApiTestIndicator')
    data = response.json()
    
    found = [r for r in data if r['value'] == 50]
    if len(found) == 1:
        print("PASS: Indicator Result Filter works")
    else:
        print(f"FAIL: Indicator filter returned: {len(data)}")

    print("--- Phase 6 Granular API Verification End ---")

if __name__ == "__main__":
    verify_granular_api()
