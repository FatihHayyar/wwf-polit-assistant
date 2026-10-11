# WWF Polit-Assistant

Ein MVP für WWF Schweiz zur Suche und Beobachtung parlamentarischer Entwicklungen, entwickelt im Wirtschaftsprojekt der Hochschule Luzern.

## Quick Start mit Docker

Benötigt werden **Docker Desktop** (gestartet) und **Git**. Alternativ kann das Repository als ZIP heruntergeladen werden. Python und PostgreSQL müssen nicht separat installiert werden; eine `.env` ist für die Demo nicht erforderlich.

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

Docker startet die **Python-/FastAPI-Anwendung**, **PostgreSQL 17**, die **Alembic-Datenbankmigrationen** und **Mailpit** als lokalen Mailserver. Der erste Start benötigt Internet für die Docker-Images und Python-Pakete und kann einige Minuten dauern.

Eine leere Demo-Datenbank erhält automatisch **500 Beispieldatensätze pro Bereich**: Geschäfte, Traktanden, Sitzungen, Abstimmungen, Ereignisse, Dokumente, Texte, Gruppen und Interessenbindungen. Zusätzlich werden verknüpfte Referenzdatensätze geladen, damit die Detailansichten ihren politischen Kontext zeigen. Deshalb enthalten einige Bereiche mehr als 500 Einträge. Die vorhandenen WWF-Klassifikationen sind enthalten.

Die Beispieldaten liegen bereits im Repository; ein vollständiger OpenParlData-Import ist nicht notwendig. Bereits vorhandene Demo-Daten werden beim Neustart erhalten. Die Demo verwendet eine eigene Datenbank und startet keine tägliche Synchronisierung.

### 3. Anwendung öffnen

| Dienst | Adresse |
|---|---|
| Polit-Assistant | http://localhost:8081 |
| Swagger / OpenAPI | http://localhost:8081/docs |
| Lokale E-Mails (Mailpit) | http://localhost:8025 |

Bei Startproblemen zeigt dieser Befehl die Ausgabe:

```sh
docker compose -f docker-compose.demo.yml logs -f app
```

### E-Mails und Abonnements ausprobieren

In der Anwendung auf **Registrieren** klicken und eine E-Mail-Adresse eingeben. Den Bestätigungslink in **Mailpit** öffnen; anschliessend Themen, Kantone oder Suchbegriffe abonnieren und Abonnements verwalten. Auch spätere Anmeldelinks erscheinen dort.

Alle Demo-E-Mails bleiben im lokalen Mailpit. Gmail- oder andere SMTP-Zugangsdaten werden nicht benötigt. Neue parlamentarische Benachrichtigungen entstehen erst bei einer Synchronisierung mit relevanten Änderungen; die Demo startet diese nicht automatisch.

### Container stoppen

```sh
docker compose -f docker-compose.demo.yml down
```

Die Datenbank bleibt im Docker-Volume erhalten.

> `docker compose -f docker-compose.demo.yml down -v` löscht den lokalen Demo-Datenbestand. Nur für einen bewussten Neustart mit den Beispieldaten verwenden.

## Funktionen

- Neun Bereiche in der linken Navigation mit eigener Suche und Filtern nach Thema, Unterthema, Kanton und Datum.
- Detailansichten mit verknüpften Geschäften, Sitzungen, Traktanden, Abstimmungen, Dokumenten und weiteren verfügbaren Informationen.
- Oberfläche in Deutsch, Französisch, Italienisch und Englisch. Quelltexte werden nicht automatisch übersetzt.
- Öffentlicher Zugriff auf Inhalte; ein Konto wird für E-Mail-Abonnements und das Verfolgen einzelner Einträge benötigt.
- Regelbasierte WWF-Klassifikation mit Hauptthemen und Unterthemen.
- Speicherung von Änderungen getrennt von ihrer Benachrichtigungsrelevanz: technische und reine FormatÄnderungen sollen keine E-Mails auslösen.

## Entwicklung und laufender Betrieb

Stack: **Python 3.13, FastAPI, SQLAlchemy, PostgreSQL 17, Alembic, Docker, OpenAPI und SMTP**. Das Frontend wird von derselben Anwendung ausgeliefert.

Die Demo-Konfiguration dient der lokalen Erprobung. Für den vollständigen Datenbestand, tägliche Synchronisierung, API-Start/-Status/-Abbruch und die Konfiguration eigener SMTP-Zugangsdaten siehe [Betrieb und Monitoring](docs/monitoring.md). Das bestehende `docker-compose.yml` enthält die Entwicklungsdatenbank und den Scheduler; der Quick Start verwendet bewusst `docker-compose.demo.yml`.

Geschäfte werden anhand des Update-Checkpoints geprüft. Andere Datensätze verwenden je nach verfügbaren Quellfeldern eine Änderungsabfrage oder einen vollständigen Bestandsvergleich mit gespeichertem Fortschritt. Relevante Änderungen verknüpfter Datensätze werden den zugehörigen Geschäften zugeordnet und für Abonnenten zusammengefasst.

Weitere Dokumentation:

- [WWF-Anforderungen und offene Abstimmungen](docs/wwf-requirements.md)
- [Stand und Tagesreview vom 11. Oktober 2026](docs/daily-review-2026-10-11.md)

Die genaue WWF-Taxonomie und die Integration in die interne Azure-Umgebung müssen noch mit WWF abgestimmt werden. Externe Dokumentanhänge werden nicht vollständig heruntergeladen. Der aktuelle Stand ist ein Entwicklungs-MVP.

## Daten und Lizenz

Die enthaltenen parlamentarischen Beispieldaten stammen von **OpenParlData.ch**, lizenziert unter **CC BY 4.0**. Die Demo enthält keine bestehenden Benutzerkonten, Abonnements oder Versandwarteschlangen.

Eine projektspezifische Softwarelizenz ist noch nicht festgelegt.
