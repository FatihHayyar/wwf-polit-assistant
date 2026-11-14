# Projektplan

Der WWF Polit-Assistant entsteht als Wirtschaftsprojekt (WIPRO) im Herbstsemester 2026. Das Projekt ist in **drei Milestones** gegliedert, die sich am offiziellen [WIPRO-Terminplan](#termine-aus-dem-wipro-terminplan) ausrichten. Innerhalb der Milestones wird iterativ mit **User Stories** gearbeitet: Jede Story hat Akzeptanzkriterien, und jedes Kriterium wird durch einen Test nachgewiesen.

## Vorgehen

```
Aufgabenstellung + WWF-Rückmeldungen
   → Anforderungsliste (R01–R22)
      → User Stories je Milestone («Als … möchte ich …, damit …»)
         → Akzeptanzkriterien je Story (Gegeben / Wenn / Dann)
            → Test je Kriterium (automatisiert oder manueller Testfall)
               → Testprotokoll und Milestone-Review
```

- **Anforderungen:** [Anforderungsliste](../02-requirements/requirements.md) mit Quelle (Aufgabenstellung, WWF-Rückmeldung, technische Ergänzung).
- **Backlog:** [User Stories](../02-requirements/user-stories.md) mit Priorität nach MoSCoW (Must, Should, Could, Won't), Milestone und Status.
- **Nachweis:** [Rückverfolgbarkeit](../02-requirements/acceptance-criteria.md) von der Anforderung bis zum Test.
- **Fragen:** Offene Punkte werden laufend in der [Fragenliste](question-log.md) notiert und in Besprechungen geklärt.
- **Entscheidungen:** Änderungen am Backlog mit Begründung im [Entscheidungsregister](decision-log.md).

### Definition of Done einer User Story

1. Alle Akzeptanzkriterien sind durch einen automatisierten Test oder einen beschriebenen manuellen Testfall abgedeckt, und diese laufen erfolgreich.
2. Die gesamte Testsuite läuft weiterhin erfolgreich (keine Regression).
3. Die Benutzer- und Technikdokumentation ist nachgeführt.
4. Fachliche Fragen, die nur WWF beantworten kann, sind in der Fragenliste erfasst.

## Milestones

| Milestone | Zeitraum (Semesterwoche) | Ziel | Wichtigste Ergebnisse | Abschluss |
|---|---|---|---|---|
| **M1 – Projektstart und Planung** | SW 1–3 (14.09.–02.10.2026) | Auftrag verstehen, Umfang klären, Projekt aufsetzen | Pitch und Kick-off am 24.09.2026, Fragen und Notizen, Analyse von OpenParlData, Aufgabenstellung (eingereicht bis 28.09.2026), GitHub-Repository mit Milestones und Issues, Anforderungsliste, User Stories, Dokumentstruktur | Signierte Aufgabenstellung; Backlog steht |
| **M2 – Umsetzung bis zur Zwischenpräsentation** | SW 4–10 (bis 18.11.2026) | Lauffähiger MVP, Story für Story umgesetzt und getestet | Datenintegration, Klassifikation, Recherche, Konto, Abonnements, Benachrichtigungen, Docker-Demo; Erweiterungen nach der WWF-Rückmeldung (mehrere Abonnements, Geschäftstyp, Fragen in natürlicher Sprache, WWF-Unterthemen, Qualitätsmessung); Verbesserungen aus dem eigenen Test; gesammelte Fragen; Zwischenpräsentation | Zwischenpräsentation am 18.11.2026 gehalten; Rückmeldungen erfasst |
| **M3 – Rückmeldungen, Fertigstellung und WIPRO-Dokumentation** | SW 10–15 (19.11.–21.12.2026) | Rückmeldungen der Zwischenpräsentation umsetzen, technischen Teil abschliessen, Bericht fertigstellen | Stories aus den Rückmeldungen, Übergabeunterlagen, Abnahme mit WWF, WIPRO-Bericht | Abgabe in Complesis; Abschlusspräsentation (18.01.–05.02.2027) |

Die konkreten Stories je Milestone stehen im [Backlog](../02-requirements/user-stories.md).

## Termine aus dem WIPRO-Terminplan

Quelle: Terminplan WIPRO & BAA HS 2026 (Version 24.02.2026, als «voraussichtlich» bezeichnet).

| Termin | Ereignis |
|---|---|
| 14.09.2026 (SW 1) | Regulärer Projektstart |
| **24.09.2026** (SW 2) | **Kick-off-Meeting mit Pitch-Präsentation** (vorgesehen in SW 1) |
| 28.09.2026, 23:59 | Einreichung der Aufgabenstellung in Complesis |
| Mitte SW 3 | Signierung der definitiven Aufgabenstellung |
| **18.11.2026** (SW 10) | **Zwischenpräsentation** (Zeitfenster SW 7–10) |
| 21.12.2026, 12:00 | Abgabe der Arbeit in Complesis, Kopie an WWF |
| 18.01.–05.02.2027 | Abschlusspräsentation |

Fett markiert sind die tatsächlichen Projekttermine. Der Entwicklungsverlauf ist in der Git-Historie nachvollziehbar.

## Rollen in den User Stories

| Rolle | Beschreibung |
|---|---|
| **WWF-Fachperson** | Recherchiert parlamentarische Geschäfte zu WWF-Themen, mit oder ohne Konto |
| **Abonnent:in** | WWF-Mitarbeiter:in mit Konto, die per E-Mail über neue Inhalte und Änderungen informiert werden möchte |
| **WWF-IT** | Übernimmt Betrieb, Integration und Weiterentwicklung |
| **Projektleitung** | Student:in; plant, setzt um und dokumentiert das Projekt (Arbeitspakete in M1) |

## Werkzeuge

- **GitHub:** [Projekt-Board](https://github.com/users/FatihHayyar/projects/3), [Milestones](https://github.com/FatihHayyar/wwf-polit-assistant/milestones) und ein [Issue](https://github.com/FatihHayyar/wwf-polit-assistant/issues) pro User Story oder Arbeitspaket mit den Akzeptanzkriterien als Checkliste ([Aufbau](github-tracking.md)).
- **Tests:** Python-Unittests (Backend, API, Sync, Klassifikation), Frontend-Prüfungen mit Node und Browser-Durchläufe mit Edge ([Testplan](../05-testing/test-plan.md)).
- **Arbeitsjournal und Protokolle:** im privaten Abgabeordner; öffentlich nur bereinigte [Sitzungsnotizen](meeting-notes/README.md).
- **Weiterentwicklung nach dem WIPRO** (Azure-Betrieb, KI-Klassifikation, Chat) ist nicht Teil dieser drei Milestones; Ideen stehen im [Scope](scope-and-priorities.md).
