"""
Script to populate latitude/longitude for existing projects.
This adds sample coordinates around Lusaka, Zambia.
"""
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from projects.models import Project

# Lusaka center coordinates
LUSAKA_LAT = -15.4167
LUSAKA_LON = 28.2833

# Sample locations around Lusaka (±0.3 degrees for spread)
projects = Project.objects.all()

if not projects.exists():
    print("No projects found in database.")
else:
    count = 0
    for project in projects:
        # Generate random coordinates around Lusaka
        lat_offset = random.uniform(-0.3, 0.3)
        lon_offset = random.uniform(-0.3, 0.3)
        
        project.latitude = LUSAKA_LAT + lat_offset
        project.longitude = LUSAKA_LON + lon_offset
        project.save()
        count += 1
        print(f"✓ Updated {project.name}: ({project.latitude}, {project.longitude})")
    
    print(f"\n✅ Successfully added coordinates to {count} projects!")
