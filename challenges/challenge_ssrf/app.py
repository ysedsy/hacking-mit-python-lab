"""Uebungs-Ziel: SSRF (Server-Side Request Forgery) -> interne Seite abrufen.

BEWUSST VERWUNDBAR. Der "Steckbrief-Importer" laedt ein Bild von einer vom
Nutzer angegebenen URL herunter -- ohne das Ziel zu pruefen. Damit bringt man
den SERVER dazu, beliebige URLs abzurufen, auch solche, die nur er erreicht:
das interne Marshal-Board unter http://127.0.0.1:<port>/intern, das von aussen
gesperrt ist (es glaubt, nur localhost duerfe ran).

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5011

Ziel: den Inhalt von /intern lesen, obwohl er fuer externe Clients 403 liefert.

GRENZE: Nur gegen diese eigene Uebungs-Instanz. Keine echten fremden URLs
abrufen -- der Importer ist hier auf http(s) + den eigenen Host beschraenkt.
"""
import os
import urllib.error
import urllib.request

from flask import Flask, render_template_string, request

app = Flask(__name__)
PORT = int(os.environ.get("PORT", "5011"))
GEHEIM = "MARSHAL-BOARD: Tresor-Code 7-3-9-1, naechste Razzia Freitag."

HEAD = """<!doctype html>
<title>Steckbrief-Importer (SSRF-Lab)</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem} a.btn,button{background:#92400e;color:#fde68a;
      border:0;border-radius:6px;cursor:pointer;text-decoration:none;padding:.5rem .9rem}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 pre{white-space:pre-wrap;word-break:break-all;background:#efe3c4;padding:.6rem;border-radius:6px}
 .muted{color:#6b5b45;font-size:.85rem}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (SSRF). Nur lokal/autorisiert.</p>
<h1>&#128444; Steckbrief-Importer</h1>
"""


def render(body, **ctx):
    return render_template_string(HEAD + body, **ctx)


def _ist_lokal():
    # Das interne Board "vertraut" Anfragen, die vom Server selbst kommen.
    return request.remote_addr in ("127.0.0.1", "::1", "localhost")


@app.route("/")
def index():
    return render("""
      <p>Importiere das Steckbrief-Foto eines Gesuchten per URL.</p>
      <form method="get" action="/import" class="card">
        <p><input name="url" size="48" placeholder="http://.../foto.jpg"></p>
        <button type="submit">Importieren</button>
      </form>
      <p class="muted">Hinweis: Das Marshal-Board unter <code>/intern</code> ist
      nur fuer den Server selbst sichtbar.</p>""")


@app.route("/import")
def importieren():
    url = request.args.get("url", "")
    # (Harmlose) Einschraenkung fuer das Lab: nur http/https.
    if not url.startswith(("http://", "https://")):
        return render("<div class='card'>Nur http(s)-URLs.</div>"), 400
    try:
        # DIE LUECKE: beliebige (auch interne) URL wird serverseitig abgerufen.
        with urllib.request.urlopen(url, timeout=3) as r:  # noqa: S310 (Lab)
            daten = r.read(4096)
    except (urllib.error.URLError, ValueError, OSError) as e:
        return render("<div class='card'>Import fehlgeschlagen: {{ e }}</div>",
                      e=str(e)), 502
    text = daten.decode("utf-8", "replace")
    geschafft = GEHEIM in text
    return render("""
      {% if hit %}<div class="card"><h2>&#129309; Angriff geglueckt</h2>
        <p>Der Server hat die interne Seite fuer dich abgerufen.</p></div>{% endif %}
      <div class="card">Antwort von <code>{{ url }}</code>:</div>
      <pre>{{ text }}</pre>
      <p><a class="btn" href="/">zurueck</a></p>""", url=url, text=text, hit=geschafft)


@app.route("/intern")
def intern():
    if not _ist_lokal():
        return render("<div class='card'>403 &ndash; Nur intern (localhost).</div>"), 403
    return GEHEIM


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    print("[!] UEBUNGS-LAB: SSRF - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{PORT}  (Ziel: /intern ueber den Server lesen)")
    app.run(host=host, port=PORT, debug=False, threaded=True)
