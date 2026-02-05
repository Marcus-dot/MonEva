import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
INSPECTION_ID = "d814fc10-42cf-4842-ac63-d9b84ef1e7a6"
MILESTONE_ID = "ef68ebbb-a324-4939-9f46-0e191a45e167"
PROJECT_ID = "e4777ac3-b53a-4f19-8f2b-e1d47cdb7a63"

def get_token(username, password):
    resp = requests.post(f"{BASE_URL}/auth/token/", json={"username": username, "password": password})
    resp.json() # Debug
    return resp.json()['access']

def approve_inspection(token, inspection_id):
    headers = {"Authorization": f"Bearer {token}"}
    # Check current status
    resp = requests.get(f"{BASE_URL}/inspections/{inspection_id}/", headers=headers)
    print(f"Current Status: {resp.json().get('quality_verdict')}")
    
    # Approve logic might be a status update on the Milestone? 
    # Or purely internal. Let's assume we update the Milestone status to COMPLETED if inspection passes.
    # But wait, looking at my knowledge, `manage_inspection_status` might be the key.
    
    # Let's try to PATCH the milestone status to COMPLETED as a result of inspection
    print("Approving Milestone...")
    patch_resp = requests.patch(f"{BASE_URL}/milestones/{MILESTONE_ID}/", headers=headers, json={"status": "COMPLETED"})
    if patch_resp.status_code == 200:
        print("Milestone Marked COMPLETED.")
    else:
        print(f"Milestone update failed: {patch_resp.status_code}")

def create_claim(token, project_id, milestone_id):
    headers = {"Authorization": f"Bearer {token}"}
    # Hardcoded contract ID from previous step step or query it
    CONTRACT_ID = "68bfc2a6-8cd3-4120-b71c-9875656826be"
    
    data = {
        "contract": CONTRACT_ID,
        "amount": 10000,
        "claim_date": "2024-03-20",
        "status": "DRAFT",
        "description": "E2E Final Payment"
    }
    print("Creating Payment Claim (Draft)...")
    resp = requests.post(f"{BASE_URL}/claims/", headers=headers, json=data)
    if resp.status_code == 201:
        claim_id = resp.json()['id']
        print(f"Claim Created: {claim_id}")
        
        # Link Milestone
        # Assuming there's an endpoint or we do it via update?
        # A M2M on create handles IDs list usually
        # But let's try just updating status to SUBMITTED now
        print("Submitting Claim...")
        submit_resp = requests.patch(f"{BASE_URL}/claims/{claim_id}/", headers=headers, json={"status": "SUBMITTED"})
        if submit_resp.status_code == 200:
             print("Claim Submitted Successfully!")
        else:
             print(f"Claim Submission Failed: {submit_resp.text}")

    else:
        print(f"Claim Failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    try:
        token = get_token("admin", "admin")
        approve_inspection(token, INSPECTION_ID)
        create_claim(token, PROJECT_ID, MILESTONE_ID)
    except Exception as e:
        print(f"Error: {e}")
