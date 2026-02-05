#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"

echo "Checking Server Status..."
curl -I http://localhost:8000/admin/

echo -e "\n\nTesting Map Layers API..."
# Create Layer
echo "Creating Map Layer..."
curl -X POST -H "Content-Type: application/json" -u admin:admin -d '{
    "name": "Test Weather Layer",
    "layer_type": "WMS",
    "url": "https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png",
    "attribution": "OpenWeatherMap",
    "is_active": true
}' "$BASE_URL/map-layers/"

# List Layers
echo -e "\n\nListing Map Layers..."
curl "$BASE_URL/map-layers/"

# Test Weather Proxy
echo -e "\n\nTesting Weather Proxy..."
curl -I "$BASE_URL/weather/?lat=-15.3875&lon=28.3228"
