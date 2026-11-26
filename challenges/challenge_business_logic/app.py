"""Uebungs-Ziel: Business-Logic-Fehler -> negative Mengen im Shop.

BEWUSST VERWUNDBAR. Der Saloon-Laden rechnet die Bestellung als
Summe(preis * menge) und prueft nur "Summe <= Gold". Ob eine Menge NEGATIV ist,
prueft niemand. -10 Whiskey ergibt eine negative Teilsumme -- also eine
Gutschrift, mit der man den teuren Sheriffstern "bezahlt".

Start (nur lokal / eigene Instanz):

    pip install flask
    python app.py                 # http://127.0.0.1:5009

Startguthaben 50 Gold. Ziel: den Sheriffstern (500 Gold) besitzen.

GRENZE: Nur gegen diese eigene Uebungs-Instanz.
"""
import os
import uuid

from flask import (Flask, make_response, redirect, render_template_string,
                   request, url_for)

app = Flask(__name__)
WAREN = {
    "whiskey": ("Whiskey", 5),
    "bohnen": ("Dose Bohnen", 2),
    "hufeisen": ("Hufeisen", 12),
    "stern": ("Sheriffstern", 500),
}
KUNDEN = {}      # kunden-id -> {"gold": int, "inventar": {ware: menge}}

HEAD = """<!doctype html>
<title>Saloon-Laden (Logik-Lab)</title>
<style>
 body{font-family:Georgia,serif;max-width:680px;margin:2rem auto;padding:0 1rem;
      background:#f4ecd8;color:#2b2119}
 .warn{background:#7c2d12;color:#fde68a;padding:.6rem .9rem;border-radius:6px;font-size:.9rem}
 input,button{padding:.5rem;font-size:1rem} a.btn,button{background:#92400e;color:#fde68a;
      border:0;border-radius:6px;cursor:pointer;text-decoration:none;padding:.5rem .9rem}
 .card{background:#fffbf0;border:1px solid #d6c7a1;border-radius:8px;padding:1rem;margin:1rem 0}
 .muted{color:#6b5b45;font-size:.85rem}
 table{width:100%;border-collapse:collapse} td,th{border:1px solid #d6c7a1;padding:.4rem;text-align:left}
</style>
<p class="warn">UEBUNGS-LAB &mdash; bewusst verwundbar (Business Logic). Nur lokal/autorisiert.</p>
<h1>&#129360; Kramladen &bdquo;Zum staubigen Stiefel&ldquo;</h1>
"""


def render(body, **ctx):
    return render_template_string(HEAD + body, **ctx)


def kunde():
    kid = request.cookies.get("kunde", "")
    return kid, KUNDEN.get(kid)


@app.route("/")
def laden():
    kid, k = kunde()
    if not k:
        kid = uuid.uuid4().hex
        KUNDEN[kid] = k = {"gold": 50, "inventar": {}}
    resp = make_response(render("""
      <div class="card">Dein Gold: <b>{{ k.gold }}</b>
        &middot; Inventar: {{ k.inventar or 'leer' }}</div>
      {% if k.inventar.get('stern', 0) > 0 %}<div class="card"><h2>&#11088; Angriff geglueckt</h2>
        <p>Du besitzt den Sheriffstern &mdash; mit nur 50 Gold Startkapital.</p></div>{% endif %}
      <form method="post" action="/kaufen" class="card"><table>
        <tr><th>Ware</th><th>Preis</th><th>Menge</th></tr>
        {% for key, (name, preis) in waren.items() %}
        <tr><td>{{ name }}</td><td>{{ preis }} Gold</td>
            <td><input type="number" name="menge_{{ key }}" value="0" min="0" size="4"></td></tr>
        {% endfor %}
      </table><p><button type="submit">Kaufen</button></p></form>
      <p><a class="btn" href="/reset">Neu anfangen</a></p>""", k=k, waren=WAREN))
    resp.set_cookie("kunde", kid)
    return resp


@app.route("/kaufen", methods=["POST"])
def kaufen():
    _, k = kunde()
    if not k:
        return redirect(url_for("laden"))
    bestellung = {}
    for key in WAREN:
        try:
            menge = int(request.form.get(f"menge_{key}", "0"))
        except ValueError:
            menge = 0
        if menge:
            # DIE LUECKE: keine Pruefung auf menge > 0 (nur das HTML hat min="0").
            bestellung[key] = menge
    summe = sum(WAREN[key][1] * m for key, m in bestellung.items())
    if summe > k["gold"]:
        return render("<div class='card'>Zu wenig Gold: Bestellung kostet "
                      "{{ s }}, du hast {{ g }}.</div><p><a class='btn' href='/'>zurueck</a></p>",
                      s=summe, g=k["gold"]), 402
    k["gold"] -= summe
    for key, m in bestellung.items():
        k["inventar"][key] = k["inventar"].get(key, 0) + m
    return redirect(url_for("laden"))


@app.route("/reset")
def reset():
    _, k = kunde()
    if k:
        k.update(gold=50, inventar={})
    return redirect(url_for("laden"))


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5009"))
    print("[!] UEBUNGS-LAB: Business Logic - nur lokal/autorisiert.")
    print(f"[i] Start auf http://{host}:{port}  (Ziel: Sheriffstern mit 50 Gold)")
    app.run(host=host, port=port, debug=False)
