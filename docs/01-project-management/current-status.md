# Aktueller Aufgabenstand – 21. Oktober 2026

Dieser Stand ersetzt die offenen technischen Prüfpunkte aus dem [Review vom 11. Oktober](../daily-review-2026-10-11.md). Historische Ergebnisse bleiben dort erhalten. Der Entwicklungs-MVP ist technisch demonstrierbar; eine gemeinsame WWF-Abnahme wurde noch nicht durchgeführt.

## Ergänzungen vom 21. Oktober

Abgleich mit der Aufgabenstellung und den E-Mail-Konkretisierungen von WWF; jede Anforderung ist in der [Anforderungsprüfung](../wwf-requirements.md) mit Nachweis verknüpft.

- **Mehrere Abonnements:** bis zu zehn benannte Abonnements je Konto mit Themen, Kantonen, Geschäftstypen, Stichwörtern und Bereichen; Bearbeiten, Pausieren, Löschen. Bestehende Abonnements wurden migriert (`20261021_subscription_profiles`).
- **Geschäftstyp** als Such- und Abonnementfilter (Motion, Postulat, Interpellation …), auch für verknüpfte Datensätze.
- **Dialogorientierte Abfrage:** Fragen in vier Sprachen werden regelbasiert in Filter übersetzt; das Ergebnis lässt sich als Abonnement speichern. Schnittstelle für eine spätere KI-Variante vorhanden.
- **Synchronisierung neu aufgebaut:** nur Änderungen, neue und fehlende IDs; vollständige Vergleiche in festen Abständen. Geschäfte: rund 3 Sekunden statt 74 Minuten. Checkpoints aller Bereiche stehen wieder auf dem 21. Oktober (Dokumente zuvor 11. Oktober, 2'854 Dokumente nachgeholt). Start um 04:30 nach den Quellexporten.
- **Klassifikation v8:** Rechenzentren und Grossverbraucher getrennt, Vorbildfunktion der öffentlichen Hand unter Klima & Energie, Ausschluss- und Infix-Regeln, viele neue Fachbegriffe. Zweites blindes Prüfset B: Recall 0.667 statt 0.361 bei Precision 1.0. Alle 2'958'331 Datensätze neu klassifiziert. [Auswertung](../05-testing/evidence/holdout-evaluation.md)
- **Azure:** Container ohne Root-Rechte, Healthcheck, konkrete [Zielarchitektur](../03-architecture/azure-integration.md).
- **Sicherheit:** gleiche Antwort für bekannte und unbekannte Adressen, Ratenbegrenzung für E-Mail-, Token- und Frage-Endpunkte, Bestätigungsseite mit POST statt Token-Verbrauch beim Öffnen, Ursprungsprüfung, Token-Widerruf beim Abmelden, Sicherheits-Header mit CSP, PostgreSQL nur lokal erreichbar.
- **Demo:** Testbenachrichtigung über ein fiktives Geschäft, das die echte Klassifikation und den echten Versand durchläuft; Anleitung auf der Startseite.
- **Wartbarkeit:** Frontend in Module aufgeteilt, Sync-Code vereinheitlicht (sieben veraltete Skripte entfernt), Dokumentation vollständig deutsch, ruff und GitHub-Actions-CI.
- **Tests:** 155 isolierte Tests erfolgreich; Browser-Durchlauf der Demo mit Frage, zwei Abonnements, Testbenachrichtigung und Abmeldung in einer isolierten Instanz erfolgreich; Migrationen auf PostgreSQL 17 vor- und zurückgespielt. Die Änderungen liegen auf dem Branch `improvements/wipro-review` und sind nicht gepusht.

## Ergänzungen vom 13. Oktober

- Ollama-Experimente verworfen; regelbasierte Klassifikation als MVP-Basis bestätigt. LLM und Chatbot bleiben mögliche spätere Semesterarbeiten ohne aktuellen Implementierungsauftrag.
- Taxonomie in JSON konfigurierbar, je Hauptthema lokales Sonstiges, klar erkennbare Titelzusammensetzungen, Umwelt-Qualifier und robuste Textnormalisierung.
- Gemischtes Entwicklungsset: bisherige Regeln 40/50, neue Regeln 50/50; unabhängige WWF-Expertenevaluation bleibt offen.
- 2.951.254 Datensätze in neun Bereichen neu klassifiziert; unabhängige Abfrage bestätigt 0 fehlende/alte Zuordnungen. Quelldaten und Benachrichtigungen unverändert.
- Haupt-/Unterthema auf Karten sichtbar. Gleichnamige Geschäftsquellen derselben Körperschaft/desselben Tages gruppiert, alle Originalzugänge erhalten; Anzahl und Pagination berücksichtigen die Gruppen.
- 91 Backend-Tests und Frontend-Checks erfolgreich. Neue Browser-/Docker-Abnahme nicht behauptet. Beim letzten Prozesscheck lief nur PostgreSQL, kein API-/Scheduler-Dienst. Änderungen noch nicht gepusht; externe GitHub-Statusangaben wurden nicht aktualisiert.

Nachweise: [Prüfung vom 13. Oktober](../05-testing/review-2026-10-13.md), [Konfiguration](../configuration.md) und [Klassifikationskonzept](../04-technical-concepts/classification-concept.md). Die folgenden Angaben dokumentieren den 12. Oktober.

## Abgleich der Aufgaben am 12. Oktober

| Bisherige Aufgabe | Ergebnis am 12. Oktober | Was tatsächlich offen bleibt |
|---|---|---|
| Erfolgreichen kompletten Sync und Wiederaufnahme nachweisen | Wiederaufgenommener Lauf, neuer unabhängiger Lauf und letzter manueller Nutzerlauf erfolgreich mit 9/9; neuer Lauf ohne Dataset-/Versandfehler | Reguläre Läufe weiter beobachten; keine dauerhafte Fehlerfreiheit behaupten |
| Quelle gegen lokale Daten prüfen | Erneut 500 Beispiele je Dataset, insgesamt 4.500, ohne fehlende Inhalte, Inhaltsabweichungen oder Mappingfehler; API-Gesamtzahlen stimmen mit lokalen Zeilenzahlen überein | Vollständiger historischer Inhaltsvergleich und fachliche Bewertung sind damit nicht bewiesen |
| SMTP-Fehler untersuchen und Versand bestätigen | Wiederaufgenommener Lauf meldete 14 erfolgreiche Versandgruppen ohne Versandfehler; CLI meldet künftige Versandfehler korrekt | Organisationsprovider und Limits bei WWF-Übernahme festlegen; alte verworfene Nachrichten nicht automatisch erneut senden |
| Aussagekräftige Änderungen und Nachrichten prüfen | Relevanzregeln und Regressionen geprüft; HTML/Klartext überarbeitet, Links benannt, Sonderzeichen korrigiert, mehrfache Dokumentzuordnungen zusammengefasst | Ein täglicher Gesamtdigest und weitergehende SMTP-Optimierungen sind optionale Erweiterungen |
| MVP-Szenarien dokumentieren | Backend, Frontend, Desktop/Mobile, neun Listen-/Detail-APIs und Docker-/Mailpit-Kontoablauf geprüft; Nachweise verlinkt | Gemeinsamer WWF-Durchlauf und fachliche Akzeptanz bleiben offen |

## Weitere am 12. Oktober abgeschlossene Arbeiten

- Event-Mapping vereinheitlicht und Dokumentabgleich repariert: 1.158 Dokumente nachgetragen, 32 geändert. Diese Zahlen belegen lokale Reparaturen, keine ausschliesslich heute veröffentlichten Quellinhalte.
- Windows-Dateisperren beim atomischen Checkpoint-Schreiben behandelt und unter Windows reproduzierbar geprüft.
- Scheduler auf aktuelles Image gebracht, persistente Logs gemeinsam eingebunden und STARTTLS-Konfiguration durchgereicht.
- Migrationen auf `20261012_recipients (head)` gebracht. Zwei grosse experimentelle Suchindizes sind ausdrücklich zurückgestellt; die öffentliche Bereichssuche benötigt sie nicht.
- Oberflächenkorrekturen für Ergebnisse, Detailansichten und Abonnementverwaltung umgesetzt. Verfolgen gehört in die Verwaltung; die separate schwebende Konto-Leiste wurde entfernt.
- 81 Backend-Tests unter Windows erfolgreich; im Linux-Image 80 erfolgreich und eine Windows-spezifische Prüfung übersprungen. JavaScript- und Browserkontrollen ebenfalls erfolgreich.
- Deutsche Dokumentation strukturiert; technische Übergabe, Benutzerhandbuch, Anforderungen, Tests und Ergebnisunterlagen vorbereitet. GitHub-Issues/Milestones angelegt. Ein Projects-Board benötigt noch die passende Berechtigung.

## Bedeutung der unveränderten Checkpoints (Stand 12. Oktober)

Dieser Abschnitt erklärt den damaligen Befund. Seit dem 21. Oktober schreiben alle Bereiche ihren Checkpoint nach jedem erfolgreichen Lauf auf die neueste gelesene Quellposition fort; vollständige Vergleiche werden in `last_full_scan_at` vermerkt ([Synchronisierungsstrategie](../monitoring.md#synchronisierungsstrategie)).

`last_updated_at` und `last_id` speichern die erfolgreich verarbeitete Quellposition, `last_run_at` den letzten gespeicherten Dataset-Abgleich. Damals blieben die Zeitcursor der sechs Bestandsvergleichs-Datasets leer, und der Dokumenten-Cursor rückte nicht vor, obwohl täglich kontrolliert wurde.

Die damaligen vollständigen Läufe meldeten **1.682.302 unveränderte verarbeitete Einträge**, keine neuen/geänderten Inhalte und keine Fehler. Der direkte API-Vergleich bestätigte diesen Befund für die geprüften Beispiele.

## Nächste Schritte vor Abschluss

1. Demonstration und Präsentation mit konkreten Such-, Frage-, Kontext- und Monitoringbeispielen vorbereiten.
2. WWF-Taxonomie bestätigen (u. a. Begriffe zur Kühlung) und die Prüfsets gemeinsam mit WWF-Fachpersonen nachannotieren. Nach weiteren Regeländerungen mit einem neuen Prüfset messen.
3. WWF-Anwendungsfälle durchgehen; Feedback, Abnahme und verbleibende Anpassungen dokumentieren.
4. Formale Kursunterlagen fertigstellen und die tatsächliche Übergabe durchführen. Private personenbezogene Kursunterlagen bleiben ausserhalb des öffentlichen Repositorys.
5. Softwarelizenz festlegen.

Die Azure-Bereitstellung erfolgt bei Übernahme durch WWF nach der [Azure-Anleitung](../03-architecture/azure-integration.md). KI-gestützte Klassifikation, Zusammenfassungen, ein Chat mit Quellenangaben, Organisations-SSO und ein täglicher Gesamtdigest bleiben Weiterentwicklung.

Nachweise: [Gesamtprüfung](../05-testing/review-2026-10-12.md), [Testergebnisse](../05-testing/test-results.md), [GitHub-Tracking](github-tracking.md), [Projektübersicht](../../README.md).
