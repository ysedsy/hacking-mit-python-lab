# challenge_ssti/ — Übungs-Ziel: SSTI → RCE

Bewusst verwundbare Mini-Flask-App. Der „Visitenkarten-Generator" baut deinen
Namen direkt in einen Jinja2-**Template-String** und rendert ihn
(`render_template_string` auf Nutzereingabe) → `{{ ... }}` wird serverseitig
ausgewertet, bis hin zur Code-Ausführung.

> Nur gegen die eigene/autorisierte Instanz. Standard-Bind `127.0.0.1`; für die
> Nachbar-Challenge im Kurs-Netz `HOST=0.0.0.0` setzen.

## Dateien
- `app.py` — die verwundbare App (`python app.py` → `http://127.0.0.1:5003`)
- `challenge.md` — die Aufgabenstellung

## Schnellstart
```powershell
pip install -r requirements.txt
python app.py
# Name = {{7*7}}                                         -> 49
# Name = {{ config }}                                    -> Flask-Config
# Name = {{ lipsum.__globals__.os.popen('whoami').read() }}  -> Befehl ausgeführt
```

**Fix:** Nutzereingaben nie in Template-Text stecken; feste Templates + Werte als
Kontext-Variable (`render_template_string("Hallo {{ name }}", name=name)`).
