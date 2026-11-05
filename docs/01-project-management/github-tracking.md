# GitHub-Projektverwaltung

[Repository](https://github.com/FatihHayyar/wwf-polit-assistant) · [Projekt-Board](https://github.com/users/FatihHayyar/projects/3) · [Milestones](https://github.com/FatihHayyar/wwf-polit-assistant/milestones) · [Issues](https://github.com/FatihHayyar/wwf-polit-assistant/issues)

Das Projekt wird auf GitHub genau so geführt wie im [Projektplan](project-plan.md) und im [Backlog](../02-requirements/user-stories.md) beschrieben: drei Milestones, ein Issue pro User Story oder Arbeitspaket und ein Board mit dem Bearbeitungsstand.

## Aufbau

| Element | Inhalt |
|---|---|
| **Milestones** | M1 – Projektstart und Planung (fällig 02.10.2026), M2 – Umsetzung bis zur Zwischenpräsentation (18.11.2026), M3 – Rückmeldungen, Fertigstellung und WIPRO-Dokumentation (21.12.2026) |
| **Issues** | Ein Issue pro User Story (Label `user-story`) mit Story-Text, Rolle, Priorität, Anforderung und den Akzeptanzkriterien als Checkliste samt Testnachweis; ein Issue pro Arbeitspaket (Label `arbeitspaket`) |
| **Labels** | `user-story`, `arbeitspaket`, Priorität nach MoSCoW (`prio:must`, `prio:should`, `prio:could`), Themenbereiche (`area:…`) |
| **Board** | «WWF Polit-Assistant – WIPRO» mit Status *Todo*, *In Progress* und *Done*; mit dem Repository verknüpft |

Ein Issue wird geschlossen, wenn alle Akzeptanzkriterien erfüllt sind. Stories, die umgesetzt sind, aber noch auf eine Bestätigung von WWF warten (US-15, US-16), bleiben offen und stehen auf *In Progress*.

## Stand am 5. November 2026

| Milestone | Issues | Erledigt | Offen |
|---|---|---|---|
| M1 – Projektstart und Planung | #29–#36 (AP-1.1 – AP-1.8) | 8 | 0 |
| M2 – Umsetzung bis zur Zwischenpräsentation | #37–#58 (US-01 – US-20, AP-2.1, AP-2.2) | 19 | 3 (US-15, US-16, AP-2.2) |
| M3 – Rückmeldungen, Fertigstellung und WIPRO-Dokumentation | #59–#64 (US-21 – US-23, AP-3.1 – AP-3.3) | 0 | 6 |

| Story / Arbeitspaket | Issue | Story / Arbeitspaket | Issue |
|---|---|---|---|
| AP-1.1 – AP-1.8 | [#29](https://github.com/FatihHayyar/wwf-polit-assistant/issues/29) – [#36](https://github.com/FatihHayyar/wwf-polit-assistant/issues/36) | US-13 | [#49](https://github.com/FatihHayyar/wwf-polit-assistant/issues/49) |
| US-01 | [#37](https://github.com/FatihHayyar/wwf-polit-assistant/issues/37) | US-14 | [#50](https://github.com/FatihHayyar/wwf-polit-assistant/issues/50) |
| US-02 | [#38](https://github.com/FatihHayyar/wwf-polit-assistant/issues/38) | US-15 | [#51](https://github.com/FatihHayyar/wwf-polit-assistant/issues/51) |
| US-03 | [#39](https://github.com/FatihHayyar/wwf-polit-assistant/issues/39) | US-16 | [#52](https://github.com/FatihHayyar/wwf-polit-assistant/issues/52) |
| US-04 | [#40](https://github.com/FatihHayyar/wwf-polit-assistant/issues/40) | US-17 | [#53](https://github.com/FatihHayyar/wwf-polit-assistant/issues/53) |
| US-05 | [#41](https://github.com/FatihHayyar/wwf-polit-assistant/issues/41) | US-18 | [#54](https://github.com/FatihHayyar/wwf-polit-assistant/issues/54) |
| US-06 | [#42](https://github.com/FatihHayyar/wwf-polit-assistant/issues/42) | US-19 | [#55](https://github.com/FatihHayyar/wwf-polit-assistant/issues/55) |
| US-07 | [#43](https://github.com/FatihHayyar/wwf-polit-assistant/issues/43) | US-20 | [#56](https://github.com/FatihHayyar/wwf-polit-assistant/issues/56) |
| US-08 | [#44](https://github.com/FatihHayyar/wwf-polit-assistant/issues/44) | AP-2.1, AP-2.2 | [#57](https://github.com/FatihHayyar/wwf-polit-assistant/issues/57), [#58](https://github.com/FatihHayyar/wwf-polit-assistant/issues/58) |
| US-09 | [#45](https://github.com/FatihHayyar/wwf-polit-assistant/issues/45) | US-21 | [#59](https://github.com/FatihHayyar/wwf-polit-assistant/issues/59) |
| US-10 | [#46](https://github.com/FatihHayyar/wwf-polit-assistant/issues/46) | US-22 | [#60](https://github.com/FatihHayyar/wwf-polit-assistant/issues/60) |
| US-11 | [#47](https://github.com/FatihHayyar/wwf-polit-assistant/issues/47) | US-23 | [#61](https://github.com/FatihHayyar/wwf-polit-assistant/issues/61) |
| US-12 | [#48](https://github.com/FatihHayyar/wwf-polit-assistant/issues/48) | AP-3.1 – AP-3.3 | [#62](https://github.com/FatihHayyar/wwf-polit-assistant/issues/62) – [#64](https://github.com/FatihHayyar/wwf-polit-assistant/issues/64) |

## Umstellung vom 5. November 2026

Bis zu diesem Datum waren auf GitHub 28 technisch formulierte Issues in sieben Milestones erfasst (am 12.10.2026 nachträglich angelegt). Sie wurden durch die Story-Issues ersetzt und entfernt; ihr Inhalt ist vollständig in den Stories und Arbeitspaketen aufgegangen. Eine Sicherung der früheren Issues, Milestones und Labels ist lokal ausserhalb des Repositorys abgelegt. Die Issues der neuen Struktur sind deshalb ab #29 nummeriert, und ihre Erstellungsdaten zeigen den Tag der Umstellung, nicht den Zeitpunkt der Umsetzung; dieser ist in der Git-Historie nachvollziehbar.
