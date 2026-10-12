# Fehlerbehebung

## Sync endet mit „Successful: 8/9“

Mindestens ein Dataset ist fehlgeschlagen. Das abschliessende Fehlerresultat bedeutet nicht, dass alle Daten zurückgerollt wurden: erfolgreiche Batches bleiben gespeichert. Benachrichtigungen bleiben bis zu einem erfolgreichen Wiederanlauf ausstehend. Die Freigabe des Sync-Locks am Ende ist normal.

Im Bericht `logs/sync_<run_id>.json` und im Laufprotokoll das fehlgeschlagene Dataset und dessen ursprüngliche Fehlermeldung suchen. Ursache beheben und den Job fortsetzen; bereits abgeschlossene Stufen werden berücksichtigt. Bei API-Läufen kann `/api/v1/sync/runs/{run_id}/resume` mit dem Sync-Schlüssel verwendet werden. Checkpoints nicht ohne Diagnose löschen.

## Ein Lauf ist schnell und meldet keine Änderungen

Das kann korrekt sein, beweist aber allein keine vollständige Datenabdeckung. `python -m scripts.sync.audit_latest` vergleicht eine aktuelle Quellstichprobe mit dem lokalen Bestand und schreibt `logs/latest_source_audit.json`. Das Werkzeug benötigt Quellzugang und Datenbanklesezugriff; es repariert keine Datensätze. Eine Stichprobe ist keine vollständige Bestandsprüfung.

Bei Dokumenten sind Anzahl lokaler Zeilen und Anzahl eindeutiger Quell-IDs verschieden. Mehrfachzuordnungen dürfen nicht als fehlende Dokumente gezählt werden. Der Dokumenten-Sync prüft zusätzlich Bestands- und ID-Lücken; zuverlässige Zeitstempel allein reichen bei nachträglich eingestellten Inhalten nicht immer aus.

## Oberfläche zeigt einen alten Stand

Prüfen, ob der laufende Server aus dem bearbeiteten Projektordner gestartet wurde. Nach Backend-Änderungen den API-Prozess neu starten; bei Docker neu bauen. Die aktuelle Anwendung liefert versionsabhängige Asset-URLs und deaktiviert den Browsercache für HTML/Assets. Die tatsächlich geladenen Dateinamen in den Browser-Entwicklerwerkzeugen prüfen.

## Keine Anmelde- oder Monitoring-E-Mail

In der Demo zuerst Mailpit unter `http://localhost:8025` öffnen. Lokal SMTP-Konfiguration und API-Protokoll prüfen. `VERIFICATION_BASE_URL` muss auf die verwendete Anwendung zeigen. Abgelaufene Links durch einen neuen Anmeldeversuch ersetzen.

Für Monitoring zusätzlich prüfen: verifiziertes Konto, aktive Filter oder Watches, bestätigte Empfänger, passende relevante Änderung und erfolgreicher vollständiger Sync. Eine Änderung technischer Metadaten muss keine Nachricht erzeugen. Bei SMTP-Fehlern bleiben ausstehende Nachrichten erhalten; Provider-Limits können den Versand unterbrechen.

## Google-Schaltfläche fehlt

Beide Google-Variablen müssen im API-Prozess gesetzt sein. API neu starten und `/api/v1/auth/providers` prüfen. Compose reicht beliebige lokale `.env`-Werte nicht automatisch an Container weiter. Callback-URI muss einschliesslich Port und Pfad exakt zur Konfiguration passen.

## Migration dauert lange oder neue Tabelle fehlt

`python -m alembic current` und `python -m alembic heads` vergleichen. Indexaufbau auf grossen Tabellen kann lange dauern. Den zuständigen PostgreSQL-Prozess und dessen Fortschritt untersuchen, bevor etwas abgebrochen wird; keine fremden Sync- oder DB-Prozesse beenden. Tabellen nicht manuell als Ersatz für reguläre Migrationen anlegen.

Die beiden grossen experimentellen Suchindizes können für einen vorhandenen vollständigen Spiegel explizit zurückgestellt werden; der [Deployment-Leitfaden](06-handover/deployment-guide.md) beschreibt die Option und ihren späteren Aufbau. Das ist kein Überspringen erforderlicher Tabellenmigrationen.

## Windows meldet beim Checkpoint „Access is denied“

Ein kurzzeitig geöffneter Statuspfad kann die atomare Dateiersetzung blockieren, beispielsweise durch Leser oder einen Scanner. Der Writer verwendet eigene temporäre Dateien und wiederholt kurzzeitige Zugriffsfehler begrenzt. Die letzte gültige Datei bleibt bis zur erfolgreichen Ersetzung erhalten. Dauerhafte Berechtigungsfehler werden weiterhin gemeldet; danach Dateizugriff prüfen und den Job wiederaufnehmen, statt seinen Fortschritt zu löschen.

## Leere Listen nach lokaler Installation

Migrationen laden keine Quellinhalte. Die Docker-Demo verwenden oder den Erstimport aus der [Installationsanleitung](getting-started.md) gegen eine frische Datenbank durchführen. Die historischen Sollzahlen aus `validate_database.py` sind keine aktuellen Sync-Sollwerte.

## Einen Fehler melden

Siehe [Support](../SUPPORT.md). Versionsstand, Startart, betroffenen Bereich, reproduzierbare Schritte und bereinigte Fehlermeldung angeben. Keine SMTP-Zugangsdaten, JWTs, Bestätigungslinks oder privaten Adressen veröffentlichen.
