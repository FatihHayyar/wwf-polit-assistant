# Suche, Abonnements und Synchronisation

Technische Referenz zu Recherche, Abonnements, Benachrichtigungen und Datenabgleich. Einstieg und Benutzerhinweise stehen im [Dokumentationsindex](README.md).

Das lokale Frontend wird von FastAPI unter `/` ausgeliefert. Alle neun öffentlichen Bereiche besitzen eigene Navigationseinträge und bleiben über die API und Links auf verknüpfte Listen erreichbar. Die Suche unterstützt Suchbegriff, Haupt-/Unterthema, Kanton und Datumsbereich mit serverseitiger Pagination. Geschäftsdetails enthalten verknüpfte Datensätze, Links zu den vollständigen verknüpften Listen und die letzten 100 erkannten Änderungen.

## Lokal starten

PostgreSQL, JWT, SMTP und `SYNC_API_KEY` gemäss `.env.example` konfigurieren. Danach:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

`http://localhost:8000` öffnen. Registrierung und passwortlose Anmeldung erfolgen über E-Mail-Links. Oben rechts lassen sich Deutsch, Français, Italiano oder English wählen; der Browser merkt sich die Auswahl. Menüs, Filter, Abonnementsteuerung, Datumsangaben und Detailbeschriftungen folgen dieser Sprache. Quellinhalte fallen auf die verfügbare Originalsprache zurück; lange Texte werden nicht maschinell übersetzt. Detailansichten blenden technische IDs und doppelte Sprachfelder aus, zeigen einen Typ und Status, klappen lange Originaltexte ein und lassen leere verknüpfte Abschnitte weg.

Traktandenkarten verwenden ihren eigenen Titel, sonst den Titel des verknüpften Geschäfts, sonst den Sitzungsnamen, wenn die Quelle keinen Traktandentitel liefert. Sie zeigen Sitzungs- und Geschäftslinks sowie die offizielle Quelle, sofern vorhanden. Traktandendetails enthalten Sitzung, Gruppe und direkt angehängte Dokumente; Sitzungsdetails listen ihre Traktanden. Die Stichwortsuche in Traktanden durchsucht auch verknüpfte Sitzungsnamen/-beschreibungen und Geschäftstitel.

Die Recherche ist ohne Konto möglich. Ein Bereich «Auf dem Laufenden bleiben» neben den Ergebnissen bietet Registrierung, Anmeldung und Abonnementverwaltung. Themen sind unter ihren Hauptthemen gruppiert; ein ausgewähltes Hauptthema umfasst alle Unterthemen. Weitere Bereiche stehen in einem aufklappbaren Abschnitt zur Verfügung. Die Auswahl von Geschäften umfasst auch Aktualisierungen verknüpfter Datensätze.

## Anmeldung und Schutz vor Missbrauch

Registrierung und Anmeldung antworten unabhängig davon, ob ein Konto existiert, mit derselben Meldung. Bei einem bestehenden Konto erhält die Registrierung einen Anmeldelink, bei einem unbestätigten Konto die Anmeldung einen Bestätigungslink. Unbekannte Adressen erhalten keine E-Mail.

Ein E-Mail-Link öffnet zuerst eine Bestätigungsseite. Erst der Klick auf die Schaltfläche (POST, nur von derselben Herkunft) verbraucht das einmalige Token, meldet an und setzt ein HttpOnly-Sitzungscookie. Linkscanner in Unternehmens-Mailsystemen können Tokens deshalb nicht vorzeitig verbrauchen. Ein bereits geöffneter Anwendungstab meldet sich ohne Verlust der Filter an; die Anwendung versucht anschliessend, den neuen Tab zu schliessen. Die API akzeptiert weiterhin Bearer-Tokens. Für Anmelde- und Monitoring-E-Mails muss SMTP konfiguriert sein.

Abmelden widerruft alle bis dahin ausgestellten Tokens des Kontos (Sitzungsversion in `users.session_version`). Endpunkte, die E-Mails senden oder Tokens annehmen, sind begrenzt:

| Bereich | Grenze |
|---|---|
| Registrierung/Anmeldung je Client-Adresse | 10 Anfragen pro 15 Minuten |
| E-Mails an dieselbe Adresse | höchstens 1 pro Minute und 5 pro Stunde |
| Bestätigung von Links je Client-Adresse | 30 pro 15 Minuten |
| Änderung der Empfängeradressen je Konto | 10 pro Stunde |
| Bestätigungs-E-Mails zu Abonnementänderungen | 60 pro Stunde; darüber wird gespeichert, aber keine E-Mail gesendet |

Überschreitungen ergeben HTTP 429 mit `Retry-After`. Die Grenzen gelten pro API-Prozess (In-Memory); bei mehreren API-Instanzen ist ein gemeinsamer Speicher wie Redis nötig. Hinter einem Reverse Proxy muss uvicorn mit `--proxy-headers` laufen. `RATE_LIMIT_ENABLED=false` ist nur für kontrollierte Testumgebungen gedacht.

## Klassifikation bestehender Datensätze

Bestehende Geschäftsklassifikationen stehen auch der Suche verknüpfter Datensätze zur Verfügung. Um bestehende verknüpfte und eigenständige Datensätze nach ihrem eigenen Inhalt zu klassifizieren, dient der folgende Vorbereitungsjob. Er erzeugt keine Benachrichtigungen:

```powershell
.venv\Scripts\python.exe -m scripts.reclassify_rules --apply
```

Der Job umfasst alle neun Bereiche, setzt ein bestandenes Entwicklungsset voraus, spielt die konfigurierte JSON-Taxonomie ein und schreibt in Batches (Standard 1'000; Dokumente/Texte höchstens 250). Er hält die gemeinsame Synchronisationssperre und überspringt beim Neustart vollständige Klassifikationen der aktuellen Version. Ohne `--apply` bleibt PostgreSQL schreibgeschützt. `--dataset agendas` verarbeitet einen Bereich, `--force` baut nach Taxonomieänderungen auch aktuelle Klassifikationen neu auf. Für die Qualitätsschranke wird die Git-Historie mit dem festgelegten Basis-Commit benötigt. Der ältere Job `scripts.classify_entities` bleibt ohne diese Schranke verfügbar. Neue Datensätze und relevante Änderungen werden während der Synchronisation klassifiziert; unveränderte Datensätze ohne eigene Klassifikation werden beim Durchlauf ebenfalls klassifiziert.

## Abonnementverhalten

Nutzer wählen Themen, Kantone, Stichwörter und optional Bereiche. Hauptthemen schliessen ihre Unterthemen ein. Innerhalb einer Auswahlgruppe gelten Werte als Alternativen (ODER); Themen- und Kantonseinschränkung müssen gemeinsam für denselben Datensatz oder dasselbe verknüpfte Geschäft passen. Eine leere Themen- oder Kantonsgruppe schränkt nicht ein. Filterabonnements pausieren, wenn Themen, Kantone und Stichwörter leer sind. Eine leere Bereichsauswahl bedeutet alle neun Bereiche.

Stichwörter sind wörtliche Phrasen ohne Gross-/Kleinschreibung: eine pro Zeile, bis zu 20 Phrasen mit je bis zu 200 Zeichen. Jede Phrase genügt; Stichwort-, Themen- und Kantonsfilter gelten gemeinsam. Durchsucht werden dieselben gespeicherten Felder wie bei der Stichwortsuche. Verknüpfte Datensätze können zusätzlich über die Klassifikation ihres Geschäfts passen.

Die Abonnementverwaltung bietet das Verfolgen einzelner Datensätze. Geschäfts-Watches umfassen verknüpfte Änderungen; Sitzungs-Watches umfassen Datensätze mit dieser Sitzungs-ID. Watches wirken unabhängig von Filtern und sich ändernden Klassifikationen. Der Abonnementdialog listet Watches und entfernt sie. Das Speichern leerer Filter lässt Watches aktiv; «Alle Benachrichtigungen beenden» entfernt Filter, Stichwörter und Watches.

Gruppendetails listen verknüpfte Sitzungen. Gruppen-Watches umfassen den Gruppendatensatz sowie seine Sitzungen und sitzungsbezogenen Datensätze. Gruppen erben Geschäftsklassifikationen über ihre Sitzungen. Interessenbindungen besitzen eigene Klassifikationen und Watches; sie zeigen die deklarierende Person, sofern sie in der importierten Datenbank vorhanden ist. Eine Geschäftsbeziehung wird für eine Interessenbindung nicht konstruiert. Weitere Interessenbindungen einer Person sind über `person_id` abrufbar, Sitzungen einer Gruppe über `group_id`. Datumsfilter für Gruppen verwenden `updated_at`, weil das Gruppenmodell kein Beginndatum besitzt. Datumsfilter für Interessenbindungen verwenden `begin_date`; fehlende Daten passen nicht zu einer Datumseinschränkung. Die Synchronisation von Mitgliedschaften liegt ausserhalb dieser beiden Quell-Datasets.

Jede relevante Quelländerung erzeugt ein Change-Event und höchstens eine Benachrichtigung pro passendem Nutzer. Eine Sitzung mit mehreren Geschäften wird allen diesen Geschäften zugeordnet, sendet aber eine Benachrichtigung pro Nutzer. Vor dem Versand werden die aktuellen Abonnementeinstellungen erneut geprüft. Die E-Mail enthält einen Frontend-Link auf den betroffenen Datensatz.

## Benachrichtigung in der Demo testen

Mit `DEMO_MODE=true` (in `docker-compose.demo.yml` gesetzt) zeigt die Startseite eine Anleitung in vier Schritten, und der Abonnementdialog enthält «Benachrichtigung testen (Demo)». Die Funktion speichert die aktuelle Auswahl und erstellt ein fiktives neues Geschäft mit eigener ID ab 900'000'000. Es durchläuft die echte regelbasierte Klassifikation, die Benachrichtigungsrichtlinie, den Abonnementabgleich und den Digest-Versand; zugestellt wird nur an das angemeldete Konto. Passt das Testgeschäft nicht zu den gespeicherten Filtern, erklärt die Oberfläche dies statt eine E-Mail zu senden. Pro Konto sind fünf Tests in zehn Minuten möglich.

Über die Kommandozeile im Demo-Container:

```powershell
docker compose -f docker-compose.demo.yml exec app python -m scripts.demo.send_test_notification --email name@example.org --topic renewable_electricity
```

Ohne `DEMO_MODE` antworten die Demo-Endpunkte mit 404 und das Skript bricht ab. Für eine Produktionsdatenbank darf der Modus nicht aktiviert werden.

## Tägliche und manuelle Synchronisation

Der Docker-Scheduler und die geschützte Entwicklungs-API verwenden beide `scripts.sync.run_all`. Im öffentlichen Frontend gibt es keine Synchronisationssteuerung. Die manuelle Ausführung erfordert `SYNC_API_KEY` im Header `X-Sync-API-Key`. Eine Datenbanksperre verhindert parallele Gesamtläufe. Ein fehlgeschlagener Bereich wird protokolliert, die übrigen Bereiche laufen weiter. Der E-Mail-Versand beginnt erst, wenn alle Bereiche erfolgreich waren; andernfalls bleiben ausstehende Benachrichtigungen bis zu einer erfolgreichen Wiederaufnahme erhalten. JSON-Ergebnisse werden nach `logs/sync_<run_id>.json` geschrieben.

```powershell
.venv\Scripts\python.exe -m scripts.sync.run_all
```

Dieser Befehl kontaktiert OpenParlData, verändert Datensätze und versendet ausstehende Benachrichtigungen. Er ist vom Klassifikations-Vorbereitungsjob getrennt.

Geschäfte, Sitzungen und Dokumente verwenden Zeitstempel-Checkpoints. Bevor einem Checkpoint vertraut wird, wird die Quellanzahl der ersten API-Seite mit der lokalen Anzahl verglichen (eindeutige Identitäten; bei Dokumenten Zeilen inklusive Beziehungsvarianten). Eine Lücke löst einen Identitätsabgleich mit der Quelle aus, der auch Datensätze vor dem Checkpoint umfasst. Dieser Abgleichmodus wird mit jedem bestätigten Batch gespeichert, sodass ein wiederaufgenommener Job historische Datensätze weiter prüft. Hat «Dokumente» keine neueren Zeitstempel als der Cursor, werden alle fehlenden Identitäten und die aktuelle Live-Seite geladen. `--recheck` erzwingt eine vollständige Inhaltsprüfung, auch wenn die Anzahlen übereinstimmen; gleiche Anzahlen beweisen weder identische IDs noch erkennen sie historische Änderungen ohne neuen Zeitstempel. Dokumente prüfen zusätzlich die höchste Live-ID und erkennen so rückdatierte neue Dokumente, selbst wenn Löschungen die Gesamtzahl unverändert lassen.

Traktanden, Abstimmungen, Ereignisse und Texte werden vollständig durchlaufen, weil ihre Zeitstempel fehlen oder unzuverlässig sind. Auch Gruppen und Interessenbindungen werden wegen ihrer geringeren Grösse vollständig geprüft, um ältere Datensätze und fehlende Zeitstempel abzudecken. Vollständige Durchläufe sind beim Erstimport und täglich aufwendig, erkennen aber Änderungen an älteren IDs. Klassifikation und Benachrichtigungspipeline laufen nur bei Inhaltsänderungen, ergänzt um das oben beschriebene Nachholen fehlender Klassifikationen. Reine Zeitstempeländerungen erzeugen keine Benachrichtigungen. Wiederholte echte Übergänge wie A → B → A erzeugen jeweils ein neues Change-Event; das erneute Einspielen unveränderter Daten dupliziert keine Benachrichtigungen.

Verknüpfte Änderungen erscheinen in Geschäftsdetail und -verlauf und passen zu Geschäftsabonnements. Sie überschreiben das Quell-`updated_at` des Geschäfts nicht. Textänderungen bauen die Klassifikation betroffener Geschäfte neu auf; Titeländerungen eines Geschäfts lösen eine Neuklassifikation aus. Andere verknüpfte Datensätze erhalten eigene Inhaltsklassifikationen.

Dokumente verwenden in Frontend-URLs und Change-Events den lokalen Primärschlüssel, weil Quell-IDs von Dokumenten in mehreren Beziehungskontexten vorkommen können. Die ursprüngliche Quell-ID bleibt sichtbar. Mehrdeutige Dokumentidentitäten lassen den Batch scheitern, statt stillschweigend einen anderen Datensatz zu aktualisieren.

## Prüfung und Grenzen

```powershell
$env:DATABASE_URL = 'sqlite://'
$env:JWT_SECRET_KEY = 'isolated-test-key-only-not-for-production'
.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_*.py'
node tests/test_frontend.cjs
```

Die Tests verwenden SQLite und simulieren Upstream-HTTP und SMTP; es werden keine echten E-Mails versendet. Die API-Tests laufen über den echten FastAPI-Stack (`TestClient`). Die CI prüft zusätzlich die Migrationen auf PostgreSQL 17 und baut das Docker-Image. Aktuelle Befehle und Voraussetzungen stehen im [Testplan](05-testing/test-plan.md). Ein vollständiger Live-Abgleich bleibt eine Betriebsprüfung. Die Suche umfasst gespeicherte Felder; externe PDF- und Dokumentanhänge werden nicht heruntergeladen oder extrahiert.

Initiale Themenzuordnungen, Bereichsabdeckung und offene Azure-Entscheidungen stehen in der [WWF-Anforderungsprüfung](wwf-requirements.md).

Nach Codeänderungen eine lokal ohne `--reload` gestartete API neu starten und den Docker-Stack neu bauen. Neue Migrationen werden durch den Dienst `migrate` angewendet:

```powershell
docker compose up -d --build
```

## Synchronisationssteuerung für die Entwicklung

Die folgenden Endpunkte über `/docs` mit `X-Sync-API-Key` oder einen API-Client aufrufen. Der Schlüssel gehört nicht in Frontend-Code.

- `POST /api/v1/sync/run`: startet den Hintergrundprozess und liefert die Run-ID.
- `GET /api/v1/sync/runs/{run_id}`: Status, aktueller Bereich und abgeschlossene Summen.
- `GET /api/v1/sync/runs/{run_id}/log`: Worker-Ausgabe zum Fortschritt innerhalb eines Bereichs.
- `GET /api/v1/sync/status`: Checkpoints der Bereiche (ebenfalls mit Schlüssel).
- `POST /api/v1/sync/runs/{run_id}/cancel`: fordert den Abbruch an. Den Status prüfen, bis er `cancelled` lautet; die Annahme allein bestätigt den Abbruch nicht.

Der Runner prüft jede Sekunde, ob ein Abbruch angefordert wurde, und beendet dann den laufenden Bereichsprozess; Verbindungen und Runner-Sperre werden freigegeben. Bereits bestätigte Batches bleiben gespeichert; ein späterer Lauf kann unveränderte Datensätze sicher erneut einspielen. Während des Versands wird vor jeder E-Mail auf Abbruch geprüft; eine bereits laufende Zustellung lässt sich nicht zurückholen. Ältere laufende Worker antworten auf einen Abbruch mit 409 und müssen abgeschlossen oder vom Betrieb separat gestoppt werden. Die öffentliche Seite fragt keinen Synchronisationsstatus ab; Entwicklungsclients können den Status manuell oder in einem bewusst gewählten Intervall (z. B. 15 Sekunden) abfragen.

### PowerShell-Beispiel

Zuerst die lokale API starten. In einem weiteren Terminal ausführen (der Schlüssel wird ohne Echo gelesen):

```powershell
$syncBase = "http://localhost:8000/api/v1/sync"
$syncSecret = Read-Host "SYNC_API_KEY" -AsSecureString
$syncHeaders = @{ "X-Sync-API-Key" = ([System.Net.NetworkCredential]::new("", $syncSecret)).Password }
$syncRun = Invoke-RestMethod -Method Post -Uri "$syncBase/run" -Headers $syncHeaders
$syncRunId = $syncRun.run_id
$syncRun
```

Status und Worker-Ausgabe bei Bedarf abfragen:

```powershell
Invoke-RestMethod -Uri "$syncBase/runs/$syncRunId" -Headers $syncHeaders | ConvertTo-Json -Depth 5
(Invoke-RestMethod -Uri "$syncBase/runs/$syncRunId/log" -Headers $syncHeaders).log
```

Für einen bereits laufenden Lauf `$syncRunId` auf dessen ID setzen, statt einen weiteren zu starten. Hält ein anderer Worker die Sperre, antwortet der Start mit HTTP 409.

Abbruch anfordern und anschliessend den Status prüfen:

```powershell
Invoke-RestMethod -Method Post -Uri "$syncBase/runs/$syncRunId/cancel" -Headers $syncHeaders
Invoke-RestMethod -Uri "$syncBase/runs/$syncRunId" -Headers $syncHeaders
```

## Typnormalisierung und Benachrichtigungswarteschlange

Der Abgleich vergleicht Textfelder, nachdem API-Werte in ihre Textdarstellung in der Datenbank umgewandelt wurden. So entspricht zum Beispiel `item_number=1` dem gespeicherten `"1"`, während eine Änderung auf `2` weiterhin ein Event erzeugt. Reine Zeitstempelunterschiede bleiben ausgeschlossen. Checkpoint-Zähler werden nach jedem Batch gespeichert.

Der Versand hat keine Obergrenze von 100 Nachrichten. Standardmässig fasst er die zu Beginn vorhandene Warteschlange zu Zusammenfassungen zusammen; Einzelversand ist ebenfalls möglich. Jede Benachrichtigung wird pro Aufruf höchstens einmal versucht; fehlgeschlagene Sendungen bleiben für einen späteren Lauf ausstehend. Während des Versands neu eintreffende Einträge warten auf den nächsten Aufruf. Mit dem optionalen `limit` kann der Betrieb einen begrenzten Versand anfordern. Gesendete und fehlgeschlagene Summen werden regelmässig gespeichert und bleiben bei einem Abbruch erhalten.

`python -m scripts.quarantine_agenda_type_events RUN_ID` zeigt Traktanden-Events eines bestätigt abgebrochenen Laufs, die nur die Nummerierung betreffen. `--apply` schreibt eine Prüfkopie unter `logs/`, markiert diese Events als `ignored` und storniert ihre ausstehenden Benachrichtigungen. Neue Datensätze und Events mit anderen geänderten Feldern bleiben erhalten. Frühere Feldwerte wurden nicht gespeichert, daher lassen sich diese Kandidaten nicht alle rückwirkend als falsch belegen; die Quarantäne bewahrt sie zur Prüfung auf, statt sie zu löschen. Ignorierte Events erscheinen weder im öffentlichen Geschäftsverlauf noch im E-Mail-Versand.

## Unterbrochene Jobs fortsetzen

`POST /api/v1/sync/runs/{run_id}/resume` (gleicher Header) startet einen neuen Hintergrundversuch desselben Jobs und liefert eine neue Run-ID. Die Zusammenfassung enthält `job_id`, `resume_of` und `dataset_results` für abgeschlossene, laufende und fehlgeschlagene Bereiche. Abgeschlossene Bereiche werden übersprungen; ein neues `POST /sync/run` startet einen neuen täglichen bzw. manuellen Job und prüft alle Bereiche erneut.

```powershell
$syncRun = Invoke-RestMethod -Method Post -Uri "$syncBase/runs/$syncRunId/resume" -Headers $syncHeaders
$syncRunId = $syncRun.run_id
Invoke-RestMethod -Uri "$syncBase/runs/$syncRunId" -Headers $syncHeaders | ConvertTo-Json -Depth 8
```

Vollständige Durchläufe lesen den offiziellen Bulk-Export **nur als ID-Inventar**, auch bei aufgeteilten Exporten, und laden die IDs anschliessend batchweise mit `offset=0` aus der Live-API. Der ID-Filter der API wird überprüft; ein ignorierter Filter oder ein abgeschnittener Batch führt zu einem Fehler statt zu stillschweigend übersprungenen Daten. Das umgeht die Offset-Grenze von 100'000 der Quelle und verhindert, dass Live-Werte mit einem älteren Export überschrieben werden. Neue höhere IDs seit dem Export werden berücksichtigt, bevor das Inventar fixiert wird. Inkrementelle Bereiche behalten ihren erfolgreichen Checkpoint und weichen auf ein ID-Inventar aus, wenn die Tiefengrenze der API erreicht wird. Der ursprüngliche obere Update-Cursor begrenzt den Job; spätere Änderungen prüft ein nachfolgender Job.

Der Fortschritt wird nach jedem bestätigten Datenbank-Batch unter `logs/sync_jobs/JOB_ID/` gespeichert. Bei inventarbasierten Durchläufen überspringt die Wiederaufnahme bestätigte Inventar-Batches; ein Absturz zwischen Datenbank-Commit und Fortschrittsspeicherung spielt den letzten Batch sicher erneut ein. Inkrementelle API-Durchläufe beginnen bei der Wiederaufnahme an ihrem erfolgreichen Checkpoint, weil ein Offset bei sich ändernder Sortierung unsicher wäre. Der erfolgreiche Abschluss eines Bereichs wird gespeichert, bevor der Runner zum nächsten wechselt. Jeder der neun Bereiche gibt Zähler, Dauer und Checkpoint-Ergebnis aus.

Ältere abgebrochene Jobs können über explizite `OK`-Zeilen in ihren Logs fortgesetzt werden. Ihre unvollständigen Bereiche besitzen kein stabiles Batch-Manifest und werden einmal von Beginn an erneut geprüft. Bestehende Daten und Benachrichtigungen bleiben erhalten. Job-Verzeichnis und Logs müssen Neustarts überdauern; API- und Worker-Container müssen diesen Speicher teilen, damit die Wiederaufnahme funktioniert. Bulk-Inventare benötigen Netzwerk- und Speicherplatz: Der aktuelle Texte-Export ist auf mehrere Dateien verteilt, ein seltener vollständiger Dokumente-Fallback kann mehrere GB benötigen. Aus fehlenden Export- oder API-IDs werden keine Löschungen abgeleitet.

## Relevante Benachrichtigungen

Alle Quelländerungen werden weiterhin als Events gespeichert. Ob ein Event eine E-Mail auslöst, wird unabhängig davon mit einer Richtlinienversion entschieden; neue Update-Events speichern Vorher-/Nachher-Werte. Leerraum, übliches HTML-Markup, Unicode-Darstellung und Entity-Kodierung lösen keine Benachrichtigung aus. Leerer Text und `null` sind gleichwertig. Technische Aktualisierungen von URL, Quell-ID, Reihenfolge und Sprachmetadaten werden ohne E-Mail gespeichert. Neue Datensätze sind in allen Bereichen relevant.

Passende Abonnementfilter und Watches werden nach dieser Richtlinie angewendet und vor der Zustellung erneut geprüft. `python -m scripts.reapply_notification_policy` zeigt Stornierungen in der ausstehenden Warteschlange an; `--apply` speichert eine Prüfkopie und wendet sie an. Ältere Events ohne Vorher-Werte lassen sich nur über die Namen der geänderten Felder bewerten, daher sind historische Formatierungsunterschiede nicht vollständig rekonstruierbar. Events bleiben auch bei stornierten Benachrichtigungen erhalten.

Der Standardversand gruppiert ausstehende Benachrichtigungen nach Nutzer und verknüpftem Geschäft bzw. nach eigenständigem Datensatz, wenn kein Geschäft existiert. Eine erfolgreiche Zusammenfassung markiert alle enthaltenen Benachrichtigungen als gesendet. Fehlgeschlagene Gruppen bleiben ausstehend und werden pro Aufruf einmal versucht. Bis zu 30 Änderungen werden in einer Zusammenfassung aufgeführt, mit Links auf Datensatz und Verlauf für weitere Änderungen. `limit` begrenzt die Anzahl der Zusammenfassungen; `digest=False` behält den Einzelversand für den ausdrücklichen Betriebsgebrauch.

«Texte» verwendet eine besondere Quellstrategie: Die API ignoriert den `id`-Filter und meldet globale Pagination-Metadaten. Das Bulk-Inventar liefert stabile Geschäftsgruppen; anschliessend wird die Live-API mit unterstützten `affair_id`-Filtern und tatsächlicher Seitenlänge gelesen. Verwaiste Text-IDs verwenden den Detail-Endpunkt. Der Fortschritt wird pro Gruppen-Batch bestätigt, der mehr als 500 Texte enthalten kann. Neue Bulk-Inhalte überschreiben nie neuere Live-Texte.

### Darstellung der Benachrichtigungen und SMTP-Fehler

Benachrichtigungen verwenden deutsche Bezeichnungen für alle neun Bereiche und enthalten Klartext und HTML. Verknüpfte Ereignisse, Dokumente, Abstimmungen und Texte bleiben unter ihrem Geschäft gruppiert; Betreff und Text nennen die enthaltenen Bereiche. Ältere Änderungen ohne Snapshot zeigen den aktuellen Wert, statt einen alten Wert zu erfinden. Detaillierte Vorher-/Nachher-Werte erscheinen, wo Snapshots existieren. Links verwenden `VERIFICATION_BASE_URL`; ausserhalb der lokalen Entwicklung eine erreichbare URL konfigurieren.

Der Versand stoppt nach drei aufeinanderfolgenden Fehlern. Erfolgreiche Nachrichten bleiben gesendet; fehlgeschlagene und nicht versuchte bleiben ausstehend. SMTP-Antwortcodes und die fehlgeschlagene Verbindungsphase werden gespeichert. Nach Behebung des SMTP-Problems den abgeschlossenen Job fortsetzen, um ausstehende E-Mails ohne erneuten Durchlauf abgeschlossener Bereiche zu senden. Ein Fehler bei der Authentifizierung erfordert die Prüfung von SMTP-Anbieter und -Konto; ein neuer Datenlauf löst ihn nicht.

Die Prüfung der Änderungsqualität vom 11. Oktober 2026 fand unter 1'329 Text-Updates mit Snapshot 1'251 reine Formatierungsänderungen (78 mit sichtbar anderem Inhalt, darunter Rechtschreibkorrekturen). Die Richtlinie `meaningful-v2` wertet sichtbaren HTML-Text aus, ignoriert Inline-Wrapper und gleichwertige Anführungszeichen sowie Leerraum um Satzzeichen. Vorzeichen, geänderte Beträge und Verneinungen bleiben relevant. Frühere Change-Events ohne Snapshot lassen sich nicht abschliessend auf Formatierungsänderungen prüfen. Lokale Detailauswertung: `logs/change_quality_audit_20261011.json`.

### Aktuelle Richtlinie: meaningful-v3

Alle Quelländerungen aktualisieren weiterhin Datenbank, Klassifikation und Änderungsverlauf. Die E-Mail-Relevanz wird unabhängig davon bestimmt. Diese Richtlinie ersetzt die früheren, breiteren Feldregeln.

| Bereich | Benachrichtigung bei neuen Datensätzen und diesen Änderungen |
| --- | --- |
| Geschäfte | Tatsächliche Statuswechsel und Wechsel aktiv/inaktiv; Korrekturen von Titel und Beginn-/Enddatum bleiben still |
| Traktanden | Termin, Status und Ergebnis; Korrekturen von Titel, Beschreibung, Nummerierung und Verknüpfung bleiben still |
| Sitzungen | Termine, Status und Ort |
| Abstimmungen | Entscheide und Stimmenzahlen/Ergebnisse; Titelkorrekturen bleiben still |
| Ereignisse | Datum und inhaltliche Angaben; Korrekturen von Akteur, Sortierung und Verknüpfung bleiben still |
| Dokumente | Neues Dokument oder geänderter extrahierter Text; Hash, Dateiname, Datum oder URL allein bleiben still, da sie keine sichtbare Inhaltsänderung belegen |
| Texte | Neuer Text oder inhaltlich sichtbare Änderung; reine Format-, Typ- oder Datumsänderungen bleiben still |
| Gruppen | Aktivstatus (und Lebenszyklusdaten, falls geliefert); Umbenennungen bleiben still |
| Interessenbindungen | Person, Rolle, Lebenszyklusdaten und Ex-officio-Status; Namens- und URL-Korrekturen bleiben still |

Leerraum, HTML-Wrapper, gleichwertige Anführungszeichen, reine Gross-/Kleinschreibung und einzelne Ein-Zeichen-Korrekturen in alphabetischen Wörtern ab sechs Zeichen bleiben still. Zahlenänderungen, Verneinungen, eingefügte oder gelöschte Wörter und grössere Ersetzungen bleiben relevant. Es handelt sich um eine deterministische, konservative Regel und keine Garantie politischer Bedeutung; komplexe Umformulierungen können redaktionell sein. Neue Datensätze unterliegen weiterhin den aktuellen Themen-, Kantons-, Stichwort- und Watch-Filtern.

Historische Update-Events ohne Vorher-/Nachher-Snapshot werden nicht versendet, weil Feldnamen allein keine inhaltliche Änderung belegen. Bereits stornierte Benachrichtigungen bleiben storniert; alte Benachrichtigungen werden nicht neu erzeugt. Nach dieser Richtlinie bleiben 77 der 1'329 Text-Snapshots des letzten Laufs relevant (schreibgeschützte Auswertung, keine E-Mails versendet).
