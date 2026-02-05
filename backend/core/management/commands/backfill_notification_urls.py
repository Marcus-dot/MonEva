"""
Management command to backfill action_url for existing notifications
"""
from django.core.management.base import BaseCommand
from core.models import Notification


class Command(BaseCommand):
    help = 'Backfill action_url for existing notifications based on related_model and related_id'

    def handle(self, *args, **options):
        # Get all notifications without action_url but with related_model and related_id
        notifications = Notification.objects.filter(
            action_url='',
            related_model__isnull=False,
            related_id__isnull=False
        ).exclude(related_model='').exclude(related_id='')

        total = notifications.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ No notifications need backfilling'))
            return

        self.stdout.write(f'Found {total} notifications to backfill...')
        
        updated_count = 0
        for notification in notifications:
            # Generate action_url using the model method
            action_url = notification.generate_action_url()
            
            if action_url:
                notification.action_url = action_url
                notification.save(update_fields=['action_url'])
                updated_count += 1
                
                self.stdout.write(
                    f'  ✓ {notification.title[:50]}... → {action_url}'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully backfilled {updated_count} out of {total} notifications'
            )
        )
        
        if updated_count < total:
            skipped = total - updated_count
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Skipped {skipped} notifications (no URL mapping for their related_model)'
                )
            )
