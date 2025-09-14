from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_secret_key_to_something_random_and_long"  # CHANGE THIS en production

# --- Compte unique (en mémoire) ---
USER_NAME = "Langevin"
USER_PASSWORD_HASH = generate_password_hash("L@ngev1n208")

# Page d'accueil
@app.route("/")
def home():
    return render_template("index.html")

# Page de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == USER_NAME and check_password_hash(USER_PASSWORD_HASH, password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Identifiants incorrects", "error")
            return render_template("login.html"), 401

    return render_template("login.html")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", user=session["user"])
    return redirect(url_for("login"))

# Déconnexion
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
