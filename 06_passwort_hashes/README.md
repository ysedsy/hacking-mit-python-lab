# Ordner 06 — Passwortangriff auf die Hashes (offline)

Schließt den Bogen aus Ordner 05: die per SQL-Injection extrahierten
**Passwort-Hashes** werden hier **offline** geknackt. Nur gegen die eigenen Lab-Hashes.

## Hashes besorgen
```powershell
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
python seed.py            # legt alice/bob/admin mit schwachen Passwörtern an
python export_hashes.py   # -> hashes.txt (user:hash) und hashes_only.txt
```
Werkzeug erzeugt standardmäßig `pbkdf2:sha256:<iter>$<salt>$<hash>`.

## Variante A — John the Ripper
John erkennt das Django/Werkzeug-PBKDF2-Format über `user:hash`:
```bash
john --format=django --wordlist=rockyou.txt hashes.txt
john --show --format=django hashes.txt
```

## Variante B — Hashcat
PBKDF2-HMAC-SHA256 (Django-Layout) = **Modus 10000**:
```bash
hashcat -m 10000 -a 0 hashes_only.txt rockyou.txt
hashcat -m 10000 hashes_only.txt --show
```
> Der Hash muss im von Hashcat erwarteten Layout vorliegen
> (`pbkdf2_sha256$iter$salt$base64`). Werkzeugs `$`-getrenntes Format ggf. umformen —
> Schritt ist im Kurs Teil der Übung.

## Variante C — OphCrack (optional)
OphCrack knackt **Windows LM/NTLM**-Hashes über Rainbow Tables — **nicht** PBKDF2.
Für eine OphCrack-Demo erzeugt man daher NTLM-Hashes der gleichen Passwörter:
```python
import hashlib
print(hashlib.new("md4", "hunter2".encode("utf-16le")).hexdigest())  # NTLM
```
Diese NTLM-Hashes lassen sich in OphCrack mit Rainbow Tables auflösen. Lerneffekt:
**ungesalzene** Hashes (LM/NTLM) fallen sofort, **gesalzene, langsame** (PBKDF2/bcrypt)
kosten den Angreifer massiv Zeit.

## Wortlisten (Aufgaben-Hinweis „SVNDigger")
- `rockyou.txt` (Klassiker für Passwörter)
- **SVNDigger**/`raft`-Listen sind eher für **Verzeichnis-/Datei-Brute-Force**
  gedacht (siehe Ordner 14 LFI + DirBuster), nicht für Passwort-Cracking — hier zur
  Abgrenzung erwähnt.

## Lernpunkt / Verbindung
- Schwache Passwörter (`hunter2`, `letmein123`) fallen in Sekunden.
- Deshalb: **starke Passwörter erzwingen** (Ordner 01 Validierung), **2FA** (Ordner 04,
  macht den geknackten Hash allein wertlos) und **langsame, gesalzene** Hashes.

## Hinweis: Hashes via Pony-Suche ziehen
Die Hashes müssen nicht zwingend über `/search` kommen — die verwundbare **Pony-Suche**
`/ponys?q=` (siehe Ordner 05) eignet sich genauso, um per UNION `username` +
`password_hash` aus der `users`-Tabelle zu ziehen. Danach wie unten offline knacken.
