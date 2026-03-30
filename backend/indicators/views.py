from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Indicator, IndicatorTarget, IndicatorResult, LogFrameNode, FrameworkTemplate
from .serializers import (
    IndicatorSerializer, 
    IndicatorTargetSerializer, 
    IndicatorResultSerializer, 
    LogFrameNodeSerializer,
    FrameworkTemplateSerializer
)
import django_filters.rest_framework

class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'definition']

    @action(detail=False, methods=['post'], url_path='validate_formula')
    def validate_formula(self, request):
        """
        POST /api/indicators/validate_formula/
        Body: { "formula": "{uuid1} + {uuid2}", "project_id": "uuid" }

        Validates the formula string and optionally does a dry-run resolve
        against real indicator values for the given project.
        """
        from .formula import validate_formula, resolve_formula
        from .models import IndicatorTarget

        formula = request.data.get('formula', '').strip()
        project_id = request.data.get('project_id')

        if not formula:
            return Response({'valid': False, 'error': 'Formula is required.'}, status=400)

        ok, error = validate_formula(formula)
        if not ok:
            return Response({'valid': False, 'error': error})

        # Optional: dry-run with real project values
        preview_value = None
        if project_id:
            from projects.models import Project
            try:
                project = Project.objects.get(id=project_id)
                # Use a dummy target (no id) — resolve_formula handles missing self safely
                class _DummyTarget:
                    id = None
                    baseline_value = 0
                preview_value = resolve_formula(formula, _DummyTarget(), project)
            except Exception as e:
                preview_value = None

        return Response({
            'valid': True,
            'preview_value': preview_value,
        })

    @action(detail=False, methods=['get'])
    def scorecard(self, request):
        from django.db.models import Sum, Avg, F
        
        # 1. Aggregate Totals by Indicator Name (Enterprise View)
        # Group indicators by name and unit type to sum them up universally
        # e.g. "Beneficiaries Reached" across 5 projects.
        
        indicators = Indicator.objects.all()
        # To do this efficiently, we might need more complex queries or iterate.
        # For MVP/Prototype volume, iteration is fine.
        
        scorecard_data = []
        
        # Get unique indicator names to aggregate
        unique_names = indicators.values_list('name', flat=True).distinct()
        
        days = int(request.query_params.get('days', 30))
        from django.utils import timezone
        from datetime import timedelta
        
        current_end = timezone.now()
        current_start = current_end - timedelta(days=days)
        prev_start = current_start - timedelta(days=days)
        
        for name in unique_names:
            # Get all instances of this indicator
            instances = Indicator.objects.filter(name=name)
            first_instance = instances.first()
            
            # Aggregate Targets
            total_target = IndicatorTarget.objects.filter(indicator__name=name).aggregate(Sum('target_value'))['target_value__sum'] or 0
            
            # Aggregate Actuals (Latest result for each target)
            total_actual = 0
            targets = IndicatorTarget.objects.filter(indicator__name=name)
            for target in targets:
                latest_result = target.results.order_by('-date').first()
                if latest_result:
                    total_actual += latest_result.value
            
            # Calculate Health / Performance
            performance = 0
            if total_target > 0:
                performance = (total_actual / total_target) * 100
                
            status = 'OFF_TRACK'
            if performance >= 90:
                status = 'ON_TRACK'
            elif performance >= 70:
                status = 'AT_RISK'
                
            # Trend Data (Time Series for this indicator name)
            # We want to show how the Total Actual grew over time
            # Fetch all results, order by date
            all_results = IndicatorResult.objects.filter(target__indicator__name=name).order_by('date')
            trend_data = []
            cumulative_sum = 0
            # Simple cumulative sum for visualization
            for res in all_results:
                cumulative_sum += res.value # This assumes results are incremental additions (e.g. new beneficiaries). 
                # If results are snapshots (e.g. current infection rate), we shouldn't sum.
                # For this MVP, let's assume 'NUMBER' type is cumulative-ish or we just plot raw.
                # Let's plot raw values over time for now to show activity.
                trend_data.append({
                    "date": res.date,
                    "value": res.value, # Individual record
                    "cumulative": cumulative_sum # Cumulative
                })

            # Performance for current period
            current_results = IndicatorResult.objects.filter(
                target__indicator__name=name,
                date__range=[current_start, current_end]
            ).aggregate(Sum('value'))['value__sum'] or 0
            
            prev_results = IndicatorResult.objects.filter(
                target__indicator__name=name,
                date__range=[prev_start, current_start]
            ).aggregate(Sum('value'))['value__sum'] or 0
            
            growth = 0
            if prev_results > 0:
                growth = ((current_results - prev_results) / prev_results) * 100
            elif current_results > 0:
                growth = 100

            scorecard_data.append({
                "name": name,
                "unit": first_instance.unit_type,
                "direction": first_instance.direction,
                "total_target": total_target,
                "total_actual": total_actual,
                "current_period_actual": current_results,
                "prev_period_actual": prev_results,
                "growth_percent": round(growth, 1),
                "performance_percent": round(performance, 1),
                "status": status,
                "trend": trend_data[-10:] # Last 10 data points for sparkline
            })
            
        return Response(scorecard_data)

class IndicatorTargetViewSet(viewsets.ModelViewSet):
    queryset = IndicatorTarget.objects.all()
    serializer_class = IndicatorTargetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['project', 'indicator']

    @action(detail=True, methods=['post'])
    def add_result(self, request, pk=None):
        target = self.get_object()
        serializer = IndicatorResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(target=target, recorded_by=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class LogFrameNodeViewSet(viewsets.ModelViewSet):
    queryset = LogFrameNode.objects.all()
    serializer_class = LogFrameNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['project', 'parent']
    filterset_fields = ['project', 'parent']

class FrameworkTemplateViewSet(viewsets.ModelViewSet):
    queryset = FrameworkTemplate.objects.all()
    serializer_class = FrameworkTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply this template to a specific project"""
        template = self.get_object()
        project_id = request.data.get('project_id')
        
        if not project_id:
            return Response({"error": "project_id is required"}, status=400)
            
        from projects.models import Project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=404)
            
        # Clear existing logframe if requested? For now, we append.
        
        # Recursive function to build nodes from JSON
        def create_nodes(node_data, parent=None):
            node_type = node_data.get('type')
            title = node_data.get('title')
            children = node_data.get('children', [])
            
            # Create the node
            logframe_node = LogFrameNode.objects.create(
                project=project,
                parent=parent,
                node_type=node_type,
                title=title,
                description=node_data.get('description', '')
            )
            
            # Recursively create children
            for child in children:
                create_nodes(child, parent=logframe_node)
                
        # Parse structure
        structure = template.structure
        if 'nodes' in structure:
            for root_node in structure['nodes']:
                create_nodes(root_node)
                
        return Response({"status": "Template applied successfully"})

class IndicatorResultViewSet(viewsets.ModelViewSet):
    queryset = IndicatorResult.objects.all()
    serializer_class = IndicatorResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(target__project_id=project_id)
            
        indicator_name = self.request.query_params.get('indicator_name')
        if indicator_name:
            queryset = queryset.filter(target__indicator__name=indicator_name)
            
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset

    @action(detail=False, methods=['get'])
    def latest_impact(self, request):
        # Return latest results for indicators marked as IMPACT level
        # ONLY return VERIFIED results for the official impact dashboard
        latest_results = IndicatorResult.objects.filter(
            target__indicator__level='IMPACT',
            status='VERIFIED'
        ).order_by('target__indicator__name', '-date').distinct('target__indicator__name')
        
        return Response(IndicatorResultSerializer(latest_results, many=True).data)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        result = self.get_object()
        # In a real app, check permissions (e.g. request.user.is_manager)
        result.status = 'VERIFIED'
        result.verified_by = request.user
        from django.utils import timezone
        result.verified_at = timezone.now()
        result.save()
        
        # Log Activity
        from core.models import ActivityLog
        ActivityLog.objects.create(
            actor=request.user,
            action=ActivityLog.Action.APPROVE,
            target_model='IndicatorResult',
            target_id=str(result.id),
            details={
                "project_name": result.target.project.name,
                "indicator_name": result.target.indicator.name,
                "value": str(result.value)
            }
        )
        return Response({'status': 'Result verified'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        result = self.get_object()
        notes = request.data.get('notes', '')
        result.status = 'REJECTED'
        result.rejection_notes = notes
        result.save()
        
        # Log Activity
        from core.models import ActivityLog
        ActivityLog.objects.create(
            actor=request.user,
            action=ActivityLog.Action.REJECT,
            target_model='IndicatorResult',
            target_id=str(result.id),
            details={
                "project_name": result.target.project.name,
                "indicator_name": result.target.indicator.name,
                "rejection_notes": notes
            }
        )
        return Response({'status': 'Result rejected'})
    @action(detail=False, methods=['post'])
    def batch_verify(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided'}, status=400)
            
        from django.utils import timezone
        results = IndicatorResult.objects.filter(id__in=ids, status='SUBMITTED')
        count = results.update(
            status='VERIFIED',
            verified_by=request.user,
            verified_at=timezone.now()
        )
        
        # Log Activity
        if count > 0:
            from core.models import ActivityLog
            ActivityLog.objects.create(
                actor=request.user,
                action=ActivityLog.Action.APPROVE,
                target_model='IndicatorResult',
                target_id='batch',
                details={
                    "count": count,
                    "result_ids": ids[:10]
                }
            )
            
        return Response({'status': f'{count} results verified'})
