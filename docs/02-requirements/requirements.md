# Anforderungen

Quellen: **A** bereinigte Aufgabenstellung, **E** WWF-Konkretisierung, **T** technische Erweiterung. Der Implementierungsstatus bezieht sich auf den dokumentierten Arbeitsstand; fachliche oder betriebliche Abnahme ist ein eigener Nachweis.

| ID | Quelle | Anforderung | User Stories | Implementierung / Restprüfung |
|---|---|---|---|---|
| R01 | A | Datenintegration und regelmässige Aktualisierung | US-01 | Gemeinsamer Sync für neun Bereiche: Änderungen, neue und fehlende IDs, vollständige Vergleiche in Intervallen; täglich 04:30. Betreiberlauf über mehrere Tage beobachten |
| R02 | A | Strukturierte Speicherung und Verknüpfung | US-01, US-02 | Modelle/Beziehungen; Quellstichproben |
| R03 | A/E | Regelbasierte WWF-Klassifikation | US-03, US-16 | `rule-based-v8` mit Evidenz; zwei blinde Prüfsets (Precision 1.0, Recall 0.667); fachliche Freigabe der Taxonomie offen |
| R04 | A/E | Suche nach Themen, Kanton, Geschäftstyp und Keywords | US-04, US-13 | API und neun UI-Listen; WWF-Szenario offen |
| R05 | A | Neue relevante Geschäfte und Traktanden erkennen | US-06, US-08 | Change-/Matchingpipeline; fachliche Beispiele bestätigen |
| R06 | A/E | Kombinierte Abonnementfilter inkl. Geschäftstyp | US-06, US-13, US-17 | Themen, Unterthemen, Kanton, Geschäftstyp und Dataset-Auswahl; Keywords nur in der Recherche (D15) |
| R07 | E | Bestehende Inhalte beobachten | US-07, US-18 | Einzel-Watches und verbundene Änderungen |
| R08 | A | Benachrichtigungen per E-Mail | US-06, US-08 | Queue/SMTP; zuverlässiger Organisationsversand offen |
| R09 | A | Dokumentierte REST-API | US-10 | OpenAPI und API-Leitfaden |
| R10 | A | Geeignete Oberfläche | US-04, US-17–US-20 | Vier UI-Sprachen; Praxisbewertung offen |
| R11 | A | Technik, Ergebnisse und Weiterentwicklung dokumentieren | AP-1.x, US-22, AP-3.1 | Strukturierte Dokumentation; tatsächliche Übergabe offen |
| R12 | A | Anwendungsfälle und Beispieldaten validieren | US-11, US-16, US-23 | Demo vorhanden; WWF-Abnahme offen |
| R13 | E | Python-Nähe zur WWF-Landschaft | US-21 | Python/FastAPI, kein Java-Service |
| R14 | E | Azure-Anschlussfähigkeit und technischen Handover bereitstellen | US-21 | Container ohne Root-Rechte, Healthcheck, konkrete Azure-Zielarchitektur; Bereitstellung bei Übernahme durch WWF |
| R15 | E | Votes, Groups und Interessen berücksichtigen | US-02, US-04 | Unter neun öffentlichen Bereichen implementiert |
| R16 | E | Initiale Energie-/Klima-Themen abstimmen | US-15 | Fachliche Freigabe offen |
| R17 | T | Mehrere bestätigte Benachrichtigungsadressen | US-09 | Bis zu zehn Adressen |
| R18 | T | Optionale direkte Google-Anmeldung | – | Konfigurationsabhängig; kein Unternehmens-SSO |
| R19 | E | Mehrere Abonnements über einen E-Mail-basierten Zugang | US-05, US-12, US-19 | Bis zu zehn Abonnements je Konto mit erzeugten Namen, E-Mail-Link-Anmeldung |
| R20 | A | Dialogorientierte Abfragemöglichkeit | US-14 | Fragen in vier Sprachen werden regelbasiert in Filter übersetzt; als Abonnement speicherbar |
| R21 | A | Architektur für spätere KI-Integration | US-14 | Schnittstellen `QueryInterpreter` und Klassifikationsversion; Vergleich über Prüfsets |
| R22 | E | Rechenzentren und Grossverbraucher als eigene Themen, Vorbildfunktion unter Energie & Klima | US-15 | Umgesetzt in v8; fachliche Freigabe offen |

Anforderung bedeutet nicht automatisch genehmigte spätere Erweiterung. Die Anforderungen sind in [User Stories](user-stories.md) mit Akzeptanzkriterien zerlegt; die [Rückverfolgbarkeit](acceptance-criteria.md) zeigt den Weg bis zum Test. [Scope](../01-project-management/scope-and-priorities.md) und [Anwendungsfälle](use-cases.md) ergänzen den Zusammenhang.
