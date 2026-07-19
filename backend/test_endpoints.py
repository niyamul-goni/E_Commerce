"""Test the actual FastAPI endpoints to find the exact error."""
import httpx
import json

BACKEND = "http://localhost:8000/api/v1"
test_email = "endpointtest999@test.com"
test_password = "TestPass123!"

print("=" * 60)
print("TEST 1: Register via /auth/register")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BACKEND}/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": test_email,
            "phone": "01234567890",
            "password": test_password,
            "role": "customer",
        },
        timeout=30.0,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    if resp.status_code in (200, 201):
        token = resp.json().get("access_token")
    else:
        token = None
except Exception as e:
    print(f"ERROR: {e}")
    token = None

if token:
    print("\n" + "=" * 60)
    print("TEST 2: Get /auth/me with token")
    print("=" * 60)
    try:
        resp = httpx.get(
            f"{BACKEND}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("TEST 3: Login via /auth/login")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BACKEND}/auth/login",
        data={"username": test_email, "password": test_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    if resp.status_code == 200:
        login_token = resp.json().get("access_token")
    else:
        login_token = None
except Exception as e:
    print(f"ERROR: {e}")
    login_token = None

if login_token:
    print("\n" + "=" * 60)
    print("TEST 4: Get /auth/me after login")
    print("=" * 60)
    try:
        resp = httpx.get(
            f"{BACKEND}/auth/me",
            headers={"Authorization": f"Bearer {login_token}"},
            timeout=30.0,
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"ERROR: {e}")

# Test manager registration
print("\n" + "=" * 60)
print("TEST 5: Register as manager")
print("=" * 60)
manager_email = "managertest999@test.com"
try:
    resp = httpx.post(
        f"{BACKEND}/auth/register",
        json={
            "first_name": "Manager",
            "last_name": "Test",
            "email": manager_email,
            "phone": "01987654321",
            "password": test_password,
            "role": "manager",
        },
        timeout=30.0,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")
