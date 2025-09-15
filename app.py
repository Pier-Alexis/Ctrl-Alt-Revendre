from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_secret_key_to_something_random_and_long"

# --- Fichiers JSON ---
USERS_FILE = "users.json"
PC_FILE = "data.json"
CHATS_FILE = "chats.json"

# --- Fonctions utilitaires ---
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# --- Initialisation utilisateurs admin ---
users = load_json(USERS_FILE)
if not users:
    users = [
        {"username": "Daniel", "password": generate_password_hash("1234"), "role": "admin"},
        {"username": "Pier-Alexis", "password": generate_password_hash("1234"), "role": "admin"}
    ]
    save_json(USERS_FILE, users)

# --- Page d'accueil ---
@app.route("/")
def home():
    return render_template("index.html")

# --- Inscription acheteur ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Remplissez tous les champs", "error")
            return redirect(url_for("register"))

        users = load_json(USERS_FILE)
        if any(u["username"] == username for u in users):
            flash("Nom déjà utilisé", "error")
            return redirect(url_for("register"))

        users.append({
            "username": username,
            "password": generate_password_hash(password),
            "role": "buyer"
        })
        save_json(USERS_FILE, users)
        flash("Compte créé ! Connectez-vous.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

# --- Connexion ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_json(USERS_FILE)
        user = next((u for u in users if u["username"] == username), None)
        if user and check_password_hash(user["password"], password):
            session["user"] = username
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Identifiants incorrects", "error")
        return render_template("login.html"), 401
    return render_template("login.html")

# --- Dashboard ---
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    role = session.get("role")
    if role == "admin":
        pcs = load_json(PC_FILE)
        users_list = load_json(USERS_FILE)
        return render_template("dashboard.html", user=session["user"], pcs=pcs, users=users_list)
    else:
        pcs = load_json(PC_FILE)
        return render_template("buyer_dashboard.html", user=session["user"], pcs=pcs)

# --- Déconnexion ---
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect(url_for("home"))

# --- Ajouter / modifier PC (admin) ---
@app.route("/edit_pc", methods=["GET", "POST"])
def edit_pc():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    pcs = load_json(PC_FILE)
    if request.method == "POST":
        pc_name = request.form.get("name")
        pc_status = request.form.get("status")
        pc_id = request.form.get("id")

        if pc_id:  # modifier existant
            for pc in pcs:
                if pc["id"] == int(pc_id):
                    pc["name"] = pc_name
                    pc["status"] = pc_status
        else:  # nouveau PC
            new_id = max([p["id"] for p in pcs], default=0) + 1
            pcs.append({"id": new_id, "name": pc_name, "status": pc_status})

        save_json(PC_FILE, pcs)
        flash("PC sauvegardé !", "success")
        return redirect(url_for("dashboard"))

    pc_id = request.args.get("id")
    pc_data = next((p for p in pcs if str(p["id"]) == str(pc_id)), None) if pc_id else None
    return render_template("edit.html", pc=pc_data)

# --- Gérer utilisateurs admin ---
@app.route("/admin_users", methods=["GET", "POST"])
def admin_users():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    users_list = load_json(USERS_FILE)

    if request.method == "POST":
        username = request.form.get("username")
        new_password = request.form.get("new_password")
        for u in users_list:
            if u["username"] == username and u["role"] == "admin":
                u["password"] = generate_password_hash(new_password)
        save_json(USERS_FILE, users_list)
        flash("Mot de passe changé !", "success")
        return redirect(url_for("admin_users"))

    return render_template("admin_users.html", users=users_list)

# --- Chat ---
@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "user" not in session:
        return redirect(url_for("login"))

    chats = load_json(CHATS_FILE)
    if request.method == "POST":
        message = request.form.get("message")
        chats.append({
            "from": session["user"],
            "to": "admin",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        save_json(CHATS_FILE, chats)
        return redirect(url_for("chat"))

    # filtrer selon role
    role = session.get("role")
    if role == "admin":
        # voir tous les messages
        return render_template("chat.html", chats=chats, user=session["user"], role="admin")
    else:
        # voir seulement ses messages
        user_chats = [c for c in chats if c["from"] == session["user"] or c["to"] == session["user"]]
        return render_template("chat.html", chats=user_chats, user=session["user"], role="buyer")

if __name__ == "__main__":
    app.run(debug=True)
