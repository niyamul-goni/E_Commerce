"""Test re-registration and edge cases."""
import httpx
import json

BACKEND = "http://localhost:8000/api/v1"

# Test 1: Try to re-register with existing email
print("=" * 60)
print("TEST: Re-register with existing email (endpointtest999@test.com)")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BACKEND}/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "endpointtest999@test.com",
            "phone": "01234567890",
            "password": "TestPass123!",
            "role": "customer",
        },
        timeout=30.0,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Register with new email, no phone
print("\n" + "=" * 60)
print("TEST: Register with no phone")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BACKEND}/auth/register",
        json={
            "first_name": "NoPhone",
            "last_name": "User",
            "email": "nophone_test@test.com",
            "password": "TestPass123!",
            "role": "customer",
        },
        timeout=30.0,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Register with short password
print("\n" + "=" * 60)
print("TEST: Register with short password (should fail)")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BACKEND}/auth/register",
        json={
            "first_name": "Short",
            "last_name": "Pass",
            "email": "shortpass@test.com",
            "password": "123",
            "role": "customer",
        },
        timeout=30.0,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 4: Login with wrong password
print("\n" + "=" * 60)
print("TEST: Login with wrong password")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BACKEND}/auth/login",
        data={"username": "endpointtest999@test.com", "password": "WrongPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 5: Login with non-existent email
print("\n" + "=" * 60)
print("TEST: Login with non-existent email")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BACKEND}/auth/login",
        data={"username": "nonexistent@test.com", "password": "TestPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 6: Register as manager then check /auth/me returns is_admin=true
print("\n" + "=" * 60)
print("TEST: Register as manager and verify is_admin in /auth/me")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BACKEND}/auth/register",
        json={
            "first_name": "TestMgr",
            "last_name": "Admin",
            "email": "mgr_verify_test@test.com",
            "phone": "01122334455",
            "password": "TestPass123!",
            "role": "manager",
        },
        timeout=30.0,
    )
    print(f"Register Status: {resp.status_code}")
    data = resp.json()
    print(f"Register Response: {json.dumps(data, indent=2)}")
    if resp.status_code in (200, 201):
        token = data.get("access_token")
        if token:
            me_resp = httpx.get(
                f"{BACKEND}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
            )
            print(f"\n/auth/me Status: {me_resp.status_code}")
            me_data = me_resp.json()
            print(f"/auth/me Response: {json.dumps(me_data, indent=2)}")
            print(f"\nis_admin = {me_data.get('is_admin')}")
except Exception as e:
    print(f"ERROR: {e}")
