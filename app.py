import os
import requests
from flask import Flask, jsonify, request
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

APP_PASS = os.getenv("APP_PASS", "1234")
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
        res = requests.get(f"{ADGUARD_URL}/control/filtering/status", auth=adguard_auth, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        user_rules = data.get("user_rules", [])
        formatted_blocked = []
        
        if isinstance(user_rules, list):
            for rule in user_rules:
                if isinstance(rule, str):
                    if rule.startswith("||") and rule.endswith("^"):
                        domain = rule[2:-1]
                        formatted_blocked.append({"domain": domain})
                    elif rule and not rule.startswith("!"):
                        formatted_blocked.append({"domain": rule})

        state_data = {
            "blocked": formatted_blocked,
            "exceptions": [],
            "clients": []
        }
        
        return jsonify({"state": state_data, "presets": PRESETS, "now": 0})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

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
            requests.post(
                f"{ADGUARD_URL}/control/filtering/add_url",
                auth=adguard_auth,
                json={"url": rule, "name": d},
                timeout=10
            )
            
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/unblock", methods=["POST"])
def unblock():
    try:
        req_data = request.get_json() or {}
        domain = req_data.get("domain")
        if domain:
            rule = f"||{domain}^"
            requests.post(
                f"{ADGUARD_URL}/control/filtering/remove_url",
                auth=adguard_auth,
                json={"url": rule},
                timeout=10
            )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
