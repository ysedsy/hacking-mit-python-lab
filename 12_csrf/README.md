# Ordner 12 — CSRF (Cross-Site Request Forgery) + Fix

CSRF = der Angreifer bringt den **eingeloggten** Browser des Opfers dazu, eine Aktion
auszuführen. Der Browser hängt den Session-Cookie automatisch an — das Opfer „handelt",
ohne es zu merken (z. B. durch Anklicken eines Links/Bilds in einer E-Mail oder via XSS).

## Die Lücke
`/set-bio?bio=...` ist ein **State-Change per GET ohne CSRF-Token**. Das reicht schon
für einen Angriff per `<img>`.

## Angriff
1. Im Cowboy-Forum einloggen (Session aktiv).
2. `csrf_attack.html` im selben Browser öffnen (Doppelklick / `file://`).
3. Das unsichtbare `<img>` feuert `GET /set-bio?bio=CSRF war hier` mit dem
   Session-Cookie des Opfers → die Bio ist geändert, ohne dass das Opfer etwas tat.
4. Kontrolle unter `/profile`.

## Der Fix — `form.hidden_tag()`
- Änderungen nur per **POST** über ein **WTForms-Formular** (`/profile`).
- `form.hidden_tag()` rendert das **CSRF-Token**; `form.validate_on_submit()` prüft es.
- Flask-WTF lehnt POSTs ohne gültiges Token mit **400** ab. Die Angreifer-Seite kennt
  das (pro Session zufällige) Token nicht → Angriff scheitert.

Zusätzlich helfen: `SameSite=Lax`-Cookie (schon in Ordner 11 gesetzt) und Vermeidung
von state-changing GETs.

## Testen
```powershell
pip install -r requirements.txt
python seed.py
python app.py
```
- Angriff über `csrf_attack.html` funktioniert gegen `/set-bio` (GET).
- Der POST auf `/profile` ohne Token (z. B. Variante B in der Angriffsdatei) → **400**.

## Verbindung
CSRF + XSS (Ordner 10) sind eng verwandt: per XSS kann ein Angreifer den CSRF-Request
direkt im Opfer-Browser auslösen (und den Token sogar auslesen). Deshalb: XSS-Fix
(Ordner 11) **und** CSRF-Token gehören zusammen.
