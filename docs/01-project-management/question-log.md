# Fragenliste

Fragen werden notiert, sobald sie entstehen, und in der nächsten Besprechung mit Betreuung oder WWF geklärt. Die Antwort und eine daraus folgende Entscheidung werden hier und im [Entscheidungsregister](decision-log.md) festgehalten. Personenbezogene Angaben und Originalkorrespondenz liegen im privaten Abgabeordner.

**Status:** Geklärt · Offen · Teilweise (umgesetzt, Bestätigung fehlt)

| ID | Frage | Entstanden | An | Antwort / Stand | Status |
|---|---|---|---|---|---|
| F01 | Gehört die Umsetzung in Microsoft 365 zum Projekt? | M1, Kick-off 24.09.2026 | Betreuung, WWF | Nein, aus dem Umfang genommen | Geklärt (D1) |
| F02 | Ist die «dialogorientierte Abfrage» ein Chat mit Sprachmodell oder genügt eine regelbasierte Fragenerkennung? | M1, Aufgabenstellung | Betreuung, WWF | Regelbasiert umgesetzt, Schnittstelle für ein Sprachmodell vorbereitet; Bestätigung des Umfangs fehlt (US-14, [#50](https://github.com/FatihHayyar/wwf-polit-assistant/issues/50)) | Teilweise (D2, D13) |
| F03 | Welche OpenParlData-Bereiche werden gebraucht? | M1, Analyse OpenParlData | WWF | Neun Bereiche; WWF nannte zusätzlich Abstimmungen, Gruppen und Interessenbindungen | Geklärt (D4) |
| F04 | Welche Programmiersprache passt zur WWF-Landschaft? | M1 | WWF | Python; daher FastAPI statt Java | Geklärt (D3) |
| F05 | Welche Themen und Unterthemen soll die Klassifikation kennen? | M1 | WWF | WWF-Rückmeldung nennt sieben Energie-/Klima-Unterthemen, umgesetzt in v8; fachliche Freigabe fehlt (US-15, [#51](https://github.com/FatihHayyar/wwf-polit-assistant/issues/51)) | Teilweise |
| F06 | Wer betreibt die Anwendung später, und wo? | M2 | WWF | WWF übernimmt die Bereitstellung auf Azure; das Projekt liefert die Übergabe | Geklärt (D9) |
| F07 | Reicht ein Abonnement pro Konto? | M2 | WWF | Nein, mehrere Abonnements gewünscht | Geklärt (D12, US-12) |
| F08 | Soll nach Geschäftstyp gefiltert werden können? | M2 | WWF | Ja, auch für Abonnements | Geklärt (US-13) |
| F09 | Sollen individuelle Suchbegriffe Teil eines Abonnements sein? | M2, Test der Oberfläche | WWF | WWF nannte Keywords. In Abonnements verwirrten sie (sie schränken ein), daher nur noch in der Suche. Mit WWF abstimmen | Offen (D15) |
| F10 | Darf die Anmeldung anzeigen, ob eine Adresse bereits registriert ist? | M2, Test der Oberfläche | WWF | Umgesetzt zugunsten der Verständlichkeit; Datenschutzsicht von WWF einholen | Offen (D16) |
| F11 | Über welchen Mailserver versendet WWF im Betrieb? | M2 | WWF-IT | Lokal Mailpit, Versand über SMTP konfigurierbar; Organisationsversand nicht geprüft | Offen |
| F12 | Wer kann Beispiele für die Qualitätsmessung fachlich beurteilen? | M2 | WWF | Prüfsets bisher ohne WWF-Expertenwerte (US-16, [#52](https://github.com/FatihHayyar/wwf-polit-assistant/issues/52)) | Offen |
| F13 | Soll die Anmeldung über das WWF-Konto (Single Sign-on) laufen? | M2 | WWF-IT | E-Mail-Link und optional Google umgesetzt; WWF-Vorgaben offen | Offen |
| F14 | Unter welcher Lizenz wird die Software übergeben? | M2 | Betreuung, WWF | Offen; vor der Abgabe klären | Offen |
| F15 | Rückmeldungen aus der Zwischenpräsentation | M2, Zwischenpräsentation 18.11.2026 | Betreuung, Expertenperson | Nach der Präsentation eintragen | Offen |

## Für die Zwischenpräsentation am 18.11.2026

Offene Fragen mit Auswirkung auf die Abgabe: F02, F05, F09, F10 und F12. Sie betreffen den Umfang (F02), die fachliche Qualität (F05, F12) und zwei bewusste Abweichungen von der WWF-Rückmeldung (F09, F10).
