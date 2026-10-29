"""Uebungs-Ziel: Flask-Session-Abuse ohne SECRET_KEY -> Privilege Escalation.

BEWUSST VERWUNDBAR. Die Flask-Session (signierter Cookie) ist fuer sich nicht das
Problem -- der SECRET_KEY ist hier sogar zufaellig (os.urandom) und UNBEKANNT.
Die Luecke steckt in der Route /einstellungen: sie schreibt JEDES uebergebene
Formularfeld ungefiltert in die Session:

    for key, value in request.form.items():
        session[key] = value          # <-- Session-Puppetry

Damit kann man neben harmlosen Anzeige-Einstellungen auch das Feld 'rang'
setzen. Da /marshal nur auf session['rang'] == 'marshal' prueft, promotet man
sich selbst zum Marshal -- OHNE den SECRET_KEY zu kennen: der Server signiert die
manipulierte Session selbst.

(Anders als 13_session_forgery / challenge_session_forgery: dort knackt man einen
SCHWACHEN Key und faelscht den Cookie selbst. Hier ist der Key stark; der Fehler
ist, Nutzereingaben vertrauensvoll in die Session zu uebernehmen.)

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5007

Login als team-test/test123 -> Session mit rang=greenhorn. Ziel: /marshal
erreichen (rang=marshal), ohne einen Marshal-Zugang zu kennen.

GRENZE: Nur gegen diese eigene Uebungs-Instanz.
"""
import os

from flask import (Flask, redirect, render_template_string, request, session,
                   url_for)

app = Flask(__name__)
# Starker, UNBEKANNTER Key -- der Angriff braucht ihn bewusst NICHT.
app.secret_key = os.urandom(32)

USERS = {"team-test": "test123"}      # nur ein fiktives Konto; Marshal ist ein Rang
# "Geheimnis" hinter dem Admin-Gate (fiktive Fahndungsliste).
FAHNDUNG = [
    ("Black Bart", "Postkutschen-Raub", "$5000"),
    ("Calamity Sue", "Pferdediebstahl", "$1200"),
    ("Doc Sloane", "Falschspiel im Saloon", "$800"),
]

HEAD = """<!doctype html>
<title>Session-Lab (Cowboy-Forum)</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem} a.btn,button{background:#92400e;color:#fde68a;
      border:0;border-radius:6px;cursor:pointer;text-decoration:none;padding:.5rem .9rem}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .muted{color:#6b5b45;font-size:.85rem;word-break:break-all}
 table{width:100%;border-collapse:collapse} td,th{border:1px solid #d6c7a1;padding:.4rem;text-align:left}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (Session-Abuse). Nur lokal/autorisiert.</p>
<h1>&#129312; Saloon-Konto</h1>
"""


def render(body, **ctx):
    return render_template_string(HEAD + body, **ctx)


@app.route("/")
def index():
    if session.get("user"):
        body = """
          <div class="card">Eingeloggt als <b>{{ user }}</b>,
            Rang: <b>{{ rang }}</b>
            <p class="muted">Session-Inhalt: {{ sess }}</p></div>
          <p><a class="btn" href="/einstellungen">Einstellungen</a>
             <a class="btn" href="/marshal">Marshal-B&uuml;ro</a>
             <a class="btn" href="/logout">Logout</a></p>"""
        return render(body, user=session.get("user"),
                      rang=session.get("rang", "?"), sess=dict(session))
    return render('<div class="card">Nicht eingeloggt.</div>'
                  '<p><a class="btn" href="/login">Login</a></p>')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uu = request.form.get("username", "")
        pp = request.form.get("password", "")
        if USERS.get(uu) == pp:
            session.clear()
            session["user"] = uu
            session["rang"] = "greenhorn"   # jeder startet als Greenhorn
            return redirect(url_for("index"))
        return render('<div class="card">Falsche Zugangsdaten.</div>'
                      '<p><a class="btn" href="/login">zur&uuml;ck</a></p>')
    return render("""
      <h2>Login</h2>
      <form method="post">
        <p><input name="username" placeholder="Benutzer"></p>
        <p><input type="password" name="password" placeholder="Passwort"></p>
        <button type="submit">Einloggen</button>
      </form>
      <p class="muted">Test-Konto: team-test / test123 (Rang: greenhorn).</p>""")


@app.route("/einstellungen", methods=["GET", "POST"])
def einstellungen():
    if not session.get("user"):
        return redirect(url_for("login"))
    if request.method == "POST":
        # DIE LUECKE: jedes Formularfeld wandert ungefiltert in die Session.
        # Gedacht waren nur 'anzeigename' und 'revolver' -- aber hier landet auch
        # ein mitgeschicktes 'rang' (oder beliebige weitere Felder) in der Session.
        for key, value in request.form.items():
            session[key] = value
        return redirect(url_for("index"))
    return render("""
      <h2>Einstellungen</h2>
      <form method="post">
        <p>Anzeigename: <input name="anzeigename"
             value="{{ anzeigename }}"></p>
        <p>Lieblings-Revolver:
           <input name="revolver" value="{{ revolver }}"></p>
        <button type="submit">Speichern</button>
      </form>
      <p class="muted">Tipp: Was passiert, wenn das Formular noch ein
        weiteres Feld mitschickt, das gar nicht vorgesehen war?</p>""",
                  anzeigename=session.get("anzeigename", ""),
                  revolver=session.get("revolver", ""))


@app.route("/marshal")
def marshal():
    # Zugang NUR fuer den Rang 'marshal' -- der aus der Session gelesen wird.
    if session.get("rang") != "marshal":
        return render('<div class="card">Kein Zutritt. Nur f&uuml;r den '
                      'Rang <b>marshal</b> (du bist: <b>{{ rang }}</b>).</div>'
                      '<p><a class="btn" href="/">Start</a></p>',
                      rang=session.get("rang", "?")), 403
    rows = "".join(f"<tr><td>{n}</td><td>{d}</td><td>{p}</td></tr>"
                   for n, d, p in FAHNDUNG)
    return render('<div class="card"><h2>&#11088; Marshal-B&uuml;ro</h2>'
                  '<p>Angriff gegl&uuml;ckt: du bist als <b>{{ user }}</b> mit '
                  'Rang=marshal drin. Geheime Fahndungsliste:</p>'
                  '<table><tr><th>Name</th><th>Delikt</th><th>Kopfgeld</th></tr>'
                  + rows + "</table></div>", user=session.get("user", "?"))


@app.route("/einstellungen-safe", methods=["POST"])
def einstellungen_safe():
    """FIX-Demo: nur erlaubte Felder uebernehmen (Allowlist). 'rang' prallt ab."""
    if not session.get("user"):
        return redirect(url_for("login"))
    allowed = {"anzeigename", "revolver"}
    for key, value in request.form.items():
        if key in allowed:                 # Sicherheitsrelevante Felder nie aus Input
            session[key] = value
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5007"))
    print("[!] UEBUNGS-LAB: Flask-Session-Abuse (Session-Puppetry) - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: /marshal mit rang=marshal)")
    app.run(host=host, port=port, debug=False)
