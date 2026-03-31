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
        from django.db.models import Sum, Subquery, OuterRef
        from django.utils import timezone
        from datetime import timedelta

        days = int(request.query_params.get('days', 30))
        current_end = timezone.now()
        current_start = current_end - timedelta(days=days)
        prev_start = current_start - timedelta(days=days)

        # Load all indicators, targets and results in 3 queries — no per-name loops
        indicators = Indicator.objects.all()
        all_targets = (
            IndicatorTarget.objects
            .select_related('indicator')
            .prefetch_related('results')
        )
        all_results_qs = (
            IndicatorResult.objects
            .select_related('target__indicator')
            .order_by('date')
        )

        # Build lookup maps in Python
        # indicator_name → first Indicator instance (for unit/direction)
        name_to_indicator: dict = {}
        for ind in indicators:
            name_to_indicator.setdefault(ind.name, ind)

        unique_names = list(name_to_indicator.keys())

        # target_id → latest verified result value
        # We prefetch results, so no extra queries here
        name_to_targets: dict = {}
        for t in all_targets:
            name_to_targets.setdefault(t.indicator.name, []).append(t)

        # All results grouped by indicator name
        name_to_results: dict = {}
        for res in all_results_qs:
            name_to_results.setdefault(res.target.indicator.name, []).append(res)

        scorecard_data = []

        for name in unique_names:
            first_instance = name_to_indicator[name]
            targets = name_to_targets.get(name, [])

            total_target = sum(float(t.target_value or 0) for t in targets)

            # Latest verified result per target (already prefetched)
            total_actual = 0
            for t in targets:
                latest = sorted(
                    [r for r in t.results.all() if r.status == 'VERIFIED'],
                    key=lambda r: r.date,
                    reverse=True
                )
                if latest:
                    total_actual += float(latest[0].value)

            performance = (total_actual / total_target * 100) if total_target > 0 else 0

            track_status = 'OFF_TRACK'
            if performance >= 90:
                track_status = 'ON_TRACK'
            elif performance >= 70:
                track_status = 'AT_RISK'

            # Trend and period aggregations from pre-fetched list
            all_results = name_to_results.get(name, [])
            trend_data = []
            cumulative = 0
            for res in all_results:
                cumulative += float(res.value)
                trend_data.append({"date": res.date, "value": float(res.value), "cumulative": cumulative})

            current_period = sum(
                float(r.value) for r in all_results
                if current_start.date() <= r.date <= current_end.date()
            )
            prev_period = sum(
                float(r.value) for r in all_results
                if prev_start.date() <= r.date < current_start.date()
            )

            if prev_period > 0:
                growth = (current_period - prev_period) / prev_period * 100
            elif current_period > 0:
                growth = 100.0
            else:
                growth = 0.0

            scorecard_data.append({
                "name": name,
                "unit": first_instance.unit_type,
                "direction": first_instance.direction,
                "total_target": total_target,
                "total_actual": total_actual,
                "current_period_actual": current_period,
                "prev_period_actual": prev_period,
                "growth_percent": round(growth, 1),
                "performance_percent": round(performance, 1),
                "status": track_status,
                "trend": trend_data[-10:],
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
        # Return latest verified result per IMPACT indicator.
        # distinct('field') is PostgreSQL-only, so we deduplicate in Python
        # to keep SQLite compatibility in development.
        results = (
            IndicatorResult.objects
            .filter(target__indicator__level='IMPACT', status='VERIFIED')
            .select_related('target__indicator')
            .order_by('target__indicator__name', '-date')
        )
        seen: set = set()
        latest_results = []
        for r in results:
            key = r.target.indicator.name
            if key not in seen:
                seen.add(key)
                latest_results.append(r)
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
