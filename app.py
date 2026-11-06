import os
import requests
from flask import Flask, jsonify, request
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

ADGUARD_URL = os.getenv("ADGUARD_URL", "").rstrip("/")
ADGUARD_USER = os.getenv("ADGUARD_USER", "admin")
ADGUARD_PASS = os.getenv("ADGUARD_PASS", "")

adguard_auth = HTTPBasicAuth(ADGUARD_USER, ADGUARD_PASS)

PRESETS = {
    "YouTube": ["youtube.com", "googlevideo.com", "ytimg.com"],
    "TikTok": ["tiktok.com", "tiktokcdn.com", "ibytedtos.com"],
    "Instagram": ["instagram.com", "cdninstagram.com"],
    "Roblox": ["roblox.com", "rbxcdn.com"]
}

@app.route("/")
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.route("/api/state")
def api_state():
    try:
        print(f"DEBUG: Connecting to AdGuard at {ADGUARD_URL}...")
        res = requests.get(f"{ADGUARD_URL}/control/filtering/status", auth=adguard_auth, timeout=5)
        print(f"DEBUG: AdGuard status response code: {res.status_code}")
        res.raise_for_status()
        data = res.json()
        
        user_rules = data.get("user_rules", [])
        formatted_blocked = []
        
        for rule in user_rules:
            if rule and not rule.startswith("!"):
                clean_domain = rule.replace("||", "").replace("^", "").strip()
                if clean_domain:
                    formatted_blocked.append({"domain": clean_domain})

        state_data = {
            "blocked": formatted_blocked,
            "exceptions": [],
            "clients": []
        }
        return jsonify({"state": state_data, "presets": PRESETS, "now": 0})
    except Exception as e:
        print(f"DEBUG ERROR in api_state: {str(e)}")
        return jsonify({"state": {"blocked": [], "exceptions": [], "clients": []}, "presets": PRESETS, "now": 0})

@app.route("/api/block", methods=["POST"])
def block():
    try:
        req_data = request.get_json() or {}
        domain = req_data.get("domain")
        preset = req_data.get("preset")
        
        domains_to_block = []
        if preset and preset in PRESETS:
            domains_to_block = PRESETS[preset]
        elif domain:
            domains_to_block = [domain]
            
        for d in domains_to_block:
            rule = f"||{d}^"
            print(f"DEBUG: Trying to block rule: {rule}")
            response = requests.post(
                f"{ADGUARD_URL}/control/filtering/add_user_rule",
                auth=adguard_auth,
                json={"rule": rule},
                timeout=5
            )
            print(f"DEBUG: Block response code: {response.status_code}, text: {response.text}")
            
        return jsonify({"ok": True})
    except Exception as e:
        print(f"DEBUG ERROR in block: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/unblock", methods=["POST"])
def unblock():
    try:
        req_data = request.get_json() or {}
        domain = req_data.get("domain")
        if domain:
            rule = f"||{domain}^"
            print(f"DEBUG: Trying to unblock rule: {rule}")
            response = requests.post(
                f"{ADGUARD_URL}/control/filtering/remove_user_rule",
                auth=adguard_auth,
                json={"rule": rule},
                timeout=5
            )
            print(f"DEBUG: Unblock response code: {response.status_code}, text: {response.text}")
            
        return jsonify({"ok": True})
    except Exception as e:
        print(f"DEBUG ERROR in unblock: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
