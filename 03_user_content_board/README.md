# Ordner 03 — Seite mit Content von allen Usern

Dritte Stufe. Ein öffentliches **Board**: jeder eingeloggte User postet Beiträge,
die **alle** User sehen. Das ist die Bühne fürs spätere XSS-Szenario.

## Neu gegenüber Ordner 02
- `models.py`: `Post`-Modell + Relation `User.posts`
- `forms.py`: `PostForm`
- Route `/board` (GET listet alle Beiträge, POST legt einen an)
- Nav-Link „Board"

## Sicherheit an dieser Stelle
Das Board ist hier **noch sicher**: Jinja2 escaped `{{ post.content }}` automatisch.
Ein `<script>`-Beitrag wird als Text angezeigt, nicht ausgeführt.

➡️ In **Ordner 10** wird der Beitrag absichtlich mit `{{ post.content|safe }}`
gerendert — **das** ist die Stored-XSS-Lücke (Cookie-Klau / Keylogger).
**Ordner 11** liefert den Fix (Escaping + Content-Security-Policy).

## Starten
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
→ http://127.0.0.1:5000
