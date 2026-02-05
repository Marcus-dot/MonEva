"""
Test script for notification automations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from finance.models import PaymentClaim
from core.models import Notification, User
from grievances.models import Grievance

print("=" * 60)
print("NOTIFICATION AUTOMATION TEST")
print("=" * 60)

# Check users
users = User.objects.all()
print(f"\n✓ Total users: {users.count()}")

# Check claims
claims = PaymentClaim.objects.all()
print(f"✓ Total payment claims: {claims.count()}")

# Check grievances
grievances = Grievance.objects.all()
print(f"✓ Total grievances: {grievances.count()}")

# Check notifications
notifs = Notification.objects.all()
print(f"✓ Total notifications: {notifs.count()}")

print("\n" + "=" * 60)
print("STATUS CHANGE NOTIFICATION TEST")
print("=" * 60)

# Test 1: Check if we can change a claim status
if claims.exists():
    test_claim = claims.first()
    old_status = test_claim.status
    print(f"\n✓ Found test claim: {test_claim.id[:8]}")
    print(f"  Current status: {old_status}")
    print(f"  Amount: ZMW {test_claim.amount:,.2f}")
    
    # Count notifications before
    notifs_before = Notification.objects.count()
    
    # Change status to APPROVED (if not already)
    if old_status != 'APPROVED':
        print(f"\n→ Changing status to APPROVED...")
        test_claim.status = 'APPROVED'
        test_claim.save()
        
        # Count notifications after
        notifs_after = Notification.objects.count()
        new_notifs = notifs_after - notifs_before
        
        print(f"✓ Status changed successfully!")
        print(f"✓ New notifications created: {new_notifs}")
        
        # Show the new notifications
        if new_notifs > 0:
            recent_notifs = Notification.objects.order_by('-created_at')[:new_notifs]
            print(f"\nNew Notifications:")
            for notif in recent_notifs:
                print(f"  - {notif.title}")
                print(f"    To: {notif.recipient.get_full_name()}")
                print(f"    Message: {notif.message[:80]}...")
        
        # Revert status
        print(f"\n→ Reverting status to {old_status}...")
        test_claim.status = old_status
        test_claim.save()
        print(f"✓ Status reverted")
    else:
        print(f"  (Already APPROVED, skipping test)")
else:
    print("\n⚠ No payment claims found. Create a claim to test notifications.")

print("\n" + "=" * 60)
print("SCHEDULED TASKS TEST")
print("=" * 60)

from django_q.models import Schedule

schedules = Schedule.objects.filter(name__startswith='moneva_')
print(f"\n✓ Scheduled tasks: {schedules.count()}")

for schedule in schedules:
    print(f"\n  Task: {schedule.name}")
    print(f"  Function: {schedule.func}")
    print(f"  Schedule: {schedule.cron}")
    print(f"  Next run: {schedule.next_run or 'Not calculated yet'}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nTo start the task scheduler, run:")
print("  python manage.py qcluster")
print("\n")
