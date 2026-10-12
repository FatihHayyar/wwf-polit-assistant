# Ergebnisbericht – öffentliche Arbeitsfassung

**Kein final abgegebener WIPRO-Bericht.** Dieses Dokument ist eine öffentliche, bereinigte Ergebnisübersicht. Der formale Kursbericht mit Deckblatt, signiertem Auftrag, tatsächlichen Unterschriften und privaten Nachweisen bleibt ausserhalb des Repositorys.

## Problem und Ziel

Der MVP soll OpenParlData für ein WWF-bezogenes Recherche- und Monitoringverfahren nutzbar machen. Kern sind strukturierte Daten, transparente Themenregeln, kombinierte Filter und die Beobachtung bestehender Inhalte. M365 wurde laut Projektverlauf aus dem aktuellen Umfang genommen. AI und Dialogabfragen werden nach der aktuellen Projektklärung als Weiterentwicklung geführt. Azure-Anschlussfähigkeit wird dokumentiert; die konkrete Integration übernimmt WWF bei einer Übernahme.

## Vorgehen und Ergebnis

Anforderungen wurden iterativ aus Auftrag und Praxisfeedback konkretisiert. Der aktuelle Python/FastAPI-MVP verwendet PostgreSQL, Docker und OpenAPI. Neun öffentliche Bereiche besitzen Recherche und verknüpfte Details. Regeln ordnen Themen zu; Filter und Einzel-Watches wählen relevante Änderungen. Bestätigte Ziele erhalten SMTP-Zusammenfassungen. Die technische Dokumentation umfasst Installation, Architektur, Konzepte, Tests und Betrieb.

## Nachweis und Grenzen

Die vorhandene isolierte Suite umfasst 78 erfolgreiche Tests; JavaScript- und lokale Browserprüfungen ergänzen die Evidenz. Fehlerfälle führten zu robusteren Quellmappings und zusätzlichen Dokumenten-Bestandsprüfungen. Diese Ergebnisse gelten für konkrete Arbeitsstände und ersetzen keine fachliche Abnahme.

Offen sind die endgültige Energie-/Klima-Taxonomie, WWF-Szenarien und quantitative Klassifikationsgüte. Organisationsversand und Zielumgebung sind bei der späteren betrieblichen Übernahme durch WWF zu prüfen. Eine gemessene Zeitersparnis oder vollständige historische Quellenabdeckung wird nicht behauptet. Es gibt keinen implementierten Chatbot oder LLM-Dienst.

## Empfehlungen

Taxonomie und Scope bestätigen, unabhängige Fachbeispiele prüfen, WWF-Szenarien dokumentieren und den Betreiberstart in einer Testumgebung durchlaufen. Weitere AI- oder Dialogfunktionen benötigen einen gesonderten Vergleich gegen den regelbasierten MVP.

## Quellen und KI

Grundlage sind bereitgestellter Auftrag, bereinigtes Praxisfeedback, Quellcode, Tests und historische Reviews. Die Unterlagen dienten als fachliche Quellen, nicht als Auftrag für automatische Nachrichten oder Abgaben. Ein KI-Coding-Assistent unterstützte Code, Diagnose und diese Dokumentation. Eigenprüfung, Originalquellen und konkrete Versionsstände bleiben erforderlich.

Weiterführend: [Anforderungen](../02-requirements/requirements.md), [Testergebnisse](../05-testing/test-results.md), [Evaluation](evaluation-report.md) und [Erkenntnisse](lessons-learned.md).
