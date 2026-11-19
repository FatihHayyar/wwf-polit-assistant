# Vollständige Installation (Windows)

Richtet den Polit-Assistant mit **allen Daten von OpenParlData** ein (rund 3 Millionen Einträge, alle Kantone), so wie er im Betrieb läuft: mit täglicher Aktualisierung um 04:30 Uhr und E-Mail-Benachrichtigungen. Für einen ersten Eindruck genügt die [Demo](1-demo-docker.md).

| | |
|---|---|
| **Benötigt** | Windows 10 oder 11, Administratorrechte, stabile Internetverbindung |
| **Arbeitsspeicher** | mindestens 16 GB empfohlen |
| **Freier Speicher** | mindestens 50 GB |
| **Dauer** | ca. 30 Minuten Einrichtung, danach mehrere Stunden Wartezeit für Download, Import und Themenzuordnung |

Der Computer sollte während der Einrichtung **am Strom angeschlossen** sein und **nicht in den Ruhezustand** wechseln (Einstellungen → System → Energie).

## 1. Programme installieren

Jeweils herunterladen, installieren und die Vorgaben des Installationsprogramms übernehmen, sofern hier nichts anderes steht.

1. **Docker Desktop:** [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/). Falls verlangt, den Computer neu starten. Docker Desktop starten, die Nutzungsbedingungen akzeptieren, die Anmeldung überspringen («Skip») und warten, bis unten links **«Engine running»** erscheint.
2. **Git:** [git-scm.com/downloads/win](https://git-scm.com/downloads/win) → «Click here to download». Alle Vorgaben übernehmen.
3. **Python 3.13:** [python.org/downloads](https://www.python.org/downloads/) → «Download Python 3.13…». Im ersten Fenster unbedingt **«Add python.exe to PATH»** anhaken, dann **«Install Now»**.

Ein separates PostgreSQL ist nicht nötig; die Datenbank läuft in Docker.

## 2. PowerShell öffnen und Installation prüfen

1. **Windows-Taste** drücken, `PowerShell` tippen und **Windows PowerShell** öffnen.
2. Diese drei Befehle einzeln einfügen (Rechtsklick fügt ein) und mit **Enter** bestätigen:

```powershell
docker --version
git --version
py --version
```

Jeder Befehl zeigt eine Versionsnummer. Erscheint stattdessen «wird nicht erkannt», PowerShell schliessen, neu öffnen und erneut versuchen; hilft das nicht, das betreffende Programm neu installieren.

## 3. Projekt herunterladen

```powershell
cd $HOME\Documents
git clone https://github.com/FatihHayyar/wwf-polit-assistant.git
cd wwf-polit-assistant
```

Das Projekt liegt danach unter **Dokumente\wwf-polit-assistant**. Alle weiteren Befehle werden in diesem Ordner ausgeführt; die Eingabezeile zeigt dann `PS C:\Users\…\Documents\wwf-polit-assistant>`.

Der ZIP-Download reicht hier nicht: Die Themenzuordnung prüft vor dem Schreiben die Regelqualität gegen einen festen Stand in der Git-Historie.

## 4. Einstellungen anlegen

### 4.1 Einstellungsdatei erstellen

```powershell
Copy-Item .env.example .env
```

### 4.2 Zwei geheime Schlüssel erzeugen

Diesen Befehl **zweimal** ausführen und beide Ausgaben kurz in einem Textdokument notieren:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 4.3 Einstellungen bearbeiten

```powershell
notepad .env
```

Im Editor diese Zeilen ändern (alles andere unverändert lassen):

| Zeile | Neuer Wert |
|---|---|
| `JWT_SECRET_KEY=` | erster Schlüssel aus 4.2 |
| `SYNC_API_KEY=` | zweiter Schlüssel aus 4.2 |

Dann den E-Mail-Versand einrichten, **Variante A oder B**:

**A. Testpostfach (empfohlen zum Ausprobieren):** E-Mails werden nicht versendet, sondern in einem lokalen Postfach angezeigt.

| Zeile | Neuer Wert |
|---|---|
| `SMTP_HOST=` | `host.docker.internal` |
| `SMTP_PORT=` | `1025` |
| `SMTP_FROM_EMAIL=` | `polit-assistant@example.org` |

Zusätzlich am Ende der Datei eine neue Zeile einfügen: `SMTP_STARTTLS=false`

**B. Echter Mailserver:** Die Zugangsdaten des eigenen Mailservers bei `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` und `SMTP_FROM_EMAIL` eintragen. Hinweise je Anbieter stehen im [Konfigurationsleitfaden](../configuration.md).

Die Datenbankzeilen (`DATABASE_URL`, `POSTGRES_PASSWORD`) bleiben unverändert; die Datenbank ist nur von diesem Computer aus erreichbar. Datei speichern (**Strg + S**) und den Editor schliessen.

### 4.4 Testpostfach starten (nur Variante A)

```powershell
docker run -d --name polit-mailpit --restart unless-stopped -p 127.0.0.1:1025:1025 -p 127.0.0.1:8025:8025 axllent/mailpit
```

## 5. Python-Umgebung einrichten (wenige Minuten)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

## 6. Datenbank starten und vorbereiten (1–2 Minuten)

```powershell
docker compose up -d postgres
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Meldet der zweite Befehl `connection refused`, einige Sekunden warten und ihn wiederholen.

## 7. Daten herunterladen (rund 7 GB, 10–60 Minuten)

```powershell
.\.venv\Scripts\python.exe scripts/bootstrap/download_openparldata.py --workers 6
```

Fertig, wenn `All requested export files are present` erscheint. Meldet der Befehl `Bootstrap download is NOT complete`, war die Verbindung kurz unterbrochen: denselben Befehl erneut ausführen, fertige Dateien werden übersprungen.

## 8. Daten importieren (längster Schritt, mehrere Stunden)

```powershell
.\.venv\Scripts\python.exe scripts/bootstrap/import_normalized.py all
```

Das Fenster zeigt den Fortschritt je Bereich. Nach jedem Bereich wird dessen Suchindex aufgebaut (`[INDEX] Building …`); bei den Dokumenten kann das allein eine halbe Stunde dauern. Fertig, wenn `NORMALIZED IMPORT COMPLETE` erscheint.

Auf Computern mit wenig Arbeitsspeicher kann die Datenbank während der Dokumente kurz neu starten. Der Import meldet dann `[RETRY] … database connection lost`, wartet eine Minute und setzt nach der letzten fertigen Datei automatisch fort. Erst nach zehn Fehlversuchen bricht er ab; dann denselben Befehl erneut ausführen.

## 9. Themen zuordnen (mehrere Stunden)

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_classification
.\.venv\Scripts\python.exe -m scripts.reclassify_rules --apply
```

Der zweite Befehl prüft zuerst die Regelqualität und ordnet danach alle Einträge den WWF-Themen zu. Er kann unterbrochen und erneut gestartet werden; bereits zugeordnete Einträge werden übersprungen.

## 10. Anwendung starten

```powershell
docker compose up -d --build
```

Startet die Anwendung und die tägliche Aktualisierung. Nach etwa einer Minute öffnen:

| Dienst | Adresse |
|---|---|
| Polit-Assistant | [localhost:8000](http://localhost:8000) |
| Testpostfach (nur Variante A) | [localhost:8025](http://localhost:8025) |

Weiter mit den [ersten Schritten](erste-schritte.md). Die Schaltfläche «Testgeschäft erstellen und benachrichtigen» gibt es nur in der Demo; hier entstehen Benachrichtigungen durch die tägliche Aktualisierung.

## 11. Speicher freigeben

Die heruntergeladenen Rohdaten werden nicht mehr benötigt (rund 7 GB). Im Explorer den Ordner **Dokumente\wwf-polit-assistant\data\raw** löschen.

## Beenden und erneut starten

Die Anwendung startet mit Docker Desktop automatisch. Manuell:

```powershell
cd $HOME\Documents\wwf-polit-assistant
docker compose down
docker compose up -d
```

Daten, Registrierungen und Abonnements bleiben erhalten. Die erste tägliche Aktualisierung vergleicht jeden Bereich vollständig und dauert deshalb länger; danach werden nur Änderungen gelesen.

## Häufige Probleme

| Meldung oder Verhalten | Lösung |
|---|---|
| `docker`, `git` oder `py` wird nicht erkannt | Programm aus Schritt 1 installieren oder PowerShell neu öffnen. |
| `cannot connect to the Docker daemon` | Docker Desktop starten und warten, bis «Engine running» erscheint. |
| `Set JWT_SECRET_KEY in .env` | Schritt 4.3 prüfen und die Datei speichern. |
| `no configuration file provided` / Datei nicht gefunden | Die PowerShell ist nicht im Projektordner: `cd $HOME\Documents\wwf-polit-assistant` |
| `port is already allocated` | Die Demo läuft noch: `docker compose -f docker-compose.demo.yml down` |
| `no space left on device` | Zu wenig Speicher. Speicher freigeben und den unterbrochenen Befehl wiederholen. |
| `Quality gate failed` in Schritt 9 | Das Projekt wurde nicht mit Git heruntergeladen oder lokal verändert. Schritt 3 in einem neuen Ordner wiederholen. |
| Registrierung meldet einen E-Mail-Fehler | Variante A: Testpostfach aus 4.4 läuft? Variante B: Zugangsdaten prüfen. Nach Änderungen an `.env`: `docker compose up -d` |

Betrieb auf einem Server, Sicherung und Aktualisierung beschreibt das [Betriebshandbuch](../06-handover/deployment-guide.md).

## Alles entfernen

Löscht Anwendung, Datenbank (rund 15 GB), Testpostfach und Anwendungsabbilder. Registrierungen und Abonnements gehen dabei verloren.

```powershell
cd $HOME\Documents\wwf-polit-assistant
docker compose down -v --rmi local
docker rm -f polit-mailpit
```

Danach den Ordner **Dokumente\wwf-polit-assistant** löschen. Docker Desktop, Git und Python lassen sich bei Bedarf unter **Einstellungen → Apps** deinstallieren.
