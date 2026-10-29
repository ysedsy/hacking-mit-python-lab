"""Uebungs-Ziel: JWT-Faelschung (alg:none & schwaches HMAC-Secret).

BEWUSST VERWUNDBAR. Das Token (Cookie 'token') ist ein JWT. Die Pruefung hat
ZWEI klassische Fehler:
  1. Sie akzeptiert den Algorithmus "none" (ganz ohne Signatur).
  2. Das HMAC-Secret ist schwach/bekannt ("secret").
Beides erlaubt, sich selbst ein Token mit role=admin auszustellen.

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5004

Login als team-test/test123 -> Token (role=user). Ziel: /admin erreichen
(role=admin), ohne Admin-Zugang zu kennen.

GRENZE: Nur gegen diese eigene Uebungs-Instanz.
"""
import base64
import hashlib
import hmac
import json
import os

from flask import (Flask, make_response, redirect, render_template_string,
                   request, url_for)

app = Flask(__name__)

# DIE LUECKE (2): schwaches, bekanntes Secret.
JWT_SECRET = b"secret"
USERS = {"team-test": "test123"}      # nur ein fiktives Konto; admin gibt es als Rolle


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_dec(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def jwt_encode(payload, secret=JWT_SECRET, alg="HS256"):
    header = {"alg": alg, "typ": "JWT"}
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{h}.{p}".encode()
    if alg == "none":
        return f"{h}.{p}."
    sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url(sig)}"


def jwt_decode(token):
    h, p, sig = token.split(".")
    header = json.loads(_b64url_dec(h))
    payload = json.loads(_b64url_dec(p))
    alg = header.get("alg", "")
    # DIE LUECKE (1): "none" wird akzeptiert -> keine Signaturpruefung.
    if alg == "none":
        return payload
    expected = _b64url(hmac.new(JWT_SECRET, f"{h}.{p}".encode(),
                                hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig):
        raise ValueError("ungueltige Signatur")
    return payload


def current():
    tok = request.cookies.get("token")
    if not tok:
        return None
    try:
        return jwt_decode(tok)
    except Exception:
        return None


HEAD = """<!doctype html>
<title>JWT-Lab</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem} a.btn,button{background:#92400e;color:#fde68a;
      border:0;border-radius:6px;cursor:pointer;text-decoration:none;padding:.5rem .9rem}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .muted{color:#6b5b45;font-size:.85rem;word-break:break-all}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (JWT). Nur lokal/autorisiert.</p>
"""


def render(body, **ctx):
    return render_template_string(HEAD + body, **ctx)


@app.route("/")
def index():
    u = current()
    tok = request.cookies.get("token", "")
    who = (f"<div class='card'>Eingeloggt als <b>{{{{ user }}}}</b> "
           f"(role=<b>{{{{ role }}}}</b>)<p class='muted'>token: {{{{ tok }}}}</p></div>"
           if u else "<div class='card'>Nicht eingeloggt.</div>")
    body = (who + "<p><a class='btn' href='/login'>Login</a> "
            "<a class='btn' href='/admin'>Admin-Bereich</a></p>")
    return render(body, user=(u or {}).get("user", ""),
                  role=(u or {}).get("role", ""), tok=tok)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uu = request.form.get("username", "")
        pp = request.form.get("password", "")
        if USERS.get(uu) == pp:
            token = jwt_encode({"user": uu, "role": "user"})
            resp = make_response(redirect(url_for("index")))
            resp.set_cookie("token", token, httponly=False)
            return resp
        return render("<div class='card'>Falsche Zugangsdaten.</div>"
                      "<p><a class='btn' href='/login'>zurueck</a></p>")
    return render("""
      <h2>Login</h2>
      <form method="post">
        <p><input name="username" placeholder="Benutzer"></p>
        <p><input type="password" name="password" placeholder="Passwort"></p>
        <button type="submit">Einloggen</button>
      </form>
      <p class="muted">Test-Konto: team-test / test123 (role=user).</p>""")


@app.route("/admin")
def admin():
    u = current()
    if not u or u.get("role") != "admin":
        return render("<div class='card'>Kein Zugang. Nur fuer role=admin.</div>"
                      "<p><a class='btn' href='/'>Start</a></p>"), 403
    return render("<div class='card'><h2>&#128081; Admin-Bereich</h2>"
                  "<p>Angriff geglueckt: du bist als <b>{{ user }}</b> mit "
                  "role=admin drin.</p></div>", user=u.get("user", "?"))


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5004"))
    print("[!] UEBUNGS-LAB: JWT-Faelschung - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: /admin mit role=admin)")
    app.run(host=host, port=port, debug=False)
