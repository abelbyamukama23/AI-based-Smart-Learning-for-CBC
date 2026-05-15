import requests
import json

base_url = "http://127.0.0.1:8000/api/v1"

# 1. Register a dummy user to get a token
print("Registering dummy user...")
try:
    resp = requests.post(f"{base_url}/auth/register/", json={
        "email": "test_streaming2@example.com",
        "username": "test_streaming2",
        "password": "Password123!",
        "role": "learner"
    })
    print("Reg Status:", resp.status_code)
except Exception as e:
    print("Reg Error:", e)

# 2. Login to get token
print("Logging in...")
token = None
try:
    resp = requests.post(f"{base_url}/auth/login/", json={
        "email": "test_streaming2@example.com",
        "password": "Password123!"
    })
    print("Login Status:", resp.status_code)
    if resp.status_code == 200:
        token = resp.json().get("access")
except Exception as e:
    print("Login Error:", e)

if token:
    print("Got token, starting stream...")
    try:
        resp = requests.post(
            f"{base_url}/tutor/ask/",
            json={"query": "Hello", "mode": "default"},
            headers={"Authorization": f"Bearer {token}", "Origin": "http://localhost:5173"},
            stream=True
        )
        print("Ask Status:", resp.status_code)
        print("Ask Headers:", resp.headers)
        for line in resp.iter_lines():
            if line:
                print("Line:", line.decode("utf-8"))
    except Exception as e:
        print("Ask Error:", e)
else:
    print("Failed to get token!")
