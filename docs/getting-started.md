# Installation und Entwicklung

## Lokale Demo

Voraussetzungen: Git und ein laufendes Docker Desktop mit Docker Compose. Die Demo benötigt keine eigene `.env` oder Python-Installation.

```sh
git clone https://github.com/FatihHayyar/wwf-polit-assistant.git
cd wwf-polit-assistant
docker compose -f docker-compose.demo.yml up --build -d
```

Öffnen: Anwendung unter `http://localhost:8081`, API-Dokumentation unter `http://localhost:8081/docs`, lokale E-Mails unter `http://localhost:8025`.

Beim Start werden Migrationen ausgeführt und eine leere Demo-Datenbank mit der mitgelieferten Stichprobe befüllt. Bereits vorhandene Daten bleiben erhalten. Es läuft kein täglicher Sync. Mailpit fängt E-Mails lokal ab.

```sh
docker compose -f docker-compose.demo.yml logs -f app
docker compose -f docker-compose.demo.yml down
```

`down` erhält das Datenbank-Volume. `down -v` löscht den Demo-Datenbestand und darf nur zum bewussten Zurücksetzen verwendet werden.

## Entwicklungsumgebung unter Windows

Python **3.13 oder neuer**, Git und PostgreSQL werden benötigt. Die folgenden Befehle gelten für PowerShell im Projektordner:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
docker compose up -d postgres
```

Die Kopie nur bei einer neuen Umgebung erstellen, damit eine vorhandene `.env` erhalten bleibt. Datenbankverbindung, einen eigenen JWT-Schlüssel und bei Bedarf SMTP sowie den Sync-Schlüssel nach dem [Konfigurationsleitfaden](configuration.md) setzen. Die Entwicklungsdatenbank ist vom Host auf Port **5433** erreichbar; im Container-Netzwerk gilt Port **5432**.

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Anwendung: `http://localhost:8000`; Swagger: `http://localhost:8000/docs`. Ohne aktivierte virtuelle Umgebung kann überall `.\.venv\Scripts\python.exe` statt `python` verwendet werden.

Migrationen erzeugen Tabellen und Indizes, aber keine parlamentarischen Inhalte. Auf grossen Beständen können Suchindex-Migrationen lange dauern. Für eine sofort befüllte Anwendung die separate Docker-Demo verwenden.

## Vollständiger Erstimport

Der Bootstrap ist für eine **frische Zieldatenbank** vorgesehen. Der Import kann vorhandene Tabellen mit `TRUNCATE ... RESTART IDENTITY` zurücksetzen. Bestehende Entwicklungs- oder Betriebsdatenbanken vorher sichern; für laufende Aktualisierungen den Sync verwenden.

```powershell
python scripts/bootstrap/download_openparldata.py --dry-run
python scripts/bootstrap/download_openparldata.py --workers 6
python scripts/bootstrap/import_normalized.py all
python -m scripts.seed_classification
python -m scripts.classify_affairs
python -m scripts.classify_entities
```

Auch `--dry-run` lädt das Exportmanifest und speichert es lokal; es lädt keine vollständigen Exporte. Der Import wählt den neuesten passenden lokalen Snapshot und verarbeitet Referenzdaten vor abhängigen Datensätzen. Bei mehrteiligen Imports werden abgeschlossene Dateien als Wiederaufnahmestand gespeichert. Ein anderer Snapshot oder fehlender Fortschrittsstand kann einen Tabellenreset auslösen. Download, Import und Klassifikation benötigen bei Millionen von Zeilen erheblich Zeit und Speicherplatz.

`scripts/bootstrap/validate_database.py` vergleicht mit historischen Sollzahlen des ursprünglichen Imports. Diese Zahlen eignen sich nicht als Aktualitätsprüfung eines später synchronisierten Bestands.

## Laufende Aktualisierung

```powershell
python -m scripts.sync.run_all
```

Der Runner kann externe Daten lesen, Datenbankinhalte ändern und nach erfolgreichem Abgleich E-Mails versenden. Für den täglichen Betrieb kann separat `python -m scripts.sync.scheduler` oder der Compose-Dienst `scheduler` gestartet werden. Details stehen unter [Betrieb](deployment.md) und [Monitoring](monitoring.md).
