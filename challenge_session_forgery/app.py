"""Uebungs-Ziel: Session-Forgery ueber schwachen Flask-SECRET_KEY.

Eine BEWUSST VERWUNDBARE Mini-App zum Testen des Cookie-Angriffs (Challenge
"Session-Faelschung"). Flask signiert den Session-Cookie nur (itsdangerous,
HMAC-SHA1) und verschluesselt ihn nicht. Hier ist der SECRET_KEY der bekannte
Lab-Default "cowboy" -> wer ihn kennt, baut sich einen gueltigen Cookie mit
beliebiger Identitaet und umgeht die Login-Pflicht.

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                             # http://127.0.0.1:5001

Angriff zu Fuss (der eigentliche Lerninhalt) -- Cookie ueberschreiben auf
"admin", ohne dessen Passwort zu kennen:

    python -c "from flask.sessions import SecureCookieSessionInterface as S; \
import flask; a=flask.Flask(__name__); a.secret_key='cowboy'; \
print(S().get_signing_serializer(a).dumps({'user':'admin'}))"

Den ausgegebenen Wert als Cookie `session=<wert>` setzen und /dashboard
aufrufen -> eingeloggt als admin. Dasselbe erkennt/baut der Scanner im
Nachbarordner attacking/:

    python ../attacking/attack_all.py --base http://127.0.0.1:5001 --forge-user admin

GRENZE: Nur gegen diese eigene Uebungs-Instanz. Reale Systeme sind tabu.
"""
import os

from flask import (Flask, flash, redirect, render_template_string, request,
                   session, url_for)

app = Flask(__name__)

# ----------------------------------------------------------------------
# DIE LUECKE: schwacher, bekannter SECRET_KEY. Fix = langer Zufallswert
# NUR aus der Umgebung, z. B. os.environ["SECRET_KEY"] (siehe 13_session_forgery).
# ----------------------------------------------------------------------
app.secret_key = "cowboy"

# Dummy-Konten. "admin"/"opferkonto" haben ABSICHTLICH ein unbekanntes,
# zufaelliges Passwort -- regulaer kommt man dort nicht rein, nur per Forgery.
USERS = {
    "team-test": "test123",
    "admin": os.urandom(16).hex(),
    "opferkonto": os.urandom(16).hex(),
}

BASE = """<!doctype html>
<title>Session-Forgery Lab</title>
<style>
 body{font-family:Georgia,serif;max-width:640px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 a.btn,button{background:#92400e;color:#fde68a;border:0;padding:.5rem .9rem;
      border-radius:6px;text-decoration:none;cursor:pointer}
 input{padding:.4rem;margin:.2rem 0;width:100%}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .flash{color:#7c2d12}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar. Nur lokal/autorisiert.</p>
<h1>&#9823; Session-Forgery Lab</h1>
{% with msgs = get_flashed_messages() %}{% for m in msgs %}
 <p class="flash">{{ m }}</p>{% endfor %}{% endwith %}
{{ body|safe }}
"""


def page(body):
    return render_template_string(BASE, body=body)


@app.route("/")
def index():
    who = session.get("user")
    status = (f"<p>Eingeloggt als <b>{who}</b> &middot; "
              f"<a href='/logout'>Logout</a></p>") if who else \
            "<p>Nicht eingeloggt.</p>"
    return page(f"""
      <div class="card">{status}</div>
      <p><a class="btn" href="/login">Login</a>
         <a class="btn" href="/dashboard">Dashboard (geschuetzt)</a></p>
      <div class="card">
        <p><b>Ziel der Uebung:</b> Erreiche das Dashboard als <code>admin</code>,
           ohne das Passwort von <code>admin</code> zu kennen.</p>
        <p>Der Session-Cookie ist nur <i>signiert</i>, nicht verschluesselt &mdash;
           und der Key ist schwach. Baue dir einen eigenen, gueltigen Cookie.</p>
      </div>""")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u in USERS and USERS[u] == p:
            session["user"] = u          # Identitaet landet im (nur signierten) Cookie
            flash(f"Willkommen zurueck, {u}!")
            return redirect(url_for("dashboard"))
        flash("Falscher Benutzername oder Passwort.")
    return page("""
      <h2>Login</h2>
      <form method="post">
        <label>Benutzername<input name="username"></label>
        <label>Passwort<input type="password" name="password"></label>
        <button type="submit">Einloggen</button>
      </form>
      <p style="font-size:.85rem">Test-Konto: <code>team-test</code> /
         <code>test123</code>. <code>admin</code> hat ein unbekanntes Passwort.</p>""")


@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:                                   # Login-Pflicht ist da ...
        flash("Bitte zuerst einloggen.")
        return redirect(url_for("login"))
    # ... aber die Identitaet kommt ungeprueft aus dem faelschbaren Cookie.
    admin_note = ("<p><b>&#127881; Angriff geglueckt:</b> Du bist als "
                  "<code>admin</code> drin, ohne das Passwort zu kennen.</p>"
                  if user == "admin" else "")
    return page(f"""
      <h2>Dashboard</h2>
      <div class="card">
        <p>Willkommen zurueck, <b>{user}</b>.</p>
        {admin_note}
      </div>
      <p><a href="/logout">Logout</a></p>""")


@app.route("/logout")
def logout():
    session.clear()
    flash("Abgemeldet.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5001"))
    print("[!] UEBUNGS-LAB mit schwachem SECRET_KEY 'cowboy' - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: Dashboard als 'admin')")
    app.run(host=host, port=port, debug=False)
