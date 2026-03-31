"""
Management command to set up scheduled tasks for notifications
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = 'Set up scheduled tasks for automated notifications'

    def handle(self, *args, **options):
        self.stdout.write('Setting up scheduled tasks...')
        
        # Clear existing schedules (optional, for development)
        Schedule.objects.filter(name__startswith='moneva_').delete()
        
        # 1. Contract Expiry Reminders - Daily at 8:00 AM
        Schedule.objects.create(
            name='moneva_contract_expiry',
            func='core.tasks.send_contract_expiry_reminders',
            schedule_type=Schedule.DAILY,
            repeats=-1,
            cron='0 8 * * *',  # 8:00 AM every day
        )
        self.stdout.write(self.style.SUCCESS('✓ Created: Contract expiry reminders (Daily 8:00 AM)'))
        
        # 2. Milestone Deadline Reminders - Daily at 8:30 AM
        Schedule.objects.create(
            name='moneva_milestone_deadlines',
            func='core.tasks.send_milestone_deadline_reminders',
            schedule_type=Schedule.DAILY,
            repeats=-1,
            cron='30 8 * * *',  # 8:30 AM every day
        )
        self.stdout.write(self.style.SUCCESS('✓ Created: Milestone deadline reminders (Daily 8:30 AM)'))
        
        # 3. Escalation Alerts - Daily at 9:00 AM
        Schedule.objects.create(
            name='moneva_escalation_alerts',
            func='core.tasks.check_pending_approvals_escalation',
            schedule_type=Schedule.DAILY,
            repeats=-1,
            cron='0 9 * * *',  # 9:00 AM every day
        )
        self.stdout.write(self.style.SUCCESS('✓ Created: Escalation alerts (Daily 9:00 AM)'))

        # 4. Impact Evaluation Reminders - Daily at 8:15 AM
        Schedule.objects.create(
            name='moneva_impact_reminders',
            func='core.tasks.send_impact_followup_reminders',
            schedule_type=Schedule.DAILY,
            repeats=-1,
            cron='15 8 * * *',  # 8:15 AM every day
        )
        self.stdout.write(self.style.SUCCESS('✓ Created: Impact evaluation reminders (Daily 8:15 AM)'))

        # 5. Daily Digest - Daily at 7:00 AM
        Schedule.objects.create(
            name='moneva_daily_digest',
            func='core.tasks.send_daily_digests',
            schedule_type=Schedule.DAILY,
            repeats=-1,
            cron='0 7 * * *',  # 7:00 AM every day
        )
        self.stdout.write(self.style.SUCCESS('✓ Created: Daily Digest (Daily 7:00 AM)'))

        # 6. Defects Liability Period Reminders - Daily at 9:30 AM
        Schedule.objects.create(
            name='moneva_defects_liability',
            func='core.tasks.send_defects_liability_reminders',
            schedule_type=Schedule.DAILY,
            repeats=-1,
            cron='30 9 * * *',  # 9:30 AM every day
        )
        self.stdout.write(self.style.SUCCESS('✓ Created: Defects liability reminders (Daily 9:30 AM)'))

        self.stdout.write(self.style.SUCCESS('\n✅ All scheduled tasks created successfully!'))
        self.stdout.write('\nTo start the task scheduler, run:')
        self.stdout.write(self.style.WARNING('  python manage.py qcluster'))
