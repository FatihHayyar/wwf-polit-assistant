# Änderungsprotokoll

Dieses Protokoll beginnt mit dem aktuellen Entwicklungsstand. Es rekonstruiert keine früheren Releases. Für die ältere Entwicklung gilt die Git-Historie; ein Versionswert in der API ist kein Nachweis eines veröffentlichten Release-Tags.

## Unveröffentlicht

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
