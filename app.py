from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "super_secret_key"  # à changer en clé sécurisée

# Page d'accueil
@app.route("/")
def home():
    return render_template("index.html")

# Page de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Vérification basique (à améliorer plus tard)
        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Identifiants incorrects")

    return render_template("login.html")

# Page protégée
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return f"<h1>Bienvenue {session['user']} !</h1><a href='/logout'>Se déconnecter</a>"
    return redirect(url_for("login"))

# Déconnexion
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
