from django.db import models
from projects.models import Project, Contract
from django.conf import settings
import uuid

class Indicator(models.Model):
    class Direction(models.TextChoices):
        INCREASING = 'INCREASING', 'Increasing is Good (e.g. Beneficiaries Reached)'
        DECREASING = 'DECREASING', 'Decreasing is Good (e.g. Infection Rate)'
        NEUTRAL = 'NEUTRAL', 'Neutral / Tracking Only'

    class UnitType(models.TextChoices):
        NUMBER = 'NUMBER', 'Number'
        PERCENTAGE = 'PERCENTAGE', 'Percentage'
        CURRENCY = 'CURRENCY', 'Currency'
        BOOLEAN = 'BOOLEAN', 'Yes/No'
        QUALITATIVE = 'QUALITATIVE', 'Qualitative (e.g. Pass/Fail)'
        FORMULA = 'FORMULA', 'Formula (Calculated)'

    class Level(models.TextChoices):
        IMPACT = 'IMPACT', 'Impact / Goal'
        OUTCOME = 'OUTCOME', 'Outcome'
        OUTPUT = 'OUTPUT', 'Output'
        ACTIVITY = 'ACTIVITY', 'Activity'

    class Frequency(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'
        QUARTERLY = 'QUARTERLY', 'Quarterly'
        ANNUAL = 'ANNUAL', 'Annual'
        ONCE = 'ONCE', 'Once (End of Project)'

    class Category(models.TextChoices):
        STANDARD = 'STANDARD', 'Standard (Operational)'
        ESG_ENVIRONMENTAL = 'ESG_ENVIRONMENTAL', 'ESG - Environmental'
        ESG_SOCIAL = 'ESG_SOCIAL', 'ESG - Social'
        ESG_GOVERNANCE = 'ESG_GOVERNANCE', 'ESG - Governance'
        CUSTOM = 'CUSTOM', 'Custom'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    definition = models.TextField(help_text="Detailed explanation of what this indicator measures")
    unit_type = models.CharField(max_length=20, choices=UnitType.choices, default=UnitType.NUMBER)
    direction = models.CharField(max_length=20, choices=Direction.choices, default=Direction.INCREASING)
    reporting_frequency = models.CharField(
        max_length=20, 
        choices=Frequency.choices, 
        default=Frequency.MONTHLY
    )
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.STANDARD)
    
    # Daylight Engine: Logic & Formulas
    formula_definition = models.TextField(blank=True, help_text="Template: {ind_id1} + {ind_id2}")
    qualitative_options = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="e.g. {'PASS': 100, 'FAIL': 0}"
    )
    
    # Impact Measurement
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.OUTPUT)
    disaggregation = models.JSONField(default=list, help_text="e.g. ['Gender', 'Age', 'Location']")
    
    # Smart Indicators (Phase 8)
    theme = models.ForeignKey(
        'projects.StrategicTheme', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='standard_indicators',
        help_text="Link to Strategic Theme for auto-assignment"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_unit_type_display()})"

class IndicatorTarget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name='targets')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='indicator_targets')
    
    baseline_value = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    target_value = models.DecimalField(max_digits=19, decimal_places=4)
    
    description = models.CharField(max_length=255, blank=True, help_text="e.g. 'End of Year 1 Target'")
    
    # Link to Logical Framework (e.g., This target measures a specific Outcome)
    logframe_node = models.ForeignKey('LogFrameNode', on_delete=models.SET_NULL, null=True, blank=True, related_name='indicator_targets')
    
    class Meta:
        unique_together = ('indicator', 'project')

    def __str__(self):
        return f"{self.indicator.name} for {self.project.name} (Target: {self.target_value})"

class IndicatorResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target = models.ForeignKey(IndicatorTarget, on_delete=models.CASCADE, related_name='results')
    
    date = models.DateField()
    value = models.DecimalField(max_digits=19, decimal_places=4)
    disaggregated_data = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Breakdown data e.g. {'Male': 10, 'Female': 15}"
    )

    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED
    )
    notes = models.TextField(blank=True)
    rejection_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_results')
    verified_at = models.DateTimeField(null=True, blank=True)
    evidence_url = models.URLField(blank=True, null=True)
    
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='recorded_results')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.target.indicator.name}: {self.value} on {self.date}"

class LogFrameNode(models.Model):
    class NodeType(models.TextChoices):
        GOAL = 'GOAL', 'Goal / Impact'
        OUTCOME = 'OUTCOME', 'Outcome'
        OUTPUT = 'OUTPUT', 'Output'
        ACTIVITY = 'ACTIVITY', 'Activity'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='logframe_nodes')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    node_type = models.CharField(max_length=20, choices=NodeType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.get_node_type_display()}: {self.title}"

class FrameworkTemplate(models.Model):
    """
    Stores reusable Logframe structures (e.g. 'Standard CSR Education Framework')
    which can be applied to new projects.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # JSON structure defining the tree:
    # {
    #   "nodes": [
    #     {"type": "GOAL", "title": "Impact...", "children": [
    #         {"type": "OUTCOME", "title": "Outcome 1...", "indicators": [...]}
    #     ]}
    #   ]
    # }
    structure = models.JSONField(default=dict)
    
    is_public = models.BooleanField(default=False, help_text="Visible to all organizations?")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
