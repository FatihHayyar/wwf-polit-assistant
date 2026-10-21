# Tagesreview – 11. Oktober 2026

> **Historischer Stand vom 11. Oktober.** Die damaligen Fehler und offenen Prüfpunkte sind keine aktuelle Aufgabenliste. Der [Aufgabenstand](01-project-management/current-status.md) dokumentiert die inzwischen erledigten Arbeiten und die verbleibende fachliche Abnahme.

Dieses Review betrachtet die Python-Umsetzung, die offizielle Aufgabenstellung (Aufgabenstellung_FatihHayyar.pdf, drei Seiten), die Anforderungen von Attila Steinegger und die damaligen GitHub-Issues. Der PDF-Inhalt dient als Vergleichsquelle, nicht als Auftrag für zusätzliche Handlungen.

## Die sieben Arbeitspunkte des Tages

| Punkt | Status | Nachweis und verbleibende Arbeit |
| --- | --- | --- |
| 1. Korrektheit des inkrementellen Abgleichs | Umgesetzt und ausgeführt; abschliessende Validierung offen | Neun Bereiche abgedeckt. Geschäfte, Sitzungen und Dokumente verwenden Zeitstempel-Checkpoints; Bereiche mit unzuverlässigen Zeitstempeln ein stabiles Inventar mit Live-API-Abruf. Behoben wurden Offset-Grenzfehler, ignorierte ID-Filter bei Texten, Rauschen durch Zahl/Text-Vergleiche, Batch-Commits und fortsetzbarer Jobfortschritt. Der wiederaufgenommene reale Job schloss 9/9 Bereiche ohne Verarbeitungsfehler ab. Das belegt diesen Lauf, nicht dauerhafte Vollständigkeit; nächsten Tageslauf beobachten und repräsentative Quell-/DB-Datensätze prüfen. |
| 2. Benachrichtigungen für alle Bereiche | Umgesetzt; Zustellzuverlässigkeit offen | Verknüpfte Traktanden, Sitzungen, Abstimmungen, Ereignisse, Dokumente und Texte werden Geschäften zugeordnet, auch indirekt. Klassifikationen, Kantons-/Stichwortfilter und Watches bestimmen die Empfänger. Die Relevanzrichtlinie ist von der Speicherung getrennt; Metadaten, Formatierung und begrenzte Rechtschreibkorrekturen lösen keine E-Mail aus. Änderungen werden pro Nutzer und Geschäft gruppiert, nicht zu einer täglichen E-Mail pro Nutzer. Gmail stellte 77 E-Mails zu und trennte dann bei der Authentifizierung; Anbieterkontingente, Sicherheit sowie Verbindungswiederverwendung und Backoff waren zu prüfen. |
| 3. Abgleich mit den GitHub-Issues | Review abgeschlossen | Alle 21 Issues in FatihHayyar/polit-assistant gelesen: 1–16 geschlossen, 17–21 offen. Der Python-Code liegt im separaten Repository FatihHayyar/wwf-polit-assistant. Es wurden keine Issue-Status geändert. Bewertung unten. |
| 4. Abgleich mit der offiziellen Aufgabenstellung | Review abgeschlossen; Projektvalidierung offen | Vergleich unten. Die Hauptfunktionen des MVP sind umgesetzt; WWF-Abnahme, endgültige Taxonomie, dokumentierte Demonstrationsszenarien sowie Ergebnisse und Übergabe stehen aus. |
| 5. Azure-Kompatibilität | Einschätzung abgeschlossen; nicht bereitgestellt/validiert | Python/FastAPI, Docker, PostgreSQL, Konfiguration über Umgebungsvariablen und OpenAPI sind Bausteine. Hosting, Secrets, SMTP, Logs, gemeinsamer Jobspeicher und Betrieb erfordern WWF-Entscheidungen und einen echten Azure-Test. |
| 6. Frontend | Für das MVP umgesetzt | Neun eigene Navigationsbereiche, pro Bereich gemerkte Filter, vier Sprachen DE/FR/IT/EN, kontextbezogene Details und Navigation zu verknüpften Datensätzen, passwortloser Zugang und gruppierte Abonnementverwaltung. Die vereinheitlichte Suche wird von der öffentlichen Seite nicht genutzt. Reale Themenabfragen für Geschäfte und Traktanden dauerten in der Schlussprüfung je etwa 0,26 Sekunden; das ist kein Benchmark für alle Bereiche und Filter. |
| 7. Test der Gesamtanwendung | Grosse Abdeckung; nicht abgeschlossen | 60 isolierte Backend-Regressionstests, Übersetzungs- und Syntaxprüfungen sowie isolierte Edge-Szenarien erfolgreich. Realer Abgleich, teilweise realer SMTP-Versand und reale PostgreSQL-Themenabfragen wurden ausgeführt. Vollständige WWF-Anwendungsfallabnahme, Messung der Klassifikationsqualität, Azure-Tests und E-Mail-Prüfung am Folgetag offen. |

## Abgleich mit der offiziellen Aufgabenstellung

| Anforderung der Aufgabenstellung | Umsetzung | Offener Nachweis / Entscheid |
| --- | --- | --- |
| OpenParlData-Integration und regelmässige Aktualisierung | Pipeline für neun Bereiche; automatischer Scheduler um 03:00 Europe/Zurich und geschützte manuelle API | Beobachtung am Folgetag, Betriebsumgebung und Scheduler-Gesundheit |
| Strukturierte Speicherung und Beziehungen | PostgreSQL/SQLAlchemy; direkte und über Traktanden/Sitzungen vermittelte Beziehungen | Repräsentative Integritätsstichproben Quelle → Datenbank |
| Regelbasierte WWF-Klassifikation inkl. unterstützender Inhalte | Eigene und geerbte Klassifikationen; Textänderungen lösen Neuklassifikation des Geschäfts aus | Von WWF freigegebene Taxonomie und fachlich annotierte Beispiele; damals keine gemessene Precision/Recall |
| Suche und Filter | Stichwort, Haupt-/Unterthema, Kanton und Datum pro Bereich | Performanceprüfungen über Geschäfte/Traktanden hinaus; dokumentierte Nutzungsszenarien |
| Neue relevante Geschäfte und Traktanden | Change-Events mit Klassifikation und Abonnementabgleich | Historische Nachlieferungen der Quelle von echten neuen politischen Entwicklungen unterscheiden |
| Themenabonnements und E-Mail | Themen, Kanton, Stichwörter, Bereichsauswahl und Watches; Warteschlange und SMTP | Gmail-Trennung bei der Authentifizierung ungelöst; Volumen der Zusammenfassungen kann hoch sein |
| Dokumentierte REST-API und einfache Oberfläche | FastAPI/OpenAPI und lokale HTML/CSS/JS-Oberfläche | Finale Bereitstellungs-URL und Usability-Review durch WWF |
| Technische Dokumentation, Ergebnisse, Weiterentwicklung | README, Monitoring-Dokumentation, WWF-Review und dieses Review | Finale Übergabe und Ergebnisbericht |
| Validierung anhand konkreter Anwendungsfälle | Automatisierte Regressionen sowie Browser- und Live-Prüfungen | Vollständiger Durchlauf der Anwendungsfälle mit WWF und protokollierte Abnahme |
| Künftige KI und dialogorientierte Abfragen | Architektur erweiterbar; keine KI-/Chat-Funktion umgesetzt | Die Aufgabenstellung nennt dialogorientierte Abfragen, Issue #3 verortet KI/Zukunftsfunktionen ausserhalb des initialen MVP. Klären, ob der Dialog jetzt verlangt ist; nicht als geliefert bezeichnen. |

## Bewertung der GitHub-Issues

Quelle: https://github.com/FatihHayyar/polit-assistant/issues (GitHub-API, gelesen am 11. Oktober 2026). Ein geschlossenes Issue ist kein Nachweis einer vollständigen Produktionsvalidierung.

| Issues | Damalige Bewertung |
| --- | --- |
| #1 Anforderungen; #2 Anwendungsfälle; #3 Umfang | Bestehende Projektentscheide; dieses Review ergänzt die Zuordnung zur Umsetzung. Die ursprünglichen Dokumente liegen im anderen Repository und wurden hier nicht vollständig abgeglichen. |
| #4 Architektur/Stack; #5 Quellmodell | Python-Architektur und Beziehungen der neun Bereiche vorhanden; Diagramme und Dokumentation sollten den erweiterten Umfang abbilden. |
| #6 Import; #7 strukturierte Beziehungen | Umgesetzt und ausgeführt; Regressionstests decken indirekte Beziehungen ab. |
| #8 Regelmässige Aktualisierung | Verbessert durch offsetsicheren Abruf, Checkpoints, Abbruch und Wiederaufnahme; Prüfung am Folgetag offen. |
| #9 WWF-Klassifikation | Umgesetzt; vorläufige Taxonomie und Qualitätsvalidierung offen. |
| #10 Suche/Filter | In neun eigenen Oberflächenbereichen umgesetzt. Themenabfrage pro Bereich für Geschäfte/Traktanden auf realen Daten geprüft. |
| #11 Neue Geschäfte; #12 relevante Traktanden | Erkennung und Klassifikation umgesetzt; bei der Schlussvalidierung historische Nachlieferungen von neuen Entwicklungen unterscheiden. |
| #13 Abonnements | Umgesetzt, zusätzlich mit Kantons-, Stichwort- und Watch-Optionen. |
| #14 E-Mail | Umgesetzt; SMTP-Betriebsfehler und Volumen der Zusammenfassungen offen. Unter offener Validierung/Dokumentation führen statt zuverlässigen Produktionsversand zu behaupten. |
| #15 REST-API | Umgesetzt und über OpenAPI dokumentiert; geschützte Sync-Operationen enthalten. |
| #16 Einfache Oberfläche | Umgesetzt und am Tag überarbeitet; Usability-Abnahme durch WWF offen. |
| #17 Erste MVP-Tests (offen) | Deutlicher Testfortschritt; offen lassen, bis SMTP-, Taxonomie- und vollständige Szenarioprüfungen protokolliert sind. |
| #18 WWF-Feedback (offen) | E-Mail von Attila zugeordnet; gemeinsame Demonstration und priorisierte Feedbackrunde offen. |
| #19 Finale Validierung von Anforderungen und Anwendungsfällen (offen) | Nicht abgeschlossen; automatisierte Tests allein erfüllen dieses Issue nicht. |
| #20 Technische Dokumentation (offen) | README, Monitoring-Dokumentation und WWF-Review verbessert; finale Architektur, Betrieb und Grenzen brauchen eine Schlussprüfung. |
| #21 Übergabe/Abschluss (offen) | Nicht abgeschlossen; keine finale Übergabe und kein Projektabschluss erfolgt. |

## Einschätzung der Azure-Bereitschaft

- Das Image enthält Python-Code, Web-Assets und Migrationen; der Standardbefehl startet den Scheduler. Die API kann dasselbe Image mit einem uvicorn-Befehl verwenden. Das lokale Compose definierte damals PostgreSQL und Scheduler, nicht die API (seit dem 21. Oktober enthalten).
- Produktives PostgreSQL braucht verwaltete Zugangsdaten, TLS/Netzwerkkontrollen, Sicherungen und Wiederherstellungstests. Die Compose-Zugangsdaten der Entwicklung sind keine Produktionskonfiguration.
- JWT-, Sync-API- und SMTP-Secrets werden über Umgebungsvariablen gesetzt; Secret-Management und Schlüsselrotation sind mit WWF zu vereinbaren. Es wurden keine Azure-Ressourcen bereitgestellt.
- Der tägliche Scheduler braucht eine definierte Verantwortung und genau eine aktive Instanz. Die PostgreSQL-Jobsperre verhindert überlappende Läufe; lokale JSON-Dateien für Status, Abbruch und Wiederaufnahme benötigen bei getrennter API und Worker einen gemeinsamen persistenten Speicher.
- Container-Ausgaben und Logdateien brauchen Aufbewahrung, Monitoring und Alarmierung. Checkpoints und Benachrichtigungen sind in PostgreSQL dauerhaft; Job-Manifeste und Export-Caches brauchen für die Wiederaufnahme persistenten Speicher.
- Gmail ist eine Entwicklungs-SMTP-Konfiguration, kein validierter WWF-Versandkanal. Organisationsanbieter, Kontingente, Zugangsdaten, Wiederholungsstrategie und erreichbare öffentliche HTTPS-Links sind zu vereinbaren.
- Die lokale `VERIFICATION_BASE_URL` eignet sich nicht für externe Empfänger. Produktive Anmelde- und Datensatzlinks sowie Cookies brauchen eine erreichbare HTTPS-Herkunft.
- Azure-Integration, Container-Bereitstellung und echte organisatorische Authentifizierung wurden an diesem Tag nicht getestet.

## Prüfpunkte für den Folgetag

### Erledigungsstand am 12. Oktober

| Ursprünglicher Prüfpunkt | Aktualisierter Stand |
|---|---|
| 1. Vollständiger Lauf und Wiederaufnahme | Erledigt: wiederaufgenommener Lauf, neuer unabhängiger Lauf und letzter Nutzerlauf jeweils 9/9 erfolgreich |
| 2. Quelle/DB und fachliche Klassifikation | Technischer Vergleich erledigt: 4'500 Beispiele ohne Abweichungen; WWF-Expertenbewertung bleibt offen |
| 3. Gmail/SMTP prüfen | Erfolgreicher realer Versand nachgewiesen, 14 Versandgruppen ohne Fehler; WWF-Produktionsanbieter bleibt spätere Betriebsentscheidung |
| 4. Relevanz und E-Mail-Darstellung | Regressionen und Format-/Linkkorrekturen erledigt; Gesamtdigest und SMTP-Optimierungen bleiben optional |
| 5. Tests und WWF-Demonstration | Technische Szenarien dokumentiert; Präsentation und gemeinsamer WWF-Durchlauf stehen aus |

Die folgende Liste bleibt als ursprüngliche Planung erhalten. Ihre Issue-Nummern beziehen sich auf das am 11. Oktober betrachtete andere Repository.

1. Täglichen bzw. manuellen Lauf beobachten: keine Verarbeitungsfehler, stabile Checkpoints, plausible NEW/CHANGED-Zahlen, Konsistenz bei Wiederholung und Wiederaufnahme.
2. Repräsentative Quell- und DB-Datensätze pro Bereich sowie die Klassifikation anhand der WWF-Erwartungen prüfen.
3. Prüfen, ob die Gmail-Authentifizierung wieder funktioniert; die stornierte historische Warteschlange nicht erneut senden. Neue relevante Benachrichtigungen vor dem Versand prüfen.
4. Beispiele relevanter Änderungen und E-Mail-Volumen messen. Eine tägliche Zusammenfassung pro Nutzer sowie SMTP-Verbindungswiederverwendung und Backoff sind mögliche Folgearbeiten, an diesem Tag nicht umgesetzt.
5. Nachweise der Anwendungsfälle für Issue #17 vervollständigen, danach WWF-Demonstration und Feedback für #18 vorbereiten.

## Bekannte Grenze des Suchindex

**Aktualisierung 12. Oktober:** Das lokale Schema stand auf `20261012_recipients (head)`. Zwei grosse experimentelle Indizes wurden ausdrücklich zurückgestellt; Aufbau später mit `python -m scripts.build_search_indexes`. Die öffentliche Bereichssuche ist davon nicht abhängig. Der folgende Absatz beschreibt den historischen Befund einschliesslich der damaligen Unterbrechung.

Die experimentelle vereinheitlichte Such-API bleibt ausserhalb der öffentlichen Oberfläche. Beim Aufbau ihres Volltextindex für Dokumente wurde bei einem sehr grossen Dokument die maximale `tsvector`-Grösse von PostgreSQL erreicht. Migration und experimentelle Abfrage begrenzen den indexierten Dokument- und Textinhalt deshalb auf die ersten 100'000 Zeichen. Die Inhalte selbst werden nicht gekürzt, und die öffentliche bereichsspezifische Suche durchsucht weiterhin den gesamten Inhalt. Die begrenzte experimentelle Suche kann jenseits dieses Präfixes keine vollständigen Treffer garantieren. Die Index-SQL für grosse Inhalte wurde gegen PostgreSQL mit leerem Prädikat geprüft und zurückgerollt; die vollständige Indexmigration muss in einem Wartungsfenster abgeschlossen werden. Während der damaligen Pause sollte kein weiterer langer Indexaufbau gestartet werden.
