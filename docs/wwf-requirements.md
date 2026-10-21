# WWF-Anforderungsprüfung

**Stand 21. Oktober 2026.** Diese Prüfung vergleicht die Aufgabenstellung «Open Data + AI: Ein smarter Polit-Assistant» und die per E-Mail von Attila Steinegger (WWF Schweiz, Head Digital Transformation & Data) formulierten Konkretisierungen mit der Umsetzung. Jede Zeile nennt, wo die Anforderung umgesetzt oder nachgewiesen ist. Fachliche Freigaben durch WWF stehen aus und sind als solche gekennzeichnet.

## Aufgabenstellung

| Anforderung | Umsetzung | Nachweis |
|---|---|---|
| Integration und **regelmässige Aktualisierung** der OpenParlData-Daten | Erstimport aller Exporte; tägliche Synchronisierung aller neun Bereiche um 04:30 (nach den Quellexporten). Gelesen werden nur Änderungen, neue und fehlende IDs; vollständige Vergleiche in festen Abständen | [Synchronisierungsstrategie](monitoring.md#synchronisierungsstrategie), `tests/test_sync_strategy.py` |
| Strukturierte Speicherung und **Verknüpfung** | PostgreSQL mit normalisierten Tabellen; Geschäfte, Traktanden, Sitzungen, Abstimmungen, Ereignisse, Dokumente, Texte, Gruppen und Interessenbindungen sind verknüpft | [Datenmodell](03-architecture/data-model.md) |
| **Regelbasierte Klassifikation** nach WWF-Themen, auch anhand von Texten und Dokumenten | `rule-based-v8`, konfigurierbar in `taxonomy.json`; Titel, Texte und Dokumentinhalte werden ausgewertet. Unabhängiges Prüfset: Precision 1.0, Recall 0.667 | [Klassifikationskonzept](04-technical-concepts/classification-concept.md), [Prüfset-Auswertung](05-testing/evidence/holdout-evaluation.md) |
| **Suche und Filterung** nach relevanten Kriterien | Suchbegriff, Haupt-/Unterthema, Kanton, Geschäftstyp, Zeitraum in allen neun Bereichen | [API](api.md), [Benutzerhandbuch](06-handover/user-guide.md) |
| Erkennung neuer relevanter Geschäfte und **Sessionstraktanden** | Neue Datensätze und relevante Änderungen erzeugen Change-Events; Traktanden werden täglich in einem Fenster von ±60 Tagen um das Sitzungsdatum geprüft | [Benachrichtigungsregeln](monitoring.md#aktuelle-richtlinie-meaningful-v3) |
| Themen **abonnieren** und Benachrichtigungen an eine angegebene **E-Mail-Adresse** | Registrierung per E-Mail-Link; bis zu zehn Abonnements; bis zu zehn bestätigte Empfängeradressen | `tests/test_api_security.py`, Demo-Durchlauf |
| Dokumentierte **REST-API** und einfach nutzbare **Oberfläche** | FastAPI mit OpenAPI unter `/docs`; Weboberfläche in vier Sprachen | [API](api.md) |
| **Dialogorientierte Abfragemöglichkeit** | Fragen in natürlicher Sprache (DE/FR/IT/EN) werden in Filter übersetzt; die Antwort zeigt das Verstandene, die Treffer und bietet das Speichern als Abonnement | [Fragen](monitoring.md#fragen-in-natürlicher-sprache), `tests/test_query_interpreter.py` |
| Architektur für eine **spätere Integration von AI** | Definierte Schnittstellen für Fragenerkennung (`QueryInterpreter`) und Klassifikation (`classifier_version`), Prüfsets für den Vergleich | [Erweiterungspunkte für KI](03-architecture/system-architecture.md#erweiterungspunkte-für-ki) |
| Test und Validierung anhand konkreter **Anwendungsfälle** | 151 automatisierte Tests, CI, Browser-Durchlauf der Demo; zwei blinde Prüfsets für die Klassifikation | [Testplan](05-testing/test-plan.md), [Testergebnisse](05-testing/test-results.md) |
| **Technische Dokumentation**, Ergebnisse und Weiterentwicklungen | Dokumentation in `docs/`, Übergabe-, Betriebs- und Azure-Anleitung, Evaluationsbericht | [Dokumentationsindex](README.md) |
| Weiterführend: AI-Zusammenfassungen, Visualisierungen | Bewusst nicht umgesetzt (laut Aufgabenstellung abhängig von Fortschritt und Feedback); Ansatzpunkte beschrieben | [Evaluationsbericht](07-academic/evaluation-report.md) |

## Konkretisierungen per E-Mail

| Anforderung | Umsetzung |
|---|---|
| Benachrichtigung über **neue Inhalte** (Geschäfte, Abstimmungen, Sitzungen …) im eigenen Kanton | Abonnements kombinieren Kanton mit Themen, Bereichen und weiteren Filtern; alle neun Bereiche werden überwacht |
| Filter über Themen hinaus: **Kanton, WWF-Klassifikation, Unterkategorie, individuelle Keywords, Geschäftstyp** | Alle fünf Filter sind in einem Abonnement kombinierbar (ODER innerhalb einer Gruppe, UND zwischen Gruppen) |
| **Mehrere Abonnements** über einen einfachen E-Mail-basierten Zugang verwalten | Bis zu zehn benannte Abonnements je Konto; passwortlose Anmeldung per E-Mail-Link; Bearbeiten, Pausieren, Löschen; Bestätigungs-E-Mail nach jeder Änderung |
| **Bestehende Inhalte weiterverfolgen** (Update zu einem Geschäft) | Watches für einzelne Geschäfte, Sitzungen, Gruppen und weitere Datensätze; Geschäfts-Watches umfassen verknüpfte Änderungen |
| Einfache **Integration in die Azure-Umgebung** | Container ohne Root-Rechte, Konfiguration über Umgebungsvariablen, Healthcheck; konkrete Zielarchitektur mit Container Apps, PostgreSQL Flexible Server, Azure Files und Key Vault ([Azure-Integration](03-architecture/azure-integration.md)). Die Bereitstellung selbst ist nicht getestet |
| Technologie nahe an **Python/Azure/AI-Data**, Python statt Java/Spring | Python 3.13, FastAPI, SQLAlchemy, Alembic; kein Java-Dienst |
| Streamlit als vorhandene WWF-Technologie | Die Oberfläche ist schlichtes HTML/CSS/JavaScript ohne Build-Schritt, von FastAPI ausgeliefert. Streamlit wurde als vorhandene Technologie genannt, nicht als Vorgabe; die REST-API kann auch von einer Streamlit-Oberfläche genutzt werden |
| **Votes, Groups und Interest Declarations** | Als `votings`, `groups` und `interests` vollständig umgesetzt: Synchronisierung, Suche, Klassifikation, Watches und Benachrichtigungen |

## WWF-Themen (Startfokus Energie & Klima)

| Gewünschtes Thema | Umsetzung |
|---|---|
| Erneuerbare Wärme (heizen/kühlen) | `climate_energy / renewable_heat` (u. a. Wärmepumpen, Fernwärme); Begriffe zur Kühlung (z. B. Fernkälte) fehlen noch und sind mit WWF zu ergänzen |
| Erneuerbare Stromerzeugung (Wind/PV) | `climate_energy / renewable_electricity` |
| Effizienz in Gebäuden | `climate_energy / building_efficiency` |
| Elektromobilität | `climate_energy / sustainable_mobility`; umfasst auch weiteren nachhaltigen Verkehr |
| Vorbildfunktion der öffentlichen Hand | `climate_energy / public_sector`; öffentliche Akteure werden nur aus Titeln gelesen und benötigen einen Umweltbezug |
| Rechenzentren | `climate_energy / data_centers` (eigenes Unterthema seit v8) |
| Grossverbraucher | `climate_energy / large_consumers` (eigenes Unterthema seit v8) |

Bestehende Abonnements der früheren gemeinsamen Kategorie «Rechenzentren & Grossverbraucher» wurden automatisch auf beide neuen Unterthemen übertragen. Daneben bestehen die Hauptthemen Biodiversität & Landschaft, nachhaltige Wirtschaft & Konsum sowie Umwelt & Politik, da die Aufgabenstellung auch Biodiversität, Gewässer, Landwirtschaft und Raumplanung nennt. **Offen:** Die fachliche Freigabe der Themen und Begriffe durch die Energie- & Klima-Fachpersonen von WWF sowie eine Nachannotation der Prüfsets durch WWF.

## Offene Punkte für WWF

| Punkt | Art |
|---|---|
| Freigabe der Taxonomie und Nachannotation der Prüfsets | Fachliche Abnahme |
| Abnahme der Anwendungsfälle in einem gemeinsamen Durchlauf | Abnahme |
| Bereitstellung in Azure, Organisations-SMTP, Domain und Secrets | Betrieb durch WWF |
| Organisations-SSO (Microsoft Entra ID) statt E-Mail-Link | mögliche Erweiterung |
| KI-gestützte Klassifikation, Zusammenfassungen, Chat mit Quellenangaben | zweite Entwicklungsstufe |
