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

## Regelbasierte Klassifikation

Die Kategorien und Regeln liegen in [app/classification/taxonomy.json](../app/classification/taxonomy.json). Mit der Prozess-Umgebungsvariable `CLASSIFICATION_TAXONOMY_PATH` kann eine andere UTF-8-JSON-Datei gewählt werden. Kategorien lassen sich dort hinzufügen, umbenennen oder entfernen; die Oberfläche verwendet die übersetzten Namen aus der Datenbank. Stabile, eindeutige `code`-Werte erhalten historische Referenzen. Jede normale Hauptkategorie benötigt genau eine Unterkategorie mit `fallback: true` (Sonstiges); genau eine Hauptkategorie dient als globaler Fallback für fachfremde Inhalte.

Kategorien enthalten `names` für `de`, `fr`, `it`, `rm`, optional `descriptions`, `sort_order`, `threshold` (Standard 8) und `concepts`. Übersetzungen und Synonyme desselben Konzepts gehören unter denselben Konzeptcode und zählen nur einmal. `match_type: "phrase"` verlangt Wortgrenzen; `"prefix"` erlaubt Buchstaben-Endungen und Zusammensetzungen am letzten Wort ab fünf Buchstaben. Kurze Wörter bleiben exakt. `rule_type: "strong"` bezeichnet eindeutige Fachbegriffe. Generische `"context"`-Begriffe benötigen zusätzlich ein `"qualifier"`-Konzept derselben Kategorie, etwa einen ausdrücklichen Umweltbezug. Ein Qualifier allein löst keine Zuordnung aus.

Ein starkes Titelkonzept reicht zur Zuordnung; reiner Inhalt benötigt zwei unterschiedliche starke Konzepte. Alternativ genügt die Kombination aus Kontext und Qualifier bei erreichtem Schwellenwert. Spezifische Unterkategorien verdrängen den lokalen Sonstiges-Fallback ihrer Hauptkategorie. Mehrere passende Themen bleiben erhalten. HTML, typografische Apostrophe und PDF-Zeilentrennungen werden normalisiert.

Akzeptierte Titelzuordnungen beenden die Inhaltsprüfung. Kontext und Qualifier müssen derselben Kategorie entsprechen; ihre Kombination prüft keine syntaktische Beziehung im Satz. Bei fehlerhaftem HTML bleibt der ursprüngliche Text erhalten, damit der Lauf fortgesetzt werden kann. Die Oberfläche zeigt Hauptthema und Unterthema gemeinsam; globales Sonstiges hat keinen Elternbereich.

Nach Änderungen Kategorien und Regeln synchronisieren und API/Scheduler neu starten:

```powershell
.venv/Scripts/python.exe -m scripts.seed_classification
```

Entfernte Kategorien und Regeln werden deaktiviert. Bestehende Zuordnungen werden erst durch eine explizite Neuberechnung ersetzt. Ollama ist nicht Teil dieses Ablaufs.

Der gemischte Qualitätstest verwendet 50 unabhängig annotierte reale Datensätze in einer isolierten SQLite-Datenbank:

```powershell
.venv/Scripts/python.exe -m scripts.rule_quality
```

Die stapelweise Neuberechnung umfasst alle neun Datensatztypen. Ohne `--apply` bleibt PostgreSQL schreibgeschützt. `--apply` prüft zunächst das Testset und stoppt bei Fehlern. Die Verarbeitung verwendet die Synchronisationssperre, ersetzt nur Klassifikationen und erzeugt keine Benachrichtigungen:

Der Qualitätstest und die `--apply`-Schranke benötigen Git sowie den Baseline-Commit `b20f074557c310f0b1a52df15ca3336de73ed56d` in der lokalen Historie. Ein ZIP ohne `.git` oder ein unvollständiger Shallow-Clone genügt dafür nicht. Die älteren separaten Jobs `classify_affairs`/`classify_entities` bleiben verfügbar, haben jedoch keine gemeinsame Qualitätsschranke.

```powershell
.venv/Scripts/python.exe -m scripts.reclassify_rules --dataset affairs --limit 20
.venv/Scripts/python.exe -m scripts.reclassify_rules --apply
```

Erfolgreiche Stapel werden einzeln gespeichert. Unterbrochene Läufe überspringen bereits vollständig mit der aktuellen Regelversion klassifizierte Datensätze. Nach Taxonomieänderungen `--force` verwenden, um auch diese Datensätze neu zu berechnen. `--dataset` begrenzt den Lauf auf `affairs`, `agendas`, `meetings`, `votings`, `events`, `documents`, `texts`, `groups` oder `interests`.

Dokumente und Texte werden standardmässig mit bis zu vier lokalen Prozessen parallel ausgewertet (`--workers 1` für serielle Verarbeitung). Die Hilfsprozesse lesen ausschliesslich Regeln; alle Datenbankänderungen erfolgen im Hauptprozess. `python -m scripts.verify_rule_workers` vergleicht beide Verfahren schreibgeschützt anhand des Testsets und 250 weiterer Dokumente.

`python -m scripts.rule_backfill_status` prüft danach schreibgeschützt die Abdeckung aller neun Datensatztypen und meldet fehlende sowie veraltete Zuordnungen in `rule_backfill_status.json`.
