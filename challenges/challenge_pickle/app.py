"""Uebungs-Ziel: Insecure Deserialization (pickle) -> Code-Ausfuehrung.

BEWUSST VERWUNDBAR. Die App speichert die "Merkliste" des Nutzers als
pickle-Objekt in einem Cookie (base64-kodiert) und ruft beim naechsten Aufruf
pickle.loads() darauf auf. pickle fuehrt beim Entpacken __reduce__ aus --
ein praepariertes Cookie bringt den Server dazu, beliebige Befehle zu starten.

Statt echtem RCE schreibt der "Exploit" im Lab nur eine Markierungsdatei
(pwned.txt); die App zeigt dann "Angriff geglueckt". Kein Schaden, klarer Beweis.

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5012

Ziel: ueber das manipulierte Merklisten-Cookie Code auf dem Server ausfuehren.

GRENZE: Nur gegen diese eigene Uebungs-Instanz. Payload harmlos halten
(Markierungsdatei / whoami), kein echter Schaden.
"""
import base64
import os
import pickle

from flask import Flask, make_response, redirect, render_template_string, request, url_for

app = Flask(__name__)
MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pwned.txt")

HEAD = """<!doctype html>
<title>Merkliste (Pickle-Lab)</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem} a.btn,button{background:#92400e;color:#fde68a;
      border:0;border-radius:6px;cursor:pointer;text-decoration:none;padding:.5rem .9rem}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .muted{color:#6b5b45;font-size:.85rem;word-break:break-all}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (Insecure Deserialization). Nur lokal/autorisiert.</p>
<h1>&#128221; Meine Merkliste</h1>
"""


def render(body, **ctx):
    return render_template_string(HEAD + body, **ctx)


def lade_liste():
    roh = request.cookies.get("merkliste", "")
    if not roh:
        return []
    try:
        # DIE LUECKE: pickle.loads auf Daten aus dem Cookie (vom Client kontrolliert).
        return pickle.loads(base64.b64decode(roh))  # noqa: S301 (Lab)
    except Exception:
        return []


def speichere_liste(resp, liste):
    roh = base64.b64encode(pickle.dumps(liste)).decode()
    resp.set_cookie("merkliste", roh)


@app.route("/")
def index():
    liste = lade_liste()
    geschafft = os.path.exists(MARKER)
    resp = make_response(render("""
      {% if hit %}<div class="card"><h2>&#128165; Angriff geglueckt</h2>
        <p>Beim Entpacken des Cookies wurde Server-Code ausgefuehrt
        (Markierungsdatei <code>pwned.txt</code> angelegt).</p></div>{% endif %}
      <div class="card">Eintraege: <b>{{ liste or 'leer' }}</b></div>
      <form method="post" action="/add" class="card">
        <p><input name="eintrag" placeholder="Neuer Eintrag"></p>
        <button type="submit">Merken</button>
      </form>
      <p class="muted">Die Liste wird im Cookie <code>merkliste</code> gespeichert.</p>
      <p><a class="btn" href="/leeren">Liste &amp; Marker loeschen</a></p>""",
                                liste=liste, hit=geschafft))
    if not request.cookies.get("merkliste"):
        speichere_liste(resp, liste)
    return resp


@app.route("/add", methods=["POST"])
def add():
    liste = lade_liste()
    eintrag = request.form.get("eintrag", "").strip()
    if eintrag:
        liste.append(eintrag)
    resp = make_response(redirect(url_for("index")))
    speichere_liste(resp, liste)
    return resp


@app.route("/leeren")
def leeren():
    try:
        os.remove(MARKER)
    except OSError:
        pass
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("merkliste", "", expires=0)
    return resp


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5012"))
    print("[!] UEBUNGS-LAB: Insecure Deserialization (pickle) - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: Code via merkliste-Cookie)")
    app.run(host=host, port=port, debug=False)
