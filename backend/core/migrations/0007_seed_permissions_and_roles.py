# Generated migration file
from django.db import migrations


def seed_permissions_and_roles(apps, schema_editor):
    """Seed default permissions and roles"""
    Permission = apps.get_model('core', 'Permission')
    Role = apps.get_model('core', 'Role')
    
    # Define all permissions based on the permission matrix
    permissions_data = [
        # Dashboard
        {'code': 'view_dashboard', 'name': 'View Dashboard', 'module': 'dashboard', 'description': 'Access to view the dashboard'},
        {'code': 'export_data', 'name': 'Export Data', 'module': 'dashboard', 'description': 'Export dashboard data to PDF/Excel'},
        
        # Projects
        {'code': 'view_projects', 'name': 'View Projects', 'module': 'projects', 'description': 'View project list and details'},
        {'code': 'create_project', 'name': 'Create Projects', 'module': 'projects', 'description': 'Create new projects'},
        {'code': 'edit_project', 'name': 'Edit Projects', 'module': 'projects', 'description': 'Edit existing projects'},
        {'code': 'delete_project', 'name': 'Delete Projects', 'module': 'projects', 'description': 'Delete projects'},
        
        # Evaluations
        {'code': 'view_evaluations', 'name': 'View Evaluations', 'module': 'evaluations', 'description': 'View evaluation list and details'},
        {'code': 'assign_evaluations', 'name': 'Assign Evaluations', 'module': 'evaluations', 'description': 'Assign evaluations to inspectors'},
        {'code': 'conduct_evaluations', 'name': 'Conduct Evaluations', 'module': 'evaluations', 'description': 'Perform evaluations and submit reports'},
        {'code': 'approve_evaluations', 'name': 'Approve/Disapprove Evaluations', 'module': 'evaluations', 'description': 'Approve or disapprove evaluation results'},
        
        # GIS Map
        {'code': 'view_map', 'name': 'View Map', 'module': 'map', 'description': 'Access GIS map visualization'},
        {'code': 'edit_layers', 'name': 'Edit Layers', 'module': 'map', 'description': 'Modify map layers and settings'},
        
        # Users
        {'code': 'view_users', 'name': 'View Users', 'module': 'users', 'description': 'View user list'},
        {'code': 'manage_users', 'name': 'Manage Users', 'module': 'users', 'description': 'Create, edit, delete users'},
        {'code': 'manage_roles', 'name': 'Manage Roles', 'module': 'users', 'description': 'Manage roles and permissions'},
        
        # Finance
        {'code': 'view_claims', 'name': 'View Claims', 'module': 'finance', 'description': 'View payment claims'},
        {'code': 'create_claim', 'name': 'Create Claims', 'module': 'finance', 'description': 'Create new payment claims'},
        {'code': 'approve_claim', 'name': 'Approve Claims', 'module': 'finance', 'description': 'Approve payment claims'},
        
        # Investigations
        {'code': 'view_investigations', 'name': 'View Investigations', 'module': 'investigations', 'description': 'View investigation cases'},
        {'code': 'create_investigation', 'name': 'Create Investigations', 'module': 'investigations', 'description': 'Create new investigation cases'},
        {'code': 'update_investigation', 'name': 'Update Investigations', 'module': 'investigations', 'description': 'Update investigation status and notes'},
        
        # Grievances
        {'code': 'view_grievances', 'name': 'View Grievances', 'module': 'grievances', 'description': 'View grievance reports'},
        {'code': 'manage_grievances', 'name': 'Manage Grievances', 'module': 'grievances', 'description': 'Create and manage grievances'},
        
        # Organizations
        {'code': 'view_organizations', 'name': 'View Organizations', 'module': 'organizations', 'description': 'View organization list'},
        {'code': 'manage_organizations', 'name': 'Manage Organizations', 'module': 'organizations', 'description': 'Create, edit, delete organizations'},
        
        # Reports
        {'code': 'view_reports', 'name': 'View Reports', 'module': 'reports', 'description': 'Access reporting features'},
        {'code': 'export_reports', 'name': 'Export Reports', 'module': 'reports', 'description': 'Export reports to various formats'},
    ]
    
    # Create permissions
    permission_objects = {}
    for perm_data in permissions_data:
        perm, created = Permission.objects.get_or_create(
            code=perm_data['code'],
            defaults={
                'name': perm_data['name'],
                'module': perm_data['module'],
                'description': perm_data['description']
            }
        )
        permission_objects[perm_data['code']] = perm
    
    # Define roles with their permissions
    roles_data = [
        {
            'name': 'Administrator',
            'description': 'Full access to all system features and settings',
            'is_system_role': True,
            'permissions': [p['code'] for p in permissions_data]  # All permissions
        },
        {
            'name': 'Project Manager',
            'description': 'Manage projects, evaluations, and teams',
            'is_system_role': True,
            'permissions': [
                'view_dashboard', 'export_data',
                'view_projects', 'create_project', 'edit_project',
                'view_evaluations', 'assign_evaluations', 'approve_evaluations',
                'view_map',
                'view_users',
                'view_claims', 'create_claim',
                'view_investigations', 'create_investigation', 'update_investigation',
                'view_grievances', 'manage_grievances',
                'view_organizations', 'manage_organizations',
                'view_reports', 'export_reports',
            ]
        },
        {
            'name': 'Evaluator',
            'description': 'Conduct evaluations and submit reports',
            'is_system_role': True,
            'permissions': [
                'view_dashboard',
                'view_projects',
                'view_evaluations', 'conduct_evaluations',
                'view_map',
                'view_claims',
                'view_investigations', 'update_investigation',
                'view_grievances',
                'view_organizations',
                'view_reports',
            ]
        },
        {
            'name': 'Viewer',
            'description': 'Read-only access to dashboards and reports',
            'is_system_role': True,
            'permissions': [
                'view_dashboard',
                'view_projects',
                'view_evaluations',
                'view_map',
                'view_claims',
                'view_investigations',
                'view_grievances',
                'view_organizations',
                'view_reports',
            ]
        },
    ]
    
    # Create roles and assign permissions
    for role_data in roles_data:
        role, created = Role.objects.get_or_create(
            name=role_data['name'],
            defaults={
                'description': role_data['description'],
                'is_system_role': role_data['is_system_role']
            }
        )
        
        # Assign permissions to role
        if created or role.permissions.count() == 0:
            for perm_code in role_data['permissions']:
                if perm_code in permission_objects:
                    role.permissions.add(permission_objects[perm_code])


def migrate_existing_users(apps, schema_editor):
    """Migrate existing users from legacy roles to new role system"""
    User = apps.get_model('core', 'User')
    Role = apps.get_model('core', 'Role')
    
    # Get role objects
    try:
        admin_role = Role.objects.get(name='Administrator')
        pm_role = Role.objects.get(name='Project Manager')
        evaluator_role = Role.objects.get(name='Evaluator')
        viewer_role = Role.objects.get(name='Viewer')
    except Role.DoesNotExist:
        # Roles not created yet, skip migration
        return
    
    # Mapping from legacy roles to new roles
    role_mapping = {
        'ADMIN': admin_role,
        'PM': pm_role,
        'INSPECTOR': evaluator_role,
        'FINANCE': pm_role,  # Finance users get PM role
        'CONTRACTOR': viewer_role,
    }
    
    # Migrate all users
    for user in User.objects.all():
        # Assign new role based on legacy role
        if user.legacy_role and user.legacy_role in role_mapping and not user.role:
            user.role = role_mapping[user.legacy_role]
            user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_rbac_models'),
    ]

    operations = [
        migrations.RunPython(seed_permissions_and_roles),
        migrations.RunPython(migrate_existing_users),
    ]
