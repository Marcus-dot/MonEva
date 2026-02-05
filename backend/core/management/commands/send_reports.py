import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMessage
from core.models import ScheduledReport
import requests
import json

class Command(BaseCommand):
    help = 'Send scheduled reports to stakeholders'

    def handle(self, *args, **options):
        self.stdout.write("Checking for scheduled reports due to be sent...")
        
        now = timezone.now()
        due_reports = ScheduledReport.objects.filter(
            is_active=True,
            next_run_at__lte=now
        )

        for report in due_reports:
            self.stdout.write(f"Processing report: {report.report_name} for {report.user.username}")
            
            try:
                # 1. Generate Report Content (Mocking the attachment generation for now)
                # In a real scenario, this would call the export logic
                content = f"Automated {report.report_type} Report: {report.report_name}\n"
                content += f"Frequency: {report.frequency}\n"
                content += f"Generated At: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                content += "-" * 40 + "\n"
                content += "This is an automated report from MonEva.\n"
                
                # 2. Setup Email
                subject = f"[MonEva] Scheduled Report: {report.report_name}"
                email = EmailMessage(
                    subject,
                    content,
                    'reports@moneva.org',
                    report.recipients,
                )
                
                # 3. Simulate Attachment
                # In real implementation: attachment = generate_pdf_or_excel(report)
                # email.attach(f"{report.report_name}.{report.format.lower()}", attachment, 'application/pdf')
                
                email.send()
                
                # 4. Update ScheduledReport state
                report.last_sent_at = now
                
                # Calculate next run time
                if report.frequency == ScheduledReport.Frequency.DAILY:
                    report.next_run_at = now + datetime.timedelta(days=1)
                elif report.frequency == ScheduledReport.Frequency.WEEKLY:
                    report.next_run_at = now + datetime.timedelta(weeks=1)
                elif report.frequency == ScheduledReport.Frequency.MONTHLY:
                    # Approximation
                    report.next_run_at = now + datetime.timedelta(days=30)
                
                report.save()
                self.stdout.write(self.style.SUCCESS(f"Successfully sent report: {report.report_name}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send report {report.id}: {str(e)}"))

