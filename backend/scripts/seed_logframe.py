import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def get_token(username, password):
    resp = requests.post(f"{BASE_URL}/auth/token/", json={"username": username, "password": password})
    return resp.json()['access']

def seed_logframe(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get Project
    proj_resp = requests.get(f"{BASE_URL}/projects/", headers=headers)
    if not proj_resp.json():
        print("No projects found.")
        return
    project_id = proj_resp.json()[0]['id']
    print(f"Using Project: {project_id}")

    # 2. Create Goal
    goal_data = {
        "project": project_id,
        "node_type": "GOAL",
        "title": "Improved Education Quality",
        "description": "Long term impact on literacy."
    }
    goal_resp = requests.post(f"{BASE_URL}/logframes/", headers=headers, json=goal_data)
    if goal_resp.status_code != 201:
        print(f"Failed to create Goal: {goal_resp.text}")
        return
    goal_id = goal_resp.json()['id']
    print(f"Goal Created: {goal_id}")

    # 3. Create Outcome (Child of Goal)
    outcome_data = {
        "project": project_id,
        "parent": goal_id,
        "node_type": "OUTCOME",
        "title": "Increased Student Attendance",
        "description": "90% attendance by 2025"
    }
    out_resp = requests.post(f"{BASE_URL}/logframes/", headers=headers, json=outcome_data)
    outcome_id = out_resp.json()['id']
    print(f"Outcome Created: {outcome_id}")

    # 4. Create Outputs (Children of Outcome)
    outputs = ["New Classrooms Constructed", "Teachers Trained"]
    for title in outputs:
        output_data = {
            "project": project_id,
            "parent": outcome_id,
            "node_type": "OUTPUT",
            "title": title
        }
        requests.post(f"{BASE_URL}/logframes/", headers=headers, json=output_data)
        print(f"Output Created: {title}")

if __name__ == "__main__":
    try:
        token = get_token("admin", "admin")
        seed_logframe(token)
    except Exception as e:
        print(f"Error: {e}")
