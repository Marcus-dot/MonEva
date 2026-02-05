import os
import django
import sys
from datetime import date

# Setup Django
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from projects.models import Project, Beneficiary, BeneficiaryFeedback
from core.models import User
from rest_framework.test import APIClient

def verify_gis_impact():
    print("--- Phase 5 GIS Impact Verification Start ---")
    
    # 1. Setup Test Data
    client = APIClient()
    admin = User.objects.filter(is_superuser=True).first()
    client.force_authenticate(user=admin)
    
    project = Project.objects.first()
    if not project:
        print("Error: No project found")
        return
        
    # Ensure project is ACTIVE and has a location
    project.status = 'ACTIVE'
    project.location = {"type": "Point", "coordinates": [28.3228, -15.3875]} # Lusaka
    project.save()
    
    print(f"Using Project: {project.name} (ID: {project.id})")
    
    # Create mock beneficiaries
    Beneficiary.objects.filter(project=project).delete()
    Beneficiary.objects.create(project=project, first_name="Male", last_name="1", gender="MALE", year_of_birth=2010) # 16yo
    Beneficiary.objects.create(project=project, first_name="Female", last_name="1", gender="FEMALE", year_of_birth=1990) # 36yo
    Beneficiary.objects.create(project=project, first_name="Female", last_name="2", gender="FEMALE", year_of_birth=2000) # 26yo
    
    # Create mock feedback
    BeneficiaryFeedback.objects.filter(project=project).delete()
    BeneficiaryFeedback.objects.create(project=project, content="Great!", sentiment="POSITIVE")
    BeneficiaryFeedback.objects.create(project=project, content="Okay", sentiment="NEUTRAL")
    
    # 2. Call map_data API
    response = client.get('/api/v1/projects/map_data/')
    if response.status_code != 200:
        print(f"Error: API returned {response.status_code}")
        return
        
    data = response.json()
    
    # Find our project in the features
    feature = next((f for f in data['projects']['features'] if f['properties']['id'] == str(project.id)), None)
    
    if not feature:
        print("Error: Project not found in map_data response")
        return
        
    stats = feature['properties']['impact_stats']
    print(f"Impact Stats: {stats}")
    
    # 3. Assertions
    assert stats['total_beneficiaries'] == 3
    assert stats['gender_split']['MALE'] == 1
    assert stats['gender_split']['FEMALE'] == 2
    assert stats['age_buckets']['<18'] == 1
    assert stats['age_buckets']['18-35'] == 1
    assert stats['age_buckets']['36-60'] == 1
    assert stats['sentiment_score'] == 0.5 # (1 + 0) / 2
    
    print("Success: Backend impact aggregation verified!")
    print("--- Phase 5 GIS Impact Verification End ---")

if __name__ == "__main__":
    verify_gis_impact()
