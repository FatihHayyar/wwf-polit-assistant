# Klassifikationskonzept

Die WWF-Zuordnung ist regelbasiert. Mehrsprachige Begriffe und Muster, Gewichte, Scores und Evidenz bilden die Entscheidungsbasis. Es ist kein LLM oder trainiertes Modell eingebunden. Verknüpfte Inhalte können zur Einordnung eines Geschäfts beitragen; weitere Datentypen besitzen eigene Klassifikationen.

## Themenbaum und Matching

Kategorien sind hierarchisch organisiert. Ein Abonnement oder Suchfilter eines Hauptthemas umfasst dessen Unterthemen. Eigene und über verknüpfte Geschäfte verfügbare Klassifikationen unterstützen Recherche und Monitoring. Jedes der vier Hauptthemen besitzt eine lokale Sonstiges-Unterkategorie für erkannte Themen ohne spezifisches Unterthema. Davon getrennt ist globales Sonstiges für Inhalte ohne erkannte WWF-Zuordnung. Die Oberfläche zeigt **Hauptthema / Unterthema**.

Der Themenbaum liegt in [taxonomy.json](../../app/classification/taxonomy.json), nicht als Python-Literal im Code. Namen, Übersetzungen, Hierarchie, Reihenfolge, Schwellenwerte und Konzepte sind editierbar. Stabile Codes erhalten Datenbankreferenzen; entfernte Kategorien und Regeln werden beim Seeding deaktiviert. Die Datei wird validiert: genau ein globaler Fallback und je gewöhnlichem Hauptthema genau ein lokaler Fallback. Details: [Konfiguration](../configuration.md#regelbasierte-klassifikation).

`rule-based-v7` zählt Übersetzungen und Synonyme desselben Konzepts einmal. Ein starkes Titelkonzept genügt bei erreichtem Schwellenwert; Inhalt benötigt zwei unterschiedliche starke Konzepte. Generische Kontextkonzepte benötigen einen Umwelt-Qualifier derselben Kategorie. Diese Kombination ist eine Kategorieprüfung, keine Analyse syntaktischer Beziehungen zwischen Wörtern. Titel werden zuerst geprüft; akzeptierte Titelzuordnungen beenden die Inhaltsprüfung. Die Klassifikation kann mehrere Unterthemen liefern. Spezifische Unterthemen entfernen nur den lokalen Fallback desselben Elternbereichs.

Opt-in-Präfixregeln erlauben Buchstaben-Endungen am letzten Wort ab fünf Zeichen, etwa Photovoltaikanlage oder Windenergie-Nutzung; kurze Begriffe bleiben exakt. HTML, typografische Apostrophe, Unicode und PDF-Zeilentrennungen werden normalisiert. Bei fehlerhaftem HTML bleibt der ursprüngliche Text zur Auswertung erhalten. Gewichte und Evidenz unterstützen die Nachvollziehbarkeit; Confidence ist kein kalibrierter Wahrscheinlichkeitswert.

## Provisorische Fachlogik

Der initiale WWF-Fokus umfasst Energie und Klima mit den genannten Unterthemen Wärme, Strom, Gebäudeeffizienz, Elektromobilität, öffentliche Hand, Rechenzentren und Grossverbraucher. Der aktuelle Themenbaum ist breiter und nicht fachlich freigegeben. Rechenzentren und Grossverbraucher sind kombiniert; Mobilität ist breiter als Elektromobilität; öffentliche Hand befindet sich unter einem anderen Hauptthema.

Diese Abweichungen vor einem Qualitätsurteil mit WWF klären. Ein Split oder eine Verschiebung kann Regeln, gespeicherte Klassifikationen und Abonnements betreffen.

## Historische Vorbereitung

```powershell
python -m scripts.seed_classification
python -m scripts.rule_quality
python -m scripts.reclassify_rules --dataset affairs --limit 20
python -m scripts.reclassify_rules --apply
python -m scripts.rule_backfill_status
```

Ohne `--apply` ist die PostgreSQL-Neuberechnung schreibgeschützt. `--apply` verlangt ein erfolgreiches Entwicklungsset, synchronisiert die Taxonomie und verarbeitet alle neun Bereiche unter derselben Sperre wie der Sync-Runner. Batches werden einzeln gespeichert; vollständige aktuelle Zuordnungen werden bei Wiederaufnahme übersprungen. Nach Regel-/Taxonomieänderungen `--force` nutzen. Dokumente und Texte verwenden bis zu vier lesende Arbeitsprozesse; Datenbankänderungen erfolgen im Hauptprozess. Quellen und Benachrichtigungen werden nicht verändert. Die älteren Jobs `classify_affairs` und `classify_entities` bleiben verfügbar, besitzen aber nicht diese gemeinsame Qualitätsschranke.

Am 13. Oktober wurden 2.951.254 Datensätze vollständig neu klassifiziert. Das ist ein lokaler Ausführungsnachweis; eine neue Installation benötigt ihren eigenen Backfill. Laufzeit hängt insbesondere von der Textmenge ab.

## Evaluation

Expertenbeispiele vor Regelanpassung und Prüfung trennen. Kategorien, positive/negative Fälle und strittige Beispiele dokumentieren. Aus vorhandenen Klassifikationszeilen keine Precision-/Recall-Werte ableiten. Die [Evaluation](../07-academic/evaluation-report.md) definiert die noch offenen fachlichen Nachweise.

Das aktuelle Entwicklungsset enthält 50 reale Datensätze mit unabhängigen Quellenannotationen, aber ohne WWF-Expertenfreigabe: 20 eindeutige WWF-Themen, 20 fachfremde und zehn Grenzfälle. Alte Regeln erreichten 40/50, v7 50/50. Die Regeln wurden anhand dieses Sets entwickelt; ein getrenntes ungesehenes Prüfset steht aus. Quellen, Kriterien und Grenzen stehen in der [Prüfung vom 13. Oktober](../05-testing/review-2026-10-13.md).
