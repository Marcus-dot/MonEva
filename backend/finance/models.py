from django.db import models
from projects.models import Contract, Milestone
from django.conf import settings
import uuid
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class PaymentClaim(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        APPROVED = 'APPROVED', 'Approved'
        PAID = 'PAID', 'Paid'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='claims')
    milestones = models.ManyToManyField(Milestone, related_name='claims', blank=True)
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    claim_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    description = models.TextField(blank=True)
    
    # Audit Fields
    prepared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='prepared_claims')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_claims')
    rejection_reason = models.TextField(blank=True, null=True)
    assigned_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='claims_to_approve'
    )
    
    # ML Risk Scoring (Phase 2)
    risk_score = models.FloatField(null=True, blank=True, help_text="AI calculated risk score (0-100)")
    risk_factors = models.JSONField(default=dict, blank=True, help_text="Explanation for the risk score")

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Claim {self.amount} - {self.contract}"

    def clean(self):
        """Validate claim data"""
        errors = {}
        
        # Validate claim amount doesn't exceed contract total
        if self.contract and self.amount:
            if self.amount > self.contract.total_value:
                errors['amount'] = 'Claim amount cannot exceed contract total value'
        
        # Validate claim_date is within contract period
        if self.contract and self.claim_date:
            if self.claim_date < self.contract.start_date:
                errors['claim_date'] = 'Claim date cannot be before contract start date'
            if self.claim_date > self.contract.end_date:
                errors['claim_date'] = 'Claim date cannot be after contract end date'
        
        if errors:
            raise ValidationError(errors)


class ClaimComment(models.Model):
    """Comments/notes on payment claims for team collaboration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim = models.ForeignKey(PaymentClaim, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='claim_comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-created_at']
