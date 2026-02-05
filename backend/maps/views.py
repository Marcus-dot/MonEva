from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ExternalMapLayer
from .serializers import ExternalMapLayerSerializer
import requests
import os
from django.conf import settings

class ExternalMapLayerViewSet(viewsets.ModelViewSet):
    queryset = ExternalMapLayer.objects.filter(is_active=True)
    serializer_class = ExternalMapLayerSerializer
    permission_classes = [permissions.IsAuthenticated]

class WeatherProxyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        
        if not lat or not lon:
            return Response({"error": "Missing lat/lon parameters"}, status=400)
            
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        if not api_key:
            return Response({"error": "Server configuration error: parameters missing"}, status=503)
            
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return Response(response.json())
        except requests.RequestException as e:
            return Response({"error": "Weather service unavailable"}, status=502)
