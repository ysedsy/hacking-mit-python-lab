# challenge_ssrf/ — Übungs-Ziel: Server-Side Request Forgery

Bewusst verwundbare Mini-Flask-App. Der „Steckbrief-Importer" ruft eine vom
Nutzer gelieferte URL serverseitig ab, ohne das Ziel zu prüfen. So lässt sich
die interne Seite `/intern` auslesen, die externen Clients `403` gibt, weil der
Abruf nun von `localhost` (dem Server selbst) kommt.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1`; für die
> Nachbar-Challenge `HOST=0.0.0.0` setzen. Der Importer ist bewusst auf http(s)
> beschränkt — keine echten fremden URLs abrufen.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5011`)
- `challenge.md` — die Aufgabenstellung

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# Angriff:
#   curl "http://127.0.0.1:5011/import?url=http://127.0.0.1:5011/intern"
```

**Fix:** Ziel-URLs allowlisten, interne/lokale Adressen blocken, nicht auf
„Anfrage kommt von localhost" als Autorisierung vertrauen.
