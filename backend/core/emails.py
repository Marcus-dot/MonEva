from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_plain_notification_email(recipient_email, recipient_name, title, message,
                                   action_url='', notification_type=''):
    """
    Send a simple notification email. Used by Notification.create_notification()
    so that every in-app notification also reaches users via email.
    """
    from .models import EmailLog
    try:
        html = render_to_string('emails/plain_notification.html', {
            'recipient_name': recipient_name,
            'title': title,
            'message': message,
            'action_url': action_url,
        })

        msg = EmailMultiAlternatives(
            subject=f'[MonEva] {title}',
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)

        EmailLog.objects.create(
            recipient=recipient_email,
            notification_type=notification_type or 'general',
            status=EmailLog.Status.SENT,
            sent_at=timezone.now()
        )
    except Exception as e:
        logger.error(f"Plain notification email failed for {recipient_email}: {e}")
        try:
            EmailLog.objects.create(
                recipient=recipient_email,
                notification_type=notification_type or 'general',
                status=EmailLog.Status.FAILED,
                error_message=str(e)
            )
        except Exception:
            pass


class EmailTemplates:
    """Email template renderer for system notifications"""

    @staticmethod
    def send_notification_email(recipient_email, notification_type, context):
        """
        Send a notification email using HTML templates.

        Args:
            recipient_email: Email address to send to
            notification_type: Type of notification (e.g., 'grievance_opened')
            context: Dict with template context (subject, message, action_url, recipient_name, etc.)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Map notification types to templates
        templates = {
            'grievance_opened': 'emails/grievance_opened.html',
            'grievance_status_change': 'emails/grievance_status_change.html',
            'investigation_assigned': 'emails/investigation_assigned.html',
            'claim_pending_approval': 'emails/claim_pending_approval.html',
            'milestone_deadline': 'emails/milestone_deadline.html',
            'contract_expiry': 'emails/contract_expiry.html',
            'approval_escalation': 'emails/approval_escalation.html',
        }

        template_path = templates.get(notification_type)
        if not template_path:
            logger.warning(f"Unknown notification type: {notification_type}")
            return False

        try:
            from .models import EmailLog

            # Render HTML template
            html_content = render_to_string(template_path, context)

            # Create email
            msg = EmailMultiAlternatives(
                subject=context.get('subject', 'MonEva Notification'),
                body=f"View: {context.get('action_url', '')}",  # text fallback
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            msg.attach_alternative(html_content, "text/html")

            # Send email
            msg.send(fail_silently=False)

            # Log success
            EmailLog.objects.create(
                recipient=recipient_email,
                notification_type=notification_type,
                status=EmailLog.Status.SENT,
                sent_at=timezone.now()
            )

            logger.info(f"Email sent to {recipient_email} ({notification_type})")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            try:
                from .models import EmailLog
                EmailLog.objects.create(
                    recipient=recipient_email,
                    notification_type=notification_type,
                    status=EmailLog.Status.FAILED,
                    error_message=str(e)
                )
            except Exception:
                pass
            return False

    @staticmethod
    def send_daily_digest(user_email, recipient_name, pending_items):
        """
        Send morning digest of pending actions.

        Args:
            user_email: User's email address
            recipient_name: User's display name
            pending_items: Dict with keys: claims, grievances, investigations, approvals

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            from .models import EmailLog
            html_content = render_to_string('emails/daily_digest.html', {
                'recipient_name': recipient_name,
                'pending_claims': pending_items.get('claims', []),
                'pending_grievances': pending_items.get('grievances', []),
                'pending_investigations': pending_items.get('investigations', []),
                'pending_approvals': pending_items.get('approvals', []),
                'date': timezone.now().date(),
            })

            msg = EmailMultiAlternatives(
                subject='[MonEva] Your Daily Digest',
                body='View your pending items in MonEva',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            EmailLog.objects.create(
                recipient=user_email,
                notification_type='daily_digest',
                status=EmailLog.Status.SENT,
                sent_at=timezone.now()
            )

            logger.info(f"Daily digest sent to {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send daily digest to {user_email}: {str(e)}")
            try:
                from .models import EmailLog
                EmailLog.objects.create(
                    recipient=user_email,
                    notification_type='daily_digest',
                    status=EmailLog.Status.FAILED,
                    error_message=str(e)
                )
            except Exception:
                pass
            return False
