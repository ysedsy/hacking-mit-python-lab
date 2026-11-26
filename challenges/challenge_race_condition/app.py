"""Uebungs-Ziel: Race Condition (TOCTOU) -> Gold doppelt abheben.

BEWUSST VERWUNDBAR. Die Auszahlung prueft erst das Guthaben, "bucht" dann
mit Verzoegerung und zieht erst danach ab -- ohne Lock:

    if konto >= betrag:          # Check
        time.sleep(0.3)          # (Buchung dauert ...)
        konto -= betrag          # Use

Schickt man viele Auszahlungen GLEICHZEITIG, bestehen alle den Check, bevor
die erste abzieht. So hebt man mehr ab, als auf dem Konto liegt.

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5008

Startguthaben 100 Gold. Ziel: insgesamt mehr als 100 Gold in der Satteltasche.

GRENZE: Nur gegen diese eigene Uebungs-Instanz. Max. ~20 parallele Requests.
"""
import os
import time
import uuid

from flask import (Flask, make_response, redirect, render_template_string,
                   request, url_for)

app = Flask(__name__)
SPIELER = {}      # spieler-id -> {"konto": int, "tasche": int}

HEAD = """<!doctype html>
<title>Goldbank (Race-Lab)</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem} a.btn,button{background:#92400e;color:#fde68a;
      border:0;border-radius:6px;cursor:pointer;text-decoration:none;padding:.5rem .9rem}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .muted{color:#6b5b45;font-size:.85rem;word-break:break-all}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (Race Condition). Nur lokal/autorisiert.</p>
<h1>&#128176; Goldbank &mdash; Schalter</h1>
"""


def render(body, **ctx):
    return render_template_string(HEAD + body, **ctx)


def spieler():
    sid = request.cookies.get("spieler", "")
    return sid, SPIELER.get(sid)


@app.route("/")
def index():
    sid, s = spieler()
    if not s:
        sid = uuid.uuid4().hex
        SPIELER[sid] = s = {"konto": 100, "tasche": 0}
    resp = make_response(render("""
      <div class="card">Konto: <b>{{ s.konto }}</b> Gold &middot;
        Satteltasche: <b>{{ s.tasche }}</b> Gold</div>
      {% if s.tasche > 100 %}<div class="card"><h2>&#129689; Angriff geglueckt</h2>
        <p>Du hast {{ s.tasche }} Gold abgehoben &mdash; mehr als je auf dem Konto lag.</p></div>{% endif %}
      <form method="post" action="/abheben" class="card">
        <p><input name="betrag" value="100" size="6"> Gold</p>
        <button type="submit">Abheben</button>
      </form>
      <p><a class="btn" href="/reset">Neues Konto (100 Gold)</a></p>
      <p class="muted">Spieler-ID: {{ sid }}</p>""", s=s, sid=sid))
    resp.set_cookie("spieler", sid)
    return resp


@app.route("/abheben", methods=["POST"])
def abheben():
    _, s = spieler()
    if not s:
        return redirect(url_for("index"))
    try:
        betrag = int(request.form.get("betrag", "0"))
    except ValueError:
        betrag = 0
    if betrag <= 0:
        return render("<div class='card'>Ungueltiger Betrag.</div>"), 400
    # DIE LUECKE: Check und Abbuchung nicht atomar, kein Lock.
    if s["konto"] >= betrag:
        time.sleep(0.3)               # "Buchung beim Telegrafenamt ..."
        s["konto"] -= betrag
        s["tasche"] += betrag
        return redirect(url_for("index"))
    return render("<div class='card'>Nicht genug Guthaben.</div>"
                  "<p><a class='btn' href='/'>zurueck</a></p>"), 402


@app.route("/reset")
def reset():
    sid, s = spieler()
    if s:
        s.update(konto=100, tasche=0)
    return redirect(url_for("index"))


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5008"))
    print("[!] UEBUNGS-LAB: Race Condition - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: >100 Gold abheben)")
    app.run(host=host, port=port, debug=False, threaded=True)
