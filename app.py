import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

ADGUARD_URL = "https://adguard-production-d5a7.up.railway.app" 
ADGUARD_USER = ""  
ADGUARD_PASS = ""  

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
        r = requests.get(f"{ADGUARD_URL}/control/filtering/status", auth=(ADGUARD_USER, ADGUARD_PASS), timeout=3)
        data = r.json()
        
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
        return jsonify({"state": {"blocked": [], "paused": False}, "presets": PRESETS, "now": 0})

@app.route("/api/block", methods=["POST"])
def block():
    try:
        req_data = request.get_json() or {}
        domain = req_data.get("domain")
        preset = req_data.
