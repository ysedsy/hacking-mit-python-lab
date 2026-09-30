# Ordner 99 — Secret-Scanner (defensiv)

Die Aufgaben-Zeile „Passwörter/Secret-Keys aus GitHub ziehen und brute-forcen" zielt
auf **fremde** Repos und echte Fremd-Zugangsdaten — das ist **nicht** Teil dieses Labs
(fremde Systeme). Hier die **defensive** Variante mit derselben Lehre:

> **Finde deine eigenen geleakten Secrets, bevor es ein Angreifer tut.**

Das ist genau das Prinzip hinter `trufflehog` und `detect-secrets` (Ordner 07).

## Was das Skript macht
`scan_git_history.py` durchsucht den **kompletten Git-Verlauf** (`git log -p --all`) —
nicht nur den aktuellen Stand — nach Mustern wie Flask-`SECRET_KEY`, AWS/Google/GitHub/
Slack-Tokens, generischen `api_key=...`/`password=...` und privaten Schlüsseln.

Wichtig: Ein später **gelöschter** Key bleibt in der History und ist weiter abrufbar
(`git show <commit>`). Deshalb History scannen, nicht nur die Arbeitskopie.

## Nutzung
```powershell
python scan_git_history.py            # scannt das aktuelle Repo
python scan_git_history.py C:\pfad\zum\repo
```

Zum Ausprobieren: In Ordner 01/02 steht bewusst ein `SECRET_KEY = "dev-secret-change-me"`
im Code. Committe das und lass den Scanner laufen — er findet den Treffer.

## Wenn ein echtes Secret gefunden wird
1. **Rotieren** — der alte Wert gilt als kompromittiert.
2. **Aus der History entfernen** — `git filter-repo` oder BFG Repo-Cleaner
   (ein einfaches „neuer Commit, der es löscht" reicht **nicht**).
3. **Vorbeugen** — `.gitignore`, Secrets aus Umgebungsvariablen/Secret-Manager
   (siehe Ordner 07/13/14), und `detect-secrets` als **pre-commit**-Hook:
   ```bash
   pip install detect-secrets pre-commit
   detect-secrets scan > .secrets.baseline
   # .pre-commit-config.yaml -> hook "detect-secrets"
   ```

## Bezug zum Rest des Labs
- Ordner 13: schwacher/geleakter `SECRET_KEY` → Session-Forgery.
- Ordner 14: LFI liest `app.py` → `SECRET_KEY` im Quelltext.
- Ordner 07: `detect-secrets`/`bandit` in der CI.
Fazit: Secrets gehören **nie** in den Code oder die Git-History.
