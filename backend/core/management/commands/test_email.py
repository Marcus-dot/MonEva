from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings
from core.models import User, Notification, EmailLog
from core.emails import EmailTemplates


class Command(BaseCommand):
    help = 'Send test emails to verify SMTP configuration'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address to send test to')
        parser.add_argument('--type', type=str, default='notification',
                          help='Test email type: notification, digest, direct')

    def handle(self, *args, **options):
        email = options.get('email')
        test_type = options.get('type')

        if not email:
            # Default to first admin user
            admin = User.objects.filter(is_staff=True).first()
            if not admin or not admin.email:
                raise CommandError('No email provided and no admin user with email found')
            email = admin.email
            self.stdout.write(f"Using admin email: {email}")

        try:
            if test_type == 'direct':
                self.send_direct_test(email)
            elif test_type == 'digest':
                self.send_digest_test(email)
            else:
                self.send_notification_test(email)

        except Exception as e:
            raise CommandError(f"Failed to send test email: {str(e)}")

    def send_direct_test(self, email):
        """Send a direct SMTP test email"""
        try:
            send_mail(
                subject='[TEST] MonEva Email Configuration Test',
                message='This is a test email from MonEva to verify SMTP configuration is working correctly.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Test email sent to {email}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test email: {str(e)}'))
            raise

    def send_notification_test(self, email):
        """Send a test notification email"""
        context = {
            'recipient_name': 'Test User',
            'subject': '[TEST] Sample Grievance Notification',
            'grievance_id': 'TEST-001',
            'category': 'Quality of Work',
            'submitted_by': 'Community Member',
            'date': '15 March 2026',
            'status': 'Open',
            'summary': 'This is a test grievance notification to verify the email system is working correctly.',
            'action_url': 'http://localhost:3000/dashboard/grievances/TEST-001'
        }

        success = EmailTemplates.send_notification_email(
            recipient_email=email,
            notification_type='grievance_opened',
            context=context
        )

        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ Test notification email sent to {email}'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test notification email'))
            raise CommandError("Email sending failed")

    def send_digest_test(self, email):
        """Send a test daily digest email"""
        pending_items = {
            'claims': [
                {
                    'contractor_name': 'ABC Contractors Ltd',
                    'amount': 50000.00,
                    'project_name': 'Road Rehabilitation Project',
                    'submitted_date': '14 March 2026'
                }
            ],
            'grievances': [
                {
                    'category': 'Delayed Payment',
                    'summary': 'Contractor payment delayed by 10 days',
                    'created_date': '13 March 2026'
                }
            ],
            'investigations': [
                {
                    'title': 'Investigation into contract breach',
                    'project_name': 'Water Supply Project',
                    'assigned_date': '12 March 2026'
                }
            ],
            'approvals': [
                {
                    'type': 'Payment Claim',
                    'title': 'ZMW 75,000 claim from XYZ Suppliers',
                    'pending_since': '13 March 2026'
                }
            ]
        }

        success = EmailTemplates.send_daily_digest(
            user_email=email,
            recipient_name='Test User',
            pending_items=pending_items
        )

        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ Test digest email sent to {email}'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test digest email'))
            raise CommandError("Email sending failed")
