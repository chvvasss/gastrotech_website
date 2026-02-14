
import requests
import json
import os

def get_token():
    auth_url = "http://localhost:8000/api/v1/auth/login/"
    creds = {
        "email": "debug@gastrotech.com.tr",
        "password": "Debug123!"
    }
    try:
        resp = requests.post(auth_url, json=creds)
        if resp.status_code == 200:
            return resp.json()['access']
        print(f"Login failed: {resp.status_code} {resp.text}")
        return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_import():
    token = get_token()
    if not token:
        return

    url = "http://localhost:8000/api/v1/admin/import/json/preview/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    with open('temp_import.json', 'r') as f:
        data = json.load(f)
        
    print(f"Sending {len(data)} items to {url}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Preview Status: {response.status_code}")
        if response.status_code != 200:
            print(response.text)
            return

        res_json = response.json()
        print(f"Preview Response: {json.dumps(res_json, indent=2)}")
        
        job_id = res_json.get('dry_run_id')
        if not job_id:
            print("No job_id returned")
            return
            
        print(f"Committing job {job_id}...")
        commit_url = "http://localhost:8000/api/v1/admin/import/json/commit/"
        commit_resp = requests.post(commit_url, json={"job_id": job_id}, headers=headers)
        print(f"Commit Status: {commit_resp.status_code}")
        print("Commit Response:")
        print(commit_resp.text)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_import()
