# API-Leitfaden

Die laufende Anwendung stellt `/docs` und `/openapi.json` bereit. Dort stehen die verbindlichen Request- und Response-Schemas des installierten Stands. Alle folgenden fachlichen Routen beginnen mit `/api/v1`.

## Recherche ohne Anmeldung

| Methode und Pfad | Funktion |
|---|---|
| `GET /entities` | Verfügbare Bereiche |
| `GET /entities/search` | Bereichsübergreifende Suche |
| `GET /entities/{dataset}` | Bereichsliste mit Filtern |
| `GET /entities/{dataset}/{record_id}` | Detailansicht und Beziehungen |
| `GET /affairs`, `GET /affairs/{affair_id}` | Geschäftssuche und Geschäftsdetails |
| `GET /categories`, `GET /cantons`, `GET /affair-types` | Filterwerte |
| `POST /ask` | Frage in natürlicher Sprache in Filter übersetzen und erste Ergebnisseite liefern |
| `GET /health` am Server-Root | Erreichbarkeit und Datenbankverbindung |

Beispiel: `GET /api/v1/entities/agendas?q=Photovoltaik&canton=ZH&page=1&page_size=10`.

Bereichslisten unterstützen unter anderem `q`, `category`, `subcategory`, `canton`, `affair_type` (nur Geschäfte, Wert aus `/affair-types`), `year`, `month`, `date_from` und `date_to`. Verknüpfungsfilter wie `affair_id`, `meeting_id`, `agenda_id`, `group_id` oder `person_id` gelten je nach Bereich. `page` beginnt bei 1; `page_size` liegt zwischen 1 und 50, standardmässig 10. Jahre sind auf 1900–2100 begrenzt. Dokumentensuche lädt keine externen PDFs nach.

### Frage in natürlicher Sprache

```http
POST /api/v1/ask
{"question": "Motionen zum Wolf im Wallis seit 2024", "page": 1}
```

```json
{
  "question": "Motionen zum Wolf im Wallis seit 2024",
  "dataset": "affairs",
  "filters": {"category": "biodiversity_landscape", "subcategory": "species_habitats",
              "canton": "VS", "affair_type": "Motion", "date_from": "2024-01-01"},
  "recognised": [{"kind": "affair_type", "value": "Motion", "text": "Motion"}, "..."],
  "results": {"items": ["..."], "pagination": {"page": 1, "page_size": 10, "total_items": 3, "total_pages": 1}}
}
```

Die Frage umfasst 3–300 Zeichen; höchstens 30 Fragen pro Minute und Client-Adresse. `recognised` nennt für jeden erkannten Teil Art (`dataset`, `category`, `subcategory`, `canton`, `affair_type`, `period`, `keyword`), Wert und Fundstelle.

## Authentifizierung und Konto

| Methode und Pfad | Funktion |
|---|---|
| `POST /auth/register` | Registrierung mit E-Mail-Bestätigung |
| `GET /auth/verify-email` | Bestätigungsseite des Registrierungslinks (verbraucht das Token nicht) |
| `POST /auth/verify-email` | Registrierung bestätigen und anmelden (Formularfeld `token`) |
| `POST /auth/login` | Anmeldelink an bestehendes Konto senden |
| `GET /auth/verify-login` | Bestätigungsseite des Anmeldelinks |
| `POST /auth/verify-login` | Anmeldung bestätigen (Formularfeld `token`) |
| `GET /auth/providers` | Aktivierte externe Anbieter |
| `GET /auth/google`, `GET /auth/google/callback` | Optionaler Google-Anmeldefluss |
| `GET /auth/me` | Angemeldetes Konto |
| `POST /auth/logout` | Sitzungscookie entfernen und alle ausgestellten Tokens widerrufen |
| `DELETE /auth/me` | Eigenes Konto und zugehörige Daten löschen |

Register und Login erhalten einen JSON-Body mit `email` und antworten immer mit derselben Meldung, unabhängig davon, ob ein Konto existiert; E-Mails werden im Hintergrund versendet. Ein Link öffnet eine Bestätigungsseite; erst deren POST verbraucht das Token, setzt ein HttpOnly-Cookie `access_token` und leitet zur Oberfläche weiter. POSTs mit fremdem `Origin` werden mit 403 abgewiesen. API-Clients können alternativ `Authorization: Bearer <JWT>` verwenden; ein vorhandener Bearer-Header hat Vorrang vor dem Cookie. Logout erhöht die Sitzungsversion des Kontos und macht damit alle zuvor ausgestellten Tokens ungültig.

E-Mail- und Token-Endpunkte sind ratenbegrenzt und antworten bei Überschreitung mit `429` und `Retry-After`. Die Grenzen stehen in der [Monitoring-Dokumentation](monitoring.md#anmeldung-und-schutz-vor-missbrauch).

## Abonnements und Empfänger

Ein Konto besitzt bis zu zehn benannte Abonnements. Alle Routen benötigen eine Anmeldung; Anlegen und Ändern zusätzlich eine bestätigte E-Mail-Adresse.

| Methode und Pfad | Funktion |
|---|---|
| `GET /subscriptions` | Übersicht: Abonnements, Watches, `active`, `max_profiles` |
| `POST /subscriptions/profiles` | Abonnement anlegen (`201`; `409` ab dem elften) |
| `PUT /subscriptions/profiles/{id}` | Abonnement vollständig ersetzen |
| `DELETE /subscriptions/profiles/{id}` | Abonnement löschen |
| `DELETE /subscriptions` | Alle Abonnements und Watches entfernen |

```json
{
  "name": "Energie-Motionen in Bern",
  "active": true,
  "category_ids": [1],
  "canton_keys": ["BE"],
  "affair_types": ["Motion", "Postulat"],
  "datasets": ["affairs", "documents"],
  "keywords": ["Photovoltaik"]
}
```

Kategorie-IDs stammen aus `/categories`, Geschäftstypen aus `/affair-types`. Bis zu 20 Suchbegriffe mit je 1–200 Zeichen. Innerhalb einer Gruppe gilt OR, zwischen Gruppen AND, zwischen Abonnements OR. Leere Dataset-Auswahl bedeutet alle Bereiche. Sind Themen, Kantone, Geschäftstypen und Suchbegriffe leer, ist das Abonnement pausiert (`paused: true`); Einzel-Watches bleiben aktiv. Fremde oder unbekannte Abonnement-IDs ergeben `404`. Jede Änderung löst eine Bestätigungs-E-Mail mit der Zusammenfassung aus (höchstens 60 pro Stunde).

`PUT /subscriptions/watches/{dataset}/{record_id}` beobachtet einen Inhalt, `DELETE` entfernt die Beobachtung. `record_id` ist die positive lokale ID; bei Dokumenten ist dies `pk`, nicht `source_id`.

`GET /subscriptions/recipients` liest Adressen und Bestätigungsstatus. `PUT` ersetzt die Liste mit `{"emails": ["name@example.org"]}`; insgesamt 1–10 Adressen. Fremde Adressen erhalten einen Bestätigungslink zu `/subscriptions/recipients/verify?token=...`; auch dieser öffnet eine Bestätigungsseite, die Bestätigung erfolgt per POST. Änderungen der Adressliste sind auf zehn pro Stunde begrenzt. Nur bestätigte Adressen erhalten Monitoring-Nachrichten. Diese Verwaltungsrouten benötigen eine gültige Benutzersitzung; der Bestätigungslink verwendet seinen eigenen Token.

## Demo-Testbenachrichtigung

Nur mit `DEMO_MODE=true`; sonst antworten die Routen mit `404` bzw. `GET /demo/status` mit `enabled: false`.

| Methode und Pfad | Funktion |
|---|---|
| `GET /demo/status` | Ob der Demo-Modus aktiv ist und welche Mailbox-URL angezeigt wird |
| `GET /demo/topics` | Auswählbare Themen und Vorauswahl aus den eigenen Abonnements (Anmeldung erforderlich) |
| `POST /demo/notifications` | Testgeschäft zu `category_code` erstellen, klassifizieren und Benachrichtigung an das eigene Konto senden; fünf pro zehn Minuten |

## Geschützte Sync-Verwaltung

Alle Sync-Routen verlangen `X-Sync-API-Key: <SYNC_API_KEY>`. Eine normale Benutzersitzung oder ein Administrator-JWT ersetzt diesen Schlüssel nicht.

| Methode und Pfad | Funktion |
|---|---|
| `POST /sync/run` | Hintergrundlauf starten |
| `GET /sync/status`, `GET /sync/latest` | Checkpoints und letzter Bericht |
| `GET /sync/runs/{run_id}` | Laufstatus |
| `GET /sync/runs/{run_id}/log` | Laufprotokoll |
| `POST /sync/runs/{run_id}/cancel` | Abbruch anfordern |
| `POST /sync/runs/{run_id}/resume` | Job in einem neuen Lauf fortsetzen |

Ein fehlender konfigurierter Sync-Schlüssel führt zu `503`, ein falscher Schlüssel zu `401`, ein konkurrierender Lauf zu `409`. Ein angenommener Hintergrundlauf ist noch kein erfolgreicher Datenabgleich. Details zu Fortschritt und Wiederaufnahme stehen im [Monitoring-Leitfaden](monitoring.md).
