from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Role, Permission, User


class Command(BaseCommand):
    help = 'Grant admin user system-wide access with Administrator role'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username to grant admin access (default: admin)'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        self.stdout.write(self.style.WARNING(f'\n🔐 Granting System-Wide Access to: {username}\n'))
        
        try:
            with transaction.atomic():
                # Get or create admin user
                try:
                    user = User.objects.get(username=username)
                    self.stdout.write(f'✓ Found user: {user.username}')
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'✗ User "{username}" not found!'))
                    self.stdout.write('\nAvailable users:')
                    for u in User.objects.all()[:10]:
                        self.stdout.write(f'  - {u.username}')
                    return
                
                # Get Administrator role (or create it)
                admin_role, created = Role.objects.get_or_create(
                    name='Administrator',
                    defaults={'is_system_role': True, 'is_admin': True, 'description': 'Full system access'}
                )
                if not admin_role.is_admin:
                    admin_role.is_admin = True
                    admin_role.save(update_fields=['is_admin'])
                self.stdout.write(f'{"✓ Created" if created else "✓ Found"} Administrator role with {admin_role.permissions.count()} permissions')
                
                # Assign role to user
                old_role = user.role.name if user.role else 'None'
                user.role = admin_role
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully granted Administrator role to {username}'))
                self.stdout.write(f'  Previous role: {old_role}')
                self.stdout.write(f'  New role: {admin_role.name}')
                
                # Display permissions summary
                self.stdout.write(f'\n📋 Permissions Summary:')
                permissions_by_module = {}
                for perm in admin_role.permissions.all():
                    if perm.module not in permissions_by_module:
                        permissions_by_module[perm.module] = []
                    permissions_by_module[perm.module].append(perm.name)
                
                for module, perms in sorted(permissions_by_module.items()):
                    self.stdout.write(f'\n  {module.upper()}:')
                    for perm in perms:
                        self.stdout.write(f'    ✓ {perm}')
                
                self.stdout.write(self.style.SUCCESS(f'\n🎉 {username} now has full system access!\n'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error: {str(e)}\n'))
            raise
