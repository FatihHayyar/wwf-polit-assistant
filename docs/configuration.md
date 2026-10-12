# Konfiguration

Die Einstellungen liegen in [app/core/config.py](../app/core/config.py). Lokal werden Umgebungsvariablen und eine UTF-8-Datei `.env` gelesen. Umgebungsvariablen haben Vorrang. Einstellungen werden pro Prozess zwischengespeichert; Änderungen erfordern einen Neustart des jeweiligen API- oder Scheduler-Prozesses.

| Variable | Standard | Zweck |
|---|---|---|
| `DATABASE_URL` | erforderlich | SQLAlchemy-Verbindung, z. B. `postgresql+psycopg://USER:PASSWORD@localhost:5433/DB` |
| `JWT_SECRET_KEY` | erforderlich | Eigener geheimer Signaturschlüssel; Demo-Werte nicht für den Betrieb übernehmen |
| `JWT_ALGORITHM` | `HS256` | JWT-Signaturalgorithmus |
| `JWT_EXPIRE_MINUTES` | `10080` | Sitzungsdauer, standardmässig sieben Tage |
| `SYNC_API_KEY` | nicht gesetzt | Gemeinsamer Schlüssel für die Sync-Verwaltungs-API |
| `SMTP_HOST` | nicht gesetzt | SMTP-Server für Verifikation und Benachrichtigungen |
| `SMTP_PORT` | `587` | SMTP-Port |
| `SMTP_STARTTLS` | `true` | STARTTLS; Mailpit verwendet lokal `false` |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | nicht gesetzt | SMTP-Anmeldedaten |
| `SMTP_FROM_EMAIL` | nicht gesetzt | Absenderadresse |
| `SMTP_FROM_NAME` | `WWF Polit-Assistant` | Absendername |
| `VERIFICATION_BASE_URL` | `http://localhost:8000` | Öffentlich erreichbare Basis für Bestätigungslinks und Google-Callback; HTTPS aktiviert sichere Cookies |
| `EMAIL_VERIFICATION_MINUTES` | `30` | Gültigkeit von Bestätigungslinks |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | nicht gesetzt | Optionale Google-OAuth-Anmeldung; beide erforderlich |
| `FRONTEND_URL` | `http://localhost:3000` | Vorhandene Einstellung; aktuelle Auth-Rückleitungen verwenden relative Pfade zur Anwendung |
| `APP_NAME`, `APP_VERSION` | `WWF Polit-Assistant API`, `0.1.0` | Vorhandene Einstellungen; Metadaten in `app/main.py` sind derzeit separat festgelegt |

Eine Vorlage befindet sich in [.env.example](../.env.example). Keine echten Zugangsdaten, Tokens oder personenbezogenen Logs ins Repository aufnehmen.

## Container und lokale Prozesse

Eine `.env` für Docker Compose ersetzt nicht automatisch die `environment`-Liste des Containers. Die Demo hat eigene, feste lokale Werte in [docker-compose.demo.yml](../docker-compose.demo.yml). Google-Zugangsdaten werden dort derzeit nicht durchgereicht; dafür eine passende Compose-Override-Konfiguration ergänzen.

[docker-compose.yml](../docker-compose.yml) enthält PostgreSQL und den Scheduler, aber keinen API-Dienst. Die API läuft in der Entwicklungsanleitung auf dem Host. Das Dockerfile startet standardmässig den Scheduler; ein API-Container benötigt einen abweichenden Startbefehl.

## Google-Anmeldung

Einen Google-OAuth-Client vom Typ Webanwendung mit der exakten Weiterleitungs-URI `${VERIFICATION_BASE_URL}/api/v1/auth/google/callback` konfigurieren. Lokal lautet sie `http://localhost:8000/api/v1/auth/google/callback`; in der Demo wäre es `http://localhost:8081/api/v1/auth/google/callback`.

Beide Google-Variablen im API-Prozess setzen und neu starten. `GET /api/v1/auth/providers` zeigt, ob Google aktiviert ist. Ohne Konfiguration bleibt die Anmeldung über E-Mail-Links bestehen. Details zur Registrierung eines Clients stehen in der [Google-OAuth-Dokumentation](https://developers.google.com/identity/protocols/oauth2/web-server).
