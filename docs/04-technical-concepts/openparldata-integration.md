# OpenParlData-Integration

Der Erstimport und der laufende Sync sind unterschiedliche Verfahren. Bootstrap lädt Exporte und importiert sie normalisiert; er kann bestehende Tabellen zurücksetzen. Deshalb nur eine frische Zieldatenbank oder eine bewusst gesicherte Neuinitialisierung verwenden. Die [Installation](../getting-started.md) enthält die tatsächlichen Skripte.

## Laufende Aktualisierung

Die OpenParlData-API bietet Sortierung (`sort_by`), `offset`/`limit` mit einer Grenze von 100'000, `exclude_null` sowie funktionierende, aber undokumentierte ID-Filter; einen Filter nach Änderungsdatum gibt es nicht, und Traktanden besitzen kein `updated_at`. Die täglichen Exporte entstehen gegen 02:05–02:18 UTC.

Alle neun Bereiche verwenden deshalb denselben Ablauf (`scripts/sync/entity_sync.py`):

| Phase | Verfahren | Bereiche |
|---|---|---|
| Änderungen | Sortierung nach `-updated_at` ohne Nullwerte bis zum Checkpoint | alle ausser Traktanden |
| Zeitfenster | Sitzungsdatum ±60 Tage | Traktanden |
| Neue IDs | Sortierung nach `-id` bis zur höchsten lokalen ID | alle |
| Fehlende IDs | nur bei Lücke zwischen Quell- und lokaler Anzahl; Dokumente über gezielte ID-Abfragen, Texte über Geschäftsgruppen | alle |
| Vollständiger Vergleich | ID-Inventar aus dem Export, Inhalte aus der Live-API; in festen Intervallen (7–30 Tage, Dokumente nur auf Anforderung) | alle |

API-Inhalte werden seitenweise verarbeitet und je Seite committed; Quelllimits und zeitweise Fehler erfordern Wiederholungen. `texts` besitzt spezielle Quellfiltergrenzen, weshalb der Bezug über Geschäftsgruppen erfolgt. Details: [Synchronisierungsstrategie](../monitoring.md#synchronisierungsstrategie).

## Korrektheit und Wiederaufnahme

Mapping muss fehlende Felder, skalare Werte und Übersetzungsobjekte berücksichtigen. Dokumente können mehrere Zuordnungszeilen pro Quell-ID besitzen. Cursor allein reichen nicht für nachträglich eingestellte Inhalte mit älteren Zeitstempeln. Erfolgreiche Batches werden committed, fehlerhafte Fortschritte nicht pauschal als abgeschlossen behandelt.

Der Runner verwendet einen globalen Advisory-Lock. Checkpoints und Jobdateien halten den Wiederaufnahmestand. Ein fehlgeschlagenes Dataset lässt den Gesamtjob fehlschlagen und den Versand ausstehend. Eine bereits committed Änderung wird dabei nicht zurückgerollt.

## Diagnose

`python -m scripts.sync.audit_latest` erstellt einen lesenden Vergleich aktueller Quellstichproben und lokaler Daten. Dieser Audit beweist keine vollständige historische Abdeckung. Gezielte Reparaturen sind schreibende Eingriffe und benötigen eine gesicherte Diagnose; sie ersetzen keine reguläre Wiederaufnahme.

Quellen: implementierte Module in `scripts/sync/`, [OpenParlData-API](https://api.openparldata.ch/) und [Exportmanifest](https://files.openparldata.ch/exports/index.json). Historische Prüfergebnisse bleiben im [Review](../daily-review-2026-10-11.md) unverändert eingeordnet.
