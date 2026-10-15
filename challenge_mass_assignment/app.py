"""Uebungs-Ziel: Mass Assignment -> Rechte-Eskalation.

BEWUSST VERWUNDBAR. Die Registrierung uebernimmt ALLE gesendeten Formularfelder
ungefiltert ins Benutzerobjekt (user.update(request.form)). Das Formular zeigt
nur Benutzername/Passwort -- schmuggelt man ein zusaetzliches Feld is_admin=1
mit, wird man sofort Administrator.

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5005

Ziel: /admin erreichen, ohne dass das Formular einen "Admin"-Haken anbietet.

GRENZE: Nur gegen diese eigene Uebungs-Instanz.
"""
import os

from flask import (Flask, make_response, redirect, render_template_string,
                   request, url_for)

app = Flask(__name__)
USERS = {}      # username -> dict(username, password, is_admin)

HEAD = """<!doctype html>
<title>Registrierung (Mass-Assignment-Lab)</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem} a.btn,button{background:#92400e;color:#fde68a;
      border:0;border-radius:6px;cursor:pointer;text-decoration:none;padding:.5rem .9rem}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .muted{color:#6b5b45;font-size:.85rem}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (Mass Assignment). Nur lokal/autorisiert.</p>
"""


def render(body, **ctx):
    return render_template_string(HEAD + body, **ctx)


def _truthy(v):
    return str(v).lower() in ("1", "true", "on", "yes", "admin")


@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        if not uname:
            return render("<div class='card'>Benutzername fehlt.</div>")
        if uname in USERS:
            return render("<div class='card'>Name vergeben.</div>")
        # Grundgeruest ...
        user = {"username": uname, "password": request.form.get("password", ""),
                "is_admin": False}
        # ... DIE LUECKE: ALLE Formularfelder ungefiltert uebernehmen.
        user.update(request.form.to_dict())
        # is_admin kam evtl. als String "1" rein -> als Flag interpretieren.
        user["is_admin"] = _truthy(user.get("is_admin", False))
        USERS[uname] = user
        resp = make_response(redirect(url_for("profile")))
        resp.set_cookie("username", uname, httponly=False)
        return resp
    return render("""
      <h2>Registrieren</h2>
      <form method="post">
        <p><input name="username" placeholder="Benutzername"></p>
        <p><input type="password" name="password" placeholder="Passwort"></p>
        <button type="submit">Konto anlegen</button>
      </form>
      <p class="muted">Normale Nutzer sind keine Admins. Oder etwa doch?</p>""")


@app.route("/profile")
def profile():
    u = USERS.get(request.cookies.get("username", ""))
    if not u:
        return redirect(url_for("register"))
    return render("<div class='card'>Hallo, <b>{{ u.username }}</b>. "
                  "is_admin=<b>{{ u.is_admin }}</b></div>"
                  "<p><a class='btn' href='/admin'>Admin-Bereich</a></p>", u=u)


@app.route("/admin")
def admin():
    u = USERS.get(request.cookies.get("username", ""))
    if not u or not u.get("is_admin"):
        return render("<div class='card'>Kein Zugang (nur Admins).</div>"
                      "<p><a class='btn' href='/profile'>zurueck</a></p>"), 403
    return render("<div class='card'><h2>&#128081; Admin-Bereich</h2>"
                  "<p>Angriff geglueckt: <b>{{ u.username }}</b> ist Administrator.</p>"
                  "</div>", u=u)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5005"))
    print("[!] UEBUNGS-LAB: Mass Assignment - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: Admin via is_admin=1)")
    app.run(host=host, port=port, debug=False)
