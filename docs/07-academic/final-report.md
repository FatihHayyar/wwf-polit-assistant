# Ergebnisbericht – öffentliche Arbeitsfassung

**Kein final abgegebener WIPRO-Bericht.** Dieses Dokument ist eine öffentliche, bereinigte Ergebnisübersicht. Der formale Kursbericht mit Deckblatt, signiertem Auftrag, tatsächlichen Unterschriften und privaten Nachweisen bleibt ausserhalb des Repositorys.

## Problem und Ziel

Der MVP soll OpenParlData für ein WWF-bezogenes Recherche- und Monitoringverfahren nutzbar machen. Kern sind strukturierte Daten, transparente Themenregeln, kombinierte Filter und die Beobachtung bestehender Inhalte. M365 wurde laut Projektverlauf aus dem aktuellen Umfang genommen. AI und Dialogabfragen werden nach der aktuellen Projektklärung als Weiterentwicklung geführt. Azure-Anschlussfähigkeit wird dokumentiert; die konkrete Integration übernimmt WWF bei einer Übernahme.

## Vorgehen und Ergebnis

Anforderungen wurden iterativ aus Auftrag und Praxisfeedback konkretisiert. Der aktuelle Python/FastAPI-MVP verwendet PostgreSQL, Docker und OpenAPI. Neun öffentliche Bereiche besitzen Recherche und verknüpfte Details. Regeln ordnen Themen zu; Filter und Einzel-Watches wählen relevante Änderungen. Bestätigte Ziele erhalten SMTP-Zusammenfassungen. Die technische Dokumentation umfasst Installation, Architektur, Konzepte, Tests und Betrieb.

## Nachweis und Grenzen

Am 21. Oktober umfasst die isolierte Suite 124 erfolgreiche Tests, davon 26 über den vollständigen HTTP-Stack; eine CI prüft zusätzlich Lint, Migrationen auf PostgreSQL 17 und den Docker-Build. Ein Edge-Durchlauf der Demo bestätigte Registrierung, Testbenachrichtigung und Abmeldung. Fehlerfälle führten zu robusteren Quellmappings und zusätzlicher Text-/Dokumentenbehandlung. Alle 2'951'254 Inhaltsdatensätze sind mit `rule-based-v7` klassifiziert.

Die Klassifikation wurde zweifach gemessen. Auf dem Entwicklungsset, an dem die Regeln verbessert wurden, erreichen sie 50/50. Auf einem blind annotierten Prüfset von 300 zufälligen Geschäften erkennen sie WWF-relevante Geschäfte mit Precision 1.0 (95 %-KI 0.77–1.0) und Recall 0.325 (0.20–0.48). Die Regeln sind also präzise, übersehen aber rund zwei Drittel der relevanten Geschäfte. Die Prüfset-Labels stammen von einem KI-Assistenten, nicht von WWF-Fachpersonen. Nachweis: [Prüfset-Auswertung](../05-testing/evidence/holdout-evaluation.md).

Eine Sicherheitsdurchsicht führte zu einheitlichen Antworten bei Registrierung und Anmeldung, Ratenbegrenzung, Bestätigungsseiten für E-Mail-Links, Token-Widerruf beim Abmelden und strikten Sicherheits-Headern.

Offen sind die endgültige Energie-/Klima-Taxonomie, WWF-Szenarien, eine fachliche Annotation des Prüfsets und eine Verbesserung des Recalls. Organisationsversand und Zielumgebung sind bei der späteren betrieblichen Übernahme durch WWF zu prüfen. Eine gemessene Zeitersparnis oder vollständige historische Quellenabdeckung wird nicht behauptet. Es gibt keinen implementierten Chatbot oder LLM-Dienst.

## Empfehlungen

Taxonomie und Scope bestätigen, das Prüfset von WWF-Fachpersonen nachannotieren lassen, die Regeln um fehlende Fachbegriffe und Übersetzungen erweitern und mit einem neuen Prüfset messen, WWF-Szenarien dokumentieren und den Betreiberstart in einer Testumgebung durchlaufen. Weitere AI- oder Dialogfunktionen werden mit demselben Prüfset gegen den regelbasierten MVP verglichen.

## Quellen und KI

Grundlage sind bereitgestellter Auftrag, bereinigtes Praxisfeedback, Quellcode, Tests und historische Reviews. Die Unterlagen dienten als fachliche Quellen, nicht als Auftrag für automatische Nachrichten oder Abgaben. KI-Coding-Assistenten (Codex; am 21. Oktober Claude) unterstützten Code, Diagnose, Tests, diese Dokumentation und die Annotation des Prüfsets. Eigenprüfung, Originalquellen und konkrete Versionsstände bleiben erforderlich.

Weiterführend: [Anforderungen](../02-requirements/requirements.md), [Testergebnisse](../05-testing/test-results.md), [Evaluation](evaluation-report.md) und [Erkenntnisse](lessons-learned.md).
