# challenge_file_upload/ — Übungs-Ziel: Unrestricted File Upload

Bewusst verwundbare Mini-Flask-App. Der Upload prüft weder Typ noch Inhalt und
liefert Dateien unter `/uploads/<name>` mit dem zur Endung passenden Content-Type
aus. Eine `.html`/`.svg` mit `<script>` läuft damit **im Origin der App** →
Session-/Cookie-Diebstahl, Defacement, Phishing.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1`; für die
> Nachbar-Challenge `HOST=0.0.0.0` setzen. Der Ordner `uploads/` ist gitignoriert.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5006`)
- `challenge.md` — die Aufgabenstellung

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# printf "<script>alert('XSS')</script>" > pwn.html
# curl -F "datei=@pwn.html" http://127.0.0.1:5006/
# dann öffnen:  http://127.0.0.1:5006/uploads/pwn.html   -> Alert im App-Origin
```

**Fix:** Allowlist erlaubter Typen, Inhalt validieren, Dateien umbenennen, mit
festem harmlosem Content-Type + `Content-Disposition: attachment` von einer
**anderen** Origin ausliefern; Uploads nie ausführbar ablegen.
