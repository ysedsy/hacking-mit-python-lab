# attacking/ — Generischer Web-Schwachstellen-Scanner

`attack_all.py` **crawlt eine Ziel-Seite selbst**, sammelt dabei Formulare und
URL-Parameter und fährt die im Lab behandelten Angriffe heuristisch gegen jeden
gefundenen Eingabepunkt. Es sind **keine festen Routen** mehr fest verdrahtet —
der Scanner funktioniert damit gegen beliebige (eigene) Seiten, nicht nur gegen
das Cowboy-Forum.

> Nur für die eigene Instanz oder — im Übungs-CTF **unter Einverständnis** — für
> Instanzen im **Kurs-Netz**. Keine fremden/öffentlichen Systeme. Der Scan sendet
> aktiv Angriffs-Payloads und mehrere fehlerhafte Logins; das ist ein Eingriff.

## Benutzung
```powershell
pip install -r requirements.txt

python attack_all.py --base http://127.0.0.1:5000          # eigene Instanz
python attack_all.py --base http://192.168.1.42:5000       # Mitspieler:in im Kurs-Netz

# Optionen
python attack_all.py --base http://ziel:5000 --max-pages 40 --max-targets 60
python attack_all.py --base http://ziel:5000 --cookie "session=..."   # auth. Scan
```

## Ablauf
1. **Crawl** ab `--base`, nur same-origin, bis `--max-pages` Seiten. Dabei werden
   `<form>`-Felder und URL-Query-Parameter als **Eingabepunkte** gesammelt.
2. Jeder Check läuft gegen diese Punkte (bzw. gegen die Seite global). Fehlt ein
   Angriffspunkt, meldet der Check **n/a** statt eines Fehlers.

## Was geprüft wird
| Check | Angriff / Heuristik | Lab-Bezug |
|-------|---------------------|-----------|
| Security-Header | CSP, `X-Content-Type-Options`, Clickjacking-Schutz | 11 |
| Cookie-Flags | `Secure`, `HttpOnly`, `SameSite` pro Cookie | 11/13 |
| SQL-Injection | einzelnes Quote → 500 / SQL-Fehler, + Boolean-Differential | 05/07 |
| Reflected XSS | `<svg/onload>`-Marker ungeescaped reflektiert? | 10/11 |
| Server-Side Template Injection | wird `{{123*456}}` serverseitig ausgerechnet? | — |
| OS-Command-Injection | zeit-blind: verzögert `; sleep 4` die Antwort? | — |
| Broken Access Control | geschützte Seite (`/dashboard` …) ohne Login erreichbar? | 15 |
| Path-Traversal/LFI | `../etc/passwd`, `win.ini`, `app.py`-Signaturen | 14 |
| Open Redirect | Parameter `next/url/redirect/...` → externe URL? | — |
| CORS-Fehlkonfiguration | spiegelt `Access-Control-Allow-Origin` eine beliebige Origin? | — |
| CSRF-Token | POST-Formular ohne Anti-CSRF-Token-Feld | 12 |
| Brute-Force-Schutz | viele Fehl-Logins ohne Lockout/Rate-Limit/429? | 08/09 |
| Sensible Dateien | `/.git/config`, `/.env`, `/config.py`, Backups … erreichbar? | — |
| Debug-/Stacktrace-Leak | Werkzeug-Debugger / Traceback auf Fehlerseiten | — |
| Tech-Disclosure | `Server`/`X-Powered-By` verrät Stack (info) | — |
| Session-Cookie lesbar | Cookie-Payload base64/JSON-lesbar (info) | 13 |

**Verdikte:** `[!!] VERWUNDBAR` (mit Schweregrad kritisch/hoch/mittel/niedrig),
`[ok] sicher`, `[--] n/a` (Angriffspunkt in dieser Instanz nicht vorhanden),
`[i ] info` (Hinweis, keine direkte Lücke).

## Selbsttest (ohne echtes Ziel)
`test_detection.py` prüft die Erkennungslogik gegen eine **simulierte** verwundbare
und eine gepatchte Instanz (kanned Antworten, kein echter Server/Angriff):
```powershell
python test_detection.py
# -> "alle Checks korrekt"
```

## Hinweis
Die Checks sind **best effort** und heuristisch (besonders Boolean-SQLi, CSRF und
Brute-Force können daneben liegen). Treffer immer manuell gegenprüfen. Der Scanner
ersetzt keinen ausgereiften Scanner wie OWASP ZAP oder `sqlmap`, macht aber die
typischen Lab-Lücken auf beliebigen eigenen Seiten in einem Rutsch sichtbar.
