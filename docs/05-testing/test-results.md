# Testergebnisse

**Stand: 21. Oktober 2026, Entwicklungs-MVP.** Ergebnisse gelten für den geprüften Arbeitsstand. Der historische [Review](../daily-review-2026-10-11.md) dokumentiert eine frühere Suite mit 60 Tests. Die [Prüfung vom 13. Oktober](review-2026-10-13.md) ergänzt die folgenden älteren Live-/Browsernachweise.

Die [Gesamtprüfung vom 12. Oktober](review-2026-10-12.md) dokumentiert den neuen vollständigen 9/9-Lauf, Windows-/Linux-Tests, Mailpit-Abläufe und Quellstichproben.

| Prüfung | Befund | Grenze |
|---|---|---|
| Isolierte Suite | 124 Tests erfolgreich (21. Oktober), davon 26 API-Tests über den echten FastAPI-Stack zu Anmeldung, Ratenbegrenzung, Bestätigungsseiten, Token-Widerruf, Sicherheits-Headern und Demo-Benachrichtigung | Fixtures/Mocks und SQLite; keine vollständige Live- oder Fachabnahme |
| CI | GitHub Actions: ruff, Testsuite, reproduzierbare Klassifikationsnachweise, Migrationen auf PostgreSQL 17 inkl. Downgrade/Upgrade, Docker-Build | Erst nach dem nächsten Push sichtbar |
| Regel-Entwicklungsset | Vorher 40/50, jetzt 50/50 auf denselben realen Beispielen | Regeln wurden daran verbessert; Regressionsprüfung, keine Qualitätsschätzung |
| Prüfset (Holdout) | 300 zufällige Geschäfte, blind annotiert: 268/300 streng korrekt; WWF-Relevanz Precision 1.0 (95 %-KI 0.77–1.0), Recall 0.325 (0.20–0.48); [Auswertung](evidence/holdout-evaluation.md) | Annotation durch KI-Assistenten, nicht durch WWF-Fachpersonen; nur Geschäfte; 40 positive Fälle |
| Regel-Backfill | Alle 2.951.254 Datensätze abgedeckt, 0 fehlende/alte Zuordnungen | Technische Abdeckung beweist keine korrekte Kategorisierung aller Inhalte |
| Ergebnisgruppen | Jura-Beispiel schreibgeschützt: eine Karte, beide Quell-IDs erreichbar; Pagination und Nummernsuche getestet | Gleichnamigkeit/Tag/Körperschaft ist eine Darstellungsheuristik |
| JavaScript | Übersetzungs-/Darstellungsprüfung und Syntaxkontrollen erfolgreich | Keine vollständige Browsermatrix |
| Lokale Browserdiagnosen | Detail-/Verwaltungs-Scrollverhalten, Speicherhinweis und Layout geprüft | Windows/Edge, einzelne Desktop-/Mobile-Grössen |
| Sync-/Quellprüfung | Wiederaufnahme und aktuelle Quellstichproben dokumentiert; konkrete Mapping-/Dokumentenfehler adressiert | Kein lückenloser historischer Vollständigkeitsbeweis |
| Docker-Demo | Am 12. Oktober Start, Registrierung/Anmeldung, Empfängerverifikation, Abonnements, Logout, Kontolöschung und Datenpersistenz geprüft. Am 21. Oktober in einer isolierten Instanz mit Edge: Suche, Details, Sprachwechsel, Registrierung über Mailpit und Bestätigungsseite, Testbenachrichtigung mit Zustellung, Token-Widerruf beim Abmelden, Mobilbreite, keine CSP-Verstösse | Lokale Demo, kein Azure-/Produktionsbetrieb |
| Lokaler SMTP-Versand | Am 12. Oktober 14 erfolgreiche Versandgruppen ohne Fehler im wiederaufgenommenen Lauf; früherer Authentifizierungsabbruch bleibt historischer Befund | WWF-Organisationsprovider und Produktionslimits nicht geprüft |
| WWF-Anwendungsfälle | Noch nicht vollständig mit Praxispartner dokumentiert | Offen |
| Klassifikationsgüte durch Fachpersonen | Noch keine Bewertung durch WWF | Prüfset nachannotieren lassen |
| Azure und Restore | Anschlussfähige Architektur und Betriebsunterlagen vorhanden; kein validierter WWF-Zielbetrieb | Spätere Integration durch WWF; kein fehlendes Azure-Deployment im MVP |

Aktuelle Befehle und Voraussetzungen stehen im [Testplan](test-plan.md). Bei Abschluss eines technischen Issues die konkrete Version und Prüfung nennen. Fachliche/betriebliche Prüfungen erhalten eigene offene Issues. Geschlossene Implementierung bedeutet keine pauschale Produktionsfreigabe.

## Befundformular

Test-ID / Commit / Umgebung: ____________________\
Eingabe und erwartetes Verhalten: ____________________\
Beobachtung und bereinigter Nachweis: ____________________\
Ergebnis: bestanden / fehlgeschlagen / blockiert / nicht durchgeführt\
Abweichung und Nachtest: ____________________
