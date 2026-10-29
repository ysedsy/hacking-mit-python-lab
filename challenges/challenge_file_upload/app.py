"""Uebungs-Ziel: Unrestricted File Upload -> Code im App-Origin.

BEWUSST VERWUNDBAR. Der Upload prueft weder Dateityp noch Inhalt und liefert
hochgeladene Dateien unter /uploads/<name> mit dem zur Endung passenden
Content-Type aus. Laedt man eine .html/.svg mit <script> hoch, laeuft der Code
im URSPRUNG der App -> Session-/Cookie-Diebstahl, Phishing, Defacement.

(Auf Servern, die Uploads AUSFUEHREN -- PHP/CGI/.py -- waere derselbe Fehler
volle Remote-Code-Execution. Hier ist die Wirkung Code im Browser des Opfers
im App-Origin.)

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5006

Ziel: eine Datei hochladen, die beim Oeffnen JavaScript im App-Origin ausfuehrt.

GRENZE: Nur gegen diese eigene Uebungs-Instanz.
"""
import os

from flask import (Flask, redirect, render_template_string, request,
                   send_from_directory, url_for)

app = Flask(__name__)
UPLOAD_DIR = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

HEAD = """<!doctype html>
<title>Datei-Upload (Upload-Lab)</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem} a.btn,button{background:#92400e;color:#fde68a;
      border:0;border-radius:6px;cursor:pointer;text-decoration:none;padding:.5rem .9rem}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .muted{color:#6b5b45;font-size:.85rem}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (File Upload). Nur lokal/autorisiert.</p>
<h1>&#128206; Datei-Upload</h1>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    msg = ""
    if request.method == "POST":
        f = request.files.get("datei")
        if f and f.filename:
            # DIE LUECKE: keinerlei Typ-/Inhaltspruefung.
            name = os.path.basename(f.filename)   # nur Write-Pfad absichern
            f.save(os.path.join(UPLOAD_DIR, name))
            msg = (f"<div class='card'>Hochgeladen: "
                   f"<a href='/uploads/{name}'>/uploads/{name}</a></div>")
    files = sorted(os.listdir(UPLOAD_DIR))
    rows = "".join(f"<li><a href='/uploads/{n}'>{n}</a></li>" for n in files) \
        or "<li class='muted'>noch nichts hochgeladen</li>"
    body = f"""
      {msg}
      <form method="post" enctype="multipart/form-data">
        <p><input type="file" name="datei"></p>
        <button type="submit">Hochladen</button>
      </form>
      <div class="card"><h2>Hochgeladene Dateien</h2><ul>{rows}</ul></div>
      <p class="muted">Tipp: Was passiert, wenn die Datei auf .html endet und
        &lt;script&gt; enthaelt?</p>"""
    return render_template_string(HEAD + body)


@app.route("/uploads/<path:name>")
def uploaded(name):
    # Liefert mit per Endung erratenem Content-Type (z. B. .html -> text/html),
    # im selben Origin wie die App -> Script laeuft im App-Kontext.
    return send_from_directory(UPLOAD_DIR, name)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5006"))
    print("[!] UEBUNGS-LAB: Unrestricted File Upload - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: .html mit <script> hochladen)")
    app.run(host=host, port=port, debug=False)
