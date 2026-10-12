# Betrieb und Bereitstellung

Die vorhandenen Compose-Dateien sind lokale Entwicklungs- und Demo-Konfigurationen. Ein validiertes Azure- oder anderes Produktionsdeployment ist noch nicht vorhanden.

## Prozessrollen

| Prozess | Start / Aufgabe |
|---|---|
| API | `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Migrationen | `python -m alembic upgrade head`, vor dem Start neuer Anwendungsversionen |
| Manueller Abgleich | `python -m scripts.sync.run_all` |
| Scheduler | `python -m scripts.sync.scheduler`, täglich 03:00 Europe/Zurich |
| Datenbank | PostgreSQL 17 mit persistentem Speicher |
| E-Mail-Dienst | Konfigurierter SMTP-Server; lokal Mailpit |

Das Dockerfile startet standardmässig den Scheduler. Für den API-Dienst den Startbefehl überschreiben. Nur eine verantwortliche Scheduler-Instanz betreiben. Der globale Sync-Lock verhindert konkurrierende Runner; er ersetzt keine Deployment-Koordination. API-gestartete Jobs hängen am auslösenden Prozess und sind kein externer dauerhafter Jobdienst.

## Vor einer Bereitstellung

Echte Secrets über den Secret Store der Zielumgebung setzen und feste Demo-Zugangsdaten ersetzen. Die öffentliche `VERIFICATION_BASE_URL` muss stimmen; HTTPS und eine geeignete Reverse-Proxy-Konfiguration sind für öffentlich erreichbare Kontofunktionen nötig. SMTP-Zugang, Absender und Versandlimits mit Testempfängern prüfen.

Datenbank, `logs/` und Jobdateien unter `logs/sync_jobs/` persistent halten. Eine Wiederaufnahme benötigt sowohl den DB-Checkpoint als auch die zugehörigen Dateien. Container-Neustarts ohne persistentes Jobverzeichnis können diese verlieren. Zentrale Logs, Fehleralarmierung und Datenschutzanforderungen sind noch für die Zielumgebung umzusetzen.

## Aktualisierung und Migrationen

Vor Änderungen einen Datenbank-Backup erstellen und Wiederherstellung in einer getrennten Umgebung prüfen. Migrationen zuerst auf einer repräsentativen Testkopie ausführen. Insbesondere Suchindizes auf grossen Tabellen können viel Zeit und Speicher benötigen.

Migrationen koordiniert ausführen und ihren Abschluss mit `python -m alembic current` prüfen. Danach API und Scheduler mit derselben Codeversion und Konfiguration starten. In der Demo startet das Startskript Migrationen automatisch; dieses Verhalten ist keine allgemeine Produktionsstrategie.

Ein Code-Rollback nach einer Schemaänderung muss separat geprüft werden. Datenbankänderungen oder bereits versandte E-Mails werden durch einen Git-Rollback nicht zurückgenommen.

## Sicherung und Wiederherstellung

PostgreSQL-Werkzeuge `pg_dump` und `pg_restore` in einer zur Serverversion passenden Version verwenden. Ein Custom-Format-Backup kann mit `pg_dump --format=custom --file=backup.dump --dbname=<VERBINDUNG>` erstellt werden; Passwörter nicht in geteilten Befehlen oder Logs offenlegen.

Zusätzlich Konfiguration über den Secret Store sichern und Jobmanifeste sowie Checkpoints gemeinsam berücksichtigen. Backups und personenbezogene Job-/Versanddaten gehören nicht ins Repository. Aufbewahrung und Zugriffsrechte mit dem Betreiber festlegen.

Eine Wiederherstellung zuerst in eine neue Datenbank testen, SMTP deaktivieren beziehungsweise auf einen Testserver richten und API, Datenzahlen, Migrationen und Abonnements prüfen. Erst danach den Wiederanlauf planen. Ein vollständiger Bootstrap-Import ist kein Ersatz für die Sicherung von Konten und Abonnements.

## Kontrolle

`GET /health` prüft die Datenbankverbindung. Der Endpunkt bestätigt weder Quellaktualität noch SMTP-Zustellung. Letzten erfolgreichen Lauf, Dataset-Fehler, Warteschlange und Speicherverbrauch separat überwachen. Bei fehlerhaftem Sync gilt die [Fehlerbehebung](../troubleshooting.md).
