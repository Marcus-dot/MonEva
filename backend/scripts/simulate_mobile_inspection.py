import requests
import sys
import os

BASE_URL = "http://localhost:8000/api/v1"

def get_token(username, password):
    resp = requests.post(f"{BASE_URL}/auth/token/", json={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()['access']

def submit_inspection(token, milestone_id):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a dummy image
    with open("test_evidence.jpg", "wb") as f:
        f.write(b"fake_image_bytes")

    data = {
        "milestone": milestone_id,
        "quality_verdict": "PASS",
        "notes": "E2E Test Inspection - Looks good",
        "inspected_at": "2024-03-15T10:00:00Z"
    }
    
    files = {
        "photos": open("test_evidence.jpg", "rb")
    }

    print(f"Submitting inspection for Milestone {milestone_id}...")
    resp = requests.post(f"{BASE_URL}/inspections/", headers=headers, data=data, files=files)
    
    # Cleanup
    os.remove("test_evidence.jpg")
    
    if resp.status_code == 201:
        print("Inspection Submitted Successfully!")
        return True
    else:
        print(f"Failed: {resp.status_code} - {resp.text}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simulate_mobile_inspection.py <milestone_id>")
        sys.exit(1)
        
    milestone_id = sys.argv[1]
    try:
        token = get_token("admin", "admin") # Using admin as inspector for simplicity
        submit_inspection(token, milestone_id)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
