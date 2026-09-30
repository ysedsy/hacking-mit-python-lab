# Ordner 15 — IDOR (Insecure Direct Object Reference) + Fix

IDOR = eine Objekt-**ID steht in der URL**, und der Server prüft nicht, ob der
eingeloggte User dieses Objekt überhaupt sehen darf. Durch bloßes **Hochzählen der ID**
liest man fremde Daten.

## Szenario
Jeder User hat eine **private Notiz**. `GET /note/<id>` liefert die Notiz allein anhand
der ID — **ohne** zu prüfen, wem sie gehört.

## Angriff
```powershell
pip install -r requirements.txt
python seed.py         # legt Notizen #1 (alice), #2 (bob), #3 (admin) an
python app.py
```
Als `alice` einloggen und die IDs durchprobieren:
```
http://127.0.0.1:5000/note/1   -> eigene Notiz
http://127.0.0.1:5000/note/2   -> BOBs private Notiz (!)
http://127.0.0.1:5000/note/3   -> ADMINs private Notiz (!)
```
Reine ID-Manipulation, kein „Hacking-Tool" nötig. Automatisieren mit Burp Intruder
(Payload = Zahlen 1..1000) oder einem kleinen Skript.

## Der Fix — `/note-safe/<id>`
Nicht nur nach ID filtern, sondern **auch nach Besitzer**:
```python
note = Note.query.filter_by(id=nid, user_id=current_user().id).first()
if note is None:
    abort(404)   # 404 statt 403 -> verrät nicht mal, dass es die ID gibt
```
`/note-safe/2` als `alice` → **404**. Nur die eigene Notiz ist erreichbar.

## Merksatz
Authentifizierung (wer bist du?) ≠ **Autorisierung** (darfst du DIESES Objekt?).
Bei **jedem** Objektzugriff die Zugehörigkeit/Rechte prüfen — nicht auf „unrat­bare IDs"
verlassen (UUIDs verzögern nur, sie ersetzen keinen Check).
