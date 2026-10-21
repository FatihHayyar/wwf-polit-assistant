# Entscheidungsregister

Datums- und Personenangaben werden hier nicht ergänzt. Retrospektiv beschriebene Entscheidungen sind als solche gekennzeichnet.

| ID | Entscheidung | Begründung / Quelle | Stand |
|---|---|---|---|
| D1 | M365 aus aktuellem MVP ausnehmen | Kick-off laut Projektverlauf | Retrospektiv; Originalbestätigung privat beilegen |
| D2 | KI als spätere Erweiterung führen; Dialogabfrage regelbasiert umsetzen | Aufgabenstellung verlangt eine dialogorientierte Abfrage und eine KI-fähige Architektur | Fragenerkennung regelbasiert umgesetzt (D13); KI-Funktionen bleiben Erweiterung |
| D3 | Python/FastAPI statt Java-Service | WWF-Präferenz und API-orientierter Ansatz | Implementiert; keine generelle Framework-Überlegenheit behauptet |
| D4 | Neun öffentliche Inhaltsbereiche | Auftrag und zusätzliche WWF-Relevanz | Implementiert |
| D5 | Regelbasierte Klassifikation | Nachvollziehbare MVP-Basis | Implementiert; Taxonomie/Güte offen |
| D6 | Filterabonnements und Einzel-Watches trennen | Neue Inhalte und bestehende Entwicklungen unterscheiden | Implementiert; Filterabonnements seit D12 als mehrere Abonnements |
| D7 | Änderungen speichern und Relevanz separat bewerten | Technische Updates sollen keine unnötige E-Mail erzeugen | Implementiert; fachliche Regeln weiter validieren |
| D8 | Lokale Demo mit Mailpit | Reproduzierbare Nutzung ohne realen Versand | Implementiert |
| D9 | Azure-Anschlussfähigkeit ohne eigenes Deployment liefern | Konkrete Integration bei Übernahme durch WWF | Handover-Bausteine dokumentiert |
| D10 | Kursabgabe privat halten, technische Dokumentation öffentlich strukturieren | Unterschiedliche Zwecke und personenbezogene Originale | `wipro-submission/` bleibt ignoriert |
| D11 | Sync liest nur Änderungen, neue und fehlende IDs; vollständige Vergleiche in festen Abständen | Tägliche Vollvergleiche dauerten über eine Stunde je grossem Bereich; die Quelle bietet Sortierung nach Änderungsdatum und ID, aber keinen Datumsfilter. Alternative «Exporte täglich vollständig vergleichen» verworfen (mehrere GB pro Tag) | Implementiert; Intervalle je Bereich in `FULL_SCAN_DAYS` |
| D12 | Mehrere benannte Abonnements statt eines Filtersatzes je Konto | WWF-E-Mail: mehrere Abonnements, Kombination mit Geschäftstyp. Alternative «Filtergruppen in einem Abonnement» verworfen, weil Kombinationen wie «Energie in Bern» und «Biodiversität in Zürich» sonst nicht ausdrückbar sind | Implementiert; bis zu zehn je Konto, JSON-Listen in `subscription_profiles` |
| D13 | Dialogabfrage regelbasiert, mit Schnittstelle für ein späteres Sprachmodell | Nachvollziehbar, ohne Modellbetrieb; nutzt dieselben Themenregeln wie die Klassifikation. Ein LLM-Chat hätte Betriebskosten und Halluzinationsrisiko ohne geprüfte Qualität | Implementiert (`QueryInterpreter`) |
| D14 | Rechenzentren und Grossverbraucher getrennt; Vorbildfunktion unter Klima & Energie | Themenliste in der WWF-E-Mail | Implementiert in v8; bestehende Abonnements übertragen; fachliche Freigabe offen |

Neue Entscheidungen benötigen Kontext, betrachtete Alternativen, Ergebnis und Folgen. Änderungen an der Taxonomie können eine Migration bestehender Abonnements und eine historische Neuklassifikation erfordern.

Am 13. Oktober wurde D5 bestätigt: Der getestete lokale Ollama-Ansatz verbesserte die Klassifikation nicht ausreichend und benötigte bereits für kleine Testmengen erhebliche Zeit. Er wurde verworfen; JSON-konfigurierbare Regeln und ein geprüfter Backfill bilden weiterhin die MVP-Basis. Eine eigene lokale LLM-/Chatbot-Lösung kann bei Fortsetzung im zweiten Semester separat evaluiert werden; sie ist derzeit weder implementiert noch beauftragt. Der Regel-Entwicklungstest und seine Grenzen sind in der [Prüfung vom 13. Oktober](../05-testing/review-2026-10-13.md) dokumentiert.
