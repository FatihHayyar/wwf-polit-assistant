# Azure-Integration

**Lieferumfang:** Die Anwendung ist für den Betrieb in Azure vorbereitet (Container ohne Root-Rechte, Konfiguration ausschliesslich über Umgebungsvariablen, PostgreSQL, Healthcheck, OpenAPI). Die Bereitstellung in der WWF-Umgebung übernimmt WWF; sie wurde im Projekt nicht in Azure getestet. Dieses Dokument beschreibt eine konkrete Zielarchitektur und die Punkte, die WWF dabei entscheiden und prüfen muss.

## Zielarchitektur

```mermaid
flowchart LR
    user[Browser] -->|HTTPS| ingress[Container Apps Ingress]
    ingress --> api[Container App: api]
    job[Container Apps Job: sync, täglich] --> db[(Azure Database for PostgreSQL Flexible Server 17)]
    migrate[Container Apps Job: migrate, manuell] --> db
    api --> db
    api --- files[(Azure Files: /app/logs)]
    job --- files
    job -->|HTTPS| opd[OpenParlData]
    job -->|SMTP 587| mail[Organisations-SMTP oder Azure Communication Services]
    api -->|SMTP 587| mail
    kv[Key Vault] -. Secrets .-> api
    kv -. Secrets .-> job
    api --> logs[Log Analytics]
    job --> logs
```

| Baustein | Azure-Dienst | Hinweise |
|---|---|---|
| Image | Azure Container Registry | `docker build` aus dem Repository; ein Image für alle Rollen |
| API | Container App `api` | Befehl `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers`; Ingress extern, Port 8000; Health-Probe auf `/health` |
| Tägliche Synchronisierung | Container Apps Job `sync` (Zeitplan) | Befehl `python -u -m scripts.sync.run_all`; Cron in UTC, z. B. `30 2 * * *` (04:30 Sommerzeit, 03:30 Winterzeit Zürich, beide nach den OpenParlData-Exporten). Alternative: dauerhaft laufende Container App mit dem Standardbefehl (Scheduler, `SYNC_TIME`) |
| Migrationen | Container Apps Job `migrate` (manuell) | `python -m alembic upgrade head` vor jeder neuen Anwendungsversion ausführen |
| Datenbank | Azure Database for PostgreSQL Flexible Server, Version 17 | Erweiterung `pg_trgm` unter `azure.extensions` freigeben (benötigt die Suchmigration); TLS erzwingen; Grösse nach Datenbestand (rund 3 Mio. Datensätze, mehrere GB inkl. Indizes) |
| Laufzustand | Azure Files, eingebunden unter `/app/logs` in `api` und `sync` | Laufberichte, Fortschritt und Wiederaufnahmezustand der Sync-Jobs. API und Job müssen dieselbe Freigabe sehen, sonst funktionieren Status, Abbruch und Wiederaufnahme über die API nicht |
| Secrets | Key Vault, als Container-Apps-Secrets referenziert | `DATABASE_URL`, `JWT_SECRET_KEY`, `SYNC_API_KEY`, `SMTP_PASSWORD`, optional `GOOGLE_CLIENT_SECRET` |
| E-Mail | Organisations-SMTP von WWF oder Azure Communication Services (SMTP-Relay) | Absenderdomäne mit SPF/DKIM; Versandlimits des Providers prüfen |
| Monitoring | Log Analytics, Alarme | Container-Logs; Alarm, wenn der Job fehlschlägt oder `sync_checkpoints.last_run_at` älter als 26 Stunden ist |

## Umgebungsvariablen

| Variable | Wert in Azure |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://USER:PASSWORT@SERVER.postgres.database.azure.com:5432/polit_assistant?sslmode=require` (Secret) |
| `JWT_SECRET_KEY`, `SYNC_API_KEY` | lange Zufallswerte (Secrets), je Umgebung verschieden |
| `VERIFICATION_BASE_URL` | öffentliche HTTPS-Adresse der App, z. B. eigene Domain; HTTPS aktiviert sichere Cookies |
| `SMTP_*` | Zugang des gewählten Providers |
| `TZ` | `Europe/Zurich` |
| `FORWARDED_ALLOW_IPS` | `*`, **nur** wenn die API ausschliesslich über den Ingress erreichbar ist. Ohne diese Einstellung vertraut uvicorn den Weiterleitungs-Headern des Ingress nicht, und alle Nutzer teilen sich die Ratenbegrenzung der Ingress-Adresse |
| `DEMO_MODE` | `false` (nie mit Produktionsdaten aktivieren) |

## Entscheidungen und Prüfpunkte für WWF

| Thema | Was zu entscheiden oder zu prüfen ist |
|---|---|
| Skalierung der API | Die Ratenbegrenzung hält ihren Zustand pro Prozess. Mit **einer** Replik ist sie exakt; bei mehreren Repliken ist ein gemeinsamer Speicher (z. B. Azure Cache for Redis) nachzurüsten |
| Laufzustand | Azure Files genügt für das aktuelle Volumen. Langfristig kann der Laufstatus in eine Datenbanktabelle verlagert werden; dann entfällt die Freigabe |
| Dateiberechtigungen | Der Container läuft als UID 10001. Die Azure-Files-Einbindung muss für diese UID beschreibbar sein (Mount-Optionen `uid=10001,gid=10001` oder entsprechende Freigabeberechtigungen) |
| Parallele Läufe | Ein PostgreSQL-Advisory-Lock verhindert parallele Synchronisierungen; ein zweiter Lauf endet mit `SYNC ALREADY RUNNING` und Exit-Code 2. Der Job darf daher nicht automatisch sofort wiederholt werden |
| Erstbefüllung | Der vollständige Erstimport (rund 6 GB Exporte) läuft am besten einmalig als eigener Job mit ausreichend Speicher oder als Wiederherstellung eines Datenbank-Backups (`pg_dump`/`pg_restore`) aus der Entwicklungsumgebung |
| Authentifizierung | E-Mail-Links und optional Google sind umgesetzt; ein Microsoft-Entra-SSO für WWF-Mitarbeitende wäre eine Erweiterung |
| Datenschutz | Speicherort (Region Schweiz Nord), Aufbewahrung der E-Mail-Adressen, Kontolöschung ist umgesetzt |
| Sicherung | Automatische Backups der Flexible-Server-Instanz und eine geprobte Wiederherstellung |

## Ablauf einer Bereitstellung

1. Ressourcengruppe, Container Registry, Log Analytics, Container-Apps-Umgebung, PostgreSQL Flexible Server, Azure-Files-Freigabe und Key Vault anlegen.
2. Image bauen und in die Registry übertragen.
3. `migrate` als manuellen Job ausführen; danach Klassifikation einspielen: `python -m scripts.seed_classification`.
4. Datenbestand wiederherstellen oder Erstimport ausführen (siehe [Installation](../getting-started.md)).
5. Container App `api` mit Ingress, Health-Probe, Secrets und Freigabe starten; Anmeldung per E-Mail-Link prüfen.
6. Job `sync` mit Zeitplan anlegen, einmal manuell starten und Laufbericht unter `/app/logs` sowie `GET /api/v1/sync/latest` prüfen.
7. Alarme für fehlgeschlagene Jobs und veraltete Checkpoints einrichten.

Ein erfolgreicher `/health`-Aufruf belegt nur die Datenbankverbindung. Für die Abnahme sind ein vollständiger Sync-Lauf, der E-Mail-Versand über den Organisationsprovider, ein Abbruch mit Wiederaufnahme und die Wiederherstellung einer Sicherung zu prüfen. Siehe [Deployment](../06-handover/deployment-guide.md) und [Betrieb](../06-handover/operations-guide.md).
