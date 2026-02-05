from django.utils import timezone
from datetime import timedelta
from .models import Project, Milestone
from indicators.models import IndicatorTarget, IndicatorResult

def calculate_project_risk(project):
    """
    Calculate a human-readable risk profile for a project.
    Returns: { 'score': 0-100, 'level': 'LOW|MEDIUM|HIGH', 'factors': [] }
    """
    score = 0
    factors = []
    now = timezone.now().date()
    
    # 1. Milestone Slippage (Critical)
    # Find active contracts and their pending milestones
    lagging_milestones = []
    for contract in project.contracts.all():
        overdue = contract.milestones.filter(
            status__in=['PENDING', 'IN_PROGRESS'],
            due_date__lt=now
        )
        for ms in overdue:
            days = (now - ms.due_date).days
            lagging_milestones.append(f"{ms.title} ({days} days overdue)")
            if days > 14:
                score += 30
            else:
                score += 15

    if lagging_milestones:
        factors.append({
            'type': 'SLIPPAGE',
            'message': f"Lagging milestones: {', '.join(lagging_milestones[:2])}..." if len(lagging_milestones) > 2 else f"Lagging milestones: {', '.join(lagging_milestones)}"
        })

    # 2. Reporting Delinquency (Engagement)
    delinquent_indicators = []
    targets = IndicatorTarget.objects.filter(project=project)
    for target in targets:
        freq = target.indicator.reporting_frequency
        days_limit = 45 # Default for monthly
        if freq == 'WEEKLY': days_limit = 14
        if freq == 'DAILY': days_limit = 3
        if freq == 'QUARTERLY': days_limit = 100
        
        last_result = target.results.filter(status='VERIFIED').first()
        if last_result:
            days_since = (now - last_result.date).days
            if days_since > days_limit:
                delinquent_indicators.append(target.indicator.name)
        else:
            # Never reported
            delinquent_indicators.append(target.indicator.name)
            score += 5

    if delinquent_indicators:
        score += min(len(delinquent_indicators) * 10, 40)
        factors.append({
            'type': 'REPORTING',
            'message': f"Reporting gaps in {len(delinquent_indicators)} indicators"
        })

    # 3. Verification Backlog (Governance)
    try:
        from .escalations import get_verification_backlog_score
        v_score, v_msg = get_verification_backlog_score(project)
        if v_score > 0:
            score += v_score
            factors.append({
                'type': 'GOVERNANCE',
                'message': v_msg
            })
    except ImportError:
        pass

    # Determine Level
    level = 'LOW'
    if score >= 60: level = 'HIGH'
    elif score >= 30: level = 'MEDIUM'
    
    return {
        'score': min(score, 100),
        'level': level,
        'factors': factors
    }
