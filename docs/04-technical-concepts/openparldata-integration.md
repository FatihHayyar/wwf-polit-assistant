# OpenParlData-Integration

Der Erstimport und der laufende Sync sind unterschiedliche Verfahren. Bootstrap lädt Exporte und importiert sie normalisiert; er kann bestehende Tabellen zurücksetzen. Deshalb nur eine frische Zieldatenbank oder eine bewusst gesicherte Neuinitialisierung verwenden. Die [Installation](../getting-started.md) enthält die tatsächlichen Skripte.

## Laufende Aktualisierung

| Dataset | Verfahren |
|---|---|
| `affairs`, `meetings` | Aktualisierungscursor und Checkpoints |
| `documents` | Aktualisierungscursor mit ergänzender Bestands-/ID-Prüfung |
| `agendas`, `votings`, `events`, `texts`, `groups`, `interests` | Stabiles Inventar und API-Inhaltsvergleich bei unzuverlässigen Zeitstempeln |

Das Inventar stammt aus Exporten und wird mit aktuellen API-IDs ergänzt. API-Inhalte werden batchweise verarbeitet; Quelllimits und zeitweise Fehler erfordern Wiederholungen. `texts` besitzt spezielle Quellfiltergrenzen, weshalb der Bezug über Geschäftsgruppen erfolgt. Ein Bestandsvergleich kann viele unveränderte Inhalte lesen und dauert nicht immer so kurz wie ein Cursorlauf.

## Korrektheit und Wiederaufnahme

Mapping muss fehlende Felder, skalare Werte und Übersetzungsobjekte berücksichtigen. Dokumente können mehrere Zuordnungszeilen pro Quell-ID besitzen. Cursor allein reichen nicht für nachträglich eingestellte Inhalte mit älteren Zeitstempeln. Erfolgreiche Batches werden committed, fehlerhafte Fortschritte nicht pauschal als abgeschlossen behandelt.

Der Runner verwendet einen globalen Advisory-Lock. Checkpoints und Jobdateien halten den Wiederaufnahmestand. Ein fehlgeschlagenes Dataset lässt den Gesamtjob fehlschlagen und den Versand ausstehend. Eine bereits committed Änderung wird dabei nicht zurückgerollt.

## Diagnose

`python -m scripts.sync.audit_latest` erstellt einen lesenden Vergleich aktueller Quellstichproben und lokaler Daten. Dieser Audit beweist keine vollständige historische Abdeckung. Gezielte Reparaturen sind schreibende Eingriffe und benötigen eine gesicherte Diagnose; sie ersetzen keine reguläre Wiederaufnahme.

Quellen: implementierte Module in `scripts/sync/`, [OpenParlData-API](https://api.openparldata.ch/) und [Exportmanifest](https://files.openparldata.ch/exports/index.json). Historische Prüfergebnisse bleiben im [Review](../daily-review-2026-10-11.md) unverändert eingeordnet.
