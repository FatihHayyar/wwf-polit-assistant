# Mitwirken

Danke für Beiträge zum WWF Polit-Assistant. Neue Mitwirkende beginnen mit der [Projektübersicht](README.md), [Installation](docs/getting-started.md) und [Architektur](docs/architecture.md).

## Ablauf

1. Für einen Fehler oder eine grössere Erweiterung ein GitHub-Issue mit konkretem Verhalten und Ziel anlegen. Sicherheitsprobleme nach [SECURITY.md](SECURITY.md) behandeln.
2. Einen eigenen Branch erstellen, zum Beispiel `docs/setup` oder `fix/document-mapping`.
3. Änderungen klein und nachvollziehbar halten. Bestehende Konventionen und mehrsprachige UI-Texte beachten.
4. Betroffene Prüfungen aus [docs/testing.md](docs/testing.md) ausführen und relevante Dokumentation aktualisieren.
5. Einen Pull Request mit Problem, Änderung, Prüfergebnis und offenen Risiken erstellen. Die bereitgestellte Vorlage verwenden.

## Anforderungen an Änderungen

Schemaänderungen benötigen eine Alembic-Migration. Bei Quellmapping und Sync insbesondere fehlende Felder, Übersetzungsvarianten, Wiederaufnahme und unveränderte Datensätze berücksichtigen. Technische Änderungen sollen keine unbeabsichtigten Monitoring-E-Mails erzeugen.

Frontend-Texte für Deutsch, Französisch, Italienisch und Englisch in `app/web/i18n.js` ergänzen. Bei Layoutänderungen schmale Bildschirme, lange Texte und Scrollverhalten prüfen. Neue Abhängigkeiten nur mit nachvollziehbarer Begründung hinzufügen.

Keine `.env`, Passwörter, personenbezogenen Produktionsdaten, vollständigen Raw-Exporte, Backups oder privaten Tokens committen. Integrationstests gegen isolierte Datenbanken und Mailpit durchführen. Bestehende manuelle Sync-Läufe anderer Personen nicht unterbrechen.

Die [Softwarelizenz](docs/licensing.md) ist noch offen. Beiträge erteilen nicht automatisch eine neue Projektlizenz. Fachliche Änderungen an WWF-Taxonomie und Benachrichtigungsregeln mit den Verantwortlichen abstimmen.

## Zusammenarbeit

Sachlich und respektvoll diskutieren, Kritik auf Verhalten und Code beziehen und unterschiedliche Erfahrung berücksichtigen. Persönliche Angriffe, Diskriminierung und die Veröffentlichung privater Daten haben keinen Platz in der Zusammenarbeit. Konflikte mit den Projektverantwortlichen klären.
