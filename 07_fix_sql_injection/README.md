# Ordner 07 — Fix gegen SQL-Injection

Behebt die Lücken aus **Ordner 05**. Kernregel: **nie** Benutzereingaben in einen
SQL-String verketten.

## Der Fix im Code
```python
# UNSICHER (Ordner 05):
sql = f"SELECT id, username FROM users WHERE username LIKE '%{q}%'"
db.session.execute(text(sql))

# SICHER (hier): gebundener Parameter mit ":" — der Aufgaben-Hinweis
stmt = text("SELECT id, username FROM users WHERE username LIKE :pattern") \
        .bindparams(pattern=f"%{q}%")
db.session.execute(stmt)
```
Der Wert wird als **Parameter** an die DB übergeben, nie als Code interpretiert. Ein
`... UNION SELECT password_hash ...`-Payload liefert jetzt schlicht 0 Treffer.
Alternativ (noch einfacher): reines ORM `User.query.filter(User.username.like(...))`.

Der verwundbare `/login-legacy` aus Ordner 05 ist **entfernt** — der korrekte Login
läuft über ORM + Hash-Vergleich + 2FA.

Außerdem: `SECRET_KEY` hat **keinen hartkodierten Default** mehr (kommt aus der Umgebung).

## Automatisch prüfen

### bandit (statischer Security-Linter)
```powershell
pip install bandit
bandit -r .            # scannt alle .py rekursiv
```
`bandit` meldet u. a. **B608** (hardcoded SQL / string-based query construction) und
**B105/B106** (hardcoded password/secret). Im Fix-Ordner sollte nichts Kritisches
mehr auftauchen; im Vergleich meldet `bandit -r ../05_sql_injection` die Lücken.

### detect-secrets (bandit-Alternative für Secrets)
```powershell
pip install detect-secrets
detect-secrets scan > .secrets.baseline    # Baseline anlegen
detect-secrets audit .secrets.baseline     # Funde durchgehen
```
Findet versehentlich eingecheckte Keys/Passwörter/Tokens — genau das Thema, das in
Ordner 14 (LFI → Secret Key) und im defensiven Ordner 99 (Secret-Scanner) wieder
aufgegriffen wird.

## Starten / Testen
```powershell
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
```
→ Suche mit `alice` = 1 Treffer; Suche mit UNION-Payload = 0 Treffer.
