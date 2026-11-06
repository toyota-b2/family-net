import os
from flask import Flask, jsonify, request

app = Flask(__name__)

BLOCKED_DOMAINS = []
is_paused = False

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
    formatted_blocked = [{"domain": d} for d in BLOCKED_DOMAINS]
    state_data = {
        "blocked": formatted_blocked,
        "exceptions": [],
        "clients": [],
        "paused": is_paused
    }
    return jsonify({"state": state_data, "presets": PRESETS, "now": 0})

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
            
        for d in domains_to_add:
            if d not in BLOCKED_DOMAINS:
                BLOCKED_DOMAINS.append(d)
                
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/unblock", methods=["POST"])
def unblock():
    try:
        req_data = request.get_json() or {}
        domain = req_data.get("domain")
        if domain in BLOCKED_DOMAINS:
            BLOCKED_DOMAINS.remove(domain)
            
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/pause", methods=["POST"])
def pause():
    global is_paused
    is_paused = True
    return jsonify({"ok": True})

@app.route("/api/resume", methods=["POST"])
def resume():
    global is_paused
    is_paused = False
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
