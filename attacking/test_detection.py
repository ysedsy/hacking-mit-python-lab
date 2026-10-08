"""Validiert die Erkennungslogik von attack_all.py gegen SIMULIERTE Ziele.

Kein echter Server, kein echter Angriff: eine Fake-Session liefert kanned Antworten,
einmal fuer eine verwundbare, einmal fuer eine gepatchte Instanz. Die Eingabepunkte
(Targets/Formulare) werden direkt gesetzt, sodass die generischen Checks ohne Crawl
geprueft werden koennen.

    python test_detection.py
"""
import html as _html
import re
from urllib.parse import urlsplit

import attack_all as A

EVIL_ORIGIN = "https://evil.example"


class FakeResp:
    def __init__(self, text="", status=200, headers=None):
        self.text = text
        self.status_code = status
        self.headers = headers or {}


class FakeCookie:
    def __init__(self, name, value, secure=False, rest=None):
        self.name = name
        self.value = value
        self.secure = secure
        self._rest = rest or {}


class FakeSession:
    """Routet nach Pfad; `vuln=True` schaltet verwundbares Verhalten frei."""

    def __init__(self, vuln):
        self.vuln = vuln
        self.login_attempts = 0
        if vuln:
            # Flask-aehnliches, klartext-lesbares Payload-Cookie, ohne Flags.
            self.cookies = [FakeCookie("session", "eyJ1c2VyIjoiYWRtaW4ifQ.aaa.bbb")]
            self._set_cookie = "session=...; Path=/"
        else:
            self.cookies = [FakeCookie("session", "opaque-random-xyz", secure=True,
                                       rest={"HttpOnly": True})]
            self._set_cookie = "session=...; Secure; HttpOnly; SameSite=Lax; Path=/"

    # -- requests-kompatible Schnittstelle -----------------------------------
    def get(self, url, params=None, allow_redirects=True, **kw):
        return self._route("GET", url, params or {}, allow_redirects)

    def post(self, url, data=None, allow_redirects=True, **kw):
        return self._route("POST", url, data or {}, allow_redirects)

    def _route(self, method, url, args, allow_redirects):
        path = urlsplit(url).path or "/"
        if path == "/":
            h = {"Server": "Werkzeug/3.0 Python/3.11", "Set-Cookie": self._set_cookie}
            if not self.vuln:
                h.update({"Content-Security-Policy": "default-src 'self'",
                          "X-Content-Type-Options": "nosniff",
                          "X-Frame-Options": "DENY"})
            else:
                h.update({"Access-Control-Allow-Origin": EVIL_ORIGIN,      # CORS spiegelt Origin
                          "Access-Control-Allow-Credentials": "true"})
            return FakeResp("<html>home</html>", headers=h)

        if path == "/search":
            q = args.get("q", "")
            if not self.vuln:
                return FakeResp("<div>" + _html.escape(q) + "</div>")
            if q.endswith("'"):                               # Quote bricht SQL
                return FakeResp("Internal Server Error", status=500)
            if "etc/passwd" in q:                             # Path-Traversal
                return FakeResp("root:x:0:0:root:/root:/bin/bash")
            m = re.search(r"\{\{(\d+)\*(\d+)\}\}", q)         # SSTI: Ausdruck auswerten
            if m:
                q = q.replace(m.group(0), str(int(m.group(1)) * int(m.group(2))))
            return FakeResp("<div>" + q + "</div>")           # XSS: roh reflektiert

        if path == "/go":                                     # Open Redirect
            nxt = args.get("next", "")
            if self.vuln and nxt.startswith("http"):
                return FakeResp("", status=302, headers={"Location": nxt})
            return FakeResp("", status=302, headers={"Location": "/"})

        if path == "/login":
            self.login_attempts += 1
            if not self.vuln and self.login_attempts >= 6:
                return FakeResp("Konto gesperrt", status=429)
            return FakeResp("Login fehlgeschlagen")

        if path == "/dashboard":                              # geschützte Seite
            if self.vuln:                                     # ohne Login erreichbar
                return FakeResp('<nav><a href="/logout">Logout</a></nav> Willkommen')
            return FakeResp("", status=302, headers={"Location": "/login"})

        if path.startswith("/.git") or path.startswith("/.env") or path == "/config.py":
            return FakeResp("SECRET_KEY=1", status=200 if self.vuln else 404)

        return FakeResp("not found", status=404)              # Catch-all/Random


def make_scanner(vuln):
    sc = A.Scanner("http://sim", session=FakeSession(vuln))
    sc.anon_sess = FakeSession(vuln)   # cookie-lose Session fuer den BAC-Check
    sc.session_factory = lambda: FakeSession(vuln)   # frische Sessions fuer SQLi-Proben
    # Eingabepunkte, die der Crawler sonst selbst faende:
    sc.targets = [
        A.Target("GET", "http://sim/search", {"q": "test"}, "q", "query", "http://sim/search?q=test"),
        A.Target("GET", "http://sim/go", {"next": "/home"}, "next", "query", "http://sim/go?next=/home"),
    ]
    # Gepatchte Instanz schuetzt POST-Formulare mit einem versteckten CSRF-Token.
    token = [] if vuln else [{"name": "csrf_token", "type": "hidden", "value": "tok"}]
    login_form = {"action": "http://sim/login", "method": "POST", "inputs": [
        {"name": "username", "type": "text", "value": ""},
        {"name": "password", "type": "password", "value": ""}] + token}
    comment_form = {"action": "http://sim/search", "method": "POST", "inputs": [
        {"name": "q", "type": "text", "value": ""}] + token}
    sc.pages = [("http://sim/", FakeResp(), [login_form, comment_form])]
    sc.login_forms = [("http://sim/login", login_form,
                       {"username": "test", "password": "Passwort123!"})]
    sc.bodies = [("http://sim/err",
                  "Traceback (most recent call last): ... Werkzeug Debugger" if vuln else "ok")]
    return sc


def verdicts(vuln):
    sc = make_scanner(vuln)
    out = {}
    for f in sc.run_all():
        # bei mehreren Findings pro Check zaehlt das "schlimmste" (VULN > INFO > SAFE > NA)
        rank = {A.VULN: 0, A.INFO: 1, A.SAFE: 2, A.NA: 3}
        if f.check not in out or rank[f.verdict] < rank[out[f.check]]:
            out[f.check] = f.verdict
    return out


def main():
    failures = 0

    print("== Verwundbares Ziel (muss VULN melden) ==")
    v = verdicts(vuln=True)
    expect_vuln = ["Security-Header", "Cookie-Flags", "SQL-Injection", "Reflected XSS",
                   "Path-Traversal/LFI", "Open Redirect", "CSRF-Token", "Brute-Force-Schutz",
                   "Sensible Dateien erreichbar", "Debug-/Stacktrace-Leak",
                   "Broken Access Control", "Server-Side Template Injection",
                   "CORS-Fehlkonfiguration"]
    for name in expect_vuln:
        got = v.get(name, "FEHLT")
        ok = got == A.VULN
        print(f"  {got:4}  {name}" + ("" if ok else "   !! erwartet VULN"))
        failures += not ok
    # Info-Check: lesbares Session-Cookie
    got = v.get("Session-Cookie lesbar", "FEHLT")
    print(f"  {got:4}  Session-Cookie lesbar" + ("" if got == A.INFO else "   !! erwartet INFO"))
    failures += got != A.INFO

    print("\n== Gepatchtes Ziel (kein VULN erlaubt) ==")
    s = verdicts(vuln=False)
    for name, verdict in sorted(s.items()):
        print(f"  {verdict:4}  {name}")
        if verdict == A.VULN:
            print("    !! FALSCH: gepatchtes Ziel als verwundbar gemeldet")
            failures += 1

    # Signup-Formulare werden NICHT aktiv befüllt (keine Müll-Accounts).
    print("\n== Signup-Formular wird uebersprungen ==")
    sc = A.Scanner("http://sim", session=FakeSession(True))
    login = {"action": "/login", "method": "POST", "inputs": [
        {"name": "username", "type": "text", "value": ""},
        {"name": "password", "type": "password", "value": ""}]}
    signup = {"action": "/register", "method": "POST", "inputs": [
        {"name": "username", "type": "text", "value": ""},
        {"name": "password", "type": "password", "value": ""},
        {"name": "password_confirm", "type": "password", "value": ""}]}
    sc.pages = [("http://sim/login", FakeResp(), [login]),
                ("http://sim/register", FakeResp(), [signup])]
    sc._build_targets()
    actions = {t.url for t in sc.targets}
    login_ok = "http://sim/login" in actions
    signup_skipped = "http://sim/register" not in actions and sc.skipped_signup == 1
    print(f"  Login gefuzzt: {login_ok} | Register uebersprungen: {signup_skipped}")
    failures += not (login_ok and signup_skipped)

    print("\nERGEBNIS:", "alle Checks korrekt" if failures == 0 else f"{failures} Fehler")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
