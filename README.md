# WWF Polit-Assistant

[![CI](https://github.com/FatihHayyar/wwf-polit-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/FatihHayyar/wwf-polit-assistant/actions/workflows/ci.yml)

**Parlamentarische Entwicklungen finden, einordnen und verfolgen.**

Der WWF Polit-Assistant bündelt Schweizer Parlamentsdaten aus OpenParlData und macht sie nach WWF-Themen, Kantonen, Datum und Suchbegriffen zugänglich. Zusammengehörige Geschäfte, Sitzungen, Traktanden und Dokumente lassen sich im politischen Kontext betrachten. Abonnements informieren per E-Mail über relevante neue Inhalte und Änderungen.

Das Projekt entsteht für **WWF Schweiz** im **Wirtschaftsprojekt (WIPRO)** des BSc Informatik an der **Hochschule Luzern (HSLU)**. Der aktuelle Stand ist ein funktionsfähiger Entwicklungs-MVP; die fachliche Abnahme und der Betrieb in der WWF-Umgebung stehen noch aus.

[Projektziele](#projektziele) · [Funktionen](#funktionen) · [Demo starten](#quick-start-mit-docker) · [Architektur](#architektur) · [Entwicklung](#lokale-entwicklung) · [Dokumentation](#dokumentation)

## Projektziele

Das MVP soll die politische Recherche und das Monitoring für WWF vereinfachen:

- **Relevante Inhalte finden:** parlamentarische Daten nach Themen, Kantonen und individuellen Suchbegriffen durchsuchen.
- **Zusammenhänge verstehen:** zu einem Geschäft auch die zugehörigen Termine, Ereignisse, Abstimmungen und Dokumente sehen.
- **Entwicklungen verfolgen:** Themen abonnieren oder einzelne Einträge beobachten und über relevante Veränderungen informiert werden.
- **Eine anschlussfähige Grundlage schaffen:** dokumentierte API, strukturierte Daten und eine containerisierte Python-Anwendung für die spätere Integration in die WWF-Systemlandschaft.

Die Themenklassifikation erfolgt regelbasiert. KI, semantische Suche und dialogorientierte Abfragen sind mögliche Erweiterungen; sie sind im aktuellen MVP nicht umgesetzt.

## Funktionen

### Recherche in neun Bereichen

Jeder Bereich besitzt eine eigene Liste und eigene Filter. Beim Wechsel bleiben die jeweiligen Filter erhalten. Ein Klick auf einen Eintrag öffnet seine Details und die verfügbaren Verbindungen zu anderen Datensätzen.

Der Änderungsverlauf eines Geschäfts zeigt die Titel der betroffenen Inhalte und öffnet vorhandene Einträge direkt. Mehrfache Zuordnungen desselben Quelldokuments werden zusammengefasst; unterschiedliche Dokumente und inhaltliche Aktualisierungen bleiben getrennt sichtbar. Die Schliessen-Schaltfläche langer Detailansichten bleibt beim Scrollen erreichbar.

| Bereich | Inhalt und Zusammenhang |
|---|---|
| **Geschäfte** (`affairs`) | Parlamentarische Vorstösse und Geschäfte mit Status, Klassifikation und zugehörigen Vorgängen |
| **Traktanden** (`agendas`) | Tagesordnungspunkte mit Verbindung zur Sitzung und gegebenenfalls zum Geschäft |
| **Sitzungen** (`meetings`) | Parlamentarische Termine, Sitzungsinformationen und zugehörige Traktanden |
| **Abstimmungen** (`votings`) | Abstimmungsfragen und aggregierte Ergebnisse mit verfügbaren Geschäfts- und Sitzungsbezügen |
| **Ereignisse** (`events`) | Schritte im parlamentarischen Verlauf, etwa Einreichung oder Behandlung eines Geschäfts |
| **Dokumente** (`documents`) | Publizierte Unterlagen, Quellenlinks und vorhandener extrahierter Inhalt |
| **Texte** (`texts`) | Parlamentarische Textinhalte mit Bezug zum jeweiligen Geschäft |
| **Gruppen** (`groups`) | Parlamentarische Gremien und Gruppen sowie verfügbare zugehörige Sitzungen |
| **Interessenbindungen** (`interests`) | Deklarierte Interessen mit Informationen zur zugehörigen Person |

Die Suche kombiniert **Suchbegriff, Hauptthema, Unterthema, Kanton und Datumsbereich**. Ergebnisse werden serverseitig paginiert. Die Oberfläche unterstützt **Deutsch, Französisch, Italienisch und Englisch**; parlamentarische Originaltexte werden nicht automatisch übersetzt.

Themenetiketten zeigen **Hauptthema / Unterthema**, beispielsweise **Klima & Energie / Sonstiges**. Dieses lokale Sonstiges bezeichnet einen passenden Hauptbereich ohne spezifisches Unterthema; das globale Sonstiges bezeichnet Inhalte ohne erkannte WWF-Zuordnung.

In der Bereichs- und bereichsübergreifenden Suche werden Geschäfte mit gleichem normalisiertem Titel, gleicher Körperschaft und gleichem Kalendertag als eine Ergebniskarte zusammengefasst. Beispielsweise bleiben Regierungsbotschaft und Gesetzesentwurf über getrennte Schaltflächen erreichbar. Die Originaldatensätze, IDs und Detailansichten bleiben erhalten; Trefferzahl und Pagination zählen die Gruppen. Das ist eine Darstellungsregel und keine nachgewiesene fachliche Identität der Quellen. Andere Tage oder Körperschaften bleiben getrennt.

### Konfigurierbare WWF-Themen

Die vier Hauptbereiche **Klima & Energie**, **Biodiversität & Landschaft**, **Nachhaltige Wirtschaft & Konsum** und **Umwelt & Politik** besitzen jeweils eine Sonstiges-Unterkategorie. Namen, Hierarchie, Synonyme, Regeln und Schwellenwerte werden in [taxonomy.json](app/classification/taxonomy.json) gepflegt. Die Oberfläche übernimmt die konfigurierten Namen aus der Kategorien-API.

Die aktuelle Version `rule-based-v7` erkennt eindeutige Titelbegriffe auch in Zusammensetzungen und mit Buchstaben-Endungen. Generische Begriffe benötigen einen ausdrücklichen Umweltbezug. Mehrere Themen können gleichzeitig passen; spezifische Unterthemen verdrängen den lokalen Fallback ihres Hauptthemas. Übersetzungen und Synonyme zählen als ein Konzept. Details und Befehle: [Klassifikationskonzept](docs/04-technical-concepts/classification-concept.md) und [Konfiguration](docs/configuration.md#regelbasierte-klassifikation).

### Abonnements und E-Mail-Monitoring

Die Recherche ist ohne Konto zugänglich. Für Benachrichtigungen registrieren sich Nutzer per E-Mail und melden sich über einen zeitlich begrenzten Link an. Optional steht eine konfigurierte Google-Anmeldung zur Verfügung. In der Abonnementverwaltung können bis zu zehn Benachrichtigungsadressen ausgewählt werden; zusätzliche Adressen benötigen eine Bestätigung.

Abonnements können WWF-Themen, Kantone, Suchbegriffe und Datenbereiche kombinieren. Zusätzlich lassen sich einzelne Einträge verfolgen. Hauptthemen schliessen ihre Unterthemen ein. Mehrere Werte innerhalb einer Filtergruppe gelten als Alternativen; Einschränkungen verschiedener Gruppen müssen gemeinsam passen.

Die Anwendung speichert Quelldatenänderungen getrennt von ihrer Benachrichtigungsrelevanz. Technische Metadaten, reine Formatänderungen und bestimmte geringfügige Textkorrekturen sollen keine E-Mail auslösen. Relevante Updates werden pro Nutzer und Geschäft beziehungsweise eigenständigem Eintrag zusammengefasst.

Benachrichtigungen besitzen eine HTML-Ansicht mit Inhaltskarten und eine separate Klartextfassung. Der Betreff benennt beispielsweise ein neues Dokument; Dokumentlinks, Geschäftsverlauf und Abonnementverwaltung sind eindeutig beschriftet. Bereits zugestellte E-Mails werden nicht verändert oder automatisch erneut versandt. Eine Aktualisierung ohne passende neue Entwicklung erzeugt keine neue Nachricht.

## Projektstand – 21. Oktober 2026

Datenimport, neun Synchronisationsmodule, konfigurierbare regelbasierte Klassifikation, Recherche, verknüpfte Detailansichten, passwortlose Anmeldung, Abonnementverwaltung und E-Mail-Benachrichtigungen sind umgesetzt. Präsentation, fachliche Bewertung durch WWF und formale Abnahme stehen aus. Azure-Bereitstellung sowie KI- und Dialogfunktionen gehören nicht zum Lieferumfang dieses MVP.

| Bereich | Stand und Nachweis |
|---|---|
| Datenbestand | 2'951'254 Inhaltsdatensätze in neun Bereichen. Vollständiger Lauf am 12. Oktober: 9/9 Bereiche ohne Fehler; Quellstichprobe mit 4'500 Datensätzen ohne Abweichung ([Prüfung](docs/05-testing/review-2026-10-12.md)) |
| Klassifikation | `rule-based-v7` auf allen Datensätzen. Entwicklungsset 50/50 (Regeln daran verbessert). **Blindes Prüfset mit 300 Zufallsgeschäften: Precision 1.0, Recall 0.325** – sehr präzise, aber die Mehrheit relevanter Geschäfte wird übersehen ([Auswertung](docs/05-testing/evidence/holdout-evaluation.md)) |
| Sicherheit | Gleiche Antwort für bekannte und unbekannte Adressen, Ratenbegrenzung für E-Mail- und Token-Endpunkte, Bestätigungsseite statt Token-Verbrauch beim Öffnen eines Links, Widerruf aller Tokens beim Abmelden, strikte Sicherheits-Header ([Details](docs/monitoring.md#anmeldung-und-schutz-vor-missbrauch)) |
| Tests | 124 isolierte Backend-, API- und Klassifikationstests, Frontend-Prüfungen und CI (Lint, Migrationen auf PostgreSQL 17, Docker-Build). Edge-Durchlauf der Demo inkl. Registrierung, Testbenachrichtigung und Abmeldung am 21. Oktober |
| Demo | Ein-Kommando-Start mit Beispieldaten und Mailpit; Benachrichtigungen lassen sich mit einem Testgeschäft direkt ausprobieren |

Automatisierte Tests und Stichproben ersetzen keine WWF-Abnahme. Frühere Nachweise: [Prüfung vom 13. Oktober](docs/05-testing/review-2026-10-13.md), [Testergebnisse](docs/05-testing/test-results.md), [Aufgabenstand](docs/01-project-management/current-status.md).

## Quick Start mit Docker

Für die lokale Demo werden **Docker Desktop** (gestartet) und **Git** benötigt. Alternativ kann das Repository als ZIP heruntergeladen werden. Eine separate Installation von Python oder PostgreSQL und eine eigene `.env` sind nicht erforderlich.

### 1. Repository herunterladen

```sh
git clone https://github.com/FatihHayyar/wwf-polit-assistant.git
cd wwf-polit-assistant
```

Bei einem ZIP-Download das Archiv entpacken und ein Terminal im Projektordner öffnen.

### 2. Anwendung starten

```sh
docker compose -f docker-compose.demo.yml up --build -d
```

Docker startet **FastAPI**, **PostgreSQL 17**, die **Alembic-Migrationen** und **Mailpit**. Der erste Start benötigt Internet für Images und Python-Pakete und kann einige Minuten dauern.

Eine leere Demo-Datenbank erhält automatisch **500 Beispieldatensätze pro Bereich** mit vorhandenen WWF-Klassifikationen. Zusätzliche verknüpfte Referenzdaten erhalten den Kontext der Detailansichten; deshalb enthalten einige Bereiche mehr als 500 Einträge. Die Stichprobe liegt bereits im Repository, ein vollständiger OpenParlData-Import ist nicht erforderlich.

Die Demo verwendet eine eigene Datenbank, erhält vorhandene Daten beim Neustart und startet keine tägliche Synchronisierung.

### 3. Anwendung öffnen

| Dienst | Adresse |
|---|---|
| Polit-Assistant | [localhost:8081](http://localhost:8081) |
| Swagger / OpenAPI | [localhost:8081/docs](http://localhost:8081/docs) |
| Lokale E-Mails (Mailpit) | [localhost:8025](http://localhost:8025) |

### Einen ersten Ablauf ausprobieren

1. Einen Bereich auswählen und nach einem Begriff oder WWF-Thema suchen; einen Treffer öffnen und seine verknüpften Inhalte ansehen.
2. **Registrieren** wählen und eine E-Mail-Adresse eingeben (beliebig, z. B. `test@example.org`).
3. In **Mailpit** ([localhost:8025](http://localhost:8025)) die Bestätigungs-E-Mail öffnen, dem Link folgen und **Registrierung bestätigen** klicken. Die Abonnementverwaltung öffnet sich.
4. Ein Thema wählen, z. B. **Klima & Energie**, optional auch Kantone oder Stichwörter.
5. Unter **Benachrichtigung testen (Demo)** ein Thema wählen und **Testgeschäft erstellen und benachrichtigen** klicken. Die Anwendung speichert die Auswahl, legt ein fiktives neues Geschäft an und schickt es durch die echte Klassifikation, die Relevanzprüfung und den Versand.
6. In Mailpit erscheint die Benachrichtigung zum neuen Geschäft. Passt das Testgeschäft nicht zu den gespeicherten Filtern, erklärt die Oberfläche den Grund, statt eine E-Mail zu senden.

Alle Demo-E-Mails bleiben lokal; externe SMTP-Zugangsdaten werden nicht benötigt. Die Testfunktion existiert nur mit `DEMO_MODE=true` und ist auch per Kommandozeile verfügbar:

```sh
docker compose -f docker-compose.demo.yml exec app python -m scripts.demo.send_test_notification --email test@example.org --topic renewable_electricity
```

### Logs und Beenden

```sh
docker compose -f docker-compose.demo.yml logs -f app
```

```sh
docker compose -f docker-compose.demo.yml down
```

Die PostgreSQL-Daten bleiben im Docker-Volume erhalten.

> `docker compose -f docker-compose.demo.yml down -v` löscht den lokalen Demo-Datenbestand. Nur verwenden, wenn die Demo bewusst zurückgesetzt werden soll.

## Architektur

Import und laufende Synchronisierung führen die Quelldaten in PostgreSQL zusammen. Die Klassifikation unterstützt Recherche und Abonnementabgleich. Eine separate Relevanzprüfung entscheidet, welche gespeicherten Änderungen Benachrichtigungen erzeugen.

```mermaid
flowchart TD
    source[OpenParlData] --> sync[Erstimport und Synchronisierung]
    sync --> db[(PostgreSQL)]
    db --> classification[Regelbasierte WWF-Klassifikation]
    classification --> api[FastAPI: Suche und Details]
    db --> api
    api --> ui[Weboberfläche]
    sync --> policy[Änderungserkennung und Relevanzprüfung]
    classification --> matching[Abonnementabgleich]
    policy --> matching
    matching --> queue[Benachrichtigungswarteschlange]
    queue --> email[SMTP / lokale Demo: Mailpit]
```

### Technologie-Stack

| Baustein | Umsetzung |
|---|---|
| Backend | Python 3.13, FastAPI, Pydantic |
| Datenzugriff | SQLAlchemy, Psycopg |
| Datenbank | PostgreSQL 17 |
| Migrationen | Alembic |
| Frontend | HTML, CSS und JavaScript-Module ohne Build-Schritt, von FastAPI ausgeliefert |
| API-Dokumentation | OpenAPI / Swagger |
| Ausführung | Docker und Docker Compose |
| Regelmässige Jobs | Python-Scheduler, 03:00 Europe/Zurich |
| Qualitätssicherung | unittest, FastAPI-TestClient, Node-Prüfungen, ruff, GitHub Actions |
| E-Mail | SMTP; Mailpit im Docker-Demo-Setup |

### Datenmodell und Klassifikation

Die normalisierten Daten bilden direkte und indirekte Beziehungen zwischen Geschäften, Traktanden, Sitzungen und weiteren Inhalten ab. Kantone werden unter anderem über das parlamentarische Organ aufgelöst: `affairs.body_id → bodies.id → bodies.canton_key`.

Die konfigurierbare Klassifikation verwendet hierarchische Kategorien, mehrsprachige Regeln, Gewichte, Scores, Konfidenzwerte und Klassifikationsevidenz. Verknüpfte Inhalte können die Klassifikation des zugehörigen Geschäfts ergänzen; andere Datensätze besitzen zusätzlich eigene Klassifikationen.

Der bisherige Themenbaum umfasst Klima & Energie, Biodiversität & Landschaft, nachhaltige Wirtschaft & Konsum, Umwelt & Politik sowie eine Auffangkategorie. Die endgültige Taxonomie und der initiale WWF-Fokus auf Energie & Klima müssen mit den WWF-Fachexperten abgestimmt werden.

### Datenbestand

Der erneute Quellenvergleich vom **12. Oktober 2026** ergab folgende lokale Bestände. Die API-Gesamtzahlen stimmten je Bereich mit den lokalen Zeilenzahlen überein. Gleiche Anzahlen allein beweisen jedoch keine identischen Inhalte; dazu wurde zusätzlich die oben beschriebene Stichprobe verglichen.

| Bereich | Lokale Zeilen |
|---|---:|
| Geschäfte | 326.124 |
| Traktanden | 423.161 |
| Sitzungen | 33.677 |
| Abstimmungen | 77.144 |
| Ereignisse | 916.688 |
| Dokumente | 909.151 |
| Texte | 226.062 |
| Gruppen | 8.886 |
| Interessenbindungen | 30.361 |

Die Dokumenttabelle enthält **902.993 unterschiedliche Quell-IDs**: mehrere Zeilen können unterschiedliche Zuordnungen desselben Quelldokuments repräsentieren. Referenzdaten wie Bodies, Persons und Memberships sowie die separate Demo-Datenbank sind in dieser Tabelle nicht mitgezählt.

Der vollständige Entwicklungsbestand und die kleine Docker-Stichprobe sind getrennte Datenbestände. Die folgenden Zahlen dokumentieren den ursprünglichen **Bootstrap vom 6. Oktober 2026**, nicht die aktuellen Datenbankzahlen.

<details>
<summary>Ursprünglichen Importbestand anzeigen</summary>

| Dataset | Datensätze |
|---|---:|
| Bodies | 2.411 |
| Persons | 26.864 |
| Memberships | 121.456 |
| Groups | 8.885 |
| Interests | 30.343 |
| Affairs | 325.691 |
| Meetings | 33.670 |
| Agendas | 422.971 |
| Events | 915.238 |
| Votings | 77.061 |
| Documents | 907.736 |
| Texts | 225.739 |
| **Gesamt** | **3.098.065** |

Der Erstimport umfasste ungefähr 126 komprimierte Dateien und 5,91 GB. Einzelne Stimmen parlamentarischer Mitglieder sind nicht Teil des lokalen Spiegels; aggregierte Abstimmungsergebnisse sind im Dataset `votings` verfügbar.

Alle 325.691 ursprünglichen Geschäfte wurden klassifiziert. Der damalige Stand umfasste 325.824 Klassifikationszeilen, 7.111 Evidenzzeilen und 320.121 Auffangklassifikationen. Diese historischen Zahlen sind keine Messung der fachlichen Klassifikationsqualität.

</details>

## Synchronisierung und Benachrichtigungen

Regelanpassungen und historische Neuberechnung sind vom Sync getrennt: `python -m scripts.reclassify_rules` ist eine schreibgeschützte Vorschau; `--apply` verarbeitet den Bestand nach bestandenem Entwicklungsset. `--dataset`, `--limit` und `--workers` begrenzen Umfang und Parallelität. Nach Taxonomieänderungen `--force` verwenden. Die Qualitätsschranke benötigt Git-Historie mit dem festgelegten Baseline-Commit; ein ZIP ohne `.git` reicht dafür nicht. Weitere Voraussetzungen und die älteren Einzeljobs stehen in der [Konfiguration](docs/configuration.md#regelbasierte-klassifikation).

Alle neun Bereiche besitzen eigene Sync-Module:

| Dataset | Modul | Abgleich |
|---|---|---|
| Affairs | `scripts.sync.incremental_sync` | Update-Checkpoint |
| Agendas | `scripts.sync.agendas_sync` | Bestandsvergleich |
| Meetings | `scripts.sync.meetings_sync` | Update-Checkpoint |
| Votings | `scripts.sync.votings_sync` | Bestandsvergleich |
| Events | `scripts.sync.events_sync` | Bestandsvergleich |
| Documents | `scripts.sync.docs_sync` | Update-Checkpoint |
| Texts | `scripts.sync.texts_sync` | Bestandsvergleich |
| Groups | `scripts.sync.groups_sync` | Bestandsvergleich |
| Interests | `scripts.sync.interests_sync` | Bestandsvergleich |

Der Bestandsvergleich verwendet ein stabiles Inventar und den aktuellen API-Inhalt, wenn geeignete Änderungscursor fehlen oder nicht zuverlässig sind. Dabei können viele unveränderte Datensätze gelesen werden. `CHANGED` bedeutet eine gespeicherte Inhaltsänderung und führt nicht automatisch zu einer E-Mail. Fingerprints und Normalisierung reduzieren technische Unterschiede; die Benachrichtigungsregeln bewerten zusätzlich die fachliche Bedeutung.

Verarbeitete Batches werden gespeichert. Fortschritt und abgeschlossene Dataset-Schritte ermöglichen die Wiederaufnahme unterbrochener Jobs. Ein PostgreSQL-Advisory-Lock schützt den gemeinsamen Runner vor paralleler Ausführung.

```powershell
python -m scripts.sync.run_all
```

Der separat gestartete Scheduler führt den Job täglich um **03:00 Europe/Zurich** aus. Die Entwicklungsphase unterstützt ausserdem einen geschützten API-Start im Hintergrund, Statusabfragen, Logs und Abbruch. Laufberichte und Logs werden lokal unter `logs/` gespeichert. Der Compose-Scheduler bindet dieses Verzeichnis als `/app/logs` ein, damit Fortschritt und Berichte beim Ersetzen des Containers erhalten bleiben und von der lokalen API gelesen werden können.

Relevante Änderungen an Traktanden, Sitzungen, Abstimmungen, Ereignissen, Dokumenten und Texten werden den verbundenen Geschäften zugeordnet. Der Versand erfolgt nach erfolgreichem Abschluss der Dataset-Schritte. Vor dem Senden werden Konto und Abonnement erneut geprüft. Fehlgeschlagene Sendungen bleiben zur erneuten Verarbeitung ausstehend; nicht mehr passende Benachrichtigungen können verworfen werden.

Der Standardversand besitzt **keine Gesamtgrenze von 100 Nachrichten**. Interne Batches dienen der Verarbeitung. Die Zusammenfassung erfolgt pro Nutzer und Geschäft oder eigenständigem Eintrag, nicht als eine einzige tägliche E-Mail pro Nutzer. SMTP-Limits und Versandvolumen bleiben betriebliche Prüfpunkte.

Checkpoint-Verhalten, Abbruch, Wiederaufnahme und die Regeln je Dataset sind im [Monitoring-Leitfaden](docs/monitoring.md) beschrieben.

### Warum bleibt das Checkpoint-Datum unverändert?

Ein Checkpoint ist eine **Position in der Datenquelle**, kein Zeitstempel des zuletzt gestarteten Jobs:

| Feld | Bedeutung |
|---|---|
| `last_updated_at` + `last_id` | Zuletzt erfolgreich verarbeitete Quellposition bei Geschäften, Sitzungen und Dokumenten |
| `last_id` bei den anderen sechs Bereichen | ID-Fortschritt; dort gibt es keinen zuverlässig verwendbaren Zeitcursor, deshalb bleibt `last_updated_at` leer |
| `last_run_at` | Zeitpunkt des letzten gespeicherten Dataset-Abgleichs, auch ohne neue Inhalte; Erfolg zusätzlich über Status und Laufbericht prüfen |

Beispiel aus dem geprüften Bestand: Geschäfte besitzen die Quellposition **11.10.2026, 05:23:12 / ID 341425**, obwohl der letzte Abgleich am **12.10.2026** stattfand. Ohne eine neuere Quellposition bleibt dieser Checkpoint korrekt bestehen. Auch ein Metadaten-Update kann den Quellcursor verändern, ohne eine relevante Inhaltsänderung oder Nachricht zu erzeugen.

Den Quellcursor auf die aktuelle Uhrzeit zu setzen wäre falsch: dadurch könnten später bereitgestellte Inhalte mit älteren Quellzeitstempeln übersprungen werden. Letzte Kontrollzeit, Quellposition und `NEW`/`CHANGED` sind daher getrennt zu lesen. Der aktuelle Befund lautet **keine weiteren Unterschiede in den abgeschlossenen Läufen und der Quellenstichprobe**; er beweist nicht, dass OpenParlData während des gesamten Tages weltweit keine Änderungen hatte.

## REST API

Die interaktive Dokumentation wird aus der Anwendung erzeugt: **`/docs`**; die OpenAPI-Spezifikation liegt unter **`/openapi.json`**.

| Funktion | Endpunkte |
|---|---|
| Bereichssuche | `GET /api/v1/entities/{dataset}` |
| Details und Beziehungen | `GET /api/v1/entities/{dataset}/{record_id}` |
| Geschäftssuche und Details | `GET /api/v1/affairs`, `GET /api/v1/affairs/{affair_id}` |
| Filterwerte | `GET /api/v1/categories`, `GET /api/v1/cantons`, `GET /api/v1/affair-types` |
| Registrierung und Verifikation | `POST /api/v1/auth/register`; Link: `GET /api/v1/auth/verify-email` (Bestätigungsseite), `POST` auf demselben Pfad (Bestätigung) |
| Anmeldung per E-Mail | `POST /api/v1/auth/login`; Link: `GET`/`POST /api/v1/auth/verify-login` |
| Optionale Google-Anmeldung | `GET /api/v1/auth/providers`, `GET /api/v1/auth/google`, `GET /api/v1/auth/google/callback` |
| Konto, Logout und Löschung | `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`, `DELETE /api/v1/auth/me` |
| Abonnements lesen und ersetzen | `GET /api/v1/subscriptions`, `PUT /api/v1/subscriptions` |
| Einzelne Inhalte verfolgen | `PUT /api/v1/subscriptions/watches/{dataset}/{record_id}`, `DELETE` auf demselben Pfad |
| Benachrichtigungsadressen | `GET /api/v1/subscriptions/recipients`, `PUT` auf demselben Pfad; Bestätigung über `GET`/`POST /recipients/verify` |
| Demo-Testbenachrichtigung (nur `DEMO_MODE`) | `GET /api/v1/demo/status`, `GET /api/v1/demo/topics`, `POST /api/v1/demo/notifications` |
| Sync starten | `POST /api/v1/sync/run` |
| Checkpoints und letzter Lauf | `GET /api/v1/sync/status`, `GET /api/v1/sync/latest` |
| Laufstatus und Logs | `GET /api/v1/sync/runs/{run_id}`, `GET /api/v1/sync/runs/{run_id}/log` |
| Lauf abbrechen | `POST /api/v1/sync/runs/{run_id}/cancel` |
| Unfertigen Lauf fortsetzen | `POST /api/v1/sync/runs/{run_id}/resume` |
| Verfügbarkeit | `GET /health` |

Beispiel einer Bereichssuche:

```http
GET /api/v1/entities/agendas?q=Photovoltaik&canton=ZH&page=1
```

Themen, Unterthemen und Datumsfilter lassen sich ergänzen. Die Standardseitengrösse beträgt zehn Treffer. Textsuche verwendet je nach Dataset PostgreSQL-Trigramm- oder Volltextindizes; externe Dokumentanhänge werden dadurch nicht automatisch heruntergeladen.

Beispiel eines Themen-/Kanton-Abonnements:

```json
{
  "category_ids": [1],
  "canton_keys": ["BE"]
}
```

Kategorie-IDs werden über die Kategorien-API ermittelt. Ein Hauptthema umfasst seine Unterkategorien. Leere Themen- oder Kantonsgruppen schränken die jeweilige Dimension nicht ein; reine Filterabonnements ohne Themen, Kantone und Keywords pausieren. Einzelne Record-Watches werden separat verwaltet.

| Themen | Kantone | Bedeutung |
|---|---|---|
| Klima & Energie | BE | Passende Entwicklungen im Kanton Bern |
| Klima & Energie | Alle | Passende Entwicklungen in allen Kantonen |
| Alle | ZH | Entwicklungen aller Themen im Kanton Zürich |

Die Anmeldung verwendet JWT und ein HttpOnly-Sitzungscookie für die Oberfläche; API-Clients können Bearer-Tokens verwenden. Abmelden widerruft alle bisher ausgestellten Tokens des Kontos. Registrierung und Anmeldung antworten für bekannte und unbekannte Adressen identisch; E-Mail- und Token-Endpunkte sind ratenbegrenzt (HTTP 429 mit `Retry-After`). Verwaltungsfunktionen erfordern Anmeldung, Sync-Operationen den separat konfigurierten Schlüssel im Header `X-Sync-API-Key`. Kontolöschung ist unterstützt.

## Lokale Entwicklung

Für Änderungen am Code werden **Python 3.13+** und **PostgreSQL** benötigt. Die Demo oben ist der einfachere Weg zum Ausprobieren.

### Umgebung vorbereiten

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
```

In `.env` Datenbank, JWT, SMTP und `SYNC_API_KEY` konfigurieren. Zugangsdaten bleiben lokal. `docker-compose.yml` stellt PostgreSQL auf Port **5433** (nur von diesem Rechner erreichbar), einen Migrationsdienst, die API auf Port **8000** und den Scheduler bereit; `docker compose up -d --build` startet alles.

Für die optionale Google-Anmeldung zusätzlich `GOOGLE_CLIENT_ID` und `GOOGLE_CLIENT_SECRET` setzen. Der OAuth-Webclient benötigt `${VERIFICATION_BASE_URL}/api/v1/auth/google/callback` als erlaubte Weiterleitungs-URI, lokal `http://localhost:8000/api/v1/auth/google/callback`. Nach Neustart erscheint die Google-Schaltfläche; ohne Konfiguration bleibt die E-Mail-Anmeldung verfügbar. Weitere Einstellungen: [Konfiguration](docs/configuration.md).

```powershell
docker compose up -d postgres
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Oberfläche: **http://localhost:8000** · API-Dokumentation: **http://localhost:8000/docs**.

Eine leere Entwicklungsdatenbank benötigt anschliessend den Datenimport und die Klassifikationsvorbereitung. Migrationen allein laden keine parlamentarischen Inhalte. Die Demo-Datenbank und ihr Startskript gehören zur separaten Demo-Konfiguration.

### Erstimport und Klassifikation

Der Bootstrap lädt Exporte und importiert sie in das normalisierte Schema. Er ist für eine frische Zieldatenbank vorgesehen: vorhandene Tabellen können dabei zurückgesetzt werden. Bestehende Daten vorher sichern.

```powershell
python scripts/bootstrap/download_openparldata.py --dry-run
python scripts/bootstrap/download_openparldata.py --workers 6
python scripts/bootstrap/import_normalized.py all
python -m scripts.seed_classification
python -m scripts.rule_quality
python -m scripts.reclassify_rules --apply
python -m scripts.rule_backfill_status
```

Dies sind Schritte der Importpipeline, keine vollständige Ein-Kommando-Installation des normalisierten Datenbestands. Klassifikationsvorbereitung und historische Entity-Klassifikation sind im [Monitoring-Leitfaden](docs/monitoring.md) dokumentiert. Vollständige Raw-Downloads und Datenbank-Backups werden nicht ins Repository aufgenommen; die kuratierte öffentliche Demo-Stichprobe liegt unter [data/demo](data/demo/README.md).

### Tests

Die Backend-Suite verwendet isolierte Fixtures/Mocks. In einem eigenen Testterminal ausführen:

```powershell
$env:DATABASE_URL = 'sqlite://'
$env:JWT_SECRET_KEY = 'isolated-test-key-only-not-for-production'
python -B -m unittest discover -s tests -p 'test_*.py'
node tests/test_frontend.cjs
python -m scripts.evaluate_holdout
```

Das Testterminal danach schliessen oder die beiden Variablen entfernen, bevor die echte Anwendung darin gestartet wird. Voraussetzungen und Browserabläufe: [Testplan](docs/05-testing/test-plan.md).

Die Tests decken unter anderem Sync-Fortschritt, Beziehungen, Normalisierung, Klassifikation, Benachrichtigungsregeln, Anmeldung, Ratenbegrenzung, Sicherheits-Header und den Demo-Ablauf über den echten HTTP-Stack ab. `scripts.evaluate_holdout` misst die Klassifikation auf dem blinden Prüfset, ohne PostgreSQL zu benötigen. GitHub Actions führt bei jedem Push zusätzlich ruff, die Migrationen auf PostgreSQL 17 und den Docker-Build aus. Live-Sync und Organisations-SMTP wurden separat geprüft; die fachliche WWF-Abnahme steht aus.

## Grenzen und nächste Schritte

Die behobenen Sync-, Windows-Checkpoint-, SMTP- und Oberflächenprobleme werden nicht mehr als offene Aufgaben geführt. Weitere reguläre Läufe zu beobachten ist laufende Betriebskontrolle, kein Ersatz für die bereits durchgeführten erfolgreichen Prüfungen.

### Vor Präsentation und fachlichem Abschluss

| Aufgabe | Noch ausstehender Schritt |
|---|---|
| Fachliche Qualität | WWF-Taxonomie und Fokus Energie & Klima bestätigen; das Prüfset von WWF-Fachpersonen nachannotieren lassen. Der gemessene Recall von 0.325 zeigt, dass die Regeln Synonyme, Fachbegriffe (z. B. Jagd, Wolf, Kompost, Waldentwicklung) und französische/italienische Titel ergänzen müssen; danach mit einem neuen Prüfset messen |
| Demonstration | Präsentation und nachvollziehbare Beispiele für Suche, Beziehungen, Abonnements und relevante Änderungen vorbereiten |
| WWF-Feedback und Abnahme | Gemeinsamen Anwendungsfalldurchlauf durchführen; Rückmeldungen und tatsächliche Akzeptanz dokumentieren |
| Projektabschluss | Vorbereitete Ergebnis-/Übergabeunterlagen prüfen, formalen Kursbericht abschliessen und tatsächliche Übergabe durchführen |
| Softwarelizenz | Gewünschte Lizenz für den Anwendungscode festlegen |

### Bei einer späteren Übernahme durch WWF

Container, Konfiguration, Migrationen, Sicherung, API und Betriebsrollen sind dokumentiert. WWF muss für seine Umgebung insbesondere erreichbare HTTPS-Links, Organisations-SMTP, Secrets, Monitoring und Wiederherstellung festlegen und prüfen. Lokaler SMTP-Versand wurde erfolgreich nachgewiesen; ein WWF-Produktionsprovider ist damit noch nicht geprüft.

Der MVP liefert mit Python, PostgreSQL, Docker, OpenAPI und Umgebungsvariablen eine Grundlage für die spätere Azure-Integration durch WWF. Ein eigenes Azure-Deployment gehört nicht zum aktuellen Lieferumfang; Kompatibilität mit der konkreten WWF-Umgebung wird nicht als bereits getestet ausgegeben. Lokale JSON-Laufberichte ersetzen kein zentrales Produktionsmonitoring. Harmonisierten Geschäftszuständen und Originalsprachen sind durch die Quellabdeckung Grenzen gesetzt.

### Optionale Weiterentwicklung

KI-gestützte Klassifikation, semantische Suche, Zusammenfassungen und dialogorientierte Abfragen bleiben Erweiterungen. Eine KI-Klassifikation lässt sich mit demselben Prüfset direkt gegen die Regeln vergleichen. Das aktuelle MVP bietet strukturierte Suche und Filter, keinen KI-Chat. Ebenso optional sind ein täglicher Sammeldigest, weitergehende SMTP-Optimierungen und Organisations-SSO.

Die beiden grossen Indizes für die experimentelle bereichsübergreifende Suche können mit `python -m scripts.build_search_indexes` in einem Wartungsfenster aufgebaut werden. Die öffentliche Bereichsrecherche benötigt sie nicht. Ein GitHub-Projects-Board ist noch nicht erstellt; dafür fehlt die erforderliche Projects-Berechtigung. Bestehende Issues und Milestones können bereits genutzt werden.

## Dokumentation

Die Dokumentation ist nach Projektmanagement, Anforderungen, Architektur, technischen Konzepten, Tests, Übergabe und wissenschaftlicher Einordnung gegliedert. Einstieg: [Dokumentationsindex](docs/README.md). [GitHub-Tracking](docs/01-project-management/github-tracking.md) verknüpft Aufgaben und Milestones.

| Dokument | Inhalt |
|---|---|
| [Dokumentationsindex](docs/README.md) | Einstieg in alle Projektunterlagen |
| [Aktueller Aufgabenstand](docs/01-project-management/current-status.md) | Erledigte Prüfungen, verbleibende Abnahme und Abgleich der gestrigen Aufgaben |
| [Installation](docs/getting-started.md) | Demo, Entwicklungsumgebung und vollständiger Erstimport |
| [Benutzerhandbuch](docs/06-handover/user-guide.md) | Recherche, Anmeldung und Abonnements |
| [Konfiguration](docs/configuration.md) | Umgebungsvariablen, Container, Google-Anmeldung und editierbare Klassifikation |
| [Architektur](docs/03-architecture/system-architecture.md) | Komponenten, Datenmodell und Ausführungsgrenzen |
| [API](docs/api.md) | Öffentliche Recherche und geschützte Verwaltungsrouten |
| [Tests](docs/05-testing/test-plan.md) | Automatisierte Prüfungen und manuelle Abnahme |
| [Klassifikation auf dem Prüfset](docs/05-testing/evidence/holdout-evaluation.md) | Blind annotierte Stichprobe mit Precision, Recall und Fehlerliste |
| [Betrieb](docs/06-handover/deployment-guide.md) | Prozessrollen, Migrationen und Sicherung |
| [Fehlerbehebung](docs/troubleshooting.md) | Sync-, Anmelde- und Installationsprobleme |
| [Mitwirken](CONTRIBUTING.md) | Beiträge und Pull Requests |
| [Sicherheit](SECURITY.md), [Support](SUPPORT.md) | Meldewege und Hilfe |
| [Änderungsprotokoll](CHANGELOG.md), [Lizenzen](docs/licensing.md) | Arbeitsstand und offene Lizenzentscheidung |
| [Betrieb und Monitoring](docs/monitoring.md) | Lokaler Start, Klassifikationsvorbereitung, Abonnements, Sync-Steuerung und Benachrichtigungsregeln |
| [WWF-Anforderungen](docs/wwf-requirements.md) | Zuordnung der Auftraggeberanforderungen und offene fachliche Entscheidungen |
| [Review vom 11. Oktober 2026](docs/daily-review-2026-10-11.md) | Historischer Befund mit aktualisierter Erledigungsübersicht; keine aktuelle offene Fehlerliste |
| [Demo-Stichprobe](data/demo/README.md) | Herkunft, Umfang und Erneuerung der Beispieldaten |

<details>
<summary>Frühere Integrationsnachweise vom 8. Oktober 2026</summary>

Ein damaliger manueller Lauf schloss sieben Sync-Module in 24,24 Sekunden mit null neuen Datensätzen, Änderungen und Fehlern ab. Dieser Lauf dokumentiert den früheren Implementierungsstand und beweist keine vollständige oder dauerhaft zuverlässige Aktualisierung.

Ein kontrollierter Benachrichtigungstest verwendete das Berner Geschäft **#18792**, «Komplettierung Solaranlage Schiessanlage Weier», klassifiziert unter **Erneuerbarer Strom → Klima & Energie**. Das passende Abonnement erzeugte eine Benachrichtigung; eine reale SMTP-E-Mail wurde zugestellt. Temporäre Testereignisse und Benachrichtigungen wurden anschliessend entfernt.

</details>

## Datenquelle und Lizenz

Parlamentarische Daten stammen von **[OpenParlData.ch](https://openparldata.ch/)** und stehen unter **CC BY 4.0**. Die Demo enthält keine bestehenden Benutzerkonten, Abonnements, E-Mail-Tokens oder Versandwarteschlangen.

Eine projektspezifische **Softwarelizenz** wurde noch nicht festgelegt; der [Lizenzleitfaden](docs/licensing.md) dokumentiert den Status. Die Lizenz der Quelldaten und die Lizenz des Anwendungscodes sind getrennt zu betrachten.
