# Ordner 11 — Fix gegen XSS

Behebt Ordner 10. Verteidigung in mehreren Schichten (Defense in Depth).

## 1. Ausgabe escapen (die eigentliche Ursache)
`{{ post.content }}` statt `{{ post.content|safe }}`. Jinja2 escaped automatisch,
`<script>` wird als **Text** angezeigt, nicht ausgeführt. Regel: **niemals `|safe`
auf User-Input**.

## 2. Content-Security-Policy (2. Schicht)
`app.after_request` setzt eine CSP mit `script-src 'self'` (ohne `'unsafe-inline'`).
Selbst wenn irgendwo doch ungeescapter Input durchrutscht, führt der Browser kein
inline-`<script>` aus. Inline-*Styles* bleiben erlaubt (fürs Theme; Styles sind nicht
der Angriffsvektor).

## 3. HttpOnly-Cookie (begrenzt den Schaden)
`SESSION_COOKIE_HTTPONLY = True` (+ `SameSite=Lax`). `document.cookie` sieht den
Session-Cookie nicht mehr → der Cookie-Klau aus Ordner 10 läuft ins Leere.

## Testen (Kontrast zu Ordner 10)
```powershell
pip install -r requirements.txt
python seed.py
python app.py
```
- Der Cookie-Klau-Payload aus Ordner 10 als Aushang posten → erscheint als **Text**,
  kein Request an den Collector, `loot.log` bleibt leer.
- Im Browser-DevTools: Response-Header zeigt die `Content-Security-Policy`.

## Merksatz
XSS-Schutz = **kontextrichtiges Escaping der Ausgabe** zuerst, CSP und HttpOnly als
zusätzliche Netze — nicht Eingabe-Blacklisting.
