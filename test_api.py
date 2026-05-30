import requests

# The URL of your local live FastAPI server
url = "http://127.0.0.1:8000/api/v1/tickets/triage"

# A realistic customer support ticket payload
payload = {
    "customer_email": "dev_ops_guy@enterprise.com",
    "subject": "API Webhooks failing signature verification",
    "body": "We updated to your latest package version, and now all incoming webhooks fail our SHA256 verification step. Did your signing key payload format change? Need documentation update or a fix."
}

print("🔄 Sending test ticket to local FastAPI backend...")
response = requests.post(url, json=payload)

if response.status_code == 200:
    print("✅ Success!")
    import json
    print(json.dumps(response.json(), indent=2))
else:
    print(f"❌ Failed with status code {response.status_code}")
    print(response.text)