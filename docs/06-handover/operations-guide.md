# Betriebsleitfaden

Der Betreiber benötigt Datenbank, API, genau einen zuständigen Scheduler, SMTP und persistente Jobdateien. Die konkrete Azure-Umgebung ist noch abzustimmen. [Deployment](deployment-guide.md), [Konfiguration](../configuration.md) und [Fehlerbehebung](../troubleshooting.md) ergänzen diesen Leitfaden.

## Regelbetrieb

Der separat gestartete Scheduler führt den Runner täglich um 03:00 Europe/Zurich aus. Alternativ ist `python -m scripts.sync.run_all` ein manueller Lauf. Die API kann einen geschützten Hintergrundlauf starten; diese Operationen benötigen `X-Sync-API-Key`, keine gewöhnliche Benutzeranmeldung.

`/health` bestätigt nur die DB-Verbindung. Zusätzlich letzten erfolgreichen vollständigen Sync, Dataset-Fehler, ausstehende Zustellungen, Speicherbedarf und SMTP-Probleme kontrollieren. Lokale JSON-Laufberichte ersetzen keine zentrale Betriebsalarmierung.

## Fehler und Wiederaufnahme

Bei 8/9 erfolgreichen Datasets das fehlerhafte Dataset im Bericht untersuchen. Bereits committed Daten bleiben erhalten. Ursache beheben und denselben Job über den vorgesehenen Wiederaufnahmepfad fortsetzen. Checkpoints oder Jobdateien nicht ohne Diagnose löschen. Fremde manuelle Läufe nicht unterbrechen.

Abbruchanforderungen werden vom Runner verarbeitet; sie machen bereits abgeschlossene Commits oder versandte E-Mails nicht rückgängig. API-Jobstatus und Jobdateien müssen über Neustarts hinaus erhalten bleiben.

## Sicherung, Update und Kontrolle

Datenbankbackup und Restore getrennt testen. Vor einer neuen Version Migrationen auf einer repräsentativen Kopie prüfen; grosse Suchindizes können lange benötigen. Danach Code, API und Scheduler mit abgestimmter Konfiguration starten. Die Löschung eines Demo-Volumes ist kein Backupverfahren.

Keine produktiven Zugangsdaten oder Empfängerlisten in GitHub-Issues ablegen. Betriebsverantwortung, Aufbewahrung und Alarmierung werden vor Übergabe festgelegt. Offen bleiben organisatorische Authentifizierung, SMTP und tatsächlicher Azure-/Restore-Nachweis.
