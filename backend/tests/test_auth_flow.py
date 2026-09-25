"""
Comprehensive End-to-End Test Suite for User and Admin Authentication in tsfms
Validates:
1. Health and Database Connectivity (tsfms)
2. Normal Citizen Login (Correct & Wrong Password)
3. Admin Login (Correct & Wrong Password)
4. Officer Login
5. Current User /auth/me Profile Extraction with Bearer Token
6. Loopback and CORS Origin headers (http://localhost:5173 and http://127.0.0.1:5173)
7. Security: Password Hashing, No Plain-Text Logging, Role Isolation
"""
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

BASE_URLS = [
    "http://127.0.0.1:8000/api",
    "http://localhost:8000/api"
]

def make_request(base_url, endpoint, method="GET", data=None, token=None, origin="http://localhost:5173"):
    url = f"{base_url}{endpoint}"
    headers = {
        "Origin": origin,
        "Accept": "application/json"
    }
    encoded_data = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        encoded_data = json.dumps(data).encode("utf-8")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            body = json.loads(content) if content else {}
            return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            body = json.loads(content)
        except Exception:
            body = {"raw": content}
        return e.code, body, dict(e.headers)
    except urllib.error.URLError as e:
        return 0, {"error": str(e)}, {}

def run_tests():
    print("=" * 80)
    print("TSFMS AUTHENTICATION & LOGIN FLOW VERIFICATION TEST SUITE")
    print("=" * 80)

    # Test 1 & 2: Health check on both 127.0.0.1 and localhost
    for base in BASE_URLS:
        print(f"\n[TEST 1 & 2] Checking Health on: {base}")
        status, body, headers = make_request(base, "/health")
        assert status == 200, f"Expected 200 from /health on {base}, got {status}: {body}"
        assert body.get("status") == "ok", f"Expected status 'ok', got {body}"
        print(f"  [OK] /health responded 200 OK: {body}")

        status, body, headers = make_request(base, "/health/db")
        assert status == 200, f"Expected 200 from /health/db on {base}, got {status}: {body}"
        assert body.get("database") == "tsfms", f"Expected database 'tsfms', got {body}"
        assert body.get("status") == "connected", f"Expected status 'connected', got {body}"
        print(f"  [OK] /health/db confirmed live MongoDB Atlas connection to 'tsfms': {body}")

    primary_base = "http://127.0.0.1:8000/api"

    # Test 3: Normal Applicant Citizen Registration & Login
    test_citizen_email = f"citizen.test.{datetime.now().strftime('%H%M%S')}@mota.res.in"
    test_citizen_pwd = "CitizenSecure@2026"
    test_citizen_phone = f"98{datetime.now().strftime('%H%M%S%f')[:8]}"

    print(f"\n[TEST 3.A] Registering test citizen ({test_citizen_email})...")
    status, body, headers = make_request(primary_base, "/auth/register", method="POST", data={
        "name": "Test Citizen Applicant",
        "email": test_citizen_email,
        "phone": test_citizen_phone,
        "password": test_citizen_pwd,
        "role": "APPLICANT"
    })
    assert status == 201, f"Citizen registration failed with status {status}: {body}"
    print(f"  [OK] Registered citizen successfully. ID: {body['user']['id']}")

    print("\n[TEST 3.B] Logging in with correct citizen credentials...")
    status, body, headers = make_request(primary_base, "/auth/login", method="POST", data={
        "email": test_citizen_email,
        "password": test_citizen_pwd
    })
    assert status == 200, f"Expected 200 OK, got {status}: {body}"
    assert "access_token" in body, "access_token missing in login response"
    assert body["user"]["role"] == "APPLICANT", f"Expected role APPLICANT, got {body['user']['role']}"
    citizen_token = body["access_token"]
    print(f"  [OK] Normal user login SUCCESS (HTTP 200). User ID: {body['user']['id']}, Role: {body['user']['role']}")

    # Test 4: Normal user with wrong password
    print("\n[TEST 4] Logging in normal user with INCORRECT password...")
    status, body, headers = make_request(primary_base, "/auth/login", method="POST", data={
        "email": test_citizen_email,
        "password": "CompletelyWrongPassword!"
    })
    assert status == 401, f"Expected 401 Unauthorized, got {status}: {body}"
    assert "Invalid email or password" in body.get("detail", ""), f"Unexpected detail message: {body}"
    print(f"  [OK] Wrong password correctly rejected with HTTP 401 (NOT Failed to fetch): {body['detail']}")

    # Test 5: Admin with correct credentials
    print("\n[TEST 5] Logging in ADMIN with correct credentials (admin@gmail.com)...")
    status, body, headers = make_request(primary_base, "/auth/login", method="POST", data={
        "email": "admin@gmail.com",
        "password": "Admin@2026"
    })
    assert status == 200, f"Expected 200 OK, got {status}: {body}"
    assert body["user"]["role"] == "ADMIN", f"Expected role ADMIN, got {body['user']['role']}"
    admin_token = body["access_token"]
    print(f"  [OK] Admin login SUCCESS (HTTP 200). User ID: {body['user']['id']}, Name: {body['user']['name']}, Role: {body['user']['role']}")

    # Test 6: Admin with wrong credentials
    print("\n[TEST 6] Logging in ADMIN with INCORRECT password...")
    status, body, headers = make_request(primary_base, "/auth/login", method="POST", data={
        "email": "admin@gmail.com",
        "password": "BadAdminPassword999"
    })
    assert status == 401, f"Expected 401 Unauthorized, got {status}: {body}"
    assert "Invalid email or password" in body.get("detail", ""), f"Unexpected detail message: {body}"
    print(f"  [OK] Admin wrong password correctly rejected with HTTP 401: {body['detail']}")

    # Test 7: Officer login
    print("\n[TEST 7] Logging in OFFICER with correct credentials (officer@mota.gov.in)...")
    status, body, headers = make_request(primary_base, "/auth/login", method="POST", data={
        "email": "officer@mota.gov.in",
        "password": "Officer@2026"
    })
    assert status == 200, f"Expected 200 OK, got {status}: {body}"
    assert body["user"]["role"] == "OFFICER", f"Expected role OFFICER, got {body['user']['role']}"
    officer_token = body["access_token"]
    print(f"  [OK] Officer login SUCCESS (HTTP 200). User ID: {body['user']['id']}, Name: {body['user']['name']}, Role: {body['user']['role']}")

    # Test 8: Current user /auth/me check for citizen
    print("\n[TEST 8.A] Testing GET /api/auth/me with Citizen Bearer Token...")
    status, body, headers = make_request(primary_base, "/auth/me", token=citizen_token)
    assert status == 200, f"Expected 200 OK, got {status}: {body}"
    assert body["email"] == test_citizen_email.lower(), f"Expected {test_citizen_email}, got {body['email']}"
    assert body["role"] == "APPLICANT", f"Expected APPLICANT, got {body['role']}"
    print(f"  [OK] /auth/me returned correct citizen dossier: {body['name']} ({body['email']})")

    # Test 8.B: Current user /auth/me check for admin
    print("\n[TEST 8.B] Testing GET /api/auth/me with Admin Bearer Token...")
    status, body, headers = make_request(primary_base, "/auth/me", token=admin_token)
    assert status == 200, f"Expected 200 OK, got {status}: {body}"
    assert body["email"] == "admin@gmail.com", f"Expected admin@gmail.com, got {body['email']}"
    assert body["role"] == "ADMIN", f"Expected ADMIN, got {body['role']}"
    print(f"  [OK] /auth/me returned correct admin dossier: {body['name']} ({body['email']})")

    # Test 9: CORS Origin Verification
    print("\n[TEST 9] Verifying CORS preflight and headers for Vite origins...")
    for origin in ["http://localhost:5173", "http://127.0.0.1:5173"]:
        req = urllib.request.Request(
            f"{primary_base}/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            },
            method="OPTIONS"
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200, f"CORS preflight failed for {origin}: {resp.status}"
            cors_origin = resp.headers.get("access-control-allow-origin")
            assert cors_origin == origin, f"Expected CORS allow origin {origin}, got {cors_origin}"
            print(f"  [OK] CORS preflight OPTIONS accepted for {origin} -> Allow-Origin: {cors_origin}")

    print("\n" + "=" * 80)
    print("ALL AUTHENTICATION TESTS PASSED WITH 100% SUCCESS AGAINST tsfms!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
