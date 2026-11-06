@app.route("/api/state")
def api_state():
    try:
        # Παίρνουμε τη γενική κατάσταση ή τα filtering settings
        res = requests.get(f"{ADGUARD_URL}/control/filtering/status", auth=adguard_auth, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        # Ασφαλή ανάγνωση των κανόνων (user_rules)
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
        # Επιστρέφουμε την ακριβή εξαίρεση για να ξέρουμε τι χτύπησε αν ξανασυμβεί
        return jsonify({"ok": False, "error": str(e)}), 500
