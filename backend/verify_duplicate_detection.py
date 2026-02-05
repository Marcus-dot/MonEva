import os
import sys
import django

# Setup Django Environment
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

import io
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from core.models import User
from projects.models import Project, Milestone, Contract
from assessments.models import Inspection, Evidence
from django.core.exceptions import ValidationError
from django.utils import timezone

def create_test_image():
    # Create a simple red image
    img = Image.new('RGB', (100, 100), color = 'red')
    img_io = io.BytesIO()
    img.save(img_io, format='JPEG')
    return SimpleUploadedFile("test_image.jpg", img_io.getvalue(), content_type="image/jpeg")

def run_test():
    print("--- Starting Duplicate Photo Detection Test ---")
    
    # Setup Data
    user, _ = User.objects.get_or_create(username='test_ml_user', defaults={'role': 'PROJECT_MANAGER'})
    
    # Create or Get Organization
    from core.models import Organization
    org, _ = Organization.objects.get_or_create(name="ML Test Org", defaults={'type': 'CONTRACTOR'})

    # Create or Get Project
    project = Project.objects.first()
    if not project:
        project = Project.objects.create(
            name="ML Test Project", 
            owner_org=org, 
            start_date=timezone.now(), 
            end_date=timezone.now(),
            type='ROAD'
        )

    # Create Contract
    contract, _ = Contract.objects.get_or_create(
        project=project, 
        contractor=org, 
        defaults={
            'total_value': 1000, 
            'start_date': timezone.now(), 
            'end_date': timezone.now()
        }
    )

    # Create Milestones
    m1, _ = Milestone.objects.get_or_create(
        contract=contract, 
        title="ML Test Milestone 1", 
        defaults={
            'value_amount': 100,
            'target_percent': 10,
            'due_date': timezone.now()
        }
    )
    m2, _ = Milestone.objects.get_or_create(
        contract=contract, 
        title="ML Test Milestone 2", 
        defaults={
            'value_amount': 100,
            'target_percent': 20,
            'due_date': timezone.now()
        }
    )

    # Create Inspections
    inspect1 = Inspection.objects.create(milestone=m1, inspector=user, inspected_at=timezone.now(), quality_verdict='PASS')
    inspect2 = Inspection.objects.create(milestone=m2, inspector=user, inspected_at=timezone.now(), quality_verdict='PASS')
    
    print(f"Created Inspections: {inspect1.id} and {inspect2.id}")

    # 1. Upload Original Image
    print("\n1. Uploading Original Image to Inspection 1...")
    img1 = create_test_image()
    ev1 = Evidence(inspection=inspect1, file=img1, file_type='PHOTO')
    ev1.save()
    print(f"   Success! Hash: {ev1.image_hash}")

    # 2. Try Uploading Duplicate to Inspection 2
    print("\n2. Attempting to upload DUPLICATE image to Inspection 2...")
    img2 = create_test_image() # Same content, new file object
    ev2 = Evidence(inspection=inspect2, file=img2, file_type='PHOTO')
    
    try:
        ev2.save()
        print("   FAILED: The system accepted a duplicate image!")
    except ValidationError as e:
        print(f"   PASSED: System rejected duplicate. Error: {e}")
    except Exception as e:
        print(f"   ERROR: Unexpected exception: {type(e)} - {e}")

    # Cleanup
    inspect1.delete()
    inspect2.delete()
    # Note: File cleanup is tricky without a signal, but okay for dev test.

if __name__ == "__main__":
    run_test()
