# Änderungsprotokoll

Dieses Protokoll beginnt mit dem aktuellen Entwicklungsstand. Es rekonstruiert keine früheren Releases. Für die ältere Entwicklung gilt die Git-Historie; ein Versionswert in der API ist kein Nachweis eines veröffentlichten Release-Tags.

## Unveröffentlicht

### Demo (22. Oktober 2026)

- Der Demo-Start übernimmt die aktuelle Taxonomie und klassifiziert Datensätze anderer Klassifikator-Versionen neu. Die Stichprobe enthielt bisher Klassifikationen von `rule-based-v6`; dadurch wurden z. B. Fragen zum Wolf nicht erkannt.
- Quick Start weist auf den begrenzten Datenausschnitt hin und nennt Beispielfragen, die in der Demo Treffer liefern.

### Fragen in natürlicher Sprache (22. Oktober 2026)

- «im Kanton …» löst kein zweites Thema (öffentliche Hand) mehr aus; «Biodiversität im Kanton Zürich» setzt wieder Thema und Kanton statt eines Suchbegriffs.
- Italienische Geschäftstypen («mozioni», «interpellanze», «postulati», «interrogazioni»).
- Monatsnamen in vier Sprachen: «im September 2026», «seit März 2025», «en février».

### Anforderungen von WWF (21. Oktober 2026)

- Mehrere benannte Abonnements je Konto (bis zu zehn) mit Themen, Kantonen, Geschäftstypen, Stichwörtern und Bereichen; bestehende Abonnements werden migriert (`20261021_subscription_profiles`).
- Geschäftstyp als Such- und Abonnementfilter.
- Dialogorientierte Abfrage: `POST /api/v1/ask` und Fragefeld in der Oberfläche; Speichern einer Frage als Abonnement.
- Klassifikation `rule-based-v8`: Rechenzentren und Grossverbraucher getrennt, Vorbildfunktion der öffentlichen Hand unter Klima & Energie, Ausschluss- und Infix-Regeln, Titelbeschränkung für öffentliche Akteure. Zweites blindes Prüfset; Recall 0.36 → 0.67.

### Synchronisierung (21. Oktober 2026)

- Gemeinsamer Ablauf für alle neun Bereiche: Änderungen, Traktandenfenster, neue IDs, fehlende IDs; vollständige Vergleiche in festen Abständen (`last_full_scan_at`, Migration `20261021_full_scan_schedule`).
- Checkpoints werden in allen Bereichen fortgeschrieben.
- Täglicher Start um 04:30 Europe/Zurich, konfigurierbar über `SYNC_TIME`.
- Veraltete Skripte entfernt (`affairs_sync`, `incremental_affairs`, `snapshot_diff`, `download_snapshot`, `dataset_config`, `db_upsert`, `repair_latest`).

### Betrieb (21. Oktober 2026)

- Container läuft als unprivilegierter Benutzer; Healthcheck der API in Compose.
- Konkrete Azure-Zielarchitektur dokumentiert.

### Sicherheit (21. Oktober 2026)

- Registrierung und Anmeldung antworten unabhängig vom Kontostatus identisch; E-Mails werden im Hintergrund versendet.
- Ratenbegrenzung pro Client, Zieladresse und Konto für alle Endpunkte, die E-Mails senden oder Tokens annehmen.
- E-Mail-Links öffnen eine Bestätigungsseite; Tokens werden erst per POST derselben Herkunft verbraucht.
- Abmelden widerruft alle ausgestellten Tokens (Migration `20261021_session_version`).
- Sicherheits-Header inklusive Content-Security-Policy; PostgreSQL in `docker-compose.yml` nur an `127.0.0.1` gebunden; Compose startet Migration, API und Scheduler.

### Demo und Oberfläche (21. Oktober 2026)

- Testbenachrichtigung in der Demo: fiktives Geschäft durchläuft Klassifikation, Relevanzprüfung, Abonnementabgleich und Versand; Anleitung auf der Startseite und CLI-Skript.
- Frontend in Module aufgeteilt (`core`, `search`, `detail`, `account`, `subscriptions`, `ask`, `app`), Stylesheet formatiert.

### Qualitätssicherung (21. Oktober 2026)

- Blind annotiertes Prüfset mit 300 Geschäften und Auswertungsskript `scripts.evaluate_holdout`.
- 33 neue Tests (API-Sicherheit, Demo-Ablauf, Prüfset-Integrität); GitHub-Actions-CI mit ruff, Migrationen auf PostgreSQL 17 und Docker-Build.
- Repository bereinigt (Backup-Kopien, PowerShell-Cache, Exportdateien); Nachweise unter `docs/05-testing/evidence/`.
- Dokumentation vollständig deutsch.


### Dokumentation

- Deutscher Dokumentationsindex mit Installation, Bedienung, Konfiguration, Architektur, API, Tests, Betrieb, Fehlerbehebung und Lizenzstatus.
- Beitrags-, Sicherheits- und Supporthinweise sowie GitHub-Issue- und Pull-Request-Vorlagen.
- README an die vorhandenen Bootstrap-Skripte und aktuelle Zugriffskontrolle angepasst.

### Anwendung

- Optionale Google-Anmeldung und bestätigbare Benachrichtigungsadressen für bis zu zehn Empfänger.
- Einzelinhalte werden in der Abonnementverwaltung beobachtet; Detailansichten besitzen einen beim Scrollen erreichbaren Schliessen-Bereich.
- Breitere Ergebnislisten, abgestimmte Kontoschaltflächen und dauerhaft erreichbare Aktionen im Verwaltungsdialog.
- Sichtbare Speicherbestätigung und aktualisierte Asset-Auslieferung gegen veraltete Browserdateien.
- Benachrichtigungen besitzen getrennte Klartext-/HTML-Layouts, lesbare Betreffzeilen und eindeutig beschriftete Links.
- Änderungsverläufe zeigen Inhaltstitel und öffnen vorhandene Einträge; gleiche Dokumentzuordnungen werden zusammengefasst, unterschiedliche Quellen und Änderungen bleiben erhalten.
- Beschädigte Unicode-Akzente und Fragezeichen als Verknüpfungsseparatoren korrigiert.

### Synchronisierung

- Ereignismapping berücksichtigt skalare und übersetzte Quelltitel.
- Dokumentenabgleich prüft zusätzlich Bestands- und ID-Lücken unter Berücksichtigung mehrfacher Zuordnungen.
- Fehlgeschlagene Gesamtläufe melden die Dataset-Ursache; Diagnosewerkzeuge unterstützen Quellstichproben und gezielte Reparatur.
- Atomare Statusdateien tolerieren vorübergehende Windows-Dateisperren mit begrenzten Wiederholungen und unabhängigen temporären Dateien.
- Fehlgeschlagener E-Mail-Versand behält seinen differenzierten Laufstatus und führt zu einem erfolglosen CLI-/Scheduler-Ergebnis.
- Betreiber können die zwei grossen experimentellen Suchindizes beim Migrieren explizit zurückstellen und später separat aufbauen.
- Der Compose-Scheduler teilt persistente Lauf-/Jobdateien mit dem Host und erhält die konfigurierte STARTTLS-Einstellung.

Diese Einträge beschreiben Änderungen im Arbeitsstand und behaupten keine bereits veröffentlichte GitHub-Version.
