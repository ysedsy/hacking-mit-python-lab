# Challenge: Session-Abuse — zum Marshal befördern (ohne Admin-Login)

Ziel dieser Übung: Zeigt, dass eine Flask-**Session** gefährlich wird, wenn die
App **Nutzereingaben ungefiltert in die Session übernimmt**. Du beförderst dich
selbst vom „Greenhorn" zum **Marshal** und kommst so ins Admin-Büro — **ohne**
den `SECRET_KEY` zu kennen und ohne Marshal-Zugangsdaten.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner; der/die
**Nachbar:in** greift diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5007
> ```
> (Standard ist `127.0.0.1` = nur lokal. `0.0.0.0` nur im vertrauenswürdigen
> Kurs-Netz während des Übungstermins.)

---

## Spielregeln

- Nur die eingeladene Instanz (euer:e direkte:r Nachbar:in). Keine anderen Rechner.
- Nur das fiktive Konto `team-test` / `test123`. Keine echten Daten.
- Kein DoS, kein Verändern/Löschen fremder Daten. Mit **einem** Request lösbar.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Nach dem Login bist du ein **Greenhorn** (`rang=greenhorn`). Das **Marshal-Büro**
(`/marshal`) steht nur dem Rang `marshal` offen. Es gibt eine Seite
**Einstellungen**, auf der du eigentlich nur deinen Anzeigenamen und deinen
Lieblings-Revolver speicherst.

Der Haken: Das `SECRET_KEY` ist hier **stark und zufällig** — den Cookie selbst zu
fälschen, ist also aussichtslos. Trotzdem gibt es einen Weg.

## Aufgabe

Erreiche `/marshal` als Marshal (`rang=marshal`), ohne einen Marshal-Login zu
kennen und ohne den `SECRET_KEY`.

## Hinweis

- Schau dir an, **was** die Einstellungen-Route mit den Formulardaten macht. Sie
  übernimmt **jedes** gesendete Feld in die Session — auch Felder, die im Formular
  gar nicht vorgesehen sind.
- Die Startseite zeigt dir den kompletten **Session-Inhalt** an. Beobachte, wie er
  sich nach dem Speichern verändert.
- Du musst nichts signieren/fälschen: Schick einfach ein zusätzliches Feld `rang`
  mit — der **Server** packt es in die Session und signiert sie für dich.
- Im Browser: Einstellungen öffnen, per DevTools (F12 → Elements) ein weiteres
  Feld ins Formular einfügen …
  ```html
  <input name="rang" value="marshal">
  ```
  … oder gleich per `curl` ein Feld mehr mitschicken.

## Erfolgskriterium

- Nach deinem Request zeigt die Startseite `Rang: marshal`.
- `/marshal` liefert **HTTP 200** und die geheime Fahndungsliste (nicht 403).
- Du hast weder den `SECRET_KEY` benutzt noch einen Marshal-Login gekannt.

## Zählt **nicht** als Lösung

- Den `SECRET_KEY` erraten und den Cookie offline fälschen (das ist die *andere*
  Challenge `challenge_session_forgery` / Ordner `13_session_forgery`).
- Den angezeigten Session-Text nur in den DevTools überschreiben (muss aus der
  **gespeicherten** Session kommen, also über den Server-Roundtrip).

## Kür (Impact zeigen)

Mit demselben Trick lassen sich beliebige Session-Felder setzen — z. B. die
Identität übernehmen:
```
user=marshal-buford&rang=marshal
```
Zeigt die Startseite danach einen fremden Benutzer **mit** Marshal-Rang, ist klar:
Wer die Session mitbestimmt, bestimmt Identität **und** Rechte.

---

## Verteidigung / Fix (Diskussion danach)

- **Ursache:** Die Route schreibt Nutzereingaben ungefiltert in die Session
  (`for k, v in request.form.items(): session[k] = v`). Sicherheitsrelevante
  Felder wie `rang`/`user` werden damit vom Angreifer kontrolliert.
- **Fix:** **Allowlist** der beschreibbaren Felder (nur `anzeigename`, `revolver`).
  Rollen/Rechte **serverseitig** setzen, nie aus dem Formular. Siehe die
  sichere Route `/einstellungen-safe` im selben `app.py`.
- **Defense-in-Depth:** Autorisierung gegen eine serverseitige Quelle prüfen
  (DB-Rolle), nicht gegen ein frei setzbares Session-Feld.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```bash
BASE=http://127.0.0.1:5007
# 1) einloggen, Cookie merken
curl -s -c jar -d "username=team-test&password=test123" "$BASE/login" -o /dev/null
# 2) Einstellungen speichern -- plus ein ungeplantes Feld rang=marshal
curl -s -b jar -c jar -d "anzeigename=Doc&revolver=Colt&rang=marshal" \
     "$BASE/einstellungen" -o /dev/null
# 3) Admin-Gate offen
curl -s -b jar "$BASE/marshal"     # -> 200 + Fahndungsliste
```

Fix-Gegenprobe: Schritt 2 gegen `/einstellungen-safe` -> `rang` prallt ab,
`/marshal` bleibt 403.
</details>
