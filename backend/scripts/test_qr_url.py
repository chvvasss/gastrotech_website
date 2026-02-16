"""Test the live API endpoint with auth."""
import requests, sys

# Get a token
login_resp = requests.post("http://127.0.0.1:8000/api/v1/auth/login/", json={
    "email": "admin@gastrotech.com",
    "password": "admin123"
})
print(f"Login: {login_resp.status_code}")
if login_resp.status_code != 200:
    print(f"FAIL: {login_resp.text[:200]}")
    sys.exit(1)

token = login_resp.json()["access"]
headers = {"Authorization": f"Bearer {token}"}

# List
resp = requests.get("http://127.0.0.1:8000/api/v1/admin/info-sheets/", headers=headers)
print(f"List: {resp.status_code}")
data = resp.json()
items = data if isinstance(data, list) else data.get("results", [])
for item in items:
    print(f"  id={item['id']}")
    print(f"  title={item['title']}")
    print(f"  pdf_url={item.get('pdf_url')}")
    print(f"  qr_url={item.get('qr_url')}")

# Test media
if items:
    qr_url = items[0].get("qr_url")
    if qr_url:
        r = requests.get(f"http://127.0.0.1:8000{qr_url}")
        print(f"QR image ({qr_url}): {r.status_code}")
    pdf_url = items[0].get("pdf_url")
    if pdf_url:
        r = requests.get(f"http://127.0.0.1:8000{pdf_url}")
        print(f"PDF ({pdf_url}): {r.status_code}")

# Test upload
print("\n--- Test Upload ---")
import io
pdf_data = b"%PDF-1.4 test content"
files = {"pdf_file": ("test.pdf", io.BytesIO(pdf_data), "application/pdf")}
data = {"title": "Test Upload"}
resp = requests.post("http://127.0.0.1:8000/api/v1/admin/info-sheets/", headers=headers, files=files, data=data)
print(f"Create: {resp.status_code}")
if resp.status_code in (200, 201):
    print(f"  Response: {resp.json()}")
else:
    print(f"  Error: {resp.text[:500]}")
