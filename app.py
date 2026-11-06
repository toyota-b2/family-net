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
            
        # Προσθέτουμε τους κανόνες ως User Rules στο AdGuard Home
        for d in domains_to_add:
            rule = f"||{d}^"
            requests.post(
                f"{ADGUARD_URL}/control/filtering/add_user_rule",
                json={"rule": rule}, 
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
                f"{ADGUARD_URL}/control/filtering/remove_user_rule",
                json={"rule": rule},
                auth=(ADGUARD_USER, ADGUARD_PASS),
                timeout=3
            )
            
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
