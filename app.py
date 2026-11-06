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
    state_data = {
        "blocked": [],
        "exceptions": [],
        "clients": []
    }
    return jsonify({"state": state_data, "presets": PRESETS, "now": 0})

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
                auth=adguard_
