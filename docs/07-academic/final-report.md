# Ergebnisbericht – öffentliche Arbeitsfassung

**Kein final abgegebener WIPRO-Bericht.** Dieses Dokument ist eine öffentliche, bereinigte Ergebnisübersicht. Der formale Kursbericht mit Deckblatt, signiertem Auftrag, tatsächlichen Unterschriften und privaten Nachweisen bleibt ausserhalb des Repositorys.

## Problem und Ziel

Der MVP soll OpenParlData für ein WWF-bezogenes Recherche- und Monitoringverfahren nutzbar machen. Kern sind strukturierte Daten, transparente Themenregeln, kombinierte Filter und die Beobachtung bestehender Inhalte. M365 wurde laut Projektverlauf aus dem aktuellen Umfang genommen. Die in der Aufgabenstellung genannte dialogorientierte Abfrage ist regelbasiert umgesetzt; KI-Funktionen werden als Weiterentwicklung geführt, die Architektur sieht dafür Schnittstellen vor. Azure-Anschlussfähigkeit wird dokumentiert; die konkrete Integration übernimmt WWF bei einer Übernahme.

## Vorgehen und Ergebnis

Anforderungen wurden iterativ aus Auftrag und Praxisfeedback konkretisiert. Der aktuelle Python/FastAPI-MVP verwendet PostgreSQL, Docker und OpenAPI. Neun öffentliche Bereiche besitzen Recherche und verknüpfte Details. Regeln ordnen Themen zu; bis zu zehn Abonnements je Konto (Themen, Kantone, Geschäftstypen, Stichwörter, Bereiche) und Einzel-Watches wählen relevante Änderungen. Fragen in natürlicher Sprache werden in Filter übersetzt. Die Synchronisierung liest täglich nur Änderungen, neue und fehlende IDs und vergleicht den Bestand in festen Abständen vollständig. Bestätigte Ziele erhalten SMTP-Zusammenfassungen. Die technische Dokumentation umfasst Installation, Architektur, Konzepte, Tests und Betrieb.

## Nachweis und Grenzen

Am 21. Oktober umfasst die isolierte Suite 151 erfolgreiche Tests, davon 26 über den vollständigen HTTP-Stack; eine CI prüft zusätzlich Lint, Migrationen auf PostgreSQL 17 und den Docker-Build. Ein Edge-Durchlauf der Demo bestätigte Frage, Registrierung, zwei Abonnements, Testbenachrichtigung und Abmeldung. Der tägliche Geschäftsabgleich sank von 74 Minuten auf rund 3 Sekunden. Alle 2'958'331 Inhaltsdatensätze sind mit `rule-based-v8` klassifiziert.

Die Klassifikation wurde dreifach gemessen. Auf dem Entwicklungsset, an dem die Regeln verbessert wurden, erreichen sie 50/50. Auf einem ersten blind annotierten Prüfset von 300 zufälligen Geschäften erkannte v7 WWF-relevante Geschäfte mit Precision 1.0 und Recall 0.325. Nach der Überarbeitung erreichte v8 auf einem zweiten, vorher gezogenen Prüfset Precision 1.0 (95 %-KI 0.86–1.0) und Recall 0.667 (0.50–0.80); v7 kam auf demselben Set auf 0.361. Die Regeln bleiben präzise und übersehen noch rund ein Drittel der relevanten Geschäfte. Die Prüfset-Labels stammen von einem KI-Assistenten, nicht von WWF-Fachpersonen. Nachweis: [Prüfset-Auswertung](../05-testing/evidence/holdout-evaluation.md).

Eine Sicherheitsdurchsicht führte zu einheitlichen Antworten bei Registrierung und Anmeldung, Ratenbegrenzung, Bestätigungsseiten für E-Mail-Links, Token-Widerruf beim Abmelden und strikten Sicherheits-Headern.

Offen sind die fachliche Freigabe der Energie-/Klima-Taxonomie, WWF-Szenarien, eine fachliche Annotation der Prüfsets und eine weitere Verbesserung des Recalls. Organisationsversand und Zielumgebung sind bei der späteren betrieblichen Übernahme durch WWF zu prüfen. Eine gemessene Zeitersparnis oder vollständige historische Quellenabdeckung wird nicht behauptet. Es gibt keinen implementierten Chatbot mit frei formulierten Antworten und keinen LLM-Dienst.

## Empfehlungen

Taxonomie bestätigen, die Prüfsets von WWF-Fachpersonen nachannotieren lassen, WWF-Szenarien dokumentieren und den Betreiberstart in einer Azure-Testumgebung nach der Integrationsanleitung durchlaufen. Eine KI-Klassifikation oder ein Chat mit Quellenangaben wird über die vorhandenen Schnittstellen angeschlossen und mit denselben Prüfsets gegen die Regeln verglichen.

## Quellen und KI

Grundlage sind bereitgestellter Auftrag, bereinigtes Praxisfeedback, Quellcode, Tests und historische Reviews. Die Unterlagen dienten als fachliche Quellen, nicht als Auftrag für automatische Nachrichten oder Abgaben. KI-Coding-Assistenten (Codex; am 21. Oktober Claude) unterstützten Code, Diagnose, Tests, diese Dokumentation und die Annotation des Prüfsets. Eigenprüfung, Originalquellen und konkrete Versionsstände bleiben erforderlich.

Weiterführend: [Anforderungen](../02-requirements/requirements.md), [Testergebnisse](../05-testing/test-results.md), [Evaluation](evaluation-report.md) und [Erkenntnisse](lessons-learned.md).
