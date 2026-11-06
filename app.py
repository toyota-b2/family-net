import base64
import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Διαβάζουμε τις μεταβλητές περιβάλλοντος από το Railway
APP_PASS = os.getenv("APP_PASS", "1234")
ADGUARD_URL = os.getenv("ADGUARD_URL", "").rstrip("/")
ADGUARD_USER = os.getenv("ADGUARD_USER", "admin")
ADGUARD_PASS = os.getenv("ADGUARD_PASS", "")

# Δημιουργία Base64 Basic Auth Header για το AdGuard Home
credentials = f"{ADGUARD_USER}:{ADGUARD_PASS}"
encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
    "utf-8"
)

ADGUARD_HEADERS = {
    "Authorization": f"Basic {encoded_credentials}",
    "Content-Type": "application/json",
}


def get_adguard_status():
  """Επικοινωνία με το AdGuard API για ανάγνωση κατάστασης"""
  url = f"{ADGUARD_URL}/control/filtering/status"
  response = requests.get(url, headers=ADGUARD_HEADERS, timeout=10)
  response.raise_for_status()
  return response.json()


@app.route("/")
def index():
  # Διαβάζει το index.html απευθείας από τον φάκελο, χωρίς ανάγκη για templates folder
  with open("index.html", "r", encoding="utf-8") as f:
    return f.read()


@app.route("/api/state")
def api_state():
  try:
    status = get_adguard_status()
    return jsonify({"success": True, "data": status})
  except Exception as e:
    return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/block", methods=["POST"])
def block():
  try:
    url = f"{ADGUARD_URL}/control/filtering/status"
    st = requests.get(url, headers=ADGUARD_HEADERS, timeout=10)
    st.raise_for_status()
    return jsonify({"success": True})
  except Exception as e:
    return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8080)
