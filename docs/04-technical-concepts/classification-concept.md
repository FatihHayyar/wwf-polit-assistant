# Klassifikationskonzept

Die WWF-Zuordnung ist regelbasiert. Mehrsprachige Begriffe und Muster, Gewichte, Scores und Evidenz bilden die Entscheidungsbasis. Es ist kein LLM oder trainiertes Modell eingebunden. Verknüpfte Inhalte können zur Einordnung eines Geschäfts beitragen; weitere Datentypen besitzen eigene Klassifikationen.

## Themenbaum und Matching

Kategorien sind hierarchisch organisiert. Ein Abonnement oder Suchfilter eines Hauptthemas umfasst dessen Unterthemen. Eigene und über verknüpfte Geschäfte verfügbare Klassifikationen unterstützen Recherche und Monitoring. Jedes der vier Hauptthemen besitzt eine lokale Sonstiges-Unterkategorie für erkannte Themen ohne spezifisches Unterthema. Davon getrennt ist globales Sonstiges für Inhalte ohne erkannte WWF-Zuordnung. Die Oberfläche zeigt **Hauptthema / Unterthema**.

Der Themenbaum liegt in [taxonomy.json](../../app/classification/taxonomy.json), nicht als Python-Literal im Code. Namen, Übersetzungen, Hierarchie, Reihenfolge, Schwellenwerte und Konzepte sind editierbar. Stabile Codes erhalten Datenbankreferenzen; entfernte Kategorien und Regeln werden beim Seeding deaktiviert. Die Datei wird validiert: genau ein globaler Fallback und je gewöhnlichem Hauptthema genau ein lokaler Fallback. Details: [Konfiguration](../configuration.md#regelbasierte-klassifikation).

`rule-based-v8` zählt Übersetzungen und Synonyme desselben Konzepts einmal. Ein starkes Titelkonzept genügt bei erreichtem Schwellenwert; Inhalt benötigt zwei unterschiedliche starke Konzepte. Generische Kontextkonzepte benötigen einen Umwelt-Qualifier derselben Kategorie. Diese Kombination ist eine Kategorieprüfung, keine Analyse syntaktischer Beziehungen zwischen Wörtern. Titel werden zuerst geprüft; akzeptierte Titelzuordnungen beenden die Inhaltsprüfung. Die Klassifikation kann mehrere Unterthemen liefern. Spezifische Unterthemen entfernen nur den lokalen Fallback desselben Elternbereichs.

Opt-in-Präfixregeln erlauben Buchstaben-Endungen am letzten Wort ab fünf Zeichen, etwa Photovoltaikanlage oder Windenergie-Nutzung; kurze Begriffe bleiben exakt. Infix-Regeln (ab acht Zeichen) finden einen Begriff auch mitten in Zusammensetzungen, etwa «wasserkraft» in «Kleinwasserkraftwerk». Ausschlussregeln (Gewicht 0) verhindern bekannte Fehltreffer, etwa Ortsnamen wie «Plaines-du-Loup» beim Wolf. Konzepte können auf Titel oder Inhalt beschränkt werden: Öffentliche Akteure wie «Kanton» oder «Verwaltung» zählen nur im Titel, weil sie in fast jedem Vorstosstext vorkommen. HTML, typografische Apostrophe, Unicode und PDF-Zeilentrennungen werden normalisiert. Bei fehlerhaftem HTML bleibt der ursprüngliche Text zur Auswertung erhalten. Gewichte und Evidenz unterstützen die Nachvollziehbarkeit; Confidence ist kein kalibrierter Wahrscheinlichkeitswert.

## Provisorische Fachlogik

Der initiale WWF-Fokus umfasst Energie und Klima mit den Unterthemen erneuerbare Wärme, erneuerbarer Strom, Gebäudeeffizienz, Elektromobilität, Vorbildfunktion der öffentlichen Hand, Rechenzentren und Grossverbraucher. Seit v8 entspricht der Themenbaum diesem Fokus: Rechenzentren (`data_centers`) und Grossverbraucher (`large_consumers`) sind getrennte Unterthemen, die Vorbildfunktion der öffentlichen Hand (`public_sector`) gehört zu Klima & Energie. Die frühere gemeinsame Kategorie ist über `"replaces"` mit beiden Nachfolgern verbunden; bestehende Abonnements wurden übertragen. Mobilität ist weiterhin breiter als Elektromobilität, Begriffe zur Kühlung fehlen noch.

Die übrigen Hauptthemen decken die in der Aufgabenstellung genannten Bereiche Biodiversität, Gewässer, Landwirtschaft und Raumplanung ab. Die fachliche Freigabe durch WWF steht aus.

## Historische Vorbereitung

```powershell
python -m scripts.seed_classification
python -m scripts.rule_quality
python -m scripts.reclassify_rules --dataset affairs --limit 20
python -m scripts.reclassify_rules --apply
python -m scripts.rule_backfill_status
```

Ohne `--apply` ist die PostgreSQL-Neuberechnung schreibgeschützt. `--apply` verlangt ein erfolgreiches Entwicklungsset, synchronisiert die Taxonomie und verarbeitet alle neun Bereiche unter derselben Sperre wie der Sync-Runner. Batches werden einzeln gespeichert; vollständige aktuelle Zuordnungen werden bei Wiederaufnahme übersprungen. Nach Regel-/Taxonomieänderungen `--force` nutzen. Dokumente und Texte verwenden bis zu vier lesende Arbeitsprozesse; Datenbankänderungen erfolgen im Hauptprozess. Quellen und Benachrichtigungen werden nicht verändert. Die älteren Jobs `classify_affairs` und `classify_entities` bleiben verfügbar, besitzen aber nicht diese gemeinsame Qualitätsschranke.

Am 21. Oktober wurden alle 2.958.331 Datensätze mit v8 neu klassifiziert (zuvor am 13. Oktober mit v7). 26.781 Geschäfte (8,2 %) erhielten ein WWF-Thema. Das ist ein lokaler Ausführungsnachweis; eine neue Installation benötigt ihren eigenen Backfill. Laufzeit hängt insbesondere von der Textmenge ab.

## Evaluation

Expertenbeispiele vor Regelanpassung und Prüfung trennen. Kategorien, positive/negative Fälle und strittige Beispiele dokumentieren. Aus vorhandenen Klassifikationszeilen keine Precision-/Recall-Werte ableiten. Die [Evaluation](../07-academic/evaluation-report.md) definiert die noch offenen fachlichen Nachweise.

Das Entwicklungsset enthält 50 reale Datensätze mit unabhängigen Quellenannotationen, aber ohne WWF-Expertenfreigabe: 20 eindeutige WWF-Themen, 20 fachfremde und zehn Grenzfälle. Alte Regeln erreichten 40/50, v7 und v8 50/50. Die Regeln wurden anhand dieses Sets entwickelt; es dient deshalb als Regressionsprüfung.

Die Qualität auf ungesehenen Daten messen zwei Prüfsets mit je 300 zufälligen, blind annotierten Geschäften (`python -m scripts.evaluate_holdout`):

| Prüfset | Rolle | v7 | v8 |
|---|---|---|---|
| A (am 21. Oktober gezogen) | unabhängige Messung von v7; seine Fehlerliste floss in v8 ein | Precision 1.0, Recall 0.325 | nicht mehr unabhängig |
| B (vor der Messung von v8 gezogen) | unabhängige Messung von v8 | Precision 1.0, Recall 0.361 | **Precision 1.0, Recall 0.667, F1 0.80** |

v8 verdoppelt den Recall, ohne die Precision zu senken. Nach der Erstmessung auf B wurde eine Fehlerursache behoben, die auch ausserhalb von B auftrat; die aktuellen Werte auf B (Recall 0.639) enthalten diese Korrektur, die Erstmessung bleibt die unabhängige Schätzung. Die verbleibenden Fehler betreffen indirekte Formulierungen ohne Fachbegriff, etwa «Nachtabschaltung der Strassenbeleuchtung» oder «Fischtreppe». Ein Prüfset darf nicht zum Anpassen der Regeln verwendet werden; nach weiteren Regeländerungen ist ein neues Prüfset zu ziehen. [Auswertung](../05-testing/evidence/holdout-evaluation.md)
