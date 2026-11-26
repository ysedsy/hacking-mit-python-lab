"""Challenge-Hub: ALLE Challenges unter EINEM Port + Launcher-Seite.

Dieser Ordner enthaelt KEINE eigene verwundbare Logik. Der Hub laedt die
unveraenderten challenge_*/app.py-Apps und mountet jede unter einem eigenen
Pfad-Prefix (z.B. /mass_assignment) auf demselben Port. Die Startseite ist ein
Launcher, von dem aus man jede Challenge mit einem Klick oeffnet.

    cd challenges/hub
    pip install -r requirements.txt
    python hub.py                 # http://127.0.0.1:5000

Damit die Mini-Apps unter einem Prefix laufen, ohne dass man sie anpassen muss,
schreibt eine schmale WSGI-Middleware (MountFix) die Antworten um:
  * feste Links im HTML (href/src/action="/x")  -> "/<prefix>/x"
  * Location-Header bei Redirects (falls noch ohne Prefix)
  * den Path von gesetzten Cookies  -> "/<prefix>"  (keine Cookie-Kollision)
Bereits korrekte, via url_for erzeugte Links (die den Prefix schon enthalten)
bleiben unangetastet.

GRENZE: Wie die einzelnen Challenges nur gegen die eigene/autorisierte Instanz.
Der Hub buendelt bewusst verwundbare Uebungs-Apps -- nur lokal/im Kurs-Netz,
nie oeffentlich erreichbar machen.
"""
import importlib.util
import os
import re
import sys

from flask import Flask, Response, render_template_string
from werkzeug.middleware.dispatcher import DispatcherMiddleware

HUB_DIR = os.path.dirname(os.path.abspath(__file__))
CH_DIR = os.path.dirname(HUB_DIR)               # .../challenges
sys.path.insert(0, CH_DIR)
import build_index as bi                          # CHALLENGES, extract_formulation, ...


# --------------------------------------------------------------------------- #
# Challenge-Apps laden
# --------------------------------------------------------------------------- #
def _prefix_for(path):
    return "/" + os.path.basename(path).replace("challenge_", "")


def _load_app(path):
    """Importiert challenge_x/app.py und gibt dessen Flask-Objekt zurueck."""
    app_py = os.path.join(CH_DIR, path, "app.py")
    modname = "challenge_" + os.path.basename(path).replace("challenge_", "")
    spec = importlib.util.spec_from_file_location(modname, app_py)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod.app


# --------------------------------------------------------------------------- #
# WSGI-Middleware: Antworten einer gemounteten App auf den Prefix umbiegen
# --------------------------------------------------------------------------- #
_LINK_RE = re.compile(r"""(href|src|action|formaction)=(["'])(/(?!/)[^"']*)""", re.I)


def _rewrite_html(text, prefix):
    def repl(m):
        attr, quote, url = m.group(1), m.group(2), m.group(3)
        if url == prefix or url.startswith(prefix + "/"):
            return m.group(0)          # schon korrekt (z.B. via url_for)
        return f"{attr}={quote}{prefix}{url}"
    return _LINK_RE.sub(repl, text)


def _fix_cookie_path(value, prefix):
    if re.search(r"(?i);\s*path=", value):
        return re.sub(r"(?i);\s*path=[^;]*", f"; Path={prefix}", value)
    return value + f"; Path={prefix}"


class MountFix:
    """Macht eine unter <prefix> gemountete App ohne Quellaenderung navigierbar."""

    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        captured = {}
        chunks = []

        def _start(status, headers, exc_info=None):
            captured["status"] = status
            captured["headers"] = headers
            captured["exc"] = exc_info
            return chunks.append

        app_iter = self.app(environ, _start)
        try:
            body = b"".join(app_iter) + b"".join(chunks)
        finally:
            if hasattr(app_iter, "close"):
                app_iter.close()

        ctype, out_headers = "", []
        for key, val in captured["headers"]:
            low = key.lower()
            if low == "location" and val.startswith("/") and not val.startswith("//") \
                    and val != self.prefix and not val.startswith(self.prefix + "/"):
                val = self.prefix + val
            elif low == "set-cookie":
                val = _fix_cookie_path(val, self.prefix)
            elif low == "content-type":
                ctype = val
            elif low == "content-length":
                continue                # wird neu berechnet
            out_headers.append((key, val))

        if "text/html" in ctype.lower():
            body = _rewrite_html(body.decode("utf-8", "replace"), self.prefix).encode("utf-8")

        out_headers.append(("Content-Length", str(len(body))))
        start_response(captured["status"], out_headers, captured["exc"])
        return [body]


# --------------------------------------------------------------------------- #
# Launcher-Startseite
# --------------------------------------------------------------------------- #
def _style():
    """CSS aus der generierten index.html ziehen (einheitliches Aussehen)."""
    idx = os.path.join(CH_DIR, "index.html")
    try:
        html = open(idx, encoding="utf-8").read()
        m = re.search(r"<style>(.*?)</style>", html, re.S)
        if m:
            return m.group(1)
    except OSError:
        pass
    return "body{font-family:Georgia,serif;max-width:900px;margin:2rem auto;padding:0 1rem}"


ENTRIES = []       # (prefix, vuln, owasp, port, niveau, anchor, formulation)
MOUNTS = {}

for _path, _vuln, _owasp, _port, _niveau in bi.CHALLENGES:
    _prefix = _prefix_for(_path)
    MOUNTS[_prefix] = MountFix(_load_app(_path), _prefix)
    _md = os.path.join(CH_DIR, _path, "challenge.md")
    ENTRIES.append((_prefix, _vuln, _owasp, _port, _niveau,
                    os.path.basename(_path), bi.extract_formulation(_md)))

root = Flask(__name__)

LAUNCHER = """<!doctype html>
<html lang="de"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Challenge-Hub &ndash; Hacking mit Python</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rye&family=Special+Elite&display=swap" rel="stylesheet">
<style>{{ style }}
 .launch{display:inline-block;margin:.2rem 0 .4rem;background:var(--leather);color:#fde68a;
   padding:.5rem .9rem;border-radius:8px;font-family:"Rye",serif;text-decoration:none;}
 .launch:hover{background:var(--leather-d);text-decoration:none;}
 details.task{margin:.4rem 0 .2rem;}
 details.task>summary{cursor:pointer;color:var(--accent);font-size:.9rem;}
 .hubnav{font-size:.9rem;margin:.6rem 0 0;}
</style></head>
<body>
<a id="top"></a>
<div class="wrap">
  <header class="hero">
    <h1>&#129312; Challenge-Hub</h1>
    <p class="sub">Alle {{ n }} Challenges auf einem Port &ndash; ein Klick, eine Seite</p>
    <p class="hubnav"><a href="/uebersicht">&#128220; Nur-Lese-&Uuml;bersicht (alle Aufgaben ohne L&ouml;sungen)</a></p>
  </header>
  <div class="warn">
    <b>Grenze:</b> B&uuml;ndel bewusst verwundbarer &Uuml;bungs-Apps. Nur lokal / im Kurs-Netz,
    nie &ouml;ffentlich erreichbar machen. Payloads harmlos halten, kein DoS.
  </div>
  <table class="overview">
    <thead><tr><th>#</th><th>Challenge</th><th>OWASP</th><th>Niveau</th><th>&Ouml;ffnen</th></tr></thead>
    <tbody>
    {% for pfx, vuln, owasp, port, niveau, anchor, _ in entries %}
      <tr><td class="num">{{ "%02d"|format(loop.index) }}</td>
        <td><a href="#{{ anchor }}">{{ vuln }}</a></td>
        <td>{{ owasp }}</td><td>{{ niveau }}</td>
        <td><a href="{{ pfx }}/">&#9654; starten</a></td></tr>
    {% endfor %}
    </tbody>
  </table>
  {% for pfx, vuln, owasp, port, niveau, anchor, formulation in entries %}
  <article class="card" id="{{ anchor }}">
    <div class="meta">
      <span class="badge num">#{{ "%02d"|format(loop.index) }}</span>
      <span class="badge owasp">{{ owasp }}</span>
      <span class="badge niv">{{ niveau }}</span>
    </div>
    <h2>{{ vuln }}</h2>
    <a class="launch" href="{{ pfx }}/">&#9654; Challenge starten</a>
    <details class="task"><summary>Aufgabe anzeigen (ohne L&ouml;sung)</summary>
      <div class="body">{{ formulation|safe }}</div>
    </details>
    <p class="top"><a href="#top">&uarr; nach oben</a></p>
  </article>
  {% endfor %}
  <footer>Challenge-Hub &middot; l&auml;dt die unver&auml;nderten <code>challenge_*/app.py</code>
    unter je einem Prefix &middot; Hacking mit Python &middot; Cowboy-Forum-Lab</footer>
</div></body></html>"""


@root.route("/")
def launcher():
    return render_template_string(LAUNCHER, style=_style(), entries=ENTRIES, n=len(ENTRIES))


@root.route("/uebersicht")
def uebersicht():
    idx = os.path.join(CH_DIR, "index.html")
    try:
        return Response(open(idx, encoding="utf-8").read(), mimetype="text/html")
    except OSError:
        return Response("index.html fehlt -- bitte 'python build_index.py' ausfuehren.",
                        status=404, mimetype="text/plain")


# Alles zusammenstecken: Launcher als Default, Challenges unter ihren Prefixes.
application = DispatcherMiddleware(root.wsgi_app, MOUNTS)


def _ascii(text):
    # Windows-Konsole = cp1252: Nicht-ASCII (z.B. "->") wuerde print() crashen.
    return text.encode("ascii", "replace").decode("ascii")


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    print("[!] UEBUNGS-LAB-HUB: buendelt verwundbare Apps - nur lokal/autorisiert.")
    print(f"[i] Launcher auf http://{host}:{port}  ({len(ENTRIES)} Challenges, ein Port)")
    for pfx, vuln, *_ in ENTRIES:
        print(_ascii(f"    {pfx:<22} {vuln}"))
    run_simple(host, port, application, threaded=True)
