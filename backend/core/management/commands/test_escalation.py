from django.core.management.base import BaseCommand
from core.tasks import check_pending_approvals_escalation

class Command(BaseCommand):
    help = 'Test escalation logic manually'

    def handle(self, *args, **options):
        self.stdout.write('Running escalation check...')
        result = check_pending_approvals_escalation()
        self.stdout.write(self.style.SUCCESS(f'Finished: {result}'))
