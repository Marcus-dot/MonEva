from rest_framework import serializers
from .models import PaymentClaim, ClaimComment

class PaymentClaimSerializer(serializers.ModelSerializer):
    contract_name = serializers.ReadOnlyField(source='contract.project.name')
    contractor_name = serializers.ReadOnlyField(source='contract.contractor.name')
    prepared_by_username = serializers.ReadOnlyField(source='prepared_by.username')
    approved_by_username = serializers.ReadOnlyField(source='approved_by.username')
    milestone_titles = serializers.StringRelatedField(source='milestones', many=True, read_only=True)
    
    class Meta:
        model = PaymentClaim
        fields = '__all__'
        read_only_fields = ['approved_by', 'prepared_by', 'rejection_reason', 'created_at']

    def validate_status(self, value):
        user = self.context['request'].user
        current_status = self.instance.status if self.instance else None
        
        # Init: Draft
        if not current_status:
            if value != PaymentClaim.Status.DRAFT:
                raise serializers.ValidationError("New claims must start as Draft.")
            return value

        # PM can submit Draft -> Submitted
        if current_status == PaymentClaim.Status.DRAFT and value == PaymentClaim.Status.SUBMITTED:
            return value

        # Finance can Approve/Reject/Pay
        if user.role in ['ADMIN', 'FINANCE']:
            if value in [PaymentClaim.Status.APPROVED, PaymentClaim.Status.REJECTED, PaymentClaim.Status.PAID]:
                return value
        
        # Generic check for user trying to change status they shouldn't
        if value != current_status and user.role not in ['ADMIN', 'FINANCE']:
             raise serializers.ValidationError("You do not have permission to change status to " + value)
             
        return value


class ClaimCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    
    class Meta:
        model = ClaimComment
        fields = '__all__'
        read_only_fields = ['author', 'created_at']
