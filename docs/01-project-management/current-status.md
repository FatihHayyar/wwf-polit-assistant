# Aktueller Aufgabenstand – 13. Oktober 2026

Dieser Stand ersetzt die offenen technischen Prüfpunkte aus dem [Review vom 11. Oktober](../daily-review-2026-10-11.md). Historische Ergebnisse bleiben dort erhalten. Der Entwicklungs-MVP ist technisch demonstrierbar; eine gemeinsame WWF-Abnahme wurde noch nicht durchgeführt.

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

## Bedeutung der unveränderten Checkpoints

`last_updated_at` und `last_id` speichern die erfolgreich verarbeitete Quellposition, `last_run_at` den letzten gespeicherten Dataset-Abgleich. Ohne neuere Quellposition bleibt der Cursor unverändert, obwohl heute erneut kontrolliert wurde. Bei sechs Bestandsvergleichs-Datasets bleibt das Zeitcursorfeld leer; eine ID und die Laufberichte dokumentieren den Fortschritt.

Die Datenbank bestätigt für alle neun Bereiche einen letzten Abgleich am **12. Oktober** und den Dataset-Status `idle`. Bei Geschäften lautet die Quellposition weiterhin **11.10.2026 05:23:12 / ID 341425**. Ein Quellcursor kann auch durch technisch veränderte Metadaten vorrücken; er ist keine verlässliche Uhrzeit der letzten fachlichen Änderung. Erfolgreichen Abschluss zusätzlich im Laufbericht prüfen.

Die späteren vollständigen Läufe meldeten **1.682.302 unveränderte verarbeitete Einträge**, keine neuen/geänderten Inhalte und keine Fehler. Der erneute direkte API-Vergleich bestätigt diesen Befund für die geprüften Beispiele. Das beweist nicht, dass OpenParlData am gesamten Tag keinerlei Änderung hatte. Bei den Zeitcursor-Datasets wurde nach Quelländerungsdatum/ID sortiert, bei den übrigen sechs nach ID; Letzteres ist kein globaler Nachweis der jüngsten Änderung an älteren Datensätzen.

## Nächste Schritte vor Abschluss

1. Demonstration und Präsentation mit konkreten Such-, Kontext- und Monitoringbeispielen vorbereiten.
2. WWF-Taxonomie/Fokus bestätigen und fachlich bewertete Beispiele gemeinsam prüfen.
3. WWF-Anwendungsfälle durchgehen; Feedback, Abnahme und verbleibende Anpassungen dokumentieren.
4. Formale Kursunterlagen fertigstellen und die tatsächliche Übergabe durchführen. Private personenbezogene Kursunterlagen bleiben ausserhalb des öffentlichen Repositorys.
5. Softwarelizenz festlegen.

Azure-Integration erfolgt bei Übernahme durch WWF. KI/Dialog, Organisations-SSO, täglicher Gesamtdigest und experimentelle bereichsübergreifende Suche bleiben Weiterentwicklung, keine offenen Pflichtfunktionen dieses MVP.

Nachweise: [Gesamtprüfung](../05-testing/review-2026-10-12.md), [Testergebnisse](../05-testing/test-results.md), [GitHub-Tracking](github-tracking.md), [Projektübersicht](../../README.md).
