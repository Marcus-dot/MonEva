import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def get_token(username, password):
    resp = requests.post(f"{BASE_URL}/auth/token/", json={"username": username, "password": password})
    return resp.json()['access']

def seed_data(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get or Create Project
    # We'll use the first existing project
    proj_resp = requests.get(f"{BASE_URL}/projects/", headers=headers)
    if not proj_resp.json():
        print("No projects found. Please run e2e test or create one first.")
        return
    project_id = proj_resp.json()[0]['id']
    print(f"Using Project: {project_id}")

    # 2. Create Indicator
    ind_data = {
        "name": "Schools Rehabilitated", 
        "definition": "Number of schools with completed renovation works",
        "unit_type": "NUMBER",
        "direction": "INCREASING"
    }
    ind_resp = requests.post(f"{BASE_URL}/indicators/", headers=headers, json=ind_data)
    if ind_resp.status_code == 201:
        indicator_id = ind_resp.json()['id']
        print(f"Indicator Created: {indicator_id}")
    else:
        # Maybe it already exists?
        print("Indicator creation failed (might exist), fetching first...")
        ind_resp = requests.get(f"{BASE_URL}/indicators/", headers=headers)
        indicator_id = ind_resp.json()[0]['id']

    # 3. Create Target
    target_data = {
        "project": project_id,
        "indicator_id": indicator_id,
        "baseline_value": 0,
        "target_value": 5,
        "description": "Renovate 5 schools in 2024"
    }
    target_resp = requests.post(f"{BASE_URL}/targets/", headers=headers, json=target_data)
    if target_resp.status_code == 201:
        target_id = target_resp.json()['id']
        print(f"Target Created: {target_id}")
        
        # 4. Add Result (Progress)
        res_data = {
            "date": "2024-03-01",
            "value": 2,
            "notes": "Completed schools A and B"
        }
        res_resp = requests.post(f"{BASE_URL}/targets/{target_id}/add_result/", headers=headers, json=res_data)
        print(f"Result Added: {res_resp.status_code}")
        
    else:
        print(f"Target creation failed: {target_resp.text}")

if __name__ == "__main__":
    try:
        token = get_token("admin", "admin")
        seed_data(token)
    except Exception as e:
        print(f"Error: {e}")
