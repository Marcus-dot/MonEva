from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, permissions, status, serializers, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Organization, ActivityLog, DashboardPreference, Permission, Role, Notification, ScheduledReport, Document
from projects.models import Project, Milestone, Contract
from finance.models import PaymentClaim
from investigations.models import Investigation
from assessments.models import Inspection
from .serializers import (
    UserSerializer,
    OrganizationSerializer,
    ActivityLogSerializer,
    DashboardPreferenceSerializer,
    PermissionSerializer,
    RoleSerializer,
    NotificationSerializer,
    ScheduledReportSerializer
)
from projects.serializers import MilestoneSerializer
from .ml_utils import MLPredictor, AnomalyDetector, ThemeExtractor
import datetime
from .permissions import IsAdmin

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view for available permissions.
    Used to display permission options when creating/editing roles.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['module']
    ordering_fields = ['module', 'code', 'name']
    ordering = ['module', 'code']

class RoleViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for roles.
    Only admins can create, update, or delete roles.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of system roles"""
        role = self.get_object()
        if role.is_system_role:
            return Response(
                {'error': 'Cannot delete system roles'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        """Assign multiple permissions to a role"""
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        
        # Clear existing permissions and add new ones
        role.permissions.clear()
        for perm_id in permission_ids:
            try:
                permission = Permission.objects.get(id=perm_id)
                role.permissions.add(permission)
            except Permission.DoesNotExist:
                pass
        
        serializer = self.get_serializer(role)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get all users with this role"""
        role = self.get_object()
        users = role.users.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view for Compliance/Audit logs.
    Restricted to Admins.
    """
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['actor', 'action', 'target_model']

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """Assign a role to a user"""
        user = self.get_object()
        role_id = request.data.get('role_id')
        
        try:
            role = Role.objects.get(id=role_id)
            user.role = role
            user.save()
            
            # Log the role assignment
            ActivityLog.objects.create(
                actor=request.user,
                action='UPDATE',
                target_model='User',
                target_id=str(user.id),
                details={'role_assigned': role.name}
            )
            
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except Role.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        password = request.data.get('password')

        if not password or len(password) < 8:
            return Response({'error': 'Password must be at least 8 characters long.'}, status=400)

        user.set_password(password)
        user.save()
        return Response({'status': 'Password reset successfully'})

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['type']

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        from django.utils import timezone
        from datetime import timedelta
        import logging
        from django.db.models import Count, Sum, Avg, F
        from django.db.models.functions import TruncMonth, Coalesce
        from dateutil.relativedelta import relativedelta

        logger = logging.getLogger(__name__)

        time_range = request.query_params.get('time_range', '1y')
        now = timezone.now()

        if time_range == '7d':
            start_date = now - timedelta(days=7)
        elif time_range == '30d':
            start_date = now - timedelta(days=30)
        elif time_range == '90d':
            start_date = now - timedelta(days=90)
        else: # Default 1y
            start_date = now - timedelta(days=365)

        # --- Key Metrics ---
        # Using start_date for Project since it doesn't have created_at
        total_projects = Project.objects.filter(
            status=Project.Status.ACTIVE
        ).count()

        # Milestone doesn't have updated_at, using due_date or just count all progress
        pending_inspections = Milestone.objects.filter(
            status=Milestone.Status.IN_PROGRESS
        ).count()

        recent_claims = PaymentClaim.objects.filter(
            status=PaymentClaim.Status.SUBMITTED,
            created_at__gte=start_date
        ).count()

        # Investigation use opened_at
        open_investigations = Investigation.objects.filter(
            status__in=[Investigation.Status.OPEN, Investigation.Status.IN_PROGRESS]
        ).count()

        critical_investigations = Investigation.objects.filter(
            severity=Investigation.Severity.CRITICAL,
            opened_at__gte=start_date
        ).exclude(status=Investigation.Status.CLOSED).count()

        # --- Beneficiaries ---
        from projects.models import Beneficiary
        
        total_beneficiaries = Beneficiary.objects.count()
        
        # Group by location (State/Region) - simplistic grouping by exact string match
        top_locations = Beneficiary.objects.values('location').annotate(
            value=Count('id')
        ).order_by('-value')[:7]
        
        beneficiary_distribution = [
            {"name": item['location'] or "Unknown", "value": item['value']} 
            for item in top_locations
        ]
        
        # --- Funding Trend (Allocated vs Utilized) ---
        # Allocated = Milestone Values due in that month
        # Utilized = Payment Claims paid in that month
        
        # Generate last 12 months/periods based on time_range keys
        # For simplicity, we stick to month-based aggregation
        
        allocated_qs = Milestone.objects.filter(
            due_date__gte=start_date
        ).annotate(
            month=TruncMonth('due_date')
        ).values('month').annotate(
            total=Sum('value_amount')
        ).order_by('month')
        
        utilized_qs = PaymentClaim.objects.filter(
            claim_date__gte=start_date,
            status=PaymentClaim.Status.PAID
        ).annotate(
            month=TruncMonth('claim_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        # Merge into a single timeline
        timeline_map = {}
        
        # Helper to format month
        def get_month_key(d):
            return d.strftime('%b') if d else 'Unknown'

        # Initialize map with dates from range (optional, skipping for brevity, will sparse fill)
        
        for item in allocated_qs:
            has_month = item.get('month')
            if has_month:
                key = get_month_key(has_month)
                if key not in timeline_map: timeline_map[key] = {"name": key, "allocated": 0, "utilized": 0, "sort_date": has_month}
                timeline_map[key]["allocated"] += float(item['total'] or 0)
                
        for item in utilized_qs:
            has_month = item.get('month')
            if has_month:
                key = get_month_key(has_month)
                if key not in timeline_map: timeline_map[key] = {"name": key, "allocated": 0, "utilized": 0, "sort_date": has_month}
                timeline_map[key]["utilized"] += float(item['total'] or 0)
                
        funding_trend = sorted(list(timeline_map.values()), key=lambda x: x['sort_date'])
        
        # Remove sort_date before sending
        for item in funding_trend:
            del item['sort_date']

        # --- Impact Score (Calculated) ---
        # Proxy: Percentage of Completed Milestones vs Total Milestones * 10
        total_milestones = Milestone.objects.count()
        completed_milestones = Milestone.objects.filter(status=Milestone.Status.COMPLETED).count()
        
        impact_score = 0
        if total_milestones > 0:
            impact_score = round((completed_milestones / total_milestones) * 10, 1)

        # --- Critical Path Alerts (New Phase 3) ---
        from projects.performance import calculate_project_risk
        active_projects = Project.objects.filter(status=Project.Status.ACTIVE).order_by('-id')
        critical_alerts = []
        for p in active_projects:
            risk = calculate_project_risk(p)
            if risk['score'] > 0:
                critical_alerts.append({
                    "project_id": str(p.id),
                    "project_name": p.name,
                    "score": risk['score'],
                    "level": risk['level'],
                    "factors": risk['factors']
                })
        
        # Sort by score descending
        critical_alerts = sorted(critical_alerts, key=lambda x: x['score'], reverse=True)[:20]

        logger.info(f"Dashboard Stats: range={time_range}, projects={total_projects}, alerts={len(critical_alerts)}")

        return Response({
            "total_projects": total_projects,
            "pending_inspections": pending_inspections,
            "recent_claims": recent_claims,
            "open_investigations": open_investigations,
            "critical_investigations": critical_investigations,
            # New Real Data Fields
            "total_beneficiaries": total_beneficiaries,
            "beneficiary_distribution": beneficiary_distribution,
            "funding_trend": funding_trend,
            "impact_score": impact_score,
            "critical_alerts": critical_alerts
        })

class ReportsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export standard reports to Excel or PDF"""
        report_type = request.query_params.get('type', 'portfolio')
        fmt = request.query_params.get('format', 'csv')
        
        from django.http import HttpResponse
        import io
        
        # 1. Gather Data
        data = []
        filename = f"{report_type}_report"
        
        if report_type == 'portfolio':
            projects = Project.objects.all()
            data = [['Project Name', 'Type', 'Status', 'Start Date', 'Thematic Area']]
            for p in projects:
                data.append([p.name, p.type, p.status, str(p.start_date), p.thematic_area])
        
        elif report_type == 'financial':
            from finance.models import PaymentClaim
            claims = PaymentClaim.objects.all()
            data = [['Claim ID', 'Project', 'Contractor', 'Amount', 'Date', 'Status']]
            for c in claims:
                data.append([
                    str(c.id)[:8],
                    c.contract.project.name,
                    c.contract.contractor.name,
                    float(c.amount),
                    str(c.claim_date),
                    c.status
                ])
                
        elif report_type == 'impact':
            from assessments.models import Inspection
            inspections = Inspection.objects.all()
            data = [['Project', 'Milestone', 'Quality Verdict', 'Inspected At', 'Notes']]
            for i in inspections:
                data.append([
                    i.milestone.contract.project.name if i.milestone else 'N/A',
                    i.milestone.title if i.milestone else 'N/A',
                    i.quality_verdict,
                    str(i.inspected_at.date()),
                    (i.notes[:50] + '...') if i.notes and len(i.notes) > 50 else (i.notes or '')
                ])
        
        # 2. Format Response
        if fmt == 'csv':
            import csv
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            writer = csv.writer(response)
            for row in data:
                writer.writerow(row)
            return response
            
        elif fmt == 'xlsx':
            from openpyxl import Workbook
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
            wb = Workbook()
            ws = wb.active
            ws.title = "Report"
            for row in data:
                ws.append(row)
            wb.save(response)
            return response
            
        elif fmt == 'pdf':
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            elements.append(Paragraph(f"MonEva Standard Report: {report_type.capitalize()}", styles['Title']))
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A4D2E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            
            doc.build(elements)
            response.write(buffer.getvalue())
            buffer.close()
            return response
            
        return Response({"error": "Invalid format"}, status=400)

    @action(detail=False, methods=['get'])
    def project_summary(self, request):
        projects = Project.objects.all()
        data = []
        for p in projects:
            data.append({
                "name": p.name,
                "type": p.type,
                "csr_focus": p.csr_focus,
                "status": p.status,
                "start_date": p.start_date,
                "completion": 0 # Placeholder for calculated progress
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def financial_summary(self, request):
        from projects.models import Contract
        from finance.models import PaymentClaim
        from django.db.models import Sum

        target_currency = request.query_params.get('currency', 'ZMW') # Default to ZMW as requested
        exchange_rate = 27 if target_currency == 'ZMW' else 1 # Simple mock rate: 1 USD = 27 ZMW

        # Base values are in USD
        total_budget_usd = Contract.objects.aggregate(Sum('total_value'))['total_value__sum'] or 0
        total_disbursed_usd = PaymentClaim.objects.filter(status=PaymentClaim.Status.PAID).aggregate(Sum('amount'))['amount__sum'] or 0
        pending_claims_usd = PaymentClaim.objects.filter(status=PaymentClaim.Status.SUBMITTED).aggregate(Sum('amount'))['amount__sum'] or 0

        return Response({
            "total_budget": total_budget_usd * exchange_rate,
            "total_disbursed": total_disbursed_usd * exchange_rate,
            "pending_claims": pending_claims_usd * exchange_rate,
            "currency": target_currency
        })

    @action(detail=False, methods=['get'])
    def portfolio_trends(self, request):
        """Historical aggregation of KRA scores across all projects"""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models.functions import TruncMonth
        from django.db.models import Count

        # We'll return the last 6 months of trends
        six_months_ago = timezone.now() - timedelta(days=180)

        # Aggregate by month using start_date as a proxy for trend timing
        trends = Project.objects.filter(
            start_date__gte=six_months_ago.date()
        ).annotate(
            month=TruncMonth('start_date')
        ).values('month').annotate(
            project_count=Count('id')
        ).order_by('month')

        data = []
        for t in trends:
            # Mock impact score based on project count (in real app, would use actual metrics)
            base_score = 65.0
            score = base_score + (t['project_count'] * 2)  # More projects = higher score
            data.append({
                "month": t['month'].strftime('%b %Y'),
                "count": t['project_count'],
                "score": min(float(score), 100.0)  # Cap at 100
            })

        return Response(data)

    @action(detail=False, methods=['get'])
    def project_comparison(self, request):
        """Side-by-side metrics for selected projects"""
        from django.db.models import Count, Sum
        
        ids = request.query_params.getlist('ids')
        if not ids:
            return Response({"error": "No project IDs provided"}, status=400)

        projects = Project.objects.filter(id__in=ids)
        comparison_data = []

        for p in projects:
            # 1. Completion Score (Milestone Based)
            total_milestones = p.contracts.aggregate(Count('milestones'))['milestones__count'] or 0
            completed_milestones = Milestone.objects.filter(
                contract__project=p, 
                status=Milestone.Status.COMPLETED
            ).count()
            
            completion = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
            
            # 2. Budget Utilization (Payment Claim vs Contract Value)
            total_value = p.contracts.aggregate(Sum('total_value'))['total_value__sum'] or 0
            paid_claims = PaymentClaim.objects.filter(
                contract__project=p,
                status=PaymentClaim.Status.PAID
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            utilization = (float(paid_claims) / float(total_value) * 100) if total_value > 0 else 0

            # 3. KRA Scores (Derived from indicators)
            # For demo/MVP, we map Indicators to KRAs or just use thematic proxy
            # In a full app, each Indicator would link to a KRA.
            kra_scores = {
                "SOCIO_ECONOMIC": 85 if p.thematic_area == 'EDUCATION' else 60,
                "REPUTATION": 75 if p.status == Project.Status.ACTIVE else 90,
                "FINANCIAL": min(utilization * 1.2, 100),
                "OPERATIONAL": completion
            }

            comparison_data.append({
                "id": str(p.id),
                "name": p.name,
                "type": p.type,
                "status": p.status,
                "metrics": {
                    "completion": round(completion, 1),
                    "budget_utilization": round(utilization, 1),
                    "kra_scores": kra_scores
                }
            })

        return Response({
            "comparison": comparison_data,
            "benchmarks": {
                "avg_completion": 68,
                "avg_budget_utilization": 75,
                "avg_kra_score": 70
            }
        })

    @action(detail=False, methods=['get'])
    def predictive_analytics(self, request):
        """AI-Powered predictive insights for active projects"""
        projects = Project.objects.filter(status='ACTIVE')
        
        project_features = []
        for p in projects:
            duration = (p.end_date - p.start_date).days
            milestones_count = Milestone.objects.filter(contract__project=p).count()
            
            project_features.append({
                "id": str(p.id),
                "name": p.name,
                "type": p.type,
                "duration_days": duration,
                "num_milestones": milestones_count
            })
            
        # Predict delays
        delays = MLPredictor.predict_delays(project_features)
        
        # Analyze themes from recent inspections
        inspections = Inspection.objects.all().order_by('-created_at')[:10]
        notes = [insp.notes for insp in inspections if insp.notes]
        themes_list = ThemeExtractor.extract_themes(notes)
        
        # Flatten and count themes
        from collections import Counter
        all_themes = [t for sublist in themes_list for t in sublist]
        theme_counts = dict(Counter(all_themes))
        
        results = []
        for p_feat in project_features:
            delay_days = delays.get(p_feat['id'], 0)
            
            # Auto-RAG status logic
            rag_status = 'GREEN'
            if delay_days > 10: rag_status = 'RED'
            elif delay_days > 5: rag_status = 'AMBER'
            
            results.append({
                "project_id": p_feat['id'],
                "project_name": p_feat['name'],
                "predicted_delay_days": delay_days,
                "rag_suggestion": rag_status,
                "risk_factors": ["High complexity"] if delay_days > 10 else ["On track"]
            })
            
        return Response({
            "predictions": results,
            "top_themes": theme_counts,
            "analysis_date": datetime.datetime.now().isoformat()
        })

    @action(detail=False, methods=['get'])
    def claim_anomalies(self, request):
        """AI-Powered anomaly detection for payment claims"""
        claims = PaymentClaim.objects.all().order_by('-created_at')[:50]
        if not claims:
            return Response({"anomalies": [], "message": "Insufficient data"})
            
        claim_data = [{"id": str(c.id), "amount": float(c.amount)} for c in claims]
        
        anomaly_ids = AnomalyDetector.detect_claim_anomalies(claim_data)
        
        results = []
        for c in claims:
            if str(c.id) in anomaly_ids:
                results.append({
                    "id": str(c.id),
                    "amount": c.amount,
                    "contractor": c.contract.contractor.name,
                    "reason": "Statistical outlier in amount relative to history",
                    "risk_level": "HIGH"
                })
                
        return Response({
            "anomalies": results,
            "total_scanned": len(claims),
            "anomaly_count": len(results)
        })

from .models import DashboardPreference
from .serializers import DashboardPreferenceSerializer

class DashboardPreferenceViewSet(viewsets.ModelViewSet):
    """User dashboard preferences - only access own preferences"""
    serializer_class = DashboardPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only access their own preferences
        return DashboardPreference.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Automatically set user to current user
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get', 'post', 'patch'])
    def my_preference(self, request):
        """Get or update current user's preferences"""
        pref, created = DashboardPreference.objects.get_or_create(user=request.user)
        
        if request.method in ['POST', 'PATCH']:
            serializer = self.get_serializer(pref, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
        serializer = self.get_serializer(pref)
        return Response(serializer.data)

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user notifications.
    Users can only see their own notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only notifications for the current user"""
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a single notification as read"""
        from django.utils import timezone
        
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user"""
        from django.utils import timezone
        
        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated_count} notifications marked as read',
            'count': updated_count
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return Response({'count': count})

class GlobalSearchViewSet(viewsets.ViewSet):
    """
    Global search across all major entities in the system
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """
        Search across projects, evaluations, investigations, grievances, and users
        Query parameter: q (search query)
        """
        from django.db.models import Q
        from grievances.models import Grievance
        from projects.serializers import ProjectSerializer
        from assessments.serializers import InspectionSerializer
        from investigations.serializers import InvestigationSerializer
        from grievances.serializers import GrievanceSerializer
        
        query = request.query_params.get('q', '').strip()
        
        if not query or len(query) < 2:
            return Response({
                'results': [],
                'count': 0,
                'message': 'Please enter at least 2 characters to search'
            })
        
        results = {
            'projects': [],
            'evaluations': [],
            'investigations': [],
            'grievances': [],
            'users': [],
            'count': 0
        }
        
        # Search Projects
        projects = Project.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        results['projects'] = [{
            'id': str(p.id),
            'title': p.name,
            'subtitle': p.description[:100] if p.description else 'No description',
            'url': f'/dashboard/projects/{p.id}',
            'type': 'project',
            'status': p.status
        } for p in projects]
        
        # Search Evaluations/Inspections
        inspections = Inspection.objects.filter(
            Q(milestone__title__icontains=query) |
            Q(milestone__contract__project__name__icontains=query) |
            Q(notes__icontains=query)
        ).select_related('milestone', 'milestone__contract', 'milestone__contract__project')[:5]
        results['evaluations'] = [{
            'id': str(i.id),
            'title': f"Evaluation: {i.milestone.contract.project.name if i.milestone and i.milestone.contract and i.milestone.contract.project else 'Unknown'}",
            'subtitle': i.inspected_at.strftime('%b %d, %Y') if i.inspected_at else 'No date',
            'url': f'/dashboard/inspections/{i.id}',
            'type': 'evaluation',
            'status': i.quality_verdict
        } for i in inspections]
        
        # Search Investigations
        investigations = Investigation.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        results['investigations'] = [{
            'id': str(inv.id),
            'title': inv.title,
            'subtitle': f"{inv.get_severity_display()} - {inv.get_status_display()}",
            'url': f'/dashboard/investigations/{inv.id}',
            'type': 'investigation',
            'status': inv.status
        } for inv in investigations]
        
        # Search Grievances
        grievances = Grievance.objects.filter(
            Q(description__icontains=query) |
            Q(reporter_contact__icontains=query) |
            Q(project__name__icontains=query)
        ).select_related('project')[:5]
        results['grievances'] = [{
            'id': str(g.id),
            'title': f"Grievance: {g.description[:50]}..." if len(g.description) > 50 else f"Grievance: {g.description}",
            'subtitle': f"From: {g.reporter_contact} - {g.get_priority_display()}",
            'url': f'/dashboard/grievances/{g.id}',
            'type': 'grievance',
            'status': g.status
        } for g in grievances]
        
        # Search Users (only for admins)
        if request.user.is_staff or (request.user.role and request.user.role.name == 'Administrator'):
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            )[:5]
            results['users'] = [{
                'id': str(u.id),
                'title': f"{u.first_name} {u.last_name}" if u.first_name else u.username,
                'subtitle': u.email,
                'url': f'/dashboard/users',
                'type': 'user',
                'status': 'active' if u.is_active else 'inactive'
            } for u in users]
        
        # Calculate total count
        results['count'] = (
            len(results['projects']) +
            len(results['evaluations']) +
            len(results['investigations']) +
            len(results['grievances']) +
            len(results['users'])
        )
        
        return Response(results)

class ScheduledReportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing automated report schedules"""
    serializer_class = ScheduledReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ScheduledReport.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.ReadOnlyField(source='uploaded_by.get_full_name')
    file_url = serializers.ReadOnlyField()
    file_extension = serializers.ReadOnlyField()

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'file_size', 'created_at']


class DocumentViewSet(viewsets.ModelViewSet):
    """
    Centralized document management.

    Supports filtering by:
      ?project=<uuid>
      ?contract=<uuid>
      ?category=CONTRACT|REPORT|EVALUATION|FINANCIAL|LEGAL|PHOTO|CORRESPONDENCE|OTHER
      ?public=true  (returns only is_public=True docs — no auth required)
    """
    serializer_class = DocumentSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        if self.request.query_params.get('public') == 'true' and self.action == 'list':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Document.objects.select_related('uploaded_by', 'project', 'contract')

        public = self.request.query_params.get('public')
        if public == 'true':
            qs = qs.filter(is_public=True)

        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        contract_id = self.request.query_params.get('contract')
        if contract_id:
            qs = qs.filter(contract_id=contract_id)

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        return qs

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
