"""Test cart, order, and dashboard endpoints after fixes."""
import httpx
import json

BACKEND = "http://localhost:8000/api/v1"

# First login to get a token
print("=" * 60)
print("Login to get token")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BACKEND}/auth/login",
        data={"username": "endpointtest999@test.com", "password": "TestPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    print(f"Login Status: {resp.status_code}")
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
except Exception as e:
    print(f"Login ERROR: {e}")
    exit(1)

# Test 1: Get cart items
print("\n" + "=" * 60)
print("TEST: Get my cart items (/cart-items/me)")
print("=" * 60)
try:
    resp = httpx.get(f"{BACKEND}/cart-items/me", headers=headers, timeout=30.0)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Get my orders
print("\n" + "=" * 60)
print("TEST: Get my orders (/orders/me)")
print("=" * 60)
try:
    resp = httpx.get(f"{BACKEND}/orders/me", headers=headers, timeout=30.0)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Get my wishlist
print("\n" + "=" * 60)
print("TEST: Get my wishlist (/wishlist)")
print("=" * 60)
try:
    resp = httpx.get(f"{BACKEND}/wishlist", headers=headers, timeout=30.0)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 4: Get my profile
print("\n" + "=" * 60)
print("TEST: Get my profile (/profile)")
print("=" * 60)
try:
    resp = httpx.get(f"{BACKEND}/profile", headers=headers, timeout=30.0)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 5: Get my addresses
print("\n" + "=" * 60)
print("TEST: Get my addresses (/addresses)")
print("=" * 60)
try:
    resp = httpx.get(f"{BACKEND}/addresses", headers=headers, timeout=30.0)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 6: Dashboard (login as manager first)
print("\n" + "=" * 60)
print("TEST: Dashboard KPIs (/dashboard/summary)")
print("=" * 60)
try:
    mgr_resp = httpx.post(
        f"{BACKEND}/auth/login",
        data={"username": "mgr_verify_test@test.com", "password": "TestPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    mgr_token = mgr_resp.json().get("access_token")
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
    resp = httpx.get(f"{BACKEND}/dashboard/summary", headers=mgr_headers, timeout=30.0)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 7: Products/categories (should still work)
print("\n" + "=" * 60)
print("TEST: Categories (/categories)")
print("=" * 60)
try:
    resp = httpx.get(f"{BACKEND}/categories", timeout=30.0)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Count: {len(data)}")
    if data:
        print(f"First: {json.dumps(data[0], indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")
