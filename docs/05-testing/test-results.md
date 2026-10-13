# Testergebnisse

**Stand: 13. Oktober 2026, Entwicklungs-MVP.** Ergebnisse gelten für den geprüften Arbeitsstand. Der historische [Review](../daily-review-2026-10-11.md) dokumentiert eine frühere Suite mit 60 Tests. Die [Prüfung vom 13. Oktober](review-2026-10-13.md) ergänzt die folgenden älteren Live-/Browsernachweise.

Die [Gesamtprüfung vom 12. Oktober](review-2026-10-12.md) dokumentiert den neuen vollständigen 9/9-Lauf, Windows-/Linux-Tests, Mailpit-Abläufe und Quellstichproben.

| Prüfung | Befund | Grenze |
|---|---|---|
| Isolierte Backend-Suite | 91 Tests erfolgreich; zusätzliche gezielte Gruppierungsprüfung erfolgreich | Fixtures/Mocks; keine vollständige Live- oder Fachabnahme |
| Regel-Entwicklungsset | Vorher 40/50, jetzt 50/50 auf denselben realen Beispielen | Kein unabhängiges WWF-Prüfset, keine globale Precision-/Recall-Messung |
| Regel-Backfill | Alle 2.951.254 Datensätze abgedeckt, 0 fehlende/alte Zuordnungen | Technische Abdeckung beweist keine korrekte Kategorisierung aller Inhalte |
| Ergebnisgruppen | Jura-Beispiel schreibgeschützt: eine Karte, beide Quell-IDs erreichbar; Pagination und Nummernsuche getestet | Gleichnamigkeit/Tag/Körperschaft ist eine Darstellungsheuristik |
| JavaScript | Übersetzungs-/Darstellungsprüfung und Syntaxkontrollen erfolgreich | Keine vollständige Browsermatrix |
| Lokale Browserdiagnosen | Detail-/Verwaltungs-Scrollverhalten, Speicherhinweis und Layout geprüft | Windows/Edge, einzelne Desktop-/Mobile-Grössen |
| Sync-/Quellprüfung | Wiederaufnahme und aktuelle Quellstichproben dokumentiert; konkrete Mapping-/Dokumentenfehler adressiert | Kein lückenloser historischer Vollständigkeitsbeweis |
| Docker-Demo | Am 12. Oktober Start, Registrierung/Anmeldung, Empfängerverifikation, Abonnements, Logout, Kontolöschung und Datenpersistenz geprüft | Lokale Demo, kein Azure-/Produktionsbetrieb |
| Lokaler SMTP-Versand | Am 12. Oktober 14 erfolgreiche Versandgruppen ohne Fehler im wiederaufgenommenen Lauf; früherer Authentifizierungsabbruch bleibt historischer Befund | WWF-Organisationsprovider und Produktionslimits nicht geprüft |
| WWF-Anwendungsfälle | Noch nicht vollständig mit Praxispartner dokumentiert | Offen |
| Klassifikationsgüte | Keine unabhängige Expertenmessung vorhanden | Kein Precision-/Recall-Ergebnis |
| Azure und Restore | Anschlussfähige Architektur und Betriebsunterlagen vorhanden; kein validierter WWF-Zielbetrieb | Spätere Integration durch WWF; kein fehlendes Azure-Deployment im MVP |

Aktuelle Befehle und Voraussetzungen stehen im [Testplan](test-plan.md). Bei Abschluss eines technischen Issues die konkrete Version und Prüfung nennen. Fachliche/betriebliche Prüfungen erhalten eigene offene Issues. Geschlossene Implementierung bedeutet keine pauschale Produktionsfreigabe.

## Befundformular

Test-ID / Commit / Umgebung: ____________________\
Eingabe und erwartetes Verhalten: ____________________\
Beobachtung und bereinigter Nachweis: ____________________\
Ergebnis: bestanden / fehlgeschlagen / blockiert / nicht durchgeführt\
Abweichung und Nachtest: ____________________
