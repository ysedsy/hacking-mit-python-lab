# challenge_stored_xss/ — Übungs-Ziel: Stored XSS im Ticket

Eine eigenständige, **bewusst verwundbare** Mini-Flask-App (Ticketsystem). Die
Ticket-**Beschreibung** wird beim Anzeigen **ungeescaped** gerendert
(Jinja-Filter `|safe`) — in der Detailansicht (`<p class="ticket-description">`)
und roh zurück ins Edit-`<textarea>`. Wer ein Ticket mit HTML/JS-Payload anlegt,
führt Code bei allen aus, die es später öffnen (**Stored XSS**). Zusätzlich liegt
die Identität in einem Klartext-Cookie `username` **ohne HttpOnly** (per
`document.cookie` stehlbar) — wie im Kurs-Ticketsystem beobachtet.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1` (nur
> lokal); für die Nachbar-Challenge im Kurs-Netz `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare Ticket-App (`python app.py` → `http://127.0.0.1:5002`)
- `challenge.md` — die Aufgabenstellung („Nachbar:in schmuggelt ein Script in dein Ticket")

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py                                  # http://127.0.0.1:5002

# Lösung: neues Ticket, Beschreibung =
#   <img src=x onerror=alert('XSS')>
# speichern, Ticket öffnen -> Alert feuert.
# Impact: <img src=x onerror=alert(document.cookie)>  (zeigt den username-Cookie)

# oder vom Scanner im Nachbarordner erkennen lassen:
python ..\attacking\attack_all.py --base http://127.0.0.1:5002
```

**Fix** (sichere Variante): `|safe` entfernen → Jinja-Autoescaping; zusätzlich
`HttpOnly`-Cookies und eine strenge `Content-Security-Policy`. Vgl. Lab-Ordner
`../11_fix_xss/`.
