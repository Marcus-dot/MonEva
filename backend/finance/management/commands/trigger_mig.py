from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("Starting migrations...")
        call_command('makemigrations', 'finance')
        call_command('migrate', 'finance')
        self.stdout.write("Finished migrations.")
