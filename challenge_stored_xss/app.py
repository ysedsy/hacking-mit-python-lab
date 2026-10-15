"""Uebungs-Ziel: Stored XSS im Ticket-Beschreibungsfeld.

BEWUSST VERWUNDBAR. Die Ticket-Beschreibung wird beim Anzeigen UNGEESCAPED
gerendert (Jinja-Filter |safe) -- sowohl in der Detailansicht (<p>) als auch
roh zurueck ins Edit-Textarea. Wer ein Ticket mit HTML/JS-Payload anlegt,
fuehrt damit Code im Browser aller aus, die das Ticket spaeter oeffnen
(Stored / Persistent XSS).

Zusaetzlich steht die Identitaet in einem KLARTEXT-Cookie 'username' OHNE
HttpOnly -> per document.cookie stehlbar (so wie im Kurs-Ticketsystem).

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5002

Loesung zu Fuss: in die Beschreibung z. B.
    <img src=x onerror=alert('XSS')>
eintragen, speichern, Ticket oeffnen -> Alert feuert. Impact zeigen mit
    <img src=x onerror=alert(document.cookie)>
(zeigt den Klartext-Cookie -> Session stehlbar).

GRENZE: Nur gegen diese eigene Uebungs-Instanz.
"""
import os

from flask import (Flask, make_response, redirect, render_template_string,
                   request, url_for)

app = Flask(__name__)

# In-Memory-Speicher; beim Neustart leer. Ein Seed-Ticket zum Ausprobieren.
TICKETS = [
    {"id": 1, "titel": "Sattel klemmt", "prioritaet": "mittel",
     "beschreibung": "Der Steigbuegel laesst sich nicht verstellen."},
]
_next_id = [2]

PRIOS = ["niedrig", "mittel", "hoch"]

BASE = """<!doctype html>
<title>Ticketsystem (XSS-Lab)</title>
<style>
 body{font-family:Georgia,serif;max-width:720px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 a.btn,button{background:#92400e;color:#fde68a;border:0;padding:.5rem .9rem;
      border-radius:6px;text-decoration:none;cursor:pointer}
 input,textarea,select{padding:.4rem;margin:.2rem 0;width:100%;box-sizing:border-box}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .section-heading{margin:.2rem 0}
 .ticket-description{white-space:pre-wrap}
 .muted{color:#6b5b45;font-size:.85rem}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (Stored XSS). Nur lokal/autorisiert.</p>
<p class="muted">Angemeldet als <b>{{ username or "Gast" }}</b> &middot;
  <a href="{{ url_for('login') }}">Benutzer wechseln</a></p>
<h1>&#127903; Ticketsystem</h1>
{{ body|safe }}
"""


def page(body, **ctx):
    username = request.cookies.get("username")
    # Body zuerst rendern (loest {{ beschreibung|safe }} aus Kontext-Variablen),
    # dann in die Seiten-Huelle einsetzen. Nutzerdaten kommen als ctx-Werte -
    # nicht als Template-Text -> kein SSTI, aber |safe deaktiviert das Escaping.
    rendered = render_template_string(body, username=username, **ctx)
    return render_template_string(BASE, body=rendered, username=username)


def _find(tid):
    return next((t for t in TICKETS if t["id"] == tid), None)


@app.route("/")
def index():
    rows = "".join(
        f'<li><a href="{url_for("ticket", tid=t["id"])}">#{t["id"]} {t["titel"]}'
        f'</a> <span class="muted">({t["prioritaet"]})</span></li>'
        for t in TICKETS) or "<li class='muted'>noch keine Tickets</li>"
    return page(f"""
      <p><a class="btn" href="{url_for('new')}">Neues Ticket</a></p>
      <div class="card"><h2 class="section-heading">Tickets</h2><ul>{rows}</ul></div>""")


@app.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        t = {"id": _next_id[0],
             "titel": request.form.get("titel", "").strip() or "(ohne Titel)",
             "beschreibung": request.form.get("beschreibung", ""),
             "prioritaet": request.form.get("prioritaet", "mittel")}
        _next_id[0] += 1
        TICKETS.append(t)
        return redirect(url_for("ticket", tid=t["id"]))
    opts = "".join(f'<option>{p}</option>' for p in PRIOS)
    return page(f"""
      <h2 class="section-heading">Neues Ticket</h2>
      <form method="post">
        <label for="titel">Titel</label>
        <input id="titel" name="titel">
        <label for="description">Beschreibung</label>
        <textarea id="description" name="beschreibung" rows="6"></textarea>
        <label for="priority">Prioritaet</label>
        <select id="priority" name="prioritaet">{opts}</select>
        <p><button type="submit">Speichern</button></p>
      </form>""")


@app.route("/ticket/<int:tid>")
def ticket(tid):
    t = _find(tid)
    if not t:
        return page("<p>Ticket nicht gefunden.</p>"), 404
    # DIE LUECKE: Beschreibung wird ungeescaped ausgegeben (|safe).
    return page(f"""
      <p><a href="{url_for('index')}">&larr; Uebersicht</a>
         &middot; <a href="{url_for('edit', tid=t['id'])}">Bearbeiten</a></p>
      <div class="card">
        <h1 class="section-heading">#{t['id']} {{{{ titel }}}}</h1>
        <p class="muted">Prioritaet: {{{{ prio }}}}</p>
        <h2 class="section-heading">Beschreibung</h2>
        <p class="ticket-description">{{{{ beschreibung|safe }}}}</p>
      </div>""", titel=t["titel"], prio=t["prioritaet"],
                beschreibung=t["beschreibung"])


@app.route("/ticket/<int:tid>/edit", methods=["GET", "POST"])
def edit(tid):
    t = _find(tid)
    if not t:
        return page("<p>Ticket nicht gefunden.</p>"), 404
    if request.method == "POST":
        t["titel"] = request.form.get("titel", t["titel"]).strip() or t["titel"]
        t["beschreibung"] = request.form.get("beschreibung", "")
        t["prioritaet"] = request.form.get("prioritaet", t["prioritaet"])
        return redirect(url_for("ticket", tid=t["id"]))
    opts = "".join(
        f'<option{" selected" if p == t["prioritaet"] else ""}>{p}</option>'
        for p in PRIOS)
    # DIE LUECKE (2): Beschreibung wird roh ins Textarea zurueckgeschrieben.
    return page(f"""
      <h2 class="section-heading">Ticket #{t['id']} bearbeiten</h2>
      <form method="post">
        <label for="titel">Titel</label>
        <input id="titel" name="titel" value="{{{{ titel }}}}">
        <label for="description">Beschreibung</label>
        <textarea id="description" name="beschreibung" rows="6">{{{{ beschreibung|safe }}}}</textarea>
        <label for="priority">Prioritaet</label>
        <select id="priority" name="prioritaet">{opts}</select>
        <p><button type="submit">Speichern</button></p>
      </form>""", titel=t["titel"], beschreibung=t["beschreibung"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "").strip() or "user"
        resp = make_response(redirect(url_for("index")))
        # DIE LUECKE (3): Klartext-Identitaet, kein HttpOnly -> per XSS lesbar.
        resp.set_cookie("username", u, httponly=False)
        return resp
    return page("""
      <h2 class="section-heading">Benutzer waehlen</h2>
      <form method="post">
        <label for="username">Benutzername (fiktiv)</label>
        <input id="username" name="username" placeholder="team-test">
        <p><button type="submit">Uebernehmen</button></p>
      </form>""")


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5002"))
    print("[!] UEBUNGS-LAB: Stored XSS im Ticket-Beschreibungsfeld - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: alert beim Oeffnen eines Tickets)")
    app.run(host=host, port=port, debug=False)
