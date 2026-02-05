import urllib.request
import urllib.parse
import json
import ssl

# Configure
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    if data:
        data_bytes = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        data_bytes = None

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    
    try:
        # Create unverified context to avoid potential SSL issues with localhost (though http usually fine)
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            return status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

print(f"Testing GIS Backend at {BASE_URL}")

# 1. Login
print("\n[1] Logging in...")
login_url = f"{BASE_URL}/auth/token/"
status, body = make_request(login_url, "POST", {"username": USERNAME, "password": PASSWORD})

if status != 200:
    print(f"Login failed: {status} - {body}")
    exit(1)

tokens = json.loads(body)
access_token = tokens.get("access")
print("Login successful. Got access token.")

headers = {
    "Authorization": f"Bearer {access_token}"
}

# 2. Test Create Layer
print("\n[2] Creating Map Layer...")
layer_data = {
    "name": "Integration Test Layer",
    "layer_type": "WMS",
    "url": "https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png",
    "attribution": "OpenWeatherMap",
    "is_active": True
}
status, body = make_request(f"{BASE_URL}/map-layers/", "POST", layer_data, headers)
print(f"Status: {status}")
if status == 201:
    print("Layer created successfully.")
else:
    print(f"Failed to create layer: {body}")

# 3. List Layers
print("\n[3] Listing Map Layers...")
status, body = make_request(f"{BASE_URL}/map-layers/", "GET", headers=headers)
print(f"Status: {status}")
if status == 200:
    layers = json.loads(body)
    print(f"Found {len(layers)} layers.")
    print(json.dumps(layers[:2], indent=2)) # Print first 2
else:
    print(f"Failed to list layers: {body}")

# 4. Test Weather Proxy
print("\n[4] Testing Weather Proxy...")
# Note: Weather proxy might require auth or not depending on View implementation. 
# It inherits from APIView and uses default classes, so it likely requires auth.
status, body = make_request(f"{BASE_URL}/weather/?lat=-15.3875&lon=28.3228", "GET", headers=headers)
print(f"Status: {status}")
if status == 200:
    print("Weather data retrieved successfully.")
    weather_data = json.loads(body)
    print(f"Weather: {weather_data.get('weather', [{}])[0].get('description', 'Unknown')}")
elif status == 502: # Bad Gateway from upstream
    print("Weather proxy reached upstream but got error (expected if no valid API key in env).")
    print(f"Response: {body}")
else:
    print(f"Weather proxy failed: {body}")

print("\nBackend Verification Complete.")
