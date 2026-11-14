# Akzeptanzkriterien und Rückverfolgbarkeit

Die Akzeptanzkriterien stehen direkt bei ihrer User Story im [Backlog](user-stories.md), jeweils mit dem Test, der sie nachweist. Diese Seite zeigt den Weg von der Anforderung bis zum Testergebnis.

## Von der Anforderung zum Test

| Anforderung | User Stories | Kriterien | Nachweis | Ergebnis |
|---|---|---|---|---|
| R01 Datenintegration und Aktualisierung | US-01 | 5 | `test_sync_strategy`, `test_sync_control`, `test_event_mapping` | ✅ bestanden |
| R02 Speicherung und Verknüpfung | US-01, US-02 | 9 | `test_monitoring`, `test_affair_result_groups` | ✅ bestanden |
| R03 Regelbasierte WWF-Klassifikation | US-03, US-16 | 7 | `test_rule_classifier`, `test_holdout_evaluation`, Prüfset B | ✅ bestanden; Expertenprüfung offen |
| R04 Suche nach Thema, Kanton, Typ, Stichwort | US-04, US-13 | 7 | `test_monitoring`, `test_query_interpreter` | ✅ bestanden |
| R05 Neue relevante Inhalte erkennen | US-06, US-08 | 10 | `test_monitoring`, `test_notification_policy` | ✅ bestanden |
| R06 Kombinierte Abonnementfilter | US-06, US-13, US-17 | 11 | `test_monitoring`, `browser_membership` | ✅ bestanden |
| R07 Bestehende Inhalte beobachten | US-07, US-18 | 6 | `test_monitoring`, `browser_membership` | ✅ bestanden |
| R08 Benachrichtigungen per E-Mail | US-06, US-08 | 10 | `test_monitoring`, `test_notification_presentation`, `test_notification_content` | ✅ bestanden; Organisationsversand offen (F11) |
| R09 Dokumentierte REST-API | US-10 | 3 | `test_api_security` | ✅ bestanden |
| R10 Geeignete Oberfläche | US-04, US-17–US-20 | 15 | `browser_membership`, `test_frontend.cjs` | ✅ bestanden; Praxisbewertung offen |
| R11 Dokumentation | AP-1.x, US-22, AP-3.1 | – | Durchsicht, manueller Start | In Arbeit |
| R12 Anwendungsfälle validieren | US-11, US-16, US-23 | 8 | `test_api_security` (Demo), Abnahme | Demo ✅; WWF-Abnahme offen |
| R13 Python-Nähe | US-21 | – | Technologieentscheid D3 | ✅ |
| R14 Azure-Anschlussfähigkeit | US-21 | 3 | CI-Docker-Build, Docker-Demo, Dokumentation | ✅ bestanden; Bereitstellung durch WWF (D9) |
| R15 Abstimmungen, Gruppen, Interessen | US-02, US-04 | 8 | `test_monitoring` | ✅ bestanden |
| R16 Energie-/Klima-Themen abstimmen | US-15 | 4 | `test_rule_classifier`, Freigabe | Umsetzung ✅; Freigabe offen (F05) |
| R17 Mehrere Empfängeradressen | US-09 | 2 | `test_account_preferences`, `test_api_security` | ✅ bestanden |
| R18 Optionale Google-Anmeldung | – | – | `test_google_callback_rejects_state_before_network_or_account_changes` | ✅ bestanden (technische Ergänzung) |
| R19 Mehrere Abonnements, E-Mail-Zugang | US-05, US-12, US-19 | 15 | `test_api_security`, `test_monitoring`, `browser_membership` | ✅ bestanden |
| R20 Dialogorientierte Abfrage | US-14 | 5 | `test_query_interpreter` | ✅ bestanden; Umfang bestätigen (F02) |
| R21 Architektur für KI | US-14 | – | Schnittstelle `QueryInterpreter`, Klassifikator-Version | ✅ vorbereitet |
| R22 Rechenzentren / Grossverbraucher getrennt | US-15 | 4 | `test_rule_classifier` | ✅ bestanden; Freigabe offen |

## Testlauf

Stand der letzten vollständigen Ausführung (5. November 2026):

| Testart | Umfang | Ergebnis |
|---|---|---|
| Python-Tests (Backend, API, Sync, Klassifikation) | 161 Tests | alle bestanden |
| Frontend-Prüfungen (`node tests/test_frontend.cjs`) | Übersetzungen in vier Sprachen, Modulstruktur | bestanden |
| Browser-Durchlauf (`tests/browser_membership.py`, Edge) | Anmeldung, zwei Abonnements, Speichern am Dialogende, Verfolgen mit einem Klick, Meldungen bei Registrieren/Anmelden | bestanden |
| Lint (`ruff check app tests`) | gesamter Code | keine Befunde |

Befehle und weitere Prüfungen stehen im [Testplan](../05-testing/test-plan.md).

## Was ein bestandener Test nicht belegt

Automatisierte Tests weisen nach, dass die Anwendung sich wie in den Kriterien beschrieben verhält. Ob die Themen fachlich richtig sind (F05, F12), ob der Funktionsumfang den Bedarf deckt (US-23) und ob der Versand in der WWF-Umgebung funktioniert (F11), klären erst die Rückmeldungen und die Abnahme durch WWF.
