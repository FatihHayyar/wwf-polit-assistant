# Testergebnisse

**Stand: 12. Oktober 2026, Entwicklungs-MVP.** Ergebnisse gelten für den geprüften Arbeitsstand. Der historische [Review](../daily-review-2026-10-11.md) dokumentiert eine frühere Suite mit 60 Tests.

Die [Gesamtprüfung vom 12. Oktober](review-2026-10-12.md) dokumentiert den neuen vollständigen 9/9-Lauf, Windows-/Linux-Tests, Mailpit-Abläufe und Quellstichproben.

| Prüfung | Befund | Grenze |
|---|---|---|
| Isolierte Backend-Suite | 78 Tests erfolgreich | Fixtures/Mocks; keine vollständige Live- oder Fachabnahme |
| JavaScript | Übersetzungs-/Darstellungsprüfung und Syntaxkontrollen erfolgreich | Keine vollständige Browsermatrix |
| Lokale Browserdiagnosen | Detail-/Verwaltungs-Scrollverhalten, Speicherhinweis und Layout geprüft | Windows/Edge, einzelne Desktop-/Mobile-Grössen |
| Sync-/Quellprüfung | Wiederaufnahme und aktuelle Quellstichproben dokumentiert; konkrete Mapping-/Dokumentenfehler adressiert | Kein lückenloser historischer Vollständigkeitsbeweis |
| Docker-Demo | Start, lokale Mailpit-Verifikation und Datenpersistenz historisch geprüft | Lokale Demo, kein Azure-/Produktionsbetrieb |
| Organisations-SMTP | Historischer Teilversand mit späterem Authentifizierungsabbruch | Keine zuverlässige betriebliche Abnahme |
| WWF-Anwendungsfälle | Noch nicht vollständig mit Praxispartner dokumentiert | Offen |
| Klassifikationsgüte | Keine unabhängige Expertenmessung vorhanden | Kein Precision-/Recall-Ergebnis |
| Azure und Restore | Kein validierter Zielbetrieb | Offen |

Aktuelle Befehle und Voraussetzungen stehen im [Testplan](test-plan.md). Bei Abschluss eines technischen Issues die konkrete Version und Prüfung nennen. Fachliche/betriebliche Prüfungen erhalten eigene offene Issues. Geschlossene Implementierung bedeutet keine pauschale Produktionsfreigabe.

## Befundformular

Test-ID / Commit / Umgebung: ____________________\
Eingabe und erwartetes Verhalten: ____________________\
Beobachtung und bereinigter Nachweis: ____________________\
Ergebnis: bestanden / fehlgeschlagen / blockiert / nicht durchgeführt\
Abweichung und Nachtest: ____________________
