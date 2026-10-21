# Betriebsleitfaden

Der Betreiber benötigt Datenbank, API, genau einen zuständigen Scheduler, SMTP und persistente Jobdateien. Die vorgesehene Azure-Zielarchitektur beschreibt die [Azure-Integration](../03-architecture/azure-integration.md). [Deployment](deployment-guide.md), [Konfiguration](../configuration.md) und [Fehlerbehebung](../troubleshooting.md) ergänzen diesen Leitfaden.

## Regelbetrieb

Themen und Regeln werden in `app/classification/taxonomy.json` gepflegt. Nach Änderungen `python -m scripts.seed_classification` ausführen und API/Scheduler neu starten; Container ohne Quellcode-Mount benötigen ein neues Image. Bestehende Zuordnungen anschliessend ausdrücklich mit `python -m scripts.reclassify_rules --apply --force` erneuern. Der Job prüft das Entwicklungsset, verwendet die Sync-Sperre und speichert Batches zur Wiederaufnahme. Ohne `--apply` ist die Neuberechnung schreibgeschützt. Er verändert Klassifikationen/Evidenz, keine Quellen oder Benachrichtigungen. `python -m scripts.rule_backfill_status` bestätigt danach fehlende/veraltete Zuordnungen. Details: [Konfiguration](../configuration.md#regelbasierte-klassifikation).

Der separat gestartete Scheduler führt den Runner täglich um `SYNC_TIME` aus (Standard 04:30 Europe/Zurich, nach den OpenParlData-Exporten gegen 02:15 UTC). Ein regulärer Lauf liest je Bereich nur Änderungen, neue und fehlende IDs und dauert deshalb meist Minuten; an Tagen mit fälligem vollständigem Vergleich (Intervalle in der [Synchronisierungsstrategie](../monitoring.md#synchronisierungsstrategie)) entsprechend länger. `sync_checkpoints.last_full_scan_at` zeigt den letzten vollständigen Vergleich je Bereich. Alternativ ist `python -m scripts.sync.run_all` ein manueller Lauf. Die API kann einen geschützten Hintergrundlauf starten; diese Operationen benötigen `X-Sync-API-Key`, keine gewöhnliche Benutzeranmeldung.

Der Entwicklungs-Compose-Scheduler bindet `./logs` nach `/app/logs` ein. Dadurch bleiben Jobdateien beim Ersetzen des Containers erhalten und die lokale API kann dessen Laufberichte lesen. Bei einer bestehenden Installation vor dem ersten Umstellen auf diesen Mount alte Container-Logs separat sichern. Die SMTP-STARTTLS-Einstellung wird ebenfalls an den Scheduler durchgereicht.

`/health` bestätigt nur die DB-Verbindung. Zusätzlich letzten erfolgreichen vollständigen Sync, Dataset-Fehler, ausstehende Zustellungen, Speicherbedarf und SMTP-Probleme kontrollieren. Lokale JSON-Laufberichte ersetzen keine zentrale Betriebsalarmierung.

## Fehler und Wiederaufnahme

Bei 8/9 erfolgreichen Datasets das fehlerhafte Dataset im Bericht untersuchen. Bereits committed Daten bleiben erhalten. Ursache beheben und denselben Job über den vorgesehenen Wiederaufnahmepfad fortsetzen. Checkpoints oder Jobdateien nicht ohne Diagnose löschen. Fremde manuelle Läufe nicht unterbrechen.

Abbruchanforderungen werden vom Runner verarbeitet; sie machen bereits abgeschlossene Commits oder versandte E-Mails nicht rückgängig. API-Jobstatus und Jobdateien müssen über Neustarts hinaus erhalten bleiben.

## Sicherung, Update und Kontrolle

Datenbankbackup und Restore getrennt testen. Vor einer neuen Version Migrationen auf einer repräsentativen Kopie prüfen; grosse Suchindizes können lange benötigen. Danach Code, API und Scheduler mit abgestimmter Konfiguration starten. Die Löschung eines Demo-Volumes ist kein Backupverfahren.

Keine produktiven Zugangsdaten oder Empfängerlisten in GitHub-Issues ablegen. Betriebsverantwortung, Aufbewahrung und Alarmierung werden vor Übergabe festgelegt. Offen bleiben organisatorische Authentifizierung, SMTP und tatsächlicher Azure-/Restore-Nachweis.
