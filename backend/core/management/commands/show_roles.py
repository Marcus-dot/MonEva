from django.core.management.base import BaseCommand
from core.models import Role, Permission, User


class Command(BaseCommand):
    help = 'Display roles and permissions summary'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n📊 ROLES & PERMISSIONS SUMMARY\n'))
        self.stdout.write('=' * 80)
        
        # Display all roles
        roles = Role.objects.all().prefetch_related('permissions', 'users')
        
        for role in roles:
            self.stdout.write(f'\n\n🔐 {role.name}')
            if role.is_system_role:
                self.stdout.write(self.style.WARNING('   [SYSTEM ROLE - Cannot be deleted]'))
            self.stdout.write(f'   {role.description}')
            self.stdout.write(f'   Users: {role.users.count()}')
            self.stdout.write(f'   Permissions: {role.permissions.count()}')
            
            # Group permissions by module
            permissions_by_module = {}
            for perm in role.permissions.all():
                if perm.module not in permissions_by_module:
                    permissions_by_module[perm.module] = []
                permissions_by_module[perm.module].append(perm.name)
            
            if permissions_by_module:
                self.stdout.write('\n   Permissions by Module:')
                for module, perms in sorted(permissions_by_module.items()):
                    self.stdout.write(f'     • {module.upper()}: {", ".join(perms)}')
        
        # Display users and their roles
        self.stdout.write('\n\n' + '=' * 80)
        self.stdout.write(self.style.WARNING('\n👥 USERS & THEIR ROLES\n'))
        
        users = User.objects.select_related('role').all()
        for user in users:
            role_name = user.role.name if user.role else 'No Role Assigned'
            self.stdout.write(f'  • {user.username} ({user.email or "no email"}) → {role_name}')
        
        # Display permission statistics
        self.stdout.write('\n\n' + '=' * 80)
        self.stdout.write(self.style.WARNING('\n📈 STATISTICS\n'))
        self.stdout.write(f'  Total Roles: {Role.objects.count()}')
        self.stdout.write(f'  Total Permissions: {Permission.objects.count()}')
        self.stdout.write(f'  Total Users: {User.objects.count()}')
        self.stdout.write(f'  Users with Roles: {User.objects.filter(role__isnull=False).count()}')
        self.stdout.write(f'  Users without Roles: {User.objects.filter(role__isnull=True).count()}')
        
        self.stdout.write('\n' + '=' * 80 + '\n')
