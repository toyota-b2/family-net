import os
import requests
from flask import Flask, jsonify, request
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

# Διαβάζουμε τις μεταβλητές περιβάλλοντος από το Railway
APP_PASS = os.getenv("APP_PASS", "1234")
ADGUARD_URL = os.getenv("ADGUARD_URL", "").rstrip("/")
ADGUARD_USER = os.getenv("ADGUARD_USER", "admin")
ADGUARD_PASS = os.getenv("ADGUARD_PASS", "")

# Χρησιμοποιούμε το ενσωματωμένο BasicAuth του requests για να αποφύγουμε λάθη με σύμβολα
adguard_auth = HTTPBasicAuth(ADGUARD_USER, ADGUARD_PASS)


@app.route("/")
def index():
  with open("index.html", "r", encoding="utf-8") as f:
    return f.read()


@app.route("/api/state")
def api_state():
  try:
    url = f"{ADGUARD_URL}/control/filtering/status"
    response = requests.get(url, auth=adguard_auth, timeout=10)
    response.raise_for_status()
    return jsonify({"success": True, "state": response.json(), "presets": {}, "now": 0})
  except Exception as e:
    return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/block", methods=["POST"])
def block():
  try:
    # Εδώ θα μπει η λογική του block/unblock
    return jsonify({"success": True})
  except Exception as e:
    return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8080)
