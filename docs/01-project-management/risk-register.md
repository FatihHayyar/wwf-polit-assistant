# Risikoregister

Die Einstufung ist eine qualitative Projektbewertung und keine gemessene Wahrscheinlichkeit. Verantwortlichkeiten und Termine werden im zugehörigen Issue vereinbart.

| ID | Risiko | Gewicht | Gegenmassnahme / Nachweis |
|---|---|---|---|
| P1 | Provisorische Taxonomie oder unpassende Regeln; rund ein Drittel relevanter Geschäfte wird übersehen | Hoch | WWF-Freigabe, Nachannotation der Prüfsets, neue Prüfsets nach Regeländerungen |
| P2 | Quellvarianten, ältere Zeitstempel oder historische Lücken | Hoch | Mappingtests, Phasen für neue und fehlende IDs, vollständige Vergleiche in Intervallen und dokumentierte Quellstichproben |
| P3 | SMTP-Limits oder Authentifizierungsabbrüche | Hoch | Organisationsprovider und kontrollierte Zustellung testen |
| P4 | Azure-/Authentifizierungsanforderungen ungeklärt | Mittel | Architektur-/Betriebsabstimmung vor Deployment |
| P5 | Zusatzfunktionen verdrängen Validation und Abschluss | Hoch | Kernanforderungen priorisieren und Restaufwand kontrollieren |
| P6 | Fehlende Protokolle oder Genehmigungsnachweise | Mittel | Originale privat archivieren, Rekonstruktionen kennzeichnen |
| P7 | Verlust lokaler Jobdateien bei Container-Neustart | Mittel | Persistenten Speicher und Wiederaufnahme testen |
| P8 | Suchindex-Migrationen dauern lange | Mittel | Repräsentative Testkopie, Speicherprüfung und Wartungsfenster |
| P9 | Benachrichtigungen mehrfach zugestellt | Mittel | SMTP-/Commit-Grenzen beachten und Retryverhalten prüfen |
| P10 | Personenbezogene Unterlagen öffentlich | Mittel | Private Abgabeunterlagen von öffentlicher Dokumentation trennen |
| P11 | Quelle ändert Daten ohne neues Änderungsdatum | Mittel | Vollständige Vergleiche je Bereich alle 7–30 Tagen; Dokumente nur auf Anforderung |
| P12 | Fragenerkennung versteht eine Frage falsch | Niedrig | Erkannte Teile werden angezeigt und sind im Suchformular korrigierbar |

Geschlossene Implementierungs-Issues beseitigen nicht automatisch diese Betriebs- oder Fachrisiken. Der [Evaluationsbericht](../07-academic/evaluation-report.md) hält die derzeitigen Aussagegrenzen fest.
