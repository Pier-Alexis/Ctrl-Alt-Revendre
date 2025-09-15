from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_secret_key_to_something_random_and_long"

# --- Comptes utilisateurs ---
users = {
    "Langevin": generate_password_hash("L@ngev1n208"),
    "Daniel": generate_password_hash("1234"),
    "Pier-Alexis": generate_password_hash("1234")
}

# --- Liste des PC ---
pcs = [
    {"name": "PC-01", "status": "Disponible"},
    {"name": "PC-02", "status": "En réparation"}
]

# --- Chat messages ---
chat_messages = []

# --- Page d'accueil ---
@app.route("/")
def home():
    return render_template("index.html")

# --- Inscription (register) ---
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users:
            flash("Nom d'utilisateur déjà utilisé", "error")
        else:
            users[username] = generate_password_hash(password)
            flash("Compte créé avec succès, connectez-vous", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

# --- Connexion (login) ---
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and check_password_hash(users[username], password):
            session["user"] = username
            flash(f"Bienvenue {username} !", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Identifiants incorrects", "error")
            return render_template("login.html"), 401
    return render_template("login.html")

# --- Déconnexion ---
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Déconnecté avec succès", "success")
    return redirect(url_for("home"))

# --- Dashboard Admin ---
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if request.method=="POST":
        name = request.form.get("pc_name")
        status = request.form.get("pc_status")
        if name and status:
            pcs.append({"name": name, "status": status})
            flash(f"PC {name} ajouté", "success")

    return render_template("dashboard.html", user=session["user"], pcs=pcs)

# --- Changement mot de passe ---
@app.route("/change_password", methods=["GET","POST"])
def change_password():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method=="POST":
        old = request.form.get("old_password")
        new = request.form.get("new_password")
        if check_password_hash(users[session["user"]], old):
            users[session["user"]] = generate_password_hash(new)
            flash("Mot de passe changé avec succès", "success")
        else:
            flash("Ancien mot de passe incorrect", "error")
    return render_template("change_password.html")

# --- Chat ---
@app.route("/chat", methods=["GET","POST"])
def chat():
    if "user" not in session:
        flash("Vous devez être connecté pour chatter", "error")
        return redirect(url_for("login"))

    if request.method=="POST":
        message = request.form.get("message")
        if message:
            chat_messages.append({"user": session["user"], "msg": message})
    
    return render_template("chat.html", messages=chat_messages, user=session["user"])

if __name__=="__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
