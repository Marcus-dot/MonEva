from indicators.models import LogFrameNode, Indicator, IndicatorTarget
from projects.models import Project, Contract
from core.models import Organization

# Standard Framework Templates based on Strategic Theme
STANDARD_FRAMEWORKS = {
    'HEALTH': {
        'outcome': {
            'title': 'Improved health outcomes for target population',
            'description': 'Reduction in mortality and morbidity through improved infrastructure.',
            'outputs': [
                {
                    'title': 'Health facilities constructed/renovated',
                    'indicators': [
                        {'name': 'Health facilities completed', 'unit': 'NUMBER', 'direction': 'INCREASING', 'level': 'OUTPUT', 'target': 1},
                        {'name': 'Bed capacity added', 'unit': 'NUMBER', 'direction': 'INCREASING', 'level': 'OUTPUT', 'target': 50}
                    ]
                },
                {
                    'title': 'Healthcare staff trained',
                    'indicators': [
                        {'name': 'Staff trained in new protocols', 'unit': 'NUMBER', 'direction': 'INCREASING', 'level': 'OUTPUT', 'target': 20}
                    ]
                }
            ],
            'indicators': [
                {'name': 'Patient catchment population served', 'unit': 'NUMBER', 'direction': 'INCREASING', 'level': 'OUTCOME', 'target': 10000},
                {'name': 'Reduction in average wait time', 'unit': 'PERCENTAGE', 'direction': 'DECREASING', 'level': 'OUTCOME', 'target': 20}
            ]
        }
    },
    'EDUCATION': {
        'outcome': {
            'title': 'Improved access to quality education',
            'description': 'Enhancing learning environments and student retention.',
            'outputs': [
                {
                    'title': 'Classrooms constructed',
                    'indicators': [
                        {'name': 'Classrooms built', 'unit': 'NUMBER', 'direction': 'INCREASING', 'level': 'OUTPUT', 'target': 3},
                        {'name': 'Student desks provided', 'unit': 'NUMBER', 'direction': 'INCREASING', 'level': 'OUTPUT', 'target': 100}
                    ]
                }
            ],
            'indicators': [
                {'name': 'Student enrollment rate', 'unit': 'PERCENTAGE', 'direction': 'INCREASING', 'level': 'OUTCOME', 'target': 95},
                {'name': 'Teacher-student ratio', 'unit': 'NUMBER', 'direction': 'DECREASING', 'level': 'OUTCOME', 'target': 30}
            ]
        }
    },
    'ROAD': {
        'outcome': {
            'title': 'Improved market access and mobility',
            'description': 'Facilitating trade and movement through better road networks.',
            'outputs': [
                {
                    'title': 'Road infrastructure improved',
                    'indicators': [
                        {'name': 'Kilometers of road paved', 'unit': 'NUMBER', 'direction': 'INCREASING', 'level': 'OUTPUT', 'target': 10},
                        {'name': 'Drainage structures built', 'unit': 'NUMBER', 'direction': 'INCREASING', 'level': 'OUTPUT', 'target': 5}
                    ]
                }
            ],
            'indicators': [
                {'name': 'Average travel time reduction', 'unit': 'PERCENTAGE', 'direction': 'DECREASING', 'level': 'OUTCOME', 'target': 15},
                {'name': 'Daily traffic volume', 'unit': 'NUMBER', 'direction': 'INCREASING', 'level': 'OUTCOME', 'target': 500}
            ]
        }
    }
}

def generate_standard_logframe(project: Project):
    """
    Auto-populates the LogFrame and Indicators based on the Project's Thematic Area.
    """
    theme = project.thematic_area
    if theme not in STANDARD_FRAMEWORKS:
        return # No template for this theme

    template = STANDARD_FRAMEWORKS[theme]
    
    # 1. Create Goal Node (Top Level) - Generic for now or Theme specific
    goal_node = LogFrameNode.objects.create(
        project=project,
        node_type=LogFrameNode.NodeType.GOAL,
        title=f"Strategic Goal: {project.get_thematic_area_display()}",
        description=f"Long-term impact for {project.name}",
        order=1
    )

    # 2. Create Outcome Node
    outcome_data = template['outcome']
    outcome_node = LogFrameNode.objects.create(
        project=project,
        parent=goal_node,
        node_type=LogFrameNode.NodeType.OUTCOME,
        title=outcome_data['title'],
        description=outcome_data['description'],
        order=1
    )

    # 3. Create Indicators for Outcome
    for ind_data in outcome_data.get('indicators', []):
        _create_indicator_and_target(project, outcome_node, ind_data)

    # 4. Create Output Nodes and their Indicators
    for i, output_data in enumerate(outcome_data.get('outputs', []), 1):
        output_node = LogFrameNode.objects.create(
            project=project,
            parent=outcome_node,
            node_type=LogFrameNode.NodeType.OUTPUT,
            title=output_data['title'],
            order=i
        )
        
        for ind_data in output_data.get('indicators', []):
            _create_indicator_and_target(project, output_node, ind_data)

def _create_indicator_and_target(project, node, data):
    # Check if indicator definition exists largely to reuse, but simplified: create new for specific project context usually
    # For now, let's create a fresh Indicator instance to allow project-specific renaming
    indicator = Indicator.objects.create(
        name=data['name'],
        definition=f"Standard indicator for {project.thematic_area}",
        unit_type=data['unit'],
        direction=data['direction'],
        level=data['level']
    )
    
    IndicatorTarget.objects.create(
        project=project,
        indicator=indicator,
        target_value=data['target'],
        logframe_node=node,
        description="Initial Standard Target"
    )

def check_and_create_contracts(project: Project):
    """
    Checks if any partners are CONTRACTORS and creates a formal contract if one doesn't exist.
    """
    contractors = project.partners.filter(type=Organization.Types.CONTRACTOR)
    
    for contractor in contractors:
        # Check if contract exists
        if not Contract.objects.filter(project=project, contractor=contractor).exists():
            Contract.objects.create(
                project=project,
                contractor=contractor,
                total_value=0, # Placeholder, needing manual update
                start_date=project.start_date,
                end_date=project.end_date
            )

def sync_inspection_to_milestone(inspection):
    """
    Updates Milestone status based on Inspection verdict.
    """
    if inspection.quality_verdict == 'PASS':
        milestone = inspection.milestone
        # If it's a pass, we mark milestone as completed.
        # In a real scenario, we might check if *all* required inspections are passed,
        # but for now, one PASS is sufficient.
        if milestone.status != 'COMPLETED':
            milestone.status = 'COMPLETED'
            milestone.save()
            print(f"Automation: Milestone '{milestone.title}' marked COMPLETED due to Inspection {inspection.id}")

def sync_grievance_to_indicator(grievance):
    """
    Updates 'Community Grievances' indicator count.
    """
    project = grievance.project
    from indicators.models import Indicator, IndicatorTarget, LogFrameNode, IndicatorResult
    from grievances.models import Grievance
    from django.utils import timezone
    
    # 1. Find or Create Standard Indicator for Grievances
    indicator_name = "Community Grievances Reported"
    # We look for a target that matches this name
    target = IndicatorTarget.objects.filter(
        project=project, 
        indicator__name__icontains="Grievance"
    ).first()
    
    if not target:
        # Create on the fly if missing (Social Accountability)
        ind, _ = Indicator.objects.get_or_create(
            name=indicator_name,
            defaults={
                'definition': 'Number of grievances reported by community',
                'unit_type': 'NUMBER',
                'direction': 'DECREASING', # Ideally we want 0, but tracking volume is neutral/decreasing
                'level': 'OUTPUT'
            }
        )
        
        target = IndicatorTarget.objects.create(
            project=project,
            indicator=ind,
            target_value=0, # Target is 0 grievances ideally
            description="Auto-generated Social Indicator"
        )
    
    # 2. Count Total Grievances
    total_count = Grievance.objects.filter(project=project).count()
    
    # 3. Record Result (Latest Snapshot)
    # Update or Create Result for Today
    today = timezone.now().date()
    
    result, created = IndicatorResult.objects.get_or_create(
        target=target,
        date=today,
        defaults={'value': total_count}
    )
    
    if not created:
        result.value = total_count
        result.save()
        
    print(f"Automation: Updated Grievance Indicator to {total_count}")
