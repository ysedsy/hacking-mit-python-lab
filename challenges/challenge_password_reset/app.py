"""Uebungs-Ziel: Schwaches Passwort-Reset-Token -> fremdes Konto uebernehmen.

BEWUSST VERWUNDBAR. Der "Passwort vergessen"-Flow erzeugt einen Reset-Link mit
einem vorhersagbaren Token: den aktuellen Sekunden-Zeitstempel (int(time.time())).
Wer ungefaehr weiss, WANN das Reset ausgeloest wurde, raet den Token in wenigen
Versuchen -- und setzt das Passwort eines fremden Kontos neu.

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5010

Ziel: das Passwort des Kontos 'marshal' zuruecksetzen und einloggen.

GRENZE: Nur gegen diese eigene Uebungs-Instanz.
"""
import os
import time

from flask import (Flask, redirect, render_template_string, request, session,
                   url_for)

app = Flask(__name__)
app.secret_key = os.urandom(32)

USERS = {"marshal": "unbekannt-stark", "team-test": "test123"}
RESETS = {}      # token (str) -> username

HEAD = """<!doctype html>
<title>Konto (Reset-Lab)</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem} a.btn,button{background:#92400e;color:#fde68a;
      border:0;border-radius:6px;cursor:pointer;text-decoration:none;padding:.5rem .9rem}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .muted{color:#6b5b45;font-size:.85rem;word-break:break-all}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (schwaches Reset-Token). Nur lokal/autorisiert.</p>
<h1>&#128273; Konto-Verwaltung</h1>
"""


def render(body, **ctx):
    return render_template_string(HEAD + body, **ctx)


@app.route("/", methods=["GET", "POST"])
def login():
    msg = None
    if request.method == "POST":
        u = request.form.get("username", "")
        if USERS.get(u) == request.form.get("password", ""):
            session["user"] = u
            return redirect(url_for("konto"))
        msg = "Login fehlgeschlagen."
    return render("""
      <form method="post" class="card">
        <p><input name="username" placeholder="Benutzername"></p>
        <p><input type="password" name="password" placeholder="Passwort"></p>
        <button type="submit">Einloggen</button>
      </form>
      <p><a class="btn" href="/vergessen">Passwort vergessen?</a></p>
      {% if msg %}<div class="card"><b>{{ msg }}</b></div>{% endif %}
      <p class="muted">Testzugang: team-test / test123</p>""", msg=msg)


@app.route("/vergessen", methods=["GET", "POST"])
def vergessen():
    if request.method == "POST":
        u = request.form.get("username", "")
        if u in USERS:
            # DIE LUECKE: vorhersagbares Token = aktueller Sekunden-Zeitstempel.
            token = str(int(time.time()))
            RESETS[token] = u
            # Im Ernstfall ginge der Link per Mail raus; hier nur die Tatsache.
            return render("<div class='card'>Ein Reset-Link wurde an die "
                          "hinterlegte Adresse von <b>{{ u }}</b> gesendet.</div>"
                          "<p class='muted'>(Lab: der Link ist "
                          "<code>/reset?token=&lt;...&gt;</code>)</p>", u=u)
        return render("<div class='card'>Falls das Konto existiert, wurde ein "
                      "Link gesendet.</div>")
    return render("""
      <form method="post" class="card">
        <p><input name="username" placeholder="Benutzername"></p>
        <button type="submit">Reset anfordern</button>
      </form>""")


@app.route("/reset", methods=["GET", "POST"])
def reset():
    token = request.values.get("token", "")
    user = RESETS.get(token)
    if not user:
        return render("<div class='card'>Ungueltiges oder abgelaufenes "
                      "Token.</div>"), 404
    if request.method == "POST":
        USERS[user] = request.form.get("password", "")
        del RESETS[token]
        return render("<div class='card'><h2>&#9989; Angriff geglueckt</h2>"
                      "<p>Passwort von <b>{{ u }}</b> neu gesetzt. Jetzt einloggen.</p></div>"
                      "<p><a class='btn' href='/'>Zum Login</a></p>", u=user)
    return render("""
      <div class="card">Neues Passwort fuer <b>{{ u }}</b> setzen:</div>
      <form method="post" class="card">
        <input type="hidden" name="token" value="{{ t }}">
        <p><input name="password" placeholder="Neues Passwort"></p>
        <button type="submit">Passwort setzen</button>
      </form>""", u=user, t=token)


@app.route("/konto")
def konto():
    if "user" not in session:
        return redirect(url_for("login"))
    return render("<div class='card'>Eingeloggt als <b>{{ u }}</b>.</div>"
                  "<p><a href='/logout'>Logout</a></p>", u=session["user"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5010"))
    print("[!] UEBUNGS-LAB: schwaches Reset-Token - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: Konto 'marshal' kapern)")
    app.run(host=host, port=port, debug=False)
