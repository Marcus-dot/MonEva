from django.core.management.base import BaseCommand
from projects.models import SDG

class Command(BaseCommand):
    help = 'Seed the 17 Sustainable Development Goals'

    def handle(self, *args, **options):
        sdgs = [
            ("SDG1", "No Poverty", "#E5243B"),
            ("SDG2", "Zero Hunger", "#DDA63A"),
            ("SDG3", "Good Health and Well-being", "#4C9F38"),
            ("SDG4", "Quality Education", "#C5192D"),
            ("SDG5", "Gender Equality", "#FF3A21"),
            ("SDG6", "Clean Water and Sanitation", "#26BDE2"),
            ("SDG7", "Affordable and Clean Energy", "#FCC30B"),
            ("SDG8", "Decent Work and Economic Growth", "#A21942"),
            ("SDG9", "Industry, Innovation and Infrastructure", "#FD6925"),
            ("SDG10", "Reduced Inequality", "#DD1367"),
            ("SDG11", "Sustainable Cities and Communities", "#FD9D24"),
            ("SDG12", "Responsible Consumption and Production", "#BF8B2E"),
            ("SDG13", "Climate Action", "#3F7E44"),
            ("SDG14", "Life Below Water", "#0A97D9"),
            ("SDG15", "Life on Land", "#56C02B"),
            ("SDG16", "Peace, Justice and Strong Institutions", "#00689D"),
            ("SDG17", "Partnerships for the Goals", "#19486A"),
        ]

        for code, name, color in sdgs:
            obj, created = SDG.objects.get_or_create(
                code=code,
                defaults={'name': name, 'color': color}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {code}'))
            else:
                self.stdout.write(f'{code} already exists')
