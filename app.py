from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_secret_key_to_something_random_and_long"  # CHANGE THIS in production

DATA_FILE = "data.json"

# --- Compte unique (en mémoire) ---
USER_NAME = "Langevin"
# (Pour la dev on génère le hash au démarrage à partir du mot de passe fourni.)
USER_PASSWORD_HASH = generate_password_hash("L@ngev1n208")

# ----------------------
# Helper : gestion data
# ----------------------
def load_data():
    """Charge la liste des PC depuis data.json (retourne liste)."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_data(items):
    """Sauvegarde la liste des PC dans data.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def next_id(items):
    if not items:
        return 1
    return max(item.get("id", 0) for item in items) + 1

# ----------------------
# Routes
# ----------------------
@app.route("/")
def home():
    # page publique — fond animé (handled in CSS via body.homepage)
    items = load_data()
    return render_template("index.html", computers=items)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == USER_NAME and check_password_hash(USER_PASSWORD_HASH, password):
            session["user"] = username
            flash("Connexion réussie.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Identifiants incorrects.", "error")
            return render_template("login.html"), 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Déconnecté.", "info")
    return redirect(url_for("home"))

# Dashboard : liste + création
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    items = load_data()

    if request.method == "POST":
        # Ajouter un PC
        modele = request.form.get("modele", "").strip()
        etat = request.form.get("etat", "").strip()
        composants = request.form.get("composants", "").strip()
        notes = request.form.get("notes", "").strip()
        if not modele:
            flash("Le champ modèle est requis.", "error")
        else:
            new_item = {
                "id": next_id(items),
                "modele": modele,
                "etat": etat or "Reçu",
                "composants": composants,
                "notes": notes,
                "date_ajout": datetime.utcnow().isoformat()
            }
            items.append(new_item)
            save_data(items)
            flash("PC ajouté.", "success")
            return redirect(url_for("dashboard"))

    # GET show
    return render_template("dashboard.html", user=session.get("user"), computers=items)

# Editer un PC
@app.route("/edit/<int:pc_id>", methods=["GET", "POST"])
def edit(pc_id):
    if "user" not in session:
        return redirect(url_for("login"))
    items = load_data()
    item = next((x for x in items if x.get("id") == pc_id), None)
    if not item:
        abort(404)
    if request.method == "POST":
        # update fields
        item["modele"] = request.form.get("modele", "").strip()
        item["etat"] = request.form.get("etat", "").strip()
        item["composants"] = request.form.get("composants", "").strip()
        item["notes"] = request.form.get("notes", "").strip()
        save_data(items)
        flash("PC mis à jour.", "success")
        return redirect(url_for("dashboard"))
    return render_template("edit.html", pc=item)

# Supprimer un PC
@app.route("/delete/<int:pc_id>", methods=["POST"])
def delete(pc_id):
    if "user" not in session:
        return redirect(url_for("login"))
    items = load_data()
    new_items = [x for x in items if x.get("id") != pc_id]
    if len(new_items) == len(items):
        flash("PC introuvable.", "error")
    else:
        save_data(new_items)
        flash("PC supprimé.", "success")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    # create data file if missing
    if not os.path.exists(DATA_FILE):
        save_data([])
    app.run(debug=True)
