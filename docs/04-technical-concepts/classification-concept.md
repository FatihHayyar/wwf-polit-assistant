# Klassifikationskonzept

Die WWF-Zuordnung ist regelbasiert. Mehrsprachige Begriffe und Muster, Gewichte, Scores und Evidenz bilden die Entscheidungsbasis. Es ist kein LLM oder trainiertes Modell eingebunden. Verknüpfte Inhalte können zur Einordnung eines Geschäfts beitragen; weitere Datentypen besitzen eigene Klassifikationen.

## Themenbaum und Matching

Kategorien sind hierarchisch organisiert. Ein Abonnement eines Hauptthemas umfasst dessen Unterthemen. Eigene und über verknüpfte Geschäfte verfügbare Klassifikationen unterstützen Recherche und Monitoring. Eine Auffangkategorie signalisiert keine positive fachliche Klassifikation.

## Provisorische Fachlogik

Der initiale WWF-Fokus umfasst Energie und Klima mit den genannten Unterthemen Wärme, Strom, Gebäudeeffizienz, Elektromobilität, öffentliche Hand, Rechenzentren und Grossverbraucher. Der aktuelle Themenbaum ist breiter und nicht fachlich freigegeben. Rechenzentren und Grossverbraucher sind kombiniert; Mobilität ist breiter als Elektromobilität; öffentliche Hand befindet sich unter einem anderen Hauptthema.

Diese Abweichungen vor einem Qualitätsurteil mit WWF klären. Ein Split oder eine Verschiebung kann Regeln, gespeicherte Klassifikationen und Abonnements betreffen.

## Historische Vorbereitung

```powershell
python -m scripts.seed_classification
python -m scripts.classify_affairs
python -m scripts.classify_entities
```

Die Jobs verändern Klassifikationsdaten und können auf grossen Beständen lange laufen. Die Entity-Klassifikation kann mit `--dataset` eingegrenzt und mit `--force` neu aufgebaut werden. Historischer Backfill ist kein Nachweis neuer politischer Entwicklungen und erzeugt nicht automatisch einen fachlich bestätigten Alert.

## Evaluation

Expertenbeispiele vor Regelanpassung und Prüfung trennen. Kategorien, positive/negative Fälle und strittige Beispiele dokumentieren. Aus vorhandenen Klassifikationszeilen keine Precision-/Recall-Werte ableiten. Die [Evaluation](../07-academic/evaluation-report.md) definiert die noch offenen fachlichen Nachweise.
