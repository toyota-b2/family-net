import os
from flask import Flask, jsonify, request

app = Flask(__name__)

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
    return jsonify({"ok": True})

@app.route("/api/unblock", methods=["POST"])
def unblock():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
