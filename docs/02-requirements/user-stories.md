# Backlog: Arbeitspakete und User Stories

Der Backlog wurde zu Beginn aus der [Anforderungsliste](requirements.md) abgeleitet, den [Milestones](../01-project-management/project-plan.md#milestones) zugeordnet und im Verlauf verfeinert. Änderungen nach Rückmeldungen stehen am Ende unter [Änderungen am Backlog](#änderungen-am-backlog).

**Prioritäten (MoSCoW):** Must = für den MVP nötig · Should = wichtig, aber nicht kritisch · Could = wünschenswert · Won't = bewusst nicht in diesem Projekt.
**Status:** Erledigt · In Arbeit · Offen (wartet auf WWF oder spätere Phase).
**Tests:** Python-Tests liegen in [`tests/`](../../tests); `browser_membership` ist der Edge-Durchlauf [`tests/browser_membership.py`](../../tests/browser_membership.py).

## Übersicht

| ID | Titel | Rolle | Prio | Anforderung | Milestone | Status | Issue |
|---|---|---|---|---|---|---|---|
| AP-1.1 – AP-1.8 | Projektstart und Planung | Projektleitung | Must | R11 | M1 | Erledigt | [#29](https://github.com/FatihHayyar/wwf-polit-assistant/issues/29) – [#36](https://github.com/FatihHayyar/wwf-polit-assistant/issues/36) |
| US-01 | Daten aktuell halten | WWF-Fachperson | Must | R01, R02 | M2 | Erledigt | [#37](https://github.com/FatihHayyar/wwf-polit-assistant/issues/37) |
| US-02 | Zusammenhänge eines Geschäfts sehen | WWF-Fachperson | Must | R02, R15 | M2 | Erledigt | [#38](https://github.com/FatihHayyar/wwf-polit-assistant/issues/38) |
| US-03 | Geschäfte WWF-Themen zuordnen | WWF-Fachperson | Must | R03 | M2 | Erledigt | [#39](https://github.com/FatihHayyar/wwf-polit-assistant/issues/39) |
| US-04 | Recherchieren mit Filtern | WWF-Fachperson | Must | R04, R10, R15 | M2 | Erledigt | [#40](https://github.com/FatihHayyar/wwf-polit-assistant/issues/40) |
| US-05 | Ohne Passwort registrieren und anmelden | Abonnent:in | Must | R19 | M2 | Erledigt | [#41](https://github.com/FatihHayyar/wwf-polit-assistant/issues/41) |
| US-06 | Themen abonnieren | Abonnent:in | Must | R05, R06, R08 | M2 | Erledigt | [#42](https://github.com/FatihHayyar/wwf-polit-assistant/issues/42) |
| US-07 | Einzelnes Geschäft verfolgen | Abonnent:in | Must | R07 | M2 | Erledigt | [#43](https://github.com/FatihHayyar/wwf-polit-assistant/issues/43) |
| US-08 | Nur relevante Änderungen erhalten | Abonnent:in | Must | R05, R08 | M2 | Erledigt | [#44](https://github.com/FatihHayyar/wwf-polit-assistant/issues/44) |
| US-09 | Weitere Empfängeradressen | Abonnent:in | Could | R17 | M2 | Erledigt | [#45](https://github.com/FatihHayyar/wwf-polit-assistant/issues/45) |
| US-10 | REST-API nutzen | WWF-IT | Must | R09 | M2 | Erledigt | [#46](https://github.com/FatihHayyar/wwf-polit-assistant/issues/46) |
| US-11 | Demo mit einem Befehl starten | WWF-IT | Should | R12 | M2 | Erledigt | [#47](https://github.com/FatihHayyar/wwf-polit-assistant/issues/47) |
| US-12 | Mehrere Abonnements | Abonnent:in | Must | R19 | M2 | Erledigt | [#48](https://github.com/FatihHayyar/wwf-polit-assistant/issues/48) |
| US-13 | Nach Geschäftstyp filtern | WWF-Fachperson, Abonnent:in | Must | R04, R06 | M2 | Erledigt | [#49](https://github.com/FatihHayyar/wwf-polit-assistant/issues/49) |
| US-14 | Frage in natürlicher Sprache stellen | WWF-Fachperson | Must | R20, R21 | M2 | Erledigt | [#50](https://github.com/FatihHayyar/wwf-polit-assistant/issues/50) |
| US-15 | Energie- und Klima-Unterthemen nach WWF | WWF-Fachperson | Must | R16, R22 | M2 | Erledigt; Freigabe offen | [#51](https://github.com/FatihHayyar/wwf-polit-assistant/issues/51) |
| US-16 | Klassifikationsgüte messen | Projektleitung, WWF | Should | R03, R12 | M2 | Erledigt; Expertenprüfung offen | [#52](https://github.com/FatihHayyar/wwf-polit-assistant/issues/52) |
| US-17 | Einfache Abonnementverwaltung | Abonnent:in | Should | R06, R10 | M2 | Erledigt | [#53](https://github.com/FatihHayyar/wwf-polit-assistant/issues/53) |
| US-18 | Inhalt mit einem Klick verfolgen | Abonnent:in | Should | R07, R10 | M2 | Erledigt | [#54](https://github.com/FatihHayyar/wwf-polit-assistant/issues/54) |
| US-19 | Klare Meldungen bei Registrieren und Anmelden | Abonnent:in | Should | R10, R19 | M2 | Erledigt | [#55](https://github.com/FatihHayyar/wwf-polit-assistant/issues/55) |
| US-20 | Konto löschen mit Bestätigung | Abonnent:in | Should | R10 | M2 | Erledigt | [#56](https://github.com/FatihHayyar/wwf-polit-assistant/issues/56) |
| AP-2.1 – AP-2.2 | Fragen sammeln, Zwischenpräsentation am 18.11.2026 | Projektleitung | Must | R11 | M2 | In Arbeit | [#57](https://github.com/FatihHayyar/wwf-polit-assistant/issues/57) – [#58](https://github.com/FatihHayyar/wwf-polit-assistant/issues/58) |
| US-21 | Übergabe für Azure vorbereiten | WWF-IT | Must | R13, R14 | M3 | In Arbeit | [#59](https://github.com/FatihHayyar/wwf-polit-assistant/issues/59) |
| US-22 | Anwendung anhand der Dokumentation übernehmen | WWF-IT | Must | R11 | M3 | In Arbeit | [#60](https://github.com/FatihHayyar/wwf-polit-assistant/issues/60) |
| US-23 | MVP mit WWF abnehmen | WWF-Fachperson | Must | R12 | M3 | Offen | [#61](https://github.com/FatihHayyar/wwf-polit-assistant/issues/61) |
| AP-3.1 – AP-3.3 | WIPRO-Bericht, Abgabe, Abschlusspräsentation | Projektleitung | Must | R11 | M3 | In Arbeit | [#62](https://github.com/FatihHayyar/wwf-polit-assistant/issues/62) – [#64](https://github.com/FatihHayyar/wwf-polit-assistant/issues/64) |

---

## M1 – Projektstart und Planung

In M1 entsteht noch keine Software. Die Arbeit ist deshalb in Arbeitspakete mit einem prüfbaren Ergebnis gegliedert.

| ID | Arbeitspaket | Ergebnis / Artefakt | Erledigt, wenn … | Status |
|---|---|---|---|---|
| AP-1.1 | Projektidee verstehen, Pitch vorbereiten | Pitch-Präsentation | Pitch am Kick-off gehalten | Erledigt |
| AP-1.2 | Kick-off am 24.09.2026 durchführen, Umfang eingrenzen | [Kick-off-Vermerk](../01-project-management/meeting-notes/kickoff-summary.md); Entscheide D1–D2 (M365 nicht im Umfang, KI als Weiterentwicklung) | Umfang mit Betreuung und WWF besprochen | Erledigt |
| AP-1.3 | Fragen und Notizen sammeln | [Fragenliste](../01-project-management/question-log.md) | Offene Punkte notiert und Ansprechperson zugeordnet | Erledigt, laufend gepflegt |
| AP-1.4 | OpenParlData analysieren | [OpenParlData-Integration](../04-technical-concepts/openparldata-integration.md): Endpunkte, neun Bereiche, Beziehungen, Grenzen der Quelle | Datenbereiche und Beziehungen für den MVP festgelegt | Erledigt |
| AP-1.5 | Aufgabenstellung erstellen und einreichen | Aufgabenstellung in Complesis | Eingereicht bis 28.09.2026 und signiert (SW 3) | Erledigt |
| AP-1.6 | Projektmanagement auf GitHub einrichten | [Repository, Milestones und Issues](../01-project-management/github-tracking.md) | Milestones und Issues angelegt | Erledigt (am 05.11.2026 auf Milestones, Story-Issues und Board umgestellt) |
| AP-1.7 | Anforderungen und User Stories ableiten | [Anforderungsliste](requirements.md), dieser Backlog | Jede Anforderung hat mindestens eine Story oder ein Arbeitspaket | Erledigt |
| AP-1.8 | Dokumentstruktur anlegen | [Dokumentation in sieben Bereichen](../README.md) | Ablage für Planung, Anforderungen, Architektur, Konzepte, Tests, Übergabe und Bericht steht | Erledigt |

---

## M2 – Umsetzung bis zur Zwischenpräsentation

### US-01 Daten aktuell halten

**Als** WWF-Fachperson **möchte ich**, dass die Parlamentsdaten aller Kantone täglich automatisch aktualisiert werden, **damit** ich mit aktuellen Daten arbeite.
Must · R01, R02 · Erledigt · GitHub [#37](https://github.com/FatihHayyar/wwf-polit-assistant/issues/37)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Wenn die Quelle neue Datensätze ohne Änderungsdatum enthält, dann werden sie trotzdem gefunden. | `test_new_identity_without_timestamp_is_found` |
| 2 | Wenn seit dem letzten Lauf nichts geändert wurde, dann stoppt der Abgleich am gespeicherten Stand. | `test_incremental_phase_skips_null_timestamps_and_stops_at_checkpoint` |
| 3 | Wenn ein vollständiger Vergleich fällig ist, dann werden auch stille Änderungen der Quelle erkannt. | `test_full_scan_runs_when_due_and_finds_silent_changes` |
| 4 | Gegeben ein Fehler in einem Bereich, dann wird die Ursache gemeldet und der Lauf überspringt beim Neustart erledigte Bereiche. | `test_failed_stage_reports_cause_and_does_not_send_notifications`, `test_resume_skips_completed_stage_and_retries_failed_stage` |
| 5 | Übersetzungen (DE/FR/IT) aus der Quelle bleiben erhalten. | `test_flat_export_translations_are_retained` |

### US-02 Zusammenhänge eines Geschäfts sehen

**Als** WWF-Fachperson **möchte ich** zu einem Geschäft die zugehörigen Traktanden, Sitzungen, Abstimmungen und Dokumente sehen, **damit** ich den Verlauf verstehe.
Must · R02, R15 · Erledigt · GitHub [#38](https://github.com/FatihHayyar/wwf-polit-assistant/issues/38)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Wenn ich ein Geschäft öffne, dann sehe ich verknüpfte Ereignisse und Abstimmungen mit ihren Details. | `test_supporting_event_context_and_voting_details` |
| 2 | Ein Traktandum ohne eigenen Titel zeigt den Titel seines Geschäfts. | `test_untitled_agenda_prefers_affair_and_keeps_own_title` |
| 3 | Eine Gruppe (Kommission) zeigt ihre Sitzungen und ist über die Geschäfte ihrer Sitzungen auffindbar. | `test_group_relations_and_details` |
| 4 | Mehrere Quelleinträge desselben Geschäfts erscheinen als eine Karte. | `test_same_project_sources_share_one_card_and_pagination_keeps_other_projects` |

### US-03 Geschäfte WWF-Themen zuordnen

**Als** WWF-Fachperson **möchte ich**, dass Geschäfte automatisch WWF-Themen zugeordnet werden, **damit** ich nicht jedes Geschäft selbst lesen muss.
Must · R03 · Erledigt (Güte siehe US-16) · GitHub [#39](https://github.com/FatihHayyar/wwf-polit-assistant/issues/39)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Reale Beispieltitel erhalten die erwarteten Themen. | `test_real_mixed_examples` |
| 2 | Allgemeine Verwaltungsbegriffe ohne Umweltbezug ergeben kein Umweltthema. | `test_negative_words_and_generic_administration_are_not_environment_topics` |
| 3 | Ortsnamen und Schulnamen lösen keine Themen aus. | `test_exclusions_block_place_and_school_names` |
| 4 | Jede Zuordnung speichert die Begriffe, die sie ausgelöst haben (Evidenz). | `test_index_preserves_all_overlapping_rule_matches` |

### US-04 Recherchieren mit Filtern

**Als** WWF-Fachperson **möchte ich** in allen neun Bereichen nach Thema, Unterthema, Kanton, Stichwort und Zeitraum suchen, **damit** ich relevante Inhalte schnell finde.
Must · R04, R10, R15 · Erledigt · GitHub [#40](https://github.com/FatihHayyar/wwf-polit-assistant/issues/40)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Ein Themenfilter liefert passende Treffer mit korrekter Seitennavigation. | `test_category_filter_and_pagination` |
| 2 | Stichwort, Kanton und Datum lassen sich kombinieren. | `test_keyword_canton_dates` |
| 3 | Ein Thema filtert auch verknüpfte Bereiche (z. B. Traktanden zu Klimageschäften). | `test_related_category_filters_all_datasets` |
| 4 | Die Stichwortsuche findet eigene Inhalte und behält in der Detailansicht den Kontext. | `test_unified_keyword_search_matches_own_content_and_detail_keeps_context` |

### US-05 Ohne Passwort registrieren und anmelden

**Als** Abonnent:in **möchte ich** mich mit einem Link per E-Mail registrieren und anmelden, **damit** ich kein Passwort verwalten muss.
Must · R19 · Erledigt (Meldungen verbessert in US-19) · GitHub [#41](https://github.com/FatihHayyar/wwf-polit-assistant/issues/41)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Wenn ich den Registrierungslink bestätige, dann bin ich registriert und angemeldet. | `test_registration_link_verifies_and_signs_in` |
| 2 | Das blosse Öffnen eines Links (z. B. durch einen Mail-Scanner) verbraucht ihn nicht; erst der Klick auf «Bestätigen». | `test_opening_a_link_does_not_consume_the_token` |
| 3 | Ein Link kann nur einmal verwendet werden. | `test_email_login_redirects_cookie_and_rejects_reuse` |
| 4 | Eine Bestätigung von einer fremden Website wird abgewiesen. | `test_cross_site_confirmation_is_rejected` |
| 5 | Abmelden macht alle bisherigen Sitzungen ungültig; danach ist eine neue Anmeldung möglich. | `test_logout_revokes_previously_issued_tokens`, `test_new_sign_in_after_logout_works` |

### US-06 Themen abonnieren

**Als** Abonnent:in **möchte ich** Themen, Kantone und Bereiche abonnieren, **damit** ich per E-Mail über neue passende Inhalte informiert werde.
Must · R05, R06, R08 · Erledigt (erweitert in US-12) · GitHub [#42](https://github.com/FatihHayyar/wwf-polit-assistant/issues/42)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Gegeben ein Abonnement für einen Bereich, wenn dort ein passender Inhalt neu erscheint, dann entsteht eine Benachrichtigung. | `test_dataset_subscription` |
| 2 | Ein pausiertes Abonnement benachrichtigt nicht. | `test_paused_profile_does_not_notify` |
| 3 | Vor dem Versand wird geprüft, ob das Abonnement noch passt. | `test_email_rechecks_current_subscription` |
| 4 | Eine Sitzung mit vielen passenden Traktanden ergibt eine einzige Nachricht. | `test_meeting_fanout_single_notification` |
| 5 | Ohne Anmeldung sind Abonnements nicht zugänglich. | `test_subscriptions_require_authentication` |

### US-07 Einzelnes Geschäft verfolgen

**Als** Abonnent:in **möchte ich** ein bestimmtes Geschäft verfolgen, **damit** ich über jede relevante Entwicklung informiert werde, auch wenn es zu keinem Abonnement passt.
Must · R07 · Erledigt (Bedienung verbessert in US-18) · GitHub [#43](https://github.com/FatihHayyar/wwf-polit-assistant/issues/43)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Ein verfolgtes Geschäft bleibt verfolgt, auch wenn sich seine Themen ändern. | `test_affair_watch_survives_category_and_dataset_changes` |
| 2 | Eine verfolgte Sitzung meldet auch Änderungen ihrer Traktanden. | `test_meeting_watch_includes_linked_agenda` |
| 3 | Eine verfolgte Gruppe meldet Änderungen ihrer Sitzungen und Traktanden. | `test_group_watch_covers_meeting_and_agenda_changes` |
| 4 | Wird das Verfolgen beendet, entfällt eine noch nicht versendete Nachricht. | `test_unwatch_cancels_pending_email` |

### US-08 Nur relevante Änderungen erhalten

**Als** Abonnent:in **möchte ich** nur bei inhaltlichen Änderungen eine E-Mail erhalten, **damit** mein Postfach nicht mit technischen Aktualisierungen gefüllt wird.
Must · R05, R08 · Erledigt · GitHub [#44](https://github.com/FatihHayyar/wwf-polit-assistant/issues/44)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Technische Felder und Formatierung werden gespeichert, lösen aber keine Nachricht aus. | `test_technical_and_formatting_changes_are_saved_without_notifications` |
| 2 | Eine einzelne Tippfehler-Korrektur löst keine Nachricht aus. | `test_isolated_spelling_correction_is_suppressed` |
| 3 | Kleine, aber inhaltliche Änderungen (Zahlen, Verneinungen) werden gemeldet. | `test_small_but_substantive_changes_remain_eligible` |
| 4 | Mehrere Änderungen eines Geschäfts werden in einer Nachricht zusammengefasst. | `test_digest_groups_updates_and_retries_failed_group_next_invocation` |
| 5 | Die E-Mail hat eine HTML- und eine Textfassung mit beschrifteten Links. | `test_plain_text_and_html_have_distinct_links_and_unicode` |

### US-09 Weitere Empfängeradressen

**Als** Abonnent:in **möchte ich** Benachrichtigungen auch an weitere Adressen senden, **damit** mein Team informiert ist.
Could · R17 · Erledigt · GitHub [#45](https://github.com/FatihHayyar/wwf-polit-assistant/issues/45)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Eine neue Adresse erhält erst nach ihrer Bestätigung Nachrichten. | `test_new_destination_requires_verification_and_token_is_single_use` |
| 2 | Die Bestätigung erfolgt per Klick (POST) und nur einmal. | `test_recipient_confirmation_uses_post_and_is_single_use` |

### US-10 REST-API nutzen

**Als** WWF-IT **möchte ich** eine dokumentierte REST-API, **damit** ich die Daten in andere Systeme einbinden kann.
Must · R09 · Erledigt · GitHub [#46](https://github.com/FatihHayyar/wwf-polit-assistant/issues/46)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Die OpenAPI-Dokumentation ist erreichbar. | `test_api_documentation_still_loads` |
| 2 | Geschützte Routen verlangen eine Anmeldung. | `test_subscriptions_require_authentication` |
| 3 | Die Oberfläche sendet strenge Sicherheits-Header. | `test_frontend_sends_strict_headers` |

### US-11 Demo mit einem Befehl starten

**Als** WWF-IT **möchte ich** die Anwendung mit Beispieldaten per Docker starten, **damit** ich sie ohne vollständigen Datenimport ausprobieren kann.
Should · R12 · Erledigt · GitHub [#47](https://github.com/FatihHayyar/wwf-polit-assistant/issues/47)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Die Demo erzeugt für ein abonniertes Thema eine Benachrichtigung in Mailpit. | `test_subscribed_topic_produces_a_notification_email` |
| 2 | Passt das Testgeschäft zu keinem Abonnement, erklärt die Oberfläche den Grund. | `test_unmatched_subscription_explains_instead_of_sending` |
| 3 | Ausserhalb des Demo-Modus sind die Demo-Funktionen nicht erreichbar. | `test_demo_endpoints_are_hidden_outside_demo_mode` |
| 4 | `docker compose -f docker-compose.demo.yml up` startet die Anwendung auf einem frischen Rechner. | Manueller Testfall ([Testplan](../05-testing/test-plan.md)) |

### Erweiterungen nach der WWF-Rückmeldung (Oktober 2026)

### US-12 Mehrere Abonnements

**Als** Abonnent:in **möchte ich** mehrere Abonnements führen, z. B. «Energie in Luzern» und «Bioenergie in allen Kantonen», **damit** ich unterschiedliche Kombinationen getrennt verfolgen kann.
Must · R19 (WWF-Rückmeldung) · Erledigt · GitHub [#48](https://github.com/FatihHayyar/wwf-polit-assistant/issues/48)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Ich kann ein Abonnement anlegen, ändern, pausieren und löschen; «Alle beenden» entfernt alles. | `test_profile_roundtrip_and_stop_all` |
| 2 | Mehr als zehn Abonnements sind nicht möglich; fremde Abonnements sind nicht änderbar. | `test_profile_limit_and_ownership` |
| 3 | Passen zwei Abonnements auf dieselbe Änderung, kommt nur **eine** Nachricht. | `test_overlapping_profiles_notify_once` |
| 4 | Passt nur eines von mehreren Abonnements, wird trotzdem benachrichtigt. | `test_any_matching_profile_notifies_once` |
| 5 | In der Oberfläche lassen sich zwei Abonnements nacheinander anlegen. | `browser_membership` |

### US-13 Nach Geschäftstyp filtern

**Als** WWF-Fachperson **möchte ich** nach Geschäftstyp (Motion, Postulat, Interpellation …) filtern, **damit** ich z. B. nur Vorstösse mit Handlungsauftrag sehe.
Must · R04, R06 (WWF-Rückmeldung) · Erledigt · GitHub [#49](https://github.com/FatihHayyar/wwf-polit-assistant/issues/49)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Ein Abonnement mit Typ «Motion» meldet auch Traktanden, die zu einer Motion gehören, aber nicht zu einem Postulat. | `test_affair_type_filter_applies_to_linked_records` |
| 2 | Der Typfilter wirkt in der Suche nur auf Geschäfte. | `test_affair_type_filter_applies_only_to_affairs` |
| 3 | Italienische Typbezeichnungen werden erkannt. | `test_italian_affair_types` |

### US-14 Frage in natürlicher Sprache stellen

**Als** WWF-Fachperson **möchte ich** eine Frage wie «Motionen zum Klima im Kanton Zürich seit 2024» stellen, **damit** ich ohne Filterformular suchen kann.
Must · R20, R21 · Erledigt · GitHub [#50](https://github.com/FatihHayyar/wwf-polit-assistant/issues/50)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Thema, Kanton und Geschäftstyp werden aus der Frage erkannt. | `test_topic_canton_and_affair_type` |
| 2 | Französische Fragen und Zeiträume («seit 2024») werden verstanden. | `test_since_year_and_french_question` |
| 3 | Ein Kantonsname wird als Ort und nicht als Thema «öffentliche Hand» verstanden. | `test_named_canton_is_a_place_not_the_public_sector_topic` |
| 4 | Die Antwort zeigt, was verstanden wurde, und liefert passende Treffer. | `test_question_returns_filters_and_matching_records` |
| 5 | Ungültige Fragen werden abgewiesen; zu viele Fragen werden begrenzt. | `test_invalid_question_and_rate_limit` |

### US-15 Energie- und Klima-Unterthemen nach WWF

**Als** WWF-Fachperson **möchte ich** die Unterthemen aus der WWF-Rückmeldung (u. a. Rechenzentren und Grossverbraucher getrennt), **damit** die Themen unserer Arbeitsweise entsprechen.
Must · R16, R22 · Erledigt; fachliche Freigabe durch WWF offen · GitHub [#51](https://github.com/FatihHayyar/wwf-polit-assistant/issues/51)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Rechenzentren und Grossverbraucher sind getrennte Themen unter Klima & Energie. | `test_data_centres_and_large_consumers_are_separate_climate_topics` |
| 2 | Bestehende Abonnements eines ersetzten Themas wechseln auf die neuen Themen. | `test_replaced_category_subscriptions_move_to_successors` |
| 3 | Jedes Demo-Beispiel wird seinem Thema zugeordnet. | `test_every_demo_title_is_classified_into_its_topic` |
| 4 | WWF bestätigt die Themenliste. | Offen ([Fragenliste](../01-project-management/question-log.md)) |

### US-16 Klassifikationsgüte messen

**Als** Projektleitung **möchte ich** die Klassifikation an einem unabhängigen Prüfset messen, **damit** ich ihre Qualität belegen kann statt sie zu behaupten.
Should · R03, R12 · Erledigt; Prüfung durch WWF-Fachpersonen offen · GitHub [#52](https://github.com/FatihHayyar/wwf-polit-assistant/issues/52)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Das Prüfset überschneidet sich nicht mit den Entwicklungsbeispielen. | `test_sample_is_disjoint_from_development_set` |
| 2 | Precision und Recall werden korrekt berechnet, unklare Fälle ausgenommen. | `test_binary_metrics_ignore_ambiguous_records` |
| 3 | Ergebnis Prüfset B: Precision 1.0, Recall 0.667. | [Prüfset-Auswertung](../05-testing/evidence/holdout-evaluation.md) |

### Verbesserungen aus dem eigenen Test der Oberfläche (November 2026)

### US-17 Einfache Abonnementverwaltung

**Als** Abonnent:in **möchte ich** ein Abonnement nur durch Ankreuzen anlegen und unten speichern, **damit** die Verwaltung schnell und verständlich ist.
Should · R06, R10 (Rückmeldung aus dem Test der Oberfläche, D15) · Erledigt · GitHub [#53](https://github.com/FatihHayyar/wwf-polit-assistant/issues/53)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Das Formular enthält nur Auswahlfelder: keinen Namen und keine Suchbegriffe. Der Name entsteht aus der Auswahl. | `test_profile_roundtrip_and_stop_all`, `browser_membership` |
| 2 | «Abonnement speichern» unten speichert, schliesst den Dialog und bestätigt. | `browser_membership` |
| 3 | Speichert man ein älteres Abonnement mit Suchbegriffen, entfallen diese. | `test_saving_a_former_profile_removes_its_keywords` |

### US-18 Inhalt mit einem Klick verfolgen

**Als** Abonnent:in **möchte ich** ein Geschäft direkt in seiner Detailansicht verfolgen, **damit** ich keine Nummer abtippen muss.
Should · R07, R10 · Erledigt · GitHub [#54](https://github.com/FatihHayyar/wwf-polit-assistant/issues/54)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | «☆ Verfolgen» in der Detailansicht verfolgt den Inhalt; ein zweiter Klick beendet das Verfolgen. | `browser_membership` |
| 2 | Die Verwaltung listet verfolgte Inhalte mit Titel und kann sie entfernen. | `test_profile_roundtrip_and_stop_all`, `browser_membership` |

### US-19 Klare Meldungen bei Registrieren und Anmelden

**Als** Abonnent:in **möchte ich** erfahren, ob ich mich anmelden oder zuerst registrieren muss, **damit** ich nicht rätseln muss, warum keine E-Mail kommt.
Should · R10, R19 (Rückmeldung aus dem Test, D16) · Erledigt · GitHub [#55](https://github.com/FatihHayyar/wwf-polit-assistant/issues/55)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Gegeben eine registrierte Adresse, wenn ich «Registrieren» wähle, dann werde ich zur Anmeldung geführt, und es wird keine E-Mail versendet. | `test_register_with_a_registered_address_asks_to_sign_in` |
| 2 | Gegeben eine unbekannte Adresse, wenn ich «Anmelden» wähle, dann werde ich zur Registrierung geführt. | `test_login_with_an_unknown_address_asks_to_register` |
| 3 | Wähle ich zuerst die falsche Aktion, blockiert das die richtige nicht. | `test_answers_without_email_do_not_start_the_address_cooldown` |
| 4 | Fordere ich mehrmals einen Link an, funktioniert auch der Link aus einer früheren E-Mail. | `test_requesting_again_keeps_the_earlier_link_valid` |
| 5 | Nach dem Abmelden ist das Anmeldefenster leer; die Auswahl wechselt bei falscher Aktion automatisch. | `browser_membership` |

### US-20 Konto löschen mit Bestätigung

**Als** Abonnent:in **möchte ich** beim Löschen meines Kontos eine Bestätigung erhalten, **damit** ich sicher bin, dass meine Daten entfernt sind.
Should · R10 · Erledigt · GitHub [#56](https://github.com/FatihHayyar/wwf-polit-assistant/issues/56)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Nach dem Löschen bin ich abgemeldet und erhalte eine Bestätigungs-E-Mail. | `test_account_deletion_is_confirmed_by_email` |

### Arbeitspakete in M2

| ID | Arbeitspaket | Ergebnis | Status |
|---|---|---|---|
| AP-2.1 | Fragen aus der Umsetzung sammeln | Einträge in der [Fragenliste](../01-project-management/question-log.md) | Erledigt |
| AP-2.2 | Zwischenpräsentation vorbereiten und halten | Folien (privater Abgabeordner), Rückmeldungen in der Fragenliste (F15) | Geplant am 18.11.2026 |

---

---

## M3 – Rückmeldungen, Fertigstellung und WIPRO-Dokumentation

M3 beginnt nach der Zwischenpräsentation am 18.11.2026 und endet mit der Abgabe am 21.12.2026. Stories aus den Rückmeldungen der Zwischenpräsentation werden hier ergänzt, sobald sie vorliegen.

### US-21 Übergabe für Azure vorbereiten

**Als** WWF-IT **möchte ich** einen Container und eine Zielarchitektur für Azure, **damit** wir die Anwendung in unserer Umgebung betreiben können.
Must · R13, R14 · In Arbeit (Testdeployment durch WWF offen) · GitHub [#59](https://github.com/FatihHayyar/wwf-polit-assistant/issues/59)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Das Image läuft ohne Root-Rechte und meldet seinen Zustand über `/health`. | Docker-Build in der CI; [Deployment-Anleitung](../06-handover/deployment-guide.md) |
| 2 | Zielarchitektur, Konfiguration und Betriebsanforderungen sind beschrieben. | [Azure-Integration](../03-architecture/azure-integration.md) |
| 3 | WWF startet die Anwendung in einer Testumgebung. | Offen |

### US-22 Anwendung anhand der Dokumentation übernehmen

**Als** WWF-IT **möchte ich** die Anwendung allein anhand der Dokumentation starten und betreiben, **damit** die Übergabe nicht von einer Person abhängt.
Must · R11 · In Arbeit · GitHub [#60](https://github.com/FatihHayyar/wwf-polit-assistant/issues/60)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | Eine neue Umgebung startet mit der [Schnellstart-Anleitung](../getting-started.md). | Manueller Testfall |
| 2 | Häufige Probleme sind in der [Fehlerbehebung](../troubleshooting.md) beschrieben. | Durchsicht |

### US-23 MVP mit WWF abnehmen

**Als** WWF-Fachperson **möchte ich** typische Aufgaben mit der Anwendung durchspielen, **damit** wir entscheiden können, ob der MVP unseren Bedarf deckt.
Must · R12 · Offen · GitHub [#61](https://github.com/FatihHayyar/wwf-polit-assistant/issues/61)

| AK | Gegeben / Wenn / Dann | Test |
|---|---|---|
| 1 | WWF führt die Anwendungsfälle durch; Beobachtungen und Entscheid sind dokumentiert. | Abnahmeformular im privaten Abgabeordner |

### Arbeitspakete in M3

| ID | Arbeitspaket | Ergebnis | Status |
|---|---|---|---|
| AP-3.1 | WIPRO-Bericht schreiben | Bericht nach Vorgaben «Aufbau Bericht» | In Arbeit |
| AP-3.2 | Abgabe | Abgabe in Complesis bis 21.12.2026, Kopie an WWF | Offen |
| AP-3.3 | Abschlusspräsentation | Präsentation im Zeitraum 18.01.–05.02.2027 | Offen |

---

## Nicht in diesem Projekt (Won't)

| Thema | Grund |
|---|---|
| Umsetzung in Microsoft 365 | Am Kick-off aus dem Umfang genommen (D1) |
| KI-Klassifikation und Chat mit Sprachmodell | Weiterentwicklung nach dem MVP (D2, D13); Schnittstellen sind vorbereitet |
| Produktiver Betrieb auf Azure | Aufgabe von WWF; das Projekt liefert die Übergabe (US-21) |

## Änderungen am Backlog

| Wann | Änderung | Auslöser | Entscheid |
|---|---|---|---|
| M2, nach der WWF-Rückmeldung (Oktober 2026) | Neu: US-12 mehrere Abonnements, US-13 Geschäftstyp, US-15 Unterthemen; dazu US-14 als Umsetzung der dialogorientierten Abfrage aus der Aufgabenstellung | E-Mail von WWF; Abgleich mit der Aufgabenstellung | D12–D14 |
| M2, Test der Oberfläche (November 2026) | Suchbegriffe aus Abonnements entfernt (bleiben in der Suche), Namen werden erzeugt, Verfolgen mit einem Klick (US-17, US-18) | Rückmeldung aus dem eigenen Test | D15 |
| M2, Test der Oberfläche (November 2026) | Klare Meldungen bei Registrieren/Anmelden, Bestätigung beim Löschen (US-19, US-20) | Rückmeldung aus dem eigenen Test | D16 |
