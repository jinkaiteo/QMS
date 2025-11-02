#!/usr/bin/env python3
import requests
import io

# Quick upload test with fresh backend
auth_response = requests.post("http://localhost:8000/api/v1/auth/login", 
                            json={"username": "admin", "password": "admin123"})
token = auth_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

files = {"file": ("quick_test.txt", io.BytesIO(b"Quick test after restart"), "text/plain")}
data = {"upload_reason": "Quick test after backend restart"}

response = requests.post("http://localhost:8000/api/v1/documents/files/13/upload", 
                       files=files, data=data, headers=headers)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"✅ SUCCESS! Version: {result.get('version_number')}")
    print("🎉 Upload endpoint is working - try the frontend again!")
else:
    print(f"❌ Still failing: {response.text[:200]}")
    print("Need to investigate further...")