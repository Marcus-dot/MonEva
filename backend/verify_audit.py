import os
import sys
import django

# Setup Django Environment
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from core.models import User, Organization, ActivityLog
from projects.models import Project
from django.utils import timezone

def run_test():
    print("--- Starting Audit Logging Test ---")
    
    # 1. Clear previous test logs if any (optional, but cleaner)
    # ActivityLog.objects.all().delete()

    # 2. Perform Action: Create Project
    print("\n1. Creating Project 'Audit Test Project'...")
    org, _ = Organization.objects.get_or_create(name="Audit Org", defaults={'type': 'OWNER'})
    
    project = Project.objects.create(
        name="Audit Test Project", 
        owner_org=org, 
        start_date=timezone.now(), 
        end_date=timezone.now(),
        type='ROAD'
    )
    print(f"   Project Created: {project.id}")

    # 3. Check Logs
    print("\n2. Checking Activity Logs...")
    logs = ActivityLog.objects.filter(target_model='Project', target_id=str(project.id))
    
    if logs.exists():
        log = logs.first()
        print(f"   PASSED: Log found!")
        print(f"   - Actor: {log.actor}")
        print(f"   - Action: {log.action}")
        print(f"   - Details: {log.details}")
        
        # Verify specific details
        if log.action == 'CREATE' and log.details.get('name') == 'Audit Test Project':
             print("   VERIFIED: Log content matches.")
        else:
             print("   FAILED: Log content incorrect.")
    else:
        print("   FAILED: No log created.")

    # 4. Perform Update
    print("\n3. Updating Project Status...")
    project.status = Project.Status.ACTIVE
    project.save()
    
    # Check Logs again
    logs = ActivityLog.objects.filter(target_model='Project', target_id=str(project.id), action='UPDATE')
    if logs.exists():
        print(f"   PASSED: Update Log found!")
    else:
        print(f"   FAILED: Update Log missing.")

if __name__ == "__main__":
    run_test()
