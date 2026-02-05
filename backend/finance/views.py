from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from .models import PaymentClaim, ClaimComment
from .serializers import PaymentClaimSerializer, ClaimCommentSerializer

from core.permissions import IsFinance, IsProjectManager, ReadOnly, IsAdmin

class PaymentClaimViewSet(viewsets.ModelViewSet):
    queryset = PaymentClaim.objects.all()
    serializer_class = PaymentClaimSerializer
    
    def get_permissions(self):
        # Finance/Admin can always update (approve/reject).
        # PM can update (submit) only if Draft (handled in validate_status but we allow access here).
        if self.action in ['update', 'partial_update', 'summary', 'anomalies']:
             return [permissions.IsAuthenticated()] # Logic inside serializer + perform_update
        if self.action == 'create':
            # ADMIN can also create claims now
            return [permissions.IsAuthenticated()] 
        return [permissions.IsAuthenticated(), ReadOnly()]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Aggregate financial data for reporting"""
        # 1. Total Value vs Paid vs Pending
        stats = PaymentClaim.objects.aggregate(
            total_amount=Sum('amount'),
            paid_amount=Sum('amount', filter=models.Q(status=PaymentClaim.Status.PAID)),
            pending_amount=Sum('amount', filter=models.Q(status=PaymentClaim.Status.APPROVED))
        )

        # 2. Monthly Burn Rate
        burn_rate = (
            PaymentClaim.objects.filter(status=PaymentClaim.Status.PAID)
            .annotate(month=TruncMonth('claim_date'))
            .values('month')
            .annotate(value=Sum('amount'))
            .order_by('month')
        )

        # 3. Claims by Status
        status_distribution = (
            PaymentClaim.objects.values('status')
            .annotate(count=Count('id'), value=Sum('amount'))
        )

        return Response({
            "stats": stats,
            "burn_rate": [
                {"name": b['month'].strftime('%b %Y'), "value": float(b['value'])} 
                for b in burn_rate
            ],
            "status_distribution": status_distribution
        })

    @action(detail=False, methods=['get'])
    def anomalies(self, request):
        """Detect unusual spending patterns"""
        # Anomaly 1: Claims exceeding milestone value
        # This requires joining with milestones, but PaymentClaim has a ManyToManyField
        # Let's find claims where amount > (Sum of linked milestones value / count of claims for those milestones)
        # Simplified for Prototype: Flag any claim > ZMW 500,000 or any claim > MILESTONE_VALUE
        
        anomalies = []
        
        # High Value Check
        high_value = PaymentClaim.objects.filter(amount__gt=500000).select_related('contract', 'contract__project')
        for claim in high_value:
            anomalies.append({
                "id": str(claim.id),
                "type": "HIGH_VALUE",
                "message": f"Large payment claim of ZMW {claim.amount:,.2f} detected.",
                "project": claim.contract.project.name,
                "amount": float(claim.amount)
            })

        # Milestone Overflow Check
        # (For each claim, check if its amount > total_value of its milestones)
        claims = PaymentClaim.objects.all().prefetch_related('milestones')
        for claim in claims:
            m_total = sum(m.value_amount for m in claim.milestones.all())
            if m_total > 0 and claim.amount > m_total:
                anomalies.append({
                    "id": str(claim.id),
                    "type": "MILESTONE_OVERFLOW",
                    "message": f"Claim amount (ZMW {claim.amount:,.2f}) exceeds linked milestone value (ZMW {m_total:,.2f}).",
                    "project": claim.contract.project.name,
                    "amount": float(claim.amount)
                })

        return Response(anomalies)

    def perform_create(self, serializer):
        # Maker Function: Capture who prepared the claim
        user = self.request.user
        serializer.save(prepared_by=user, status=PaymentClaim.Status.DRAFT)

    def perform_update(self, serializer):
        from rest_framework.exceptions import ValidationError, PermissionDenied

        user = self.request.user
        instance = serializer.instance
        
        # Checker Function: Enforce Segregation of Duties
        new_status = serializer.validated_data.get('status')
        if new_status == PaymentClaim.Status.APPROVED and instance.status != PaymentClaim.Status.APPROVED:
            # Prevent Maker from being Checker UNLESS Admin
            if instance.prepared_by == user and user.role != 'ADMIN':
                 raise PermissionDenied("Maker-Checker Violation: You cannot approve a claim you prepared.")
            
            serializer.save(approved_by=user)
        else:
            serializer.save()

class ClaimCommentViewSet(viewsets.ModelViewSet):
    queryset = ClaimComment.objects.all()
    serializer_class = ClaimCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        # Log Activity
        from core.models import ActivityLog
        ActivityLog.objects.create(
            actor=self.request.user,
            action=ActivityLog.Action.COMMENT,
            target_model='PaymentClaim',
            target_id=str(comment.claim.id),
            details={
                "claim_id": str(comment.claim.id),
                "comment_id": str(comment.id),
                "text": comment.comment[:50] + "..." if len(comment.comment) > 50 else comment.comment
            }
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        claim_id = self.request.query_params.get('claim')
        if claim_id:
            queryset = queryset.filter(claim_id=claim_id)
        return queryset
