# Regelbasierte Klassifikation – Backfill `rule-based-v7`

**Stand: 13. Oktober 2026.**

Die experimentelle Ollama-Anbindung und ihre Versuchsdateien wurden entfernt. Ausgehend vom Commit `b20f074` wurden ausschliesslich regelbasierte Verbesserungen erneut umgesetzt.

Jeder der vier Hauptbereiche besitzt eine lokale Kategorie **Sonstiges**. Kategorien, Übersetzungen, Synonyme, Abgleichsarten und Schwellenwerte werden in `app/classification/taxonomy.json` gepflegt. Gelöschte Kategorien und Regeln werden deaktiviert, damit historische Referenzen erhalten bleiben.

Eindeutige Begriffe im Titel werden auch in Komposita und mit Flexionsendungen erkannt. Allgemeine Begriffe aus Verwaltung, Politik, Budget und Bildung erzeugen ohne Umweltbezug keine Klassifikation. Wird innerhalb eines Hauptbereichs ein spezifisches Unterthema erkannt, entfällt das lokale Sonstiges; unterschiedliche Themen können gemeinsam vergeben werden. Ein reales Dokument mit fehlerhaftem HTML hatte den Massenlauf angehalten; eine textbewahrende Fehlertoleranz wurde ergänzt und der Lauf an der unterbrochenen Stelle fortgesetzt.

## Entwicklungsset

Frühere Regeln **40/50**, aktuelle Regeln **50/50** (eindeutige WWF-Beispiele 20/20, fachfremde Beispiele 20/20, unklare oder mehrthematische Beispiele 10/10). Die Regeln wurden anhand dieser Beispiele verbessert; das Ergebnis ist deshalb keine unverzerrte Qualitätsschätzung. Einzelergebnisse: [rule-quality-development-set.md](rule-quality-development-set.md). Die Messung auf ungesehenen Daten steht in [holdout-evaluation.md](holdout-evaluation.md).

## Technische Prüfung

90 automatisierte Tests und die Frontend-Prüfungen waren erfolgreich. Parallele und serielle Auswertung lieferten für 300 Datensätze identische Kategorien, Punktzahlen und Konfidenzstufen; bei diesem Vergleich wurde nicht in PostgreSQL geschrieben.

## Abgeschlossener Backfill

In neun Bereichen wurden **2.951.254 Datensätze** mit `rule-based-v7` klassifiziert. Eine unabhängige, schreibgeschützte Abfrage bestätigte je Bereich **0 fehlende und 0 veraltete Zuordnungen**. Quelldaten wurden nicht verändert, Benachrichtigungen wurden nicht erzeugt. Detaillierte Zahlen: [rule_backfill_status.json](rule_backfill_status.json).

| Bereich | Klassifizierte Datensätze |
|---|---:|
| Affairs | 326.124 |
| Agendas | 423.161 |
| Meetings | 33.677 |
| Votings | 77.144 |
| Events | 916.688 |
| Documents | 909.151 |
| Texts | 226.062 |
| Groups | 8.886 |
| Interests | 30.361 |

Zum Zeitpunkt des Laufs waren API und Scheduler nicht gestartet; nur der PostgreSQL-Container lief. Konfigurations- und Neuberechnungsbefehle stehen in [configuration.md](../../configuration.md).
