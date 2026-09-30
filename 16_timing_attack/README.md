# Ordner 16 — Timing-Attack (Zeitkanal) + Fix

Ein **Seitenkanal**: die *Dauer* der Antwort verrät Information. Wenn ein Token/Passwort
Zeichen für Zeichen verglichen wird und beim ersten Fehler **abbricht**, dauert eine
Antwort mit mehr korrekten Anfangszeichen messbar länger. Daraus lässt sich das Token
Stück für Stück rekonstruieren.

## Szenario
`/api/verify?token=...` nutzt `insecure_compare`: früher Abbruch beim ersten falschen
Zeichen + kleine Verzögerung pro korrektem Zeichen (verstärkt den Effekt für die Demo).
Default-Token: `S3CR3T` (per `API_TOKEN` änderbar).

## Angriff
```powershell
pip install -r requirements.txt requests
python app.py
# zweites Fenster:
python attack_timing.py
```
Das Skript probiert je Position alle Zeichen durch und wählt das mit der **längsten**
Antwortzeit — das ist das nächste korrekte Zeichen. Ausgabe wächst:
`S`, `S3`, `S3C`, … bis `S3CR3T`.

> Über echte Netze ist das Rauschen größer; man braucht mehr Messungen (Median/Mittel)
> und statistische Auswertung. Das Prinzip bleibt gleich.

## Der Fix — konstante Vergleichszeit
`/api/verify-safe` nutzt `hmac.compare_digest(a, b)`: vergleicht in **konstanter Zeit**,
unabhängig davon, wie viele Zeichen übereinstimmen. Kein früher Abbruch → kein
Zeitunterschied → nichts zu messen.
```python
import hmac
ok = hmac.compare_digest(token, API_TOKEN)
```
Regel: **jeden** Vergleich von Geheimnissen (Tokens, MAC/HMAC, Passwort-Hashes,
Reset-Tokens) mit `hmac.compare_digest` bzw. `secrets.compare_digest` machen —
nie mit `==`.
