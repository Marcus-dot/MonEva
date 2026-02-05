from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project, Contract, Milestone, ProjectComment, BeneficiaryFeedback
from .serializers import (
    ProjectSerializer, 
    ContractSerializer, 
    MilestoneSerializer, 
    ProjectCommentSerializer,
    BeneficiaryFeedbackSerializer,
    BeneficiarySerializer,
    SDGSerializer
)
from core.permissions import IsAdmin, IsProjectManager, ReadOnly

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Location Filter (contains_point=lat,lng)
        contains_point = self.request.query_params.get('contains_point')
        if contains_point:
            try:
                lat_str, lng_str = contains_point.split(',')
                lat = float(lat_str.strip())
                lng = float(lng_str.strip())
                
                # Python-side filtering for Polygon containment
                # Note: In production with PostGIS, use __contains
                matching_ids = []
                for p in queryset:
                    if p.catchment_area and self._is_point_in_polygon(lng, lat, p.catchment_area):
                        matching_ids.append(p.id)
                queryset = queryset.filter(id__in=matching_ids)
            except ValueError:
                pass 
                
        return queryset

    def _is_point_in_polygon(self, x, y, geojson):
        """
        Ray-casting algorithm to check if point (x,y) is in GeoJSON Polygon.
        x = longitude, y = latitude
        """
        try:
            if geojson.get('type') != 'Polygon':
                return False
                
            # Outer ring is the first element
            coords = geojson['coordinates'][0] 
            
            inside = False
            n = len(coords)
            p1x, p1y = coords[0]
            for i in range(1, n + 1):
                p2x, p2y = coords[i % n]
                if y > min(p1y, p2y):
                    if y <= max(p1y, p2y):
                        if x <= max(p1x, p2x):
                            if p1y != p2y:
                                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                                if p1x == p2x or x <= xinters:
                                    inside = not inside
                p1x, p1y = p2x, p2y
            return inside
        except Exception:
             return False

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsProjectManager]
        elif self.action == 'list':
            # Allow public to list projects for grievance dropdown
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'])
    def map_data(self, request):
        from datetime import date
        from django.db.models import Count, Avg, Case, When, Value, IntegerField
        from django.db.models.functions import Coalesce
        
        # 1. Fetch Active Projects
        projects = Project.objects.exclude(status='COMPLETED')
        
        # 2. Build Project GeoJSON Features
        project_features = []
        for p in projects:
            # Dynamic RAG Status Logic
            # RED if: Status is ON_HOLD or has high-risk items
            # AMBER if: Status is PLANNING or has medium-risk
            # GREEN otherwise
            rag_status = 'GREEN'
            if p.status == 'ON_HOLD':
                rag_status = 'RED'
            elif p.status == 'PLANNING':
                rag_status = 'AMBER'
            
            # Check for overdue milestones
            from .models import Milestone
            overdue_ms = Milestone.objects.filter(contract__project=p, due_date__lt=date.today(), status='PENDING').exists()
            if overdue_ms:
                rag_status = 'RED' if rag_status != 'RED' else 'RED'
            
            # Dynamic Health Score
            # Calculate based on avg performance of indicators
            # 1. Get all targets for this project
            targets = p.indicator_targets.all()
            total_performance = 0
            count = 0
            
            for t in targets:
                latest = t.results.filter(status='VERIFIED').order_by('-date').first()
                if latest and t.target_value > 0:
                    perf = (latest.value / t.target_value) * 100
                    total_performance += min(perf, 100) # Cap at 100 for scoring
                    count += 1
            
            health_score = int(total_performance / count) if count > 0 else 50 # Default to 50 (Neutral) if no data
            
            # Ensure valid location (fallback for missing coords)
            lat, lng = -15.3875, 28.3228 # Lusaka default
            if p.location and 'coordinates' in p.location:
                lng, lat = p.location['coordinates']
            
            # 3. Add Impact Metrics (Real data from Beneficiaries & Feedback)
            beneficiaries = p.beneficiaries.all()
            total_b = beneficiaries.count()
            
            # Gender Split
            gender_counts = beneficiaries.values('gender').annotate(count=Count('gender'))
            gender_split = {item['gender']: item['count'] for item in gender_counts if item['gender']}
            
            # Age Buckets
            current_year = date.today().year
            age_buckets = {'<18': 0, '18-35': 0, '36-60': 0, '60+': 0}
            for b in beneficiaries:
                if b.year_of_birth:
                    age = current_year - b.year_of_birth
                    if age < 18: age_buckets['<18'] += 1
                    elif age <= 35: age_buckets['18-35'] += 1
                    elif age <= 60: age_buckets['36-60'] += 1
                    else: age_buckets['60+'] += 1
            
            # Sentiment Score
            feedback = p.feedback.all()
            sentiment_map = {'POSITIVE': 1, 'NEUTRAL': 0, 'NEGATIVE': -1}
            sentiments = [sentiment_map.get(f.sentiment, 0) for f in feedback]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

            project_features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "properties": {
                    "id": str(p.id),
                    "name": p.name,
                    "type": p.type,
                    "rag_status": rag_status,
                    "health_score": health_score,
                    "impact_stats": {
                        "total_beneficiaries": total_b,
                        "gender_split": gender_split,
                        "age_buckets": age_buckets,
                        "sentiment_score": round(avg_sentiment, 2)
                    }
                }
            })
            
        # 3. Dynamic Regional Aggregates
        # Instead of static Chiefdoms, let's aggregate by 'province' or 'district' if available.
        # For now, we'll simulate clustering by finding the centroid of projects and creating an aggregate.
        # A simple approach: 1 super aggregate for "National" + aggregates for any high-density clusters?
        # Actually, let's keep it simple: 1 Aggregate for "National Average" + mock regions effectively removed or replaced by a real summary.
        # But front-end expects 'regional_aggregates'. Let's calculate one real aggregate based on ALL projects.
        
        total_projects = len(project_features)
        avg_health_national = sum([p['properties']['health_score'] for p in project_features]) / total_projects if total_projects else 0
        
        # We can just return a "National Overview" as a single aggregate for now, 
        # or grouped by common lat/long if we had distinct regions in the DB.
        # Since we don't have a 'Region' model, we'll just return one "National" aggregate.
        
        aggregates = [
            {
                "name": "National Overview",
                "center": [-15.4167, 28.2833], # Lusaka Center
                "radius": 500000, # Covers most of Zambia approx
                "rag_status": "AMBER" if avg_health_national < 70 else "GREEN", # Dynamic RAG
                "project_count": total_projects,
                "avg_health": int(avg_health_national)
            }
        ]
        
        return Response({
            "projects": {
                "type": "FeatureCollection",
                "features": project_features
            },
            "regional_aggregates": aggregates
        })


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectManager | ReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectManager | ReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(contract__project_id=project_id)
            
        return queryset

class ProjectCommentViewSet(viewsets.ModelViewSet):
    queryset = ProjectComment.objects.all()
    serializer_class = ProjectCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        # Log Activity
        from core.models import ActivityLog, Notification
        ActivityLog.objects.create(
            actor=self.request.user,
            action=ActivityLog.Action.COMMENT,
            target_model='Project',
            target_id=str(comment.project.id),
            details={
                "project_name": comment.project.name,
                "comment_id": str(comment.id),
                "text": comment.comment[:50] + "..." if len(comment.comment) > 50 else comment.comment
            }
        )
        
        # Trigger Notification if assigned
        if comment.assigned_to:
            Notification.create_notification(
                recipient=comment.assigned_to,
                title="New Task Assigned",
                message=f"{self.request.user.username} assigned you a task on Project: {comment.project.name}",
                notification_type=Notification.Type.TASK_ASSIGNED,
                related_model='Project',
                related_id=str(comment.project.id)
            )

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

class BeneficiaryFeedbackViewSet(viewsets.ModelViewSet):
    queryset = BeneficiaryFeedback.objects.all()
    serializer_class = BeneficiaryFeedbackSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            # Allow authenticated users (field staff) to create feedback
            return [permissions.IsAuthenticated()]
        # Allow PMs and Admins to view feedback
        return [permissions.IsAuthenticated(), (IsProjectManager | IsAdmin)()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

class BeneficiaryViewSet(viewsets.ModelViewSet):
    from .models import Beneficiary
    queryset = Beneficiary.objects.all()
    serializer_class = BeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        gender = self.request.query_params.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
            
        from datetime import date
        current_year = date.today().year
        
        age_min = self.request.query_params.get('age_min')
        if age_min:
            max_year = current_year - int(age_min)
            queryset = queryset.filter(year_of_birth__lte=max_year)
            
        age_max = self.request.query_params.get('age_max')
        if age_max:
             min_year = current_year - int(age_max)
             queryset = queryset.filter(year_of_birth__gte=min_year)
             
        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        from django.db.models import Count
        
        by_gender = self.get_queryset().values('gender').annotate(count=Count('id'))
        gender_map = {item['gender']: item['count'] for item in by_gender if item['gender']}
        
        by_vulnerability = self.get_queryset().values('vulnerability_category').annotate(count=Count('id'))
        vulnerability_map = {item['vulnerability_category']: item['count'] for item in by_vulnerability if item['vulnerability_category']}
        
        by_residence = self.get_queryset().values('residence_type').annotate(count=Count('id'))
        residence_map = {item['residence_type']: item['count'] for item in by_residence if item['residence_type']}
        
        return Response({
            "by_gender": gender_map,
            "by_vulnerability": vulnerability_map,
            "by_residence": residence_map,
            "total": self.get_queryset().count()
        })

class SDGViewSet(viewsets.ReadOnlyModelViewSet):
    from .models import SDG
    queryset = SDG.objects.all().order_by('code')
    serializer_class = SDGSerializer
    permission_classes = [permissions.AllowAny]
