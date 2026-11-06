import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Εδώ βάζεις την τοπική διεύθυνση του AdGuard Home σου (π.χ. http://192.168.1.50:80)
ADGUARD_URL = "http://192.168.1.X:80" 
ADGUARD_USER = "admin"  # Το username σου στο AdGuard
ADGUARD_PASS = "password" # Ο κωδικός σου στο AdGuard

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
        # Παίρνουμε τους αποκλεισμένους κανόνες απευθείας από το AdGuard Home
        r = requests.get(f"{ADGUARD_URL}/control/filtering/status", auth=(ADGUARD_USER, ADGUARD_PASS), timeout=3)
        data = r.json()
        
        # Φιλτράρουμε τα user rules
        blocked_domains = []
        if "user_rules" in data:
            for rule in data["user_rules"]:
                if rule.startswith("||") and rule.endswith("^"):
                    domain = rule[2:-1]
                    blocked_domains.append({"domain": domain})

        state_data = {
            "blocked": blocked_domains,
            "exceptions": [],
            "clients": [],
            "paused": not data.get("enabled", True)
        }
        return jsonify({"state": state_data, "presets": PRESETS, "now": 0})
    except Exception as e:
        # Αν υπάρξει θέμα σύνδεσης, γυρνάμε κενή λίστα για να μην κολλήσει το UI
        return jsonify({"state": {"blocked": [], "paused": False}, "presets": PRESETS, "now": 0})

@app.route("/api/block", methods=["POST"])
def block():
    try:
        req_data = request.get_json() or {}
        domain = req_data.get("domain")
        preset = req_data.get("preset")
        
        domains_to_add = []
        if preset and preset in PRESETS:
            domains_to_add = PRESETS[preset]
        elif domain:
            domains_to_add = [domain]
            
        # Προσθέτουμε τους κανόνες στο AdGuard Home μέσω του API του
        for d in domains_to_add:
            rule = f"||{d}^"
            requests.post(
                f"{ADGUARD_URL}/control/filtering/add_url",
                json={"url": rule, "name": d}, # Ή add_user_rule ανάλογα με την έκδοση
                auth=(ADGUARD_USER, ADGUARD_PASS),
                timeout=3
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
                json={"url": rule},
                auth=(ADGUARD_USER, ADGUARD_PASS),
                timeout=3
            )
            
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/pause", methods=["POST"])
def pause():
    try:
        requests.post(
            f"{ADGUARD_URL}/control/filtering/config",
            json={"enabled": False},
            auth=(ADGUARD_USER, ADGUARD_PASS),
            timeout=3
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/resume", methods=["POST"])
def resume():
    try:
        requests.post(
            f"{ADGUARD_URL}/control/filtering/config",
            json={"enabled": True},
            auth=(ADGUARD_USER, ADGUARD_PASS),
            timeout=3
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
