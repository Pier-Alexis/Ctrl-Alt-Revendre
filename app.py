from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_secret_key_to_something_random_and_long"

# --- Utilisateurs en mémoire ---
# Admins peuvent modifier PC et mots de passe
admins = {
    "Langevin": generate_password_hash("1234"),
    "Daniel": generate_password_hash("1234"),
    "Pier-Alexis": generate_password_hash("1234")
}

# Utilisateurs acheteurs (peuvent chatter)
users = {}

# Stockage des PC
pcs = []

# Stockage des messages de chat
chat_messages = {}  # clé = nom utilisateur, valeur = liste de dicts {"from": ..., "message": ..., "time": ...}


# --- PAGES PUBLIQUES ---
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Vérification admin
        if username in admins and check_password_hash(admins[username], password):
            session["user"] = username
            session["role"] = "admin"
            return redirect(url_for("dashboard"))

        # Vérification utilisateur
        elif username in users and check_password_hash(users[username], password):
            session["user"] = username
            session["role"] = "user"
            return redirect(url_for("chat", username=username))

        else:
            flash("Identifiants incorrects", "error")
            return render_template("login.html"), 401

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users or username in admins:
            flash("Nom d'utilisateur déjà pris", "error")
            return render_template("register.html")
        
        users[username] = generate_password_hash(password)
        chat_messages[username] = []
        flash("Compte créé avec succès !", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect(url_for("home"))


# --- DASHBOARD ADMIN ---
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    # Ajouter/modifier un PC
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_pc":
            pcs.append({
                "name": request.form.get("name"),
                "status": request.form.get("status")
            })
            flash("PC ajouté !", "success")
        elif action == "change_password":
            target_user = request.form.get("target_user")
            new_pass = request.form.get("new_password")
            if target_user in admins:
                admins[target_user] = generate_password_hash(new_pass)
                flash(f"Mot de passe de {target_user} changé !", "success")
            elif target_user in users:
                users[target_user] = generate_password_hash(new_pass)
                flash(f"Mot de passe de {target_user} changé !", "success")
            else:
                flash("Utilisateur non trouvé", "error")

    return render_template("dashboard.html", user=session["user"], pcs=pcs, admins=admins, users=users)


# --- CHAT UTILISATEUR ---
@app.route("/chat/<username>", methods=["GET", "POST"])
def chat(username):
    if "user" not in session or session["user"] != username or session.get("role") != "user":
        return redirect(url_for("login"))

    if request.method == "POST":
        message = request.form.get("message")
        chat_messages[username].append({
            "from": username,
            "message": message,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        flash("Message envoyé !", "success")

    messages = chat_messages.get(username, [])
    return render_template("chat.html", user=username, messages=messages)


# --- RUN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
