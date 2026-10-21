# Scope und Prioritäten

## MVP-Kern

OpenParlData beziehen und aktualisieren, Daten verknüpfen, regelbasiert WWF-Themen zuordnen, Inhalte recherchieren und relevante neue Entwicklungen beziehungsweise bestehende Inhalte beobachten. API, einfache Oberfläche, Benachrichtigungen und technische Dokumentation gehören zum Kern.

Die öffentlichen Bereiche sind Geschäfte, Traktanden, Sitzungen, Abstimmungen, Ereignisse, Dokumente, Texte, Gruppen und Interessenbindungen. Referenzdaten ergänzen deren Kontext.

## Umfang und Quellen

Der bereinigte Auftrag ist die Projektbasis. Laut geschildertem Kick-off wurde M365 aus dem aktuellen Umfang entfernt und AI als Weiterentwicklung behandelt. Die spätere WWF-Rückmeldung konkretisiert kombinierte Filter, bestehende Inhalte, zusätzliche Datentypen und die Nähe zu Python/Azure. Diese Quellen werden nicht zu einer nachträglich unterschriebenen Erweiterung verschmolzen.

Die Aufgabenstellung nennt eine dialogorientierte Abfragemöglichkeit und eine Architektur, die eine spätere AI-Integration ermöglicht. Beides ist umgesetzt: Fragen in natürlicher Sprache werden regelbasiert in nachprüfbare Filter übersetzt, und die Fragenerkennung besitzt eine Schnittstelle für ein späteres Sprachmodell. Ein Chat mit frei formulierten Antworten, Zusammenfassungen und KI-Klassifikation bleiben Weiterentwicklung.

| Priorität | Arbeit |
|---|---|
| P0 – Kernvalidierung | Energie-/Klima-Themen bestätigen, WWF-Szenarien durchführen, relevante Änderungen zuverlässig zuordnen |
| P1 – Übergabe | Dokumentation, SMTP-Abstimmung, reproduzierbare Demo und Nachweise |
| P2 – Anschlussfähigkeit | Technischen Azure-Handover vorbereiten; konkrete Integration erfolgt bei Übernahme durch WWF. Backups, Jobpersistenz und Betriebsanforderungen dokumentieren |
| P3 – Erweiterung | KI-Klassifikation, Zusammenfassungen, Chat mit Quellenangaben, Visualisierungen und weitere Komfortfunktionen |

Zusatzfunktionen wie Google und mehrere Empfänger sind technische Erweiterungen. Ihre Umsetzung ersetzt keine fachliche Freigabe des Kern-MVP. [Anforderungen](../02-requirements/requirements.md) und [Akzeptanzkriterien](../02-requirements/acceptance-criteria.md) machen diese Unterscheidung prüfbar.
