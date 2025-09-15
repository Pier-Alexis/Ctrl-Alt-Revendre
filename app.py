# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_secret_key_change_it"

USERS_FILE = "users.json"
PCS_FILE = "pcs.json"
CHATS_FILE = "chats.json"

# ---------- Helpers JSON ----------
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- Initial data ----------
users = load_json(USERS_FILE, None)
if users is None or users == []:
    # create default admins (passwords default "1234" hashed except Langevin)
    users = [
        {"username":"Langevin","password":generate_password_hash("L@ngev1n208"),"role":"admin"},
        {"username":"Daniel","password":generate_password_hash("1234"),"role":"admin"},
        {"username":"Pier-Alexis","password":generate_password_hash("1234"),"role":"admin"}
    ]
    save_json(USERS_FILE, users)

pcs = load_json(PCS_FILE, [
    {"id":1,"name":"Dell Optiplex 7010","status":"Disponible"},
    {"id":2,"name":"HP EliteBook 840","status":"Nettoyage"}
])
save_json(PCS_FILE, pcs)

# chats: list of conversation objects keyed by username (buyer)
# each conv is {"user": "alice", "messages":[{"from":"alice","text":"hi","time":"...","taken_by":null or "admin"}], "taken_by": null}
chats = load_json(CHATS_FILE, [])
save_json(CHATS_FILE, chats)

# ---------- Auth helpers ----------
def find_user(username):
    for u in users:
        if u["username"] == username:
            return u
    return None

def is_admin():
    return session.get("role") == "admin"

# ---------- Routes ----------

@app.route("/")
def index():
    return render_template("index.html", user=session.get("user"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        u = find_user(username)
        if u and check_password_hash(u["password"], password):
            session["user"] = u["username"]
            session["role"] = u["role"]
            flash(f"Bienvenue {u['username']} !", "success")
            return redirect(url_for("index"))
        flash("Identifiants incorrects", "error")
        return render_template("login.html"), 401
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        if not username or not password:
            flash("Remplissez tous les champs", "error")
            return redirect(url_for("register"))
        if find_user(username):
            flash("Nom d'utilisateur déjà pris", "error")
            return redirect(url_for("register"))
        users.append({"username":username,"password":generate_password_hash(password),"role":"buyer"})
        save_json(USERS_FILE, users)
        # create empty conversation
        chats.append({"user":username,"messages":[], "taken_by": None})
        save_json(CHATS_FILE, chats)
        flash("Compte créé — connectez-vous", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    if "user" in session:
        session.pop("user")
        session.pop("role", None)
        flash("Déconnecté avec succès", "success")
    return redirect(url_for("index"))

# ---------- Admin dashboard ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session or not is_admin():
        flash("Accès réservé aux admins", "error")
        return redirect(url_for("login"))
    # show pcs and chats summary
    pcs = load_json(PCS_FILE, [])
    chats_data = load_json(CHATS_FILE, [])
    # for admin view, show counts and unassigned messages per user
    summary = []
    for conv in chats_data:
        unassigned = [m for m in conv["messages"] if m.get("taken_by") is None]
        summary.append({"user": conv["user"], "unassigned_count": len(unassigned)})
    return render_template("dashboard.html", user=session["user"], pcs=pcs, chats_summary=summary, users=users)

# ---------- Admin actions: add/edit/delete PC ----------
@app.route("/pc/add", methods=["POST"])
def add_pc():
    if "user" not in session or not is_admin():
        return redirect(url_for("login"))
    name = request.form.get("name","").strip()
    status = request.form.get("status","").strip()
    if not name:
        flash("Nom requis", "error")
        return redirect(url_for("dashboard"))
    pcs = load_json(PCS_FILE, [])
    nid = max([p.get("id",0) for p in pcs], default=0)+1
    pcs.append({"id": nid, "name": name, "status": status or "Reçu"})
    save_json(PCS_FILE, pcs)
    flash("PC ajouté", "success")
    return redirect(url_for("dashboard"))

@app.route("/pc/delete/<int:pc_id>", methods=["POST"])
def delete_pc(pc_id):
    if "user" not in session or not is_admin():
        return redirect(url_for("login"))
    pcs = load_json(PCS_FILE, [])
    pcs = [p for p in pcs if p.get("id") != pc_id]
    save_json(PCS_FILE, pcs)
    flash("PC supprimé", "success")
    return redirect(url_for("dashboard"))

@app.route("/pc/edit/<int:pc_id>", methods=["GET","POST"])
def edit_pc(pc_id):
    if "user" not in session or not is_admin():
        return redirect(url_for("login"))
    pcs = load_json(PCS_FILE, [])
    pc = next((p for p in pcs if p.get("id")==pc_id), None)
    if not pc:
        flash("PC introuvable", "error")
        return redirect(url_for("dashboard"))
    if request.method=="POST":
        pc["name"] = request.form.get("name","").strip()
        pc["status"] = request.form.get("status","").strip()
        save_json(PCS_FILE, pcs)
        flash("PC mis à jour", "success")
        return redirect(url_for("dashboard"))
    # GET -> reuse edit template (simple)
    return render_template("edit_pc.html", pc=pc)

# ---------- Change password (requires old) ----------
@app.route("/change_password", methods=["GET","POST"])
def change_password():
    if "user" not in session:
        return redirect(url_for("login"))
    me = find_user(session["user"])
    if request.method=="POST":
        old = request.form.get("old","")
        new = request.form.get("new","")
        if not check_password_hash(me["password"], old):
            flash("Ancien mot de passe incorrect", "error")
            return redirect(url_for("change_password"))
        me["password"] = generate_password_hash(new)
        save_json(USERS_FILE, users)
        flash("Mot de passe changé", "success")
        return redirect(url_for("dashboard") if me["role"]=="admin" else url_for("index"))
    return render_template("change_password.html")

# ---------- Chat endpoints (API) ----------
@app.route("/api/chats", methods=["GET"])
def api_chats():
    # return all conversations (admins) or only user's conv (buyers)
    if "user" not in session:
        return jsonify({"error":"unauth"}), 401
    chats_data = load_json(CHATS_FILE, [])
    role = session.get("role")
    if role == "admin":
        return jsonify(chats_data)
    else:
        # find conversation of current buyer
        conv = next((c for c in chats_data if c["user"]==session["user"]), {"user":session["user"], "messages":[]})
        return jsonify(conv)

@app.route("/api/chat/send", methods=["POST"])
def api_chat_send():
    if "user" not in session:
        return jsonify({"error":"unauth"}), 401
    data = request.json or {}
    text = data.get("text","").strip()
    if not text:
        return jsonify({"error":"empty"}), 400
    chats_data = load_json(CHATS_FILE, [])
    # ensure conv exists for buyer
    conv = next((c for c in chats_data if c["user"]==session["user"]), None)
    if not conv:
        conv = {"user": session["user"], "messages": [], "taken_by": None}
        chats_data.append(conv)
    conv["messages"].append({"from": session["user"], "text": text, "time": datetime.now().isoformat(), "taken_by": None})
    save_json(CHATS_FILE, chats_data)
    return jsonify({"ok":True})

@app.route("/api/admin/send", methods=["POST"])
def api_admin_send():
    if "user" not in session or not is_admin():
        return jsonify({"error":"unauth"}), 401
    data = request.json or {}
    target = data.get("user")
    text = data.get("text","").strip()
    if not target or not text:
        return jsonify({"error":"bad"}), 400
    chats_data = load_json(CHATS_FILE, [])
    conv = next((c for c in chats_data if c["user"]==target), None)
    if not conv:
        conv = {"user": target, "messages": [], "taken_by": None}
        chats_data.append(conv)
    conv["messages"].append({"from": session["user"], "text": text, "time": datetime.now().isoformat(), "taken_by": session["user"]})
    save_json(CHATS_FILE, chats_data)
    return jsonify({"ok":True})

@app.route("/api/admin/take", methods=["POST"])
def api_admin_take():
    if "user" not in session or not is_admin():
        return jsonify({"error":"unauth"}), 401
    data = request.json or {}
    target = data.get("user")
    msg_index = data.get("index")
    if target is None or msg_index is None:
        return jsonify({"error":"bad"}), 400
    chats_data = load_json(CHATS_FILE, [])
    conv = next((c for c in chats_data if c["user"]==target), None)
    if not conv or msg_index < 0 or msg_index >= len(conv["messages"]):
        return jsonify({"error":"notfound"}), 404
    conv["messages"][msg_index]["taken_by"] = session["user"]
    save_json(CHATS_FILE, chats_data)
    return jsonify({"ok":True})

# ---------- simple templates for edit pc and change pw are referenced above ----------
# If missing templates, create minimal ones (we included them in templates below)

if __name__ == "__main__":
    # init files if missing
    save_json(USERS_FILE, users)
    save_json(PCS_FILE, pcs)
    save_json(CHATS_FILE, chats)
    app.run(debug=True, host="0.0.0.0")
