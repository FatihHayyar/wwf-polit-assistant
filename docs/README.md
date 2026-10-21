# Projektdokumentation

**Stand: 21. Oktober 2026.** Entwicklungs-MVP; technische Umsetzung, WWF-Abnahme und Betriebsfreigabe werden getrennt geführt. Der lokale Stand steht im [Aufgabenstand](01-project-management/current-status.md), die aktuelle Messung der Klassifikation in der [Prüfset-Auswertung](05-testing/evidence/holdout-evaluation.md). [GitHub-Tracking](01-project-management/github-tracking.md) dokumentiert den bisherigen externen Tracking-Stand.

## 01 – Projektmanagement

- [Aktueller Aufgabenstand und erledigte Prüfungen](01-project-management/current-status.md)
- [Projektplan](01-project-management/project-plan.md)
- [Scope und Prioritäten](01-project-management/scope-and-priorities.md)
- [Risiken](01-project-management/risk-register.md)
- [Entscheidungen](01-project-management/decision-log.md)
- [Sitzungsnotizen und Vorlagen](01-project-management/meeting-notes/README.md)
- [GitHub-Issues, Milestones und Projektübersicht](01-project-management/github-tracking.md)

## 02 – Anforderungen

- [Anforderungen](02-requirements/requirements.md)
- [Anwendungsfälle](02-requirements/use-cases.md)
- [Akzeptanzkriterien](02-requirements/acceptance-criteria.md)

## 03 – Architektur

- [Systemarchitektur](03-architecture/system-architecture.md)
- [Technologieentscheidungen](03-architecture/technology-decisions.md)
- [Datenmodell](03-architecture/data-model.md)
- [Azure-Integration](03-architecture/azure-integration.md)

## 04 – Technische Konzepte

- [OpenParlData-Integration](04-technical-concepts/openparldata-integration.md)
- [Klassifikation](04-technical-concepts/classification-concept.md)
- [Monitoring](04-technical-concepts/monitoring-concept.md)
- [Benachrichtigungen](04-technical-concepts/notification-concept.md)

## 05 – Tests

- [Testplan und Befehle](05-testing/test-plan.md)
- [Testergebnisse und Grenzen](05-testing/test-results.md)
- [Gesamtprüfung vom 12. Oktober](05-testing/review-2026-10-12.md)
- [Prüfung vom 13. Oktober](05-testing/review-2026-10-13.md)
- [Klassifikation auf dem blinden Prüfset](05-testing/evidence/holdout-evaluation.md)
- [Regelqualität auf dem Entwicklungsset](05-testing/evidence/rule-quality-development-set.md) und [Backfill `rule-based-v7`](05-testing/evidence/backfill-rule-based-v7.md)

## 06 – Übergabe

- [Deployment](06-handover/deployment-guide.md)
- [Betrieb](06-handover/operations-guide.md)
- [Benutzerhandbuch](06-handover/user-guide.md)

## 07 – Wissenschaftliche Einordnung

- [Evaluation](07-academic/evaluation-report.md)
- [Erkenntnisse](07-academic/lessons-learned.md)
- [Öffentliche Ergebnisübersicht – Arbeitsfassung](07-academic/final-report.md)

Der formale Kursbericht mit persönlichen Angaben, signiertem Auftrag und Originalnachweisen bleibt im privaten lokalen Abgabepaket. Die öffentliche Ergebnisübersicht ist keine behauptete finale Kursabgabe.

## Einstieg und ergänzende Referenzen

[Projektübersicht](../README.md), [Installation](getting-started.md), [Konfiguration](configuration.md), [API](api.md), [Fehlerbehebung](troubleshooting.md), [Lizenzstatus](licensing.md), [Demo-Stichprobe](../data/demo/README.md), [Mitwirken](../CONTRIBUTING.md), [Sicherheit](../SECURITY.md) und [Support](../SUPPORT.md).

Der detaillierte [Monitoring-Leitfaden](monitoring.md) beschreibt Anmeldung, Missbrauchsschutz, Abonnements, Demo-Benachrichtigung, Synchronisation und Benachrichtigungsregeln. Die [WWF-Anforderungsprüfung](wwf-requirements.md) ist aktualisiert; das [Review vom 11. Oktober](daily-review-2026-10-11.md) dokumentiert einen historischen Stand. Die gesamte Dokumentation ist deutsch. Alte Einstiegsdateien wie `architecture.md`, `testing.md`, `deployment.md` und `user-guide.md` verweisen auf die neuen Hauptdokumente.
