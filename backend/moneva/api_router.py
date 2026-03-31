from rest_framework.routers import DefaultRouter
from core.views import (
    UserViewSet, OrganizationViewSet, DashboardViewSet, ReportsViewSet,
    ActivityLogViewSet, DashboardPreferenceViewSet, PermissionViewSet,
    RoleViewSet, NotificationViewSet, GlobalSearchViewSet, ScheduledReportViewSet,
    DocumentViewSet
)
from projects.views import (
    ProjectViewSet, ContractViewSet, ContractAmendmentViewSet, ContractTemplateViewSet,
    MilestoneViewSet, ProjectCommentViewSet, BeneficiaryFeedbackViewSet,
    BeneficiaryViewSet, SDGViewSet
)
from assessments.views import InspectionViewSet, EvidenceViewSet, PostProjectEvaluationViewSet, ImpactFollowUpViewSet, EvaluationTemplateViewSet
from finance.views import PaymentClaimViewSet, ClaimCommentViewSet
from grievances.views import GrievanceViewSet
from investigations.views import InvestigationViewSet, InvestigationUpdateViewSet, InvestigationEvidenceViewSet, InvestigationNoteViewSet, InvestigationMilestoneViewSet
from indicators.views import IndicatorViewSet, IndicatorTargetViewSet, LogFrameNodeViewSet, FrameworkTemplateViewSet, IndicatorResultViewSet
from maps.views import ExternalMapLayerViewSet, WeatherProxyView

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'reports', ReportsViewSet, basename='reports')
router.register(r'search', GlobalSearchViewSet, basename='search')
router.register(r'users', UserViewSet)
router.register(r'permissions', PermissionViewSet, basename='permissions')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'activity-logs', ActivityLogViewSet, basename='activity-logs') 
router.register(r'dashboard-preferences', DashboardPreferenceViewSet, basename='dashboard-preferences')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'scheduled-reports', ScheduledReportViewSet, basename='scheduled-reports')
router.register(r'documents', DocumentViewSet, basename='documents')
router.register(r'organizations', OrganizationViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'project-comments', ProjectCommentViewSet)
router.register(r'contracts', ContractViewSet)
router.register(r'contract-amendments', ContractAmendmentViewSet)
router.register(r'contract-templates', ContractTemplateViewSet, basename='contract-templates')
router.register(r'milestones', MilestoneViewSet)
router.register(r'beneficiary-feedback', BeneficiaryFeedbackViewSet, basename='beneficiary-feedback')
router.register(r'beneficiaries', BeneficiaryViewSet)
router.register(r'sdgs', SDGViewSet, basename='sdgs')
router.register(r'inspections', InspectionViewSet)
router.register(r'evidence', EvidenceViewSet)
router.register(r'evaluation-templates', EvaluationTemplateViewSet, basename='evaluation-templates')
router.register(r'post-project-evaluations', PostProjectEvaluationViewSet)
router.register(r'impact-followups', ImpactFollowUpViewSet)
router.register(r'claims', PaymentClaimViewSet)
router.register(r'claim-comments', ClaimCommentViewSet)
router.register(r'grievances', GrievanceViewSet)
router.register(r'investigations', InvestigationViewSet)
router.register(r'investigation-updates', InvestigationUpdateViewSet)
router.register(r'investigation-notes', InvestigationNoteViewSet)
router.register(r'investigation-evidence', InvestigationEvidenceViewSet)
router.register(r'investigation-milestones', InvestigationMilestoneViewSet)
router.register(r'indicators', IndicatorViewSet)
router.register(r'targets', IndicatorTargetViewSet)
router.register(r'indicator-results', IndicatorResultViewSet)

router.register(r'logframes', LogFrameNodeViewSet)
router.register(r'framework-templates', FrameworkTemplateViewSet)
router.register(r'map-layers', ExternalMapLayerViewSet)

from django.urls import path
from custom_reports.views import CustomReportViewSet

router.register(r'custom-reports', CustomReportViewSet, basename='custom_reports')

urlpatterns = [
    path('weather/', WeatherProxyView.as_view(), name='weather-proxy'),
] + router.urls
