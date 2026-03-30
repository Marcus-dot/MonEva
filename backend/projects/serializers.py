from rest_framework import serializers
from .models import Project, Contract, ContractAmendment, Milestone, ProjectComment, BeneficiaryFeedback

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'

class ContractAmendmentSerializer(serializers.ModelSerializer):
    approved_by_name = serializers.ReadOnlyField(source='approved_by.get_full_name')

    class Meta:
        model = ContractAmendment
        fields = '__all__'
        read_only_fields = ['created_at']

class ContractSerializer(serializers.ModelSerializer):
    milestones = MilestoneSerializer(many=True, read_only=True)
    amendments = ContractAmendmentSerializer(many=True, read_only=True)
    contractor_name = serializers.ReadOnlyField(source='contractor.name')
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = Contract
        fields = '__all__'

class SDGSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import SDG
        model = SDG
        fields = '__all__'

class StrategicThemeSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import StrategicTheme
        model = StrategicTheme
        fields = ['id', 'name', 'code']

class ProjectSerializer(serializers.ModelSerializer):
    contracts = ContractSerializer(many=True, read_only=True)
    sdg_details = SDGSerializer(source='sdgs', many=True, read_only=True)
    themes = StrategicThemeSerializer(many=True, read_only=True)
    
    # Write-only field for initial milestones
    initial_milestones = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True, 
        required=False
    )
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'type', 'csr_focus', 'thematic_area', 'primary_kra', 
            'sdgs', 'sdg_details', 'description', 'location', 'catchment_area', 
            'latitude', 'longitude', 'start_date', 'end_date', 'status', 'owner_org',
            'assigned_team', 'partners', 'contracts', 'initial_milestones',
            'themes'
        ]

    def validate(self, data):
        """Call model's clean() method for validation"""
        # Pop M2M fields which can't be set via constructor
        val_data = data.copy()
        val_data.pop('partners', None)
        val_data.pop('assigned_team', None)
        val_data.pop('sdgs', None)
        val_data.pop('initial_milestones', None)
        
        instance = Project(**val_data)
        instance.clean()
        return data

    def create(self, validated_data):
        milestones_data = validated_data.pop('initial_milestones', [])
        
        # Use super() to handle Project creation + M2M fields (partners, assigned_team)
        project = super().create(validated_data)
        
        if milestones_data:
            # Create a default "Planning Contract" to hold these milestones
            contractor = project.owner_org 
            if project.partners.exists():
                contractor = project.partners.first()
            
            contract = Contract.objects.create(
                project=project,
                contractor=contractor,
                total_value=0, # Placeholder
                start_date=project.start_date,
                end_date=project.end_date
            )
            
            for ms_data in milestones_data:
                # Basic check to ensure required fields for the model are valid
                if not ms_data.get('due_date') or ms_data.get('due_date') == '':
                    ms_data['due_date'] = project.end_date # Fallback to project end date
                
                try:
                    Milestone.objects.create(contract=contract, **ms_data)
                except Exception as e:
                    print(f"Failed to create milestone {ms_data.get('title')}: {e}")
        
        # Phase 5 Automation
        try:
            from .automation import generate_standard_logframe, check_and_create_contracts
            generate_standard_logframe(project)
            check_and_create_contracts(project)
        except Exception as e:
            # Don't fail project creation if automation fails, but verify logging in real production
            print(f"Automation Error: {e}")
                
        return project


class ProjectCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    assigned_to_name = serializers.ReadOnlyField(source='assigned_to.username')
    
    class Meta:
        model = ProjectComment
        fields = '__all__'
        read_only_fields = ['author', 'created_at']

class BeneficiaryFeedbackSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = BeneficiaryFeedback
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']

class BeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        from .models import Beneficiary
        model = Beneficiary
        fields = '__all__'
