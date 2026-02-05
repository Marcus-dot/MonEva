import requests
import os
import json

BASE_URL = "http://localhost:8000/api"
# Check if server is running
try:
    requests.get("http://localhost:8000/admin/", timeout=2)
except requests.exceptions.ConnectionError:
    print("Error: Django server is not running.")
    exit(1)

# Test Map Layers API
print("Testing Map Layers API...")
layer_data = {
    "name": "Test Weather Layer",
    "layer_type": "WMS",
    "url": "https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png",
    "attribution": "OpenWeatherMap",
    "is_active": True
}

# Create Layer
response = requests.post(f"{BASE_URL}/map-layers/", json=layer_data, auth=('admin', 'admin'))
if response.status_code in [201, 200, 401, 403]: # 401/403 might happen if auth is needed and not provided correctly
    print(f"Create Layer Status: {response.status_code}")
    if response.status_code == 201:
        layer_id = response.json().get('id')
        print(f"Created Layer ID: {layer_id}")
    else:
        print(f"Response: {response.text}")
else:
    print(f"Failed to create layer: {response.status_code} - {response.text}")

# List Layers
response = requests.get(f"{BASE_URL}/map-layers/")
if response.status_code == 200:
    print(f"List Layers: Found {len(response.json())} layers")
else:
    print(f"Failed to list layers: {response.status_code}")

# Test Weather Proxy
print("\nTesting Weather Proxy...")
# We expect this to fail if no API key is set in backend, but the endpoint should be reachable
response = requests.get(f"{BASE_URL}/weather/?lat=-15.3875&lon=28.3228")
print(f"Weather Proxy Status: {response.status_code}")
# It might return error from upstream if key is invalid, but 200/400/502 are expected interactions
print(f"Weather Proxy Response: {response.text[:200]}...")
