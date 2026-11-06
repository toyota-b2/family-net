"""Family Net Control: μικρό web app που διαχειρίζεται blocklist/unblock στο AdGuard Home."""
import json, os, re, threading, time, uuid
import requests
from flask import Flask, jsonify, request, send_file, Response

_raw_adguard = os.environ.get("ADGUARD_URL", "http://adguard:3000").rstrip("/")
if not _raw_adguard.startswith(("http://", "https://")):
    _raw_adguard = f"http://{_raw_adguard}"
ADGUARD_URL = _raw_adguard

ADGUARD_AUTH = (os.environ.get("ADGUARD_USER", ""), os.environ.get("ADGUARD_PASS", ""))
APP_USER = os.environ.get("APP_USER", "admin")
APP_PASS = os.environ.get("APP_PASS", "")
STATE_FILE = os.path.join(os.environ.get("DATA_DIR", "data"), "state.json")
BEGIN, END = "! BEGIN FamilyNetControl", "! END FamilyNetControl"

PRESETS = {
    "Netflix": ["netflix.com", "nflxvideo.net", "nflximg.net", "nflxext.com", "nflxso.net"],
    "YouTube": ["youtube.com", "youtu.be", "googlevideo.com", "ytimg.com"],
    "TikTok": ["tiktok.com", "tiktokv.com", "tiktokcdn.com", "byteoversea.com"],
    "Instagram": ["instagram.com", "cdninstagram.com"],
    "Facebook": ["facebook.com", "fbcdn.net"],
    "Snapchat": ["snapchat.com", "sc-cdn.net"],
    "Roblox": ["roblox.com", "rbxcdn.com"],
    "Twitch": ["twitch.tv", "ttvnw.net"],
}

app = Flask(__name__)
lock = threading.Lock()
state = {"blocked": [], "exceptions": []}
last_pushed = None


def load():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            state.update(json.load(f))


def save():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def clean_domain(raw):
    d = re.sub(r"^\w+://", "", raw.strip().lower()).split("/")[0].split(":")[0]
    d = d[4:] if d.startswith("www.") else d
    return d if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", d) else None


def build_rules():
    now = time.time()
    rules = [BEGIN]
    for b in state["blocked"]:
        if not (b.get("paused_until") and b["paused_until"] > now):
            rules.append(f"||{b['domain']}^")
    for e in state["exceptions"]:
        if not e.get("until") or e["until"] > now:
            rules.append(f"@@||{e['domain']}^$client='{e['client']}'")
    rules.append(END)
    return rules


def push(force=False):
    """Στέλνει τους κανόνες στο AdGuard Home, κρατώντας ό,τι άλλο έχεις ήδη εκεί."""
    global last_pushed
    rules = build_rules()
    if rules == last_pushed and not force:
        return
    st = requests.get(f"{ADGUARD_URL}/control/filtering/status", auth=ADGUARD_AUTH, timeout=10)
    st.raise_for_status()
    others, inside = [], False
    for r in st.json().get("user_rules") or []:
        if r == BEGIN: inside = True
        elif r == END: inside = False
        elif not inside: others.append(r)
    r = requests.post(f"{ADGUARD_URL}/control/filtering/set_rules", auth=ADGUARD_AUTH,
                      json={"rules": others + rules}, timeout=10)
    r.raise_for_status()
    last_pushed = rules


def housekeeping():
    while True:
        time.sleep(30)
        try:
            with lock:
                now = time.time()
                state["exceptions"] = [e for e in state["exceptions"] if not e.get("until") or e["until"] > now]
                for b in state["blocked"]:
                    if b.get("paused_until") and b["paused_until"] <= now:
                        b["paused_until"] = None
                save()
                push()
        except Exception as exc:
            print("sync error:", exc)


@app.before_request
def auth():
    a = request.authorization
    if not (a and a.username == APP_USER and a.password == APP_PASS):
        return Response("Χρειάζεται σύνδεση", 401, {"WWW-Authenticate": 'Basic realm="Family Net Control"'})


@app.get("/")
def index():
    return send_file("index.html")


def clients():
    try:
        j = requests.get(f"{ADGUARD_URL}/control/clients", auth=ADGUARD_AUTH, timeout=10).json()
        names = [c["name"] for c in j.get("clients") or []]
        names += [c.get("name") or c["ip"] for c in j.get("auto_clients") or []]
        return sorted(set(names))
    except Exception:
        return []


@app.get("/api/state")
def get_state():
    with lock:
        return jsonify(state=state, presets=PRESETS, clients=clients(), now=time.time())


def mutate(fn):
    with lock:
        fn()
        save()
        try:
            push()
            return jsonify(ok=True)
        except Exception as exc:
            return jsonify(ok=False, error=f"Δεν μίλησα με το AdGuard Home: {exc}"), 502


@app.post("/api/block")
def block():
    j = request.json
    domains = PRESETS.get(j.get("preset")) or [clean_domain(j.get("domain", ""))]
    if not all(domains):
        return jsonify(ok=False, error="Μη έγκυρο domain"), 400
    def f():
        have = {b["domain"] for b in state["blocked"]}
        for d in domains:
            if d not in have:
                state["blocked"].append({"domain": d, "paused_until": None})
    return mutate(f)


@app.post("/api/unblock")
def unblock():
    d = request.json["domain"]
    return mutate(lambda: state.update(blocked=[b for b in state["blocked"] if b["domain"] != d]))


@app.post("/api/pause")
def pause():
    j = request.json
    until = time.time() + j["minutes"] * 60 if j.get("minutes") else None
    def f():
        for b in state["blocked"]:
            if b["domain"] in j["domains"]:
                b["paused_until"] = until
    return mutate(f)


@app.post("/api/allow")
def allow():
    j = request.json
    client = j.get("client", "").strip()
    client = client if re.fullmatch(r"[\w.:/-]+", client) else None
    if not client:
        return jsonify(ok=False, error="Βάλε όνομα ή IP συσκευής"), 400
    until = time.time() + j["minutes"] * 60 if j.get("minutes") else None
    domains = [b["domain"] for b in state["blocked"] if b["domain"] in j["domains"]]
    def f():
        for d in domains:
            state["exceptions"].append({"id": uuid.uuid4().hex[:8], "domain": d, "client": client, "until": until})
    return mutate(f)


@app.post("/api/disallow")
def disallow():
    i = request.json["id"]
    return mutate(lambda: state.update(exceptions=[e for e in state["exceptions"] if e["id"] != i]))


if __name__ == "__main__":
    if not APP_PASS:
        raise SystemExit("Όρισε APP_PASS (ο κωδικός του app).")
    load()
    threading.Thread(target=housekeeping, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
