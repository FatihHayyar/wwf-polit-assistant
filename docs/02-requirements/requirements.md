# Anforderungen

Quellen: **A** bereinigte Aufgabenstellung, **E** WWF-Konkretisierung, **T** technische Erweiterung. Der Implementierungsstatus bezieht sich auf den dokumentierten Arbeitsstand; fachliche oder betriebliche Abnahme ist ein eigener Nachweis.

| ID | Quelle | Anforderung | Implementierung / Restprüfung |
|---|---|---|---|
| R01 | A | Datenintegration und regelmässige Aktualisierung | Gemeinsamer Sync für neun Bereiche: Änderungen, neue und fehlende IDs, vollständige Vergleiche in Intervallen; täglich 04:30. Betreiberlauf über mehrere Tage beobachten |
| R02 | A | Strukturierte Speicherung und Verknüpfung | Modelle/Beziehungen; Quellstichproben |
| R03 | A/E | Regelbasierte WWF-Klassifikation | `rule-based-v8` mit Evidenz; zwei blinde Prüfsets (Precision 1.0, Recall 0.667); fachliche Freigabe der Taxonomie offen |
| R04 | A/E | Suche nach Themen, Kanton, Geschäftstyp und Keywords | API und neun UI-Listen; WWF-Szenario offen |
| R05 | A | Neue relevante Geschäfte und Traktanden erkennen | Change-/Matchingpipeline; fachliche Beispiele bestätigen |
| R06 | A/E | Kombinierte Abonnementfilter inkl. Geschäftstyp | Themen, Unterthemen, Kanton, Geschäftstyp, Keywords und Dataset-Auswahl |
| R07 | E | Bestehende Inhalte beobachten | Einzel-Watches und verbundene Änderungen |
| R08 | A | Benachrichtigungen per E-Mail | Queue/SMTP; zuverlässiger Organisationsversand offen |
| R09 | A | Dokumentierte REST-API | OpenAPI und API-Leitfaden |
| R10 | A | Geeignete Oberfläche | Vier UI-Sprachen; Praxisbewertung offen |
| R11 | A | Technik, Ergebnisse und Weiterentwicklung dokumentieren | Strukturierte Dokumentation; tatsächliche Übergabe offen |
| R12 | A | Anwendungsfälle und Beispieldaten validieren | Demo vorhanden; WWF-Abnahme offen |
| R13 | E | Python-Nähe zur WWF-Landschaft | Python/FastAPI, kein Java-Service |
| R14 | E | Azure-Anschlussfähigkeit und technischen Handover bereitstellen | Container ohne Root-Rechte, Healthcheck, konkrete Azure-Zielarchitektur; Bereitstellung bei Übernahme durch WWF |
| R15 | E | Votes, Groups und Interessen berücksichtigen | Unter neun öffentlichen Bereichen implementiert |
| R16 | E | Initiale Energie-/Klima-Themen abstimmen | Fachliche Freigabe offen |
| R17 | T | Mehrere bestätigte Benachrichtigungsadressen | Bis zu zehn Adressen |
| R18 | T | Optionale direkte Google-Anmeldung | Konfigurationsabhängig; kein Unternehmens-SSO |
| R19 | E | Mehrere Abonnements über einen E-Mail-basierten Zugang | Bis zu zehn benannte Abonnements je Konto, E-Mail-Link-Anmeldung |
| R20 | A | Dialogorientierte Abfragemöglichkeit | Fragen in vier Sprachen werden regelbasiert in Filter übersetzt; als Abonnement speicherbar |
| R21 | A | Architektur für spätere KI-Integration | Schnittstellen `QueryInterpreter` und Klassifikationsversion; Vergleich über Prüfsets |
| R22 | E | Rechenzentren und Grossverbraucher als eigene Themen, Vorbildfunktion unter Energie & Klima | Umgesetzt in v8; fachliche Freigabe offen |

Anforderung bedeutet nicht automatisch genehmigte spätere Erweiterung. [Scope](../01-project-management/scope-and-priorities.md), [Use Cases](use-cases.md) und [Akzeptanzkriterien](acceptance-criteria.md) halten Herkunft und Prüfung zusammen.
