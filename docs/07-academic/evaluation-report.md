# Evaluationsbericht – Zwischenstand

Die technische Verifikation und die fachliche Validation sind getrennt. Aktuell sind Implementierung, isolierte Regressionen und zwei unabhängige Klassifikationsmessungen nachgewiesen; WWF-Abnahme, fachliche Annotation und Produktionsbetrieb stehen aus.

| Fragestellung | Vorhandener Nachweis | Fehlender Nachweis |
|---|---|---|
| Werden bekannte Quellformen verarbeitet? | Mapping-/Beziehungstests | Breitere unabhängige Quellenkontrolle |
| Funktionieren Recherche und Monitoring technisch? | API/UI-, Matcher- und Policyprüfungen | Repräsentative WWF-Szenarien |
| Sind Themen fachlich geeignet? | Regeln v8 nach WWF-Themenliste; Prüfset B: Precision 1.0, Recall 0.667 | Expertenfreigabe und fachliche Annotation |
| Ist Monitoring praktisch nützlich? | Mehrere Abonnements, Watches, Fragen in natürlicher Sprache | Praxisfeedback und ggf. gemessener Vergleich |
| Ist die Aktualisierung effizient? | Geschäfte inkrementell rund 3 s statt 74 min; alle Checkpoints aktuell | Beobachtung über mehrere Wochen inkl. vollständiger Vergleiche |
| Ist der Betrieb zuverlässig? | Lokale Demo und Einzelbeobachtungen | Organisations-SMTP, Azure, Restore und Dauerbetrieb |

## Klassifikationsevaluation

Am 13. Oktober wurde ein gezielt zusammengestelltes Entwicklungsset mit 50 realen Quellen ausgewertet: bisherige Regeln 40/50, aktuelle Regeln 50/50. Erwartungen wurden unabhängig aus den Quellen festgelegt, jedoch nicht von WWF-Fachpersonen freigegeben. Da die Regeln anhand des Sets verbessert wurden, ersetzt es kein getrenntes ungesehenes Prüfset. Die abgeschlossenen Backfills (v7: 2.951.254, v8: 2.958.331 Datensätze) belegen technische Abdeckung, keine globale Fachgüte. Nachweise: [Prüfung vom 13. Oktober](../05-testing/review-2026-10-13.md).

Am 21. Oktober wurde ein getrenntes Prüfset gezogen: 300 Geschäfte in reproduzierbarer Zufallsreihenfolge, ohne Überschneidung mit dem Entwicklungsset, blind anhand der Kategoriendefinitionen annotiert. Ergebnis für `rule-based-v7`: 268/300 streng korrekt; WWF-Relevanz TP 13, FP 0, FN 27, TN 227, also Precision 1.0 (95 %-Wilson-Intervall 0.77–1.0) und Recall 0.325 (0.20–0.48). Die Fehler betreffen fehlende Fachbegriffe, französische und italienische Titel sowie Umschreibungen ohne Schlüsselbegriff. Details und Fehlerliste: [Prüfset-Auswertung](../05-testing/evidence/holdout-evaluation.md).

Die Fehlerliste von Prüfset A floss in `rule-based-v8` ein (fehlende Fachbegriffe, Übersetzungen, Infix-Begriffe, getrennte Rechenzentren/Grossverbraucher, Ausschlussregeln). Damit ist A für v8 nicht mehr unabhängig. Deshalb wurde vor der Messung von v8 ein zweites Prüfset B gezogen und blind annotiert (300 Geschäfte, ohne Überschneidung mit A und dem Entwicklungsset). Erstmessung von v8 auf B: TP 24, FP 0, FN 12, TN 223, Precision 1.0 (0.86–1.0), Recall 0.667 (0.50–0.80), F1 0.80. v7 erreichte auf B Recall 0.361. Die Erstmessung ist unverändert gespeichert; eine danach behobene Fehlerursache ist in den aktuellen Werten enthalten und gesondert ausgewiesen.

Einschränkungen: Die Labels stammen von einem KI-Assistenten und einer einzigen Annotation; eine Übereinstimmungsmessung fehlt. Es gibt je Prüfset nur 36–40 eindeutig positive Fälle, gemessen wurden nur Geschäfte, und die Taxonomie ist nicht freigegeben. Als nächster Schritt sollten WWF-Fachpersonen die Prüfsets nachannotieren. Nach weiteren Regelverbesserungen wird mit einem neu gezogenen Prüfset gemessen.

Precision ist der Anteil korrekt relevanter Treffer, Recall der gefundene Anteil der relevanten Beispiele. F1 kombiniert beide. Bei undefinierten Nennern keinen perfekten Wert eintragen. Grundlage: [Manning et al., Evaluation ungerankter Treffermengen](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html).

Expertenwerte für Precision, Recall oder F1 liegen weiterhin nicht vor. Eine Recherchezeitersparnis benötigt einen eigenen Vergleich identischer Aufgaben; sie wird aus der Existenz einer Oberfläche nicht abgeleitet. Quellstichproben und Demo sind ebenfalls nicht automatisch repräsentativ für alle historischen Daten.
