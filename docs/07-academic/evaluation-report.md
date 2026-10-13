# Evaluationsbericht – Zwischenstand

Die technische Verifikation und die fachliche Validation sind getrennt. Aktuell sind Implementierung und isolierte Regressionen nachgewiesen; unabhängige WWF-Abnahme, Klassifikationsmessung und Produktionsbetrieb stehen aus.

| Fragestellung | Vorhandener Nachweis | Fehlender Nachweis |
|---|---|---|
| Werden bekannte Quellformen verarbeitet? | Mapping-/Beziehungstests | Breitere unabhängige Quellenkontrolle |
| Funktionieren Recherche und Monitoring technisch? | API/UI-, Matcher- und Policyprüfungen | Repräsentative WWF-Szenarien |
| Sind Themen fachlich geeignet? | Provisorische Regeln und Evidenz | Expertenfreigabe und annotierte Beispiele |
| Ist Monitoring praktisch nützlich? | Implementierte Filter/Watches | Praxisfeedback und ggf. gemessener Vergleich |
| Ist der Betrieb zuverlässig? | Lokale Demo und Einzelbeobachtungen | Organisations-SMTP, Azure, Restore und Dauerbetrieb |

## Vorgeschlagene Klassifikationsevaluation

Am 13. Oktober wurde ein gezielt zusammengestelltes Entwicklungsset mit 50 realen Quellen ausgewertet: bisherige Regeln 40/50, aktuelle Regeln 50/50. Erwartungen wurden unabhängig aus den Quellen festgelegt, jedoch nicht von WWF-Fachpersonen freigegeben. Da die Regeln anhand des Sets verbessert wurden, ersetzt es kein getrenntes ungesehenes Prüfset. Der abgeschlossene Backfill über 2.951.254 Datensätze belegt technische Abdeckung, keine globale Fachgüte. Nachweise: [Prüfung vom 13. Oktober](../05-testing/review-2026-10-13.md).

Pro Kategorie positive und negative Beispiele verschiedener Kantone/Zeitpunkte sammeln und durch Fachpersonen annotieren lassen. Entwicklungs- und Prüfbeispiele getrennt halten. Mehrfachkategorien und Uneinigkeit transparent dokumentieren. Noch keine Stichprobengrösse oder Schwelle als genehmigt behaupten.

Precision ist der Anteil korrekt relevanter Treffer, Recall der gefundene Anteil der relevanten Beispiele. F1 kombiniert beide. Bei undefinierten Nennern keinen perfekten Wert eintragen. Grundlage: [Manning et al., Evaluation ungerankter Treffermengen](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html).

Keine unabhängigen Expertenwerte für Precision, Recall oder F1 vorhanden. Eine Recherchezeitersparnis benötigt einen eigenen Vergleich identischer Aufgaben; sie wird aus der Existenz einer Oberfläche nicht abgeleitet. Quellstichproben und Demo sind ebenfalls nicht automatisch repräsentativ für alle historischen Daten.
