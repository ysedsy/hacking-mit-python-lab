# Challenge: Stored XSS im Ticket (Script einschmuggeln)

Ziel dieser Übung: Zeigt, dass ein Eingabefeld gefährlich wird, wenn sein Inhalt
später **ungeescaped** wieder angezeigt wird. Ihr schmuggelt über die
**Beschreibung** eines Tickets JavaScript ein, das bei **allen** losläuft, die
das Ticket danach öffnen (**Stored / Persistent XSS**).

**Aufbau:** Jede:r startet die verwundbare App auf dem **eigenen** Rechner. Der/
die **Nachbar:in** legt auf eurer Instanz ein Ticket mit einem Payload an; sobald
ihr (oder „die Sachbearbeitung") das Ticket anschaut, läuft fremder Code in
eurem Browser.

> Lokal starten und im Kurs-Netz erreichbar machen:
> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5002
> ```
> (Standard ist `127.0.0.1` = nur lokal. `0.0.0.0` nur im vertrauenswürdigen
> Kurs-Netz während des Übungstermins.)

---

## Spielregeln

- Greift **ausschließlich** die Instanz an, deren Besitzer:in euch ausdrücklich
  dazu eingeladen hat (euer:e direkte:r Nachbar:in). Keine anderen Rechner/Dienste.
- Nur fiktive Konten/Inhalte. Keine echten Namen, Passwörter oder
  personenbezogenen Daten. Legt keine Massen an Tickets an.
- Kein Denial-of-Service, kein Verändern/Löschen fremder Daten. Die Challenge ist
  mit **einem** präparierten Ticket lösbar.
- Haltet den Payload harmlos (`alert`); keine echten Schad-Skripte, kein
  Weiterleiten von Daten an externe Server.
- Nur während des vorgesehenen Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Das Ticketsystem zeigt die **Beschreibung** eines Tickets auf der Detailseite an
und schreibt sie beim Bearbeiten zurück ins Formular. Du kannst Tickets anlegen
und ansehen.

## Aufgabe

Lege ein Ticket an, dessen **Beschreibung** so präpariert ist, dass beim
**Öffnen des Tickets** JavaScript ausgeführt wird — sichtbar durch ein
`alert('XSS')`.

## Hinweis

- Nicht das Eingabefeld ist entscheidend, sondern **wo die Beschreibung wieder
  ausgegeben wird**. Schau dir den Quelltext der Ticket-**Detailseite** an
  (Rechtsklick → Seitenquelltext / F12 → Elements) und suche deinen Text.
- Steht er dort **roh** (`<img …>` statt `&lt;img …&gt;`), wird nicht escaped →
  dein HTML wird Teil der Seite.
- Ein Payload, der **beim Laden** feuert, ist zuverlässiger als einer, der auf
  einen Fehler wartet:
  ```html
  <img src=x onerror=alert('XSS')>
  ```
- Achte auf den **Kontext**: Auf der Detailseite landet die Beschreibung in einem
  normalen Absatz (`<p>`) — da reicht der Payload direkt. Im **Bearbeiten**-
  Formular steht sie in einem `<textarea>`; dort musst du es erst schließen:
  ```html
  </textarea><img src=x onerror=alert('XSS')>
  ```

## Erfolgskriterium

- Du hast **ein** Ticket mit präparierter Beschreibung gespeichert.
- Beim **Öffnen dieses Tickets** erscheint ein `alert('XSS')` — ohne dass du
  sonst etwas anklickst.
- Der Payload steht im Seitenquelltext **roh** (nicht escaped).

## Zählt **nicht** als Lösung

- Den Payload nur ins Formular tippen und im `<textarea>` „sehen" (dort ist er
  als Formular-Wert escaped — das ist normal und keine Lücke).
- `alert` über die Browser-Konsole selbst auslösen.
- Die Seite lokal im Editor verändern (DevTools-DOM-Edit) — es muss aus den
  **gespeicherten** Ticketdaten kommen.

## Kür (Impact zeigen)

Dieses System legt die Identität in einem **Klartext-Cookie** `username` **ohne
HttpOnly** ab. Damit lässt sich der Cookie per XSS auslesen:
```html
<img src=x onerror=alert(document.cookie)>
```
Zeigt der Alert `username=…`, könnte ein echter Angreifer die Identität
stehlen/übernehmen. (Deshalb: `HttpOnly` setzen.)

---

## Verteidigung / Fix (Diskussion danach)

- **Ursache:** Ausgabe der Beschreibung mit abgeschaltetem Escaping
  (Jinja-Filter `|safe`) — in Detailansicht **und** Edit-Textarea.
- **Fix:** `|safe` entfernen → Jinja-**Autoescaping** macht aus `<` `&lt;` usw.
  Nutzereingaben niemals als vertrauenswürdiges HTML behandeln. Vgl. Lab-Ordner
  `../11_fix_xss/`.
- **Defense-in-Depth:** strenge `Content-Security-Policy` (z. B.
  `script-src 'self'`, keine Inline-Handler), Cookies mit `HttpOnly` + `Secure`.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```text
1. Neues Ticket -> Beschreibung:  <img src=x onerror=alert('XSS')>  -> Speichern
2. Ticket öffnen (/ticket/<id>)   -> Alert feuert
3. Quelltext prüfen: <p class="ticket-description"><img src=x onerror=...> (roh)
4. Impact: <img src=x onerror=alert(document.cookie)> zeigt den username-Cookie
```

Automatische Erkennung über den Scanner im Nachbarordner `attacking/`
(nutzt einen `<svg/onload>`-Marker):
```powershell
python ..\attacking\attack_all.py --base http://127.0.0.1:5002
```
</details>
