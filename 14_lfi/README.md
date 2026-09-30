# Ordner 14 — Local File Inclusion (LFI) + Fix

Das Forum hat eine harmlose **Disclaimer/AGB-Seite**, die Dateien über
`/disclaimer?page=...` ausliefert. Der Dateiname wird ungeprüft übernommen → mit
`../` (Path Traversal) liest der Angreifer **beliebige** Dateien vom Server,
inklusive `app.py` → daraus den **SECRET_KEY** (der dann Session-Forgery aus
Ordner 13 ermöglicht).

> Wichtig: **Server auf `127.0.0.1` laufen lassen** (Standard). Es geht darum, die
> *serverseitigen* Quelldateien zu ziehen — nur gegen die eigene Lab-Instanz.

## Szenario starten
```powershell
pip install -r requirements.txt
python seed.py
python app.py
```
Normal: `http://127.0.0.1:5000/disclaimer?page=agb.txt` zeigt die AGB.

## Angriff — Path Traversal
```
http://127.0.0.1:5000/disclaimer?page=../app.py
http://127.0.0.1:5000/disclaimer?page=..%2Fapp.py      (URL-encoded)
http://127.0.0.1:5000/disclaimer?page=../models.py
```
So lädt das Opfer `routes`/`app.py` herunter und liest den `SECRET_KEY` direkt aus dem
Quelltext. Danach: Session fälschen wie in Ordner 13.

### Kombi mit DirBuster (optional)
Mit **DirBuster/dirb/gobuster** (+ Wortlisten wie SVNDigger/`raft`) die
Verzeichnis-Struktur erraten, um lohnende Pfade für `page=` zu finden:
```bash
gobuster dir -u http://127.0.0.1:5000 -w raft-medium-directories.txt
```

## Der Fix — `/disclaimer-safe`
1. **Whitelist**: nur erlaubte Dateinamen (`disclaimer.txt`, `agb.txt`).
2. **`safe_join`** (aus `werkzeug.utils`): gibt bei `../`-Ausbruch `None` → 404.
```python
if page not in ALLOWED_DOCS: abort(404)
safe = safe_join(DOCS_DIR, page)
if safe is None: abort(404)
return send_file(safe)
```
Zusätzlich: `SECRET_KEY` gehört ohnehin **nicht in den Code** (Ordner 07/13/99),
damit ein Quelltext-Leak nicht gleich den Key preisgibt.
