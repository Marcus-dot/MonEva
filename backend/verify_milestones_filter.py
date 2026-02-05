from projects.models import Project, Milestone
from rest_framework.test import APIRequestFactory
from projects.views import MilestoneViewSet
from core.models import User

# Setup
factory = APIRequestFactory()
view = MilestoneViewSet.as_view({'get': 'list'})

# Create user
user, _ = User.objects.get_or_create(username='test_mobile', defaults={'role': 'PROJECT_MANAGER'})

# Get a project
project = Project.objects.first()
if not project:
    print("No projects found.")
    exit()

print(f"Testing for Project: {project.name} ({project.id})")

# Request
request = factory.get(f'/api/v1/milestones/?project={project.id}')
request.user = user
response = view(request)

print(f"Status Code: {response.status_code}")
print(f"Data Count: {len(response.data)}")
if len(response.data) > 0:
    print(f"First Milestone: {response.data[0]['title']}")
else:
    print("No milestones found (Expected if none exist, but Endpoint didn't 500).")
