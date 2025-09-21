import requests

# DuckDNS config
DUCKDNS_DOMAIN = "rudravcloud"
DUCKDNS_TOKEN = "459b9d65-6fa1-4331-80d3-7a3e5f913190"

# Step 1: Get public IP from external service
try:
    public_ip = requests.get("https://api.ipify.org").text
    print(f"[INFO] Public IP: {public_ip}")
except Exception as e:
    print("[ERROR] Could not get public IP:", e)
    exit(1)

# Step 2: Update DuckDNS
update_url = f"https://www.duckdns.org/update?domains={DUCKDNS_DOMAIN}&token={DUCKDNS_TOKEN}&ip={public_ip}"
response = requests.get(update_url)

if "OK" in response.text:
    print("[SUCCESS] DuckDNS updated:", DUCKDNS_DOMAIN, "->", public_ip)
else:
    print("[FAIL] DuckDNS update failed:", response.text)
