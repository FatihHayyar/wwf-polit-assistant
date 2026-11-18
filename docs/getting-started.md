# Installation und Entwicklung

Diese Seite richtet sich an Entwickler. Schritt-für-Schritt-Anleitungen ohne Vorkenntnisse:
[Demo mit Docker](installation/1-demo-docker.md), [Demo ohne Docker und Git](installation/2-demo-ohne-docker.md) und [vollständige Installation](installation/3-vollinstallation.md).

## Entwicklungsumgebung unter Windows

Python **3.13 oder neuer**, Git und PostgreSQL werden benötigt. Die folgenden Befehle gelten für PowerShell im Projektordner:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
docker compose up -d postgres
```

`docker compose up -d --build` startet stattdessen PostgreSQL, Migrationen, API und Scheduler gemeinsam in Containern.

Die Kopie nur bei einer neuen Umgebung erstellen, damit eine vorhandene `.env` erhalten bleibt. Datenbankverbindung, einen eigenen JWT-Schlüssel und bei Bedarf SMTP sowie den Sync-Schlüssel nach dem [Konfigurationsleitfaden](configuration.md) setzen. Die Entwicklungsdatenbank ist vom Host auf Port **5433** erreichbar; im Container-Netzwerk gilt Port **5432**.

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Anwendung: `http://localhost:8000`; Swagger: `http://localhost:8000/docs`. Ohne aktivierte virtuelle Umgebung kann überall `.\.venv\Scripts\python.exe` statt `python` verwendet werden.

Migrationen erzeugen Tabellen und Indizes, aber keine parlamentarischen Inhalte. Auf grossen Beständen können Suchindex-Migrationen lange dauern. Für eine sofort befüllte Anwendung die [Demo](installation/1-demo-docker.md) verwenden.

## Vollständiger Erstimport

Der Bootstrap ist für eine **frische Zieldatenbank** vorgesehen. Der Import kann vorhandene Tabellen mit `TRUNCATE ... RESTART IDENTITY` zurücksetzen. Bestehende Entwicklungs- oder Betriebsdatenbanken vorher sichern; für laufende Aktualisierungen den Sync verwenden.

```powershell
python scripts/bootstrap/download_openparldata.py --dry-run
python scripts/bootstrap/download_openparldata.py --workers 6
python scripts/bootstrap/import_normalized.py all
python -m scripts.seed_classification
python -m scripts.rule_quality
python -m scripts.reclassify_rules --apply
python -m scripts.rule_backfill_status
```

Auch `--dry-run` lädt das Exportmanifest und speichert es lokal; es lädt keine vollständigen Exporte. Der Import wählt den neuesten passenden lokalen Snapshot und verarbeitet Referenzdaten vor abhängigen Datensätzen. Bei mehrteiligen Imports werden abgeschlossene Dateien als Wiederaufnahmestand gespeichert. Ein anderer Snapshot oder fehlender Fortschrittsstand kann einen Tabellenreset auslösen. Download, Import und Klassifikation benötigen bei Millionen von Zeilen erheblich Zeit und Speicherplatz.

Der neue Klassifikations-Backfill besitzt ohne `--apply` eine schreibgeschützte Vorschau. Seine Qualitätsschranke benötigt Git-Historie mit dem festgelegten Baseline-Commit; ZIP-Downloads ohne `.git` reichen dafür nicht. Themen und Regeln werden in `app/classification/taxonomy.json` bearbeitet. Nach Änderungen seeden und Prozesse neu starten; mit `--apply --force` bestehende Zuordnungen ausdrücklich erneuern. Vollständige Voraussetzungen und ältere Einzeljobs stehen in der [Konfiguration](configuration.md#regelbasierte-klassifikation).

`scripts/bootstrap/validate_database.py` vergleicht mit historischen Sollzahlen des ursprünglichen Imports. Diese Zahlen eignen sich nicht als Aktualitätsprüfung eines später synchronisierten Bestands.

## Laufende Aktualisierung

```powershell
python -m scripts.sync.run_all
```

Der Runner kann externe Daten lesen, Datenbankinhalte ändern und nach erfolgreichem Abgleich E-Mails versenden. Direkt nach dem Erstimport besitzt noch kein Bereich einen vollständigen Vergleich; der erste Lauf vergleicht deshalb jeden Bereich vollständig und dauert entsprechend lange. Danach lesen reguläre Läufe nur Änderungen. Einzelne Bereiche lassen sich ohne E-Mail-Versand über ihr Modul abgleichen, z. B. `python -m scripts.sync.agendas_sync` (Geschäfte: `scripts.sync.incremental_sync`). Für den täglichen Betrieb kann separat `python -m scripts.sync.scheduler` oder der Compose-Dienst `scheduler` gestartet werden. Details stehen unter [Betrieb](06-handover/deployment-guide.md) und [Synchronisierungsstrategie](monitoring.md#synchronisierungsstrategie).
