"""Test the full registration and login flow to find errors."""
import traceback
import httpx
import json

from app.core.config import settings

BASE = settings.SUPABASE_URL
SERVICE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
ANON_KEY = settings.SUPABASE_ANON_KEY

test_email = "debugtest12345@test.com"
test_password = "TestPass123!"

headers_service = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}
headers_anon = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json",
}

print("=" * 60)
print("STEP 1: Create user in Supabase Auth (admin API)")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BASE}/auth/v1/admin/users",
        headers=headers_service,
        json={
            "email": test_email,
            "password": test_password,
            "email_confirm": True,
            "user_metadata": {"first_name": "Debug", "last_name": "Test", "phone": None},
        },
        timeout=15.0,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("STEP 2: Login via Supabase Auth")
print("=" * 60)
try:
    resp = httpx.post(
        f"{BASE}/auth/v1/token?grant_type=password",
        headers=headers_anon,
        json={"email": test_email, "password": test_password},
        timeout=15.0,
    )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    if resp.status_code == 200:
        token = data.get("access_token", "")
        print(f"Got access_token: {token[:50]}...")
    else:
        print(f"Response: {json.dumps(data, indent=2)[:500]}")
        token = None
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
    token = None

if token:
    print("\n" + "=" * 60)
    print("STEP 3: Get user info with token")
    print("=" * 60)
    try:
        resp = httpx.get(
            f"{BASE}/auth/v1/user",
            headers={
                "apikey": ANON_KEY,
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

print("\n" + "=" * 60)
print("STEP 4: Test raw SQL insert (customers table)")
print("=" * 60)
try:
    import psycopg2
    conn = psycopg2.connect(
        settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://"),
        sslmode="require",
    )
    cur = conn.cursor()
    
    # Try the same INSERT as the register endpoint
    cur.execute("""
        INSERT INTO customers (email, password_hash, is_active, is_admin)
        VALUES (%s, 'supabase_managed', true, false)
        ON CONFLICT (email) DO NOTHING
    """, (test_email,))
    conn.commit()
    print("INSERT INTO customers: SUCCESS")
    
    # Check if the row was inserted
    cur.execute("SELECT id, email, is_active, is_admin FROM customers WHERE email = %s", (test_email,))
    row = cur.fetchone()
    print(f"Customer row: {row}")
    
    if row:
        customer_id = row[0]
        # Try the customer_profiles insert
        cur.execute("""
            INSERT INTO customer_profiles (customer_id, first_name, last_name, phone)
            SELECT c.id, %s, %s, %s FROM customers c WHERE c.email = %s
            ON CONFLICT (customer_id) DO UPDATE SET
            first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name
        """, ("Debug", "Test", None, test_email))
        conn.commit()
        print("INSERT INTO customer_profiles: SUCCESS")
    
    # Cleanup
    cur.execute("DELETE FROM customer_profiles WHERE customer_id = (SELECT id FROM customers WHERE email = %s)", (test_email,))
    cur.execute("DELETE FROM customers WHERE email = %s", (test_email,))
    conn.commit()
    print("Cleanup: SUCCESS")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

# Cleanup Supabase auth user
print("\n" + "=" * 60)
print("STEP 5: Cleanup Supabase auth user")
print("=" * 60)
try:
    # Find user
    resp = httpx.get(
        f"{BASE}/auth/v1/admin/users",
        headers=headers_service,
        params={"filter": f"email.eq.{test_email}"},
        timeout=15.0,
    )
    users = resp.json().get("users", [])
    if users:
        user_id = users[0]["id"]
        del_resp = httpx.delete(
            f"{BASE}/auth/v1/admin/users/{user_id}",
            headers=headers_service,
            timeout=15.0,
        )
        print(f"Deleted auth user: {del_resp.status_code}")
    else:
        print("No auth user to clean up")
except Exception as e:
    print(f"ERROR: {e}")
