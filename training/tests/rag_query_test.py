import requests
import json

# The endpoint configured in your app.py
API_URL = "http://localhost:8000/api/remediate"

# Define the list of active plugins you want to audit
payload = {
    "plugins": [
        {"slug": "molie-instructure-canvas-linking-tool", "version": "1.0"}
    ]
}

print("Sending audit request to local RAG model (this may take a few seconds on your GPU)...")

try:
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("\n--- AUDIT SUCCESSFUL ---")
        print(f"Total Vulnerabilities Located in DB: {result['vulnerabilities_found']}")
        print("\n=== EXPERT REMEDIATION PLAN ===")
        print(result["remediation_plan"])
    else:
        print(f"Error {response.status_code}: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("Connection Failed. Ensure your FastAPI app is running via 'python app.py'")