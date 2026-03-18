#!/usr/bin/env python3
import requests

resp = requests.post(
    "http://localhost:8000/token", data={"username": "admin", "password": "admin123"}
)
token = resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print("Checking global documents...")
resp = requests.get(
    "http://localhost:8000/admin/global-index/documents", headers=headers, timeout=10
)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")
