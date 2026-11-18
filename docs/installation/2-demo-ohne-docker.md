# Demo ohne Docker und Git (Windows)

Startet die Anwendung mit einem **Datenausschnitt** (die Geschäfte, Sitzungen, Abstimmungen und Dokumente des letzten Jahres, Dokumenttexte gekürzt), ohne Docker und Git. Dafür werden Python, PostgreSQL und Mailpit einzeln eingerichtet.

| | |
|---|---|
| **Benötigt** | Windows 10 oder 11, Internetverbindung, Administratorrechte |
| **Freier Speicher** | ca. 2 GB |
| **Dauer** | ca. 30–45 Minuten beim ersten Mal |

> Die Demo enthält nur einen Ausschnitt der Daten. Ältere Geschäfte und vollständige Dokumenttexte fehlen. Mit Docker geht es schneller: [Demo mit Docker](1-demo-docker.md). Alle Daten: [vollständige Installation](3-vollinstallation.md).

## 1. Projekt herunterladen

1. [github.com/FatihHayyar/wwf-polit-assistant](https://github.com/FatihHayyar/wwf-polit-assistant) öffnen.
2. Auf den grünen Button **«Code»** klicken und **«Download ZIP»** wählen.
3. Die ZIP-Datei mit Rechtsklick → **«Alle extrahieren…»** entpacken, z. B. nach `C:\polit-assistant`.

Der Ordner `wwf-polit-assistant-main` mit den Ordnern `app`, `scripts` und der Datei `README.md` ist der **Projektordner**.

## 2. Python installieren

1. [python.org/downloads/windows](https://www.python.org/downloads/windows/) öffnen und bei der neuesten Version **Python 3.13** den **«Windows installer (64-bit)»** herunterladen.
2. Installer starten. **Wichtig:** Unten das Häkchen **«Add python.exe to PATH»** setzen.
3. **«Install Now»** klicken.

## 3. PostgreSQL installieren

1. [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) öffnen, **«Download the installer»** wählen und **PostgreSQL 17** für Windows herunterladen.
2. Installer starten und die Vorschläge mit **«Next»** übernehmen. Dabei:
   - ein **Passwort** für den Benutzer `postgres` festlegen und notieren, **nur Buchstaben und Zahlen** (z. B. `demo2026`);
   - den **Port** `5432` unverändert lassen.
3. Am Ende das Häkchen bei **«Stack Builder»** entfernen und **«Finish»** klicken.

## 4. Mailpit (Testpostfach) starten

1. [github.com/axllent/mailpit/releases/latest](https://github.com/axllent/mailpit/releases/latest) öffnen und unter «Assets» **`mailpit-windows-amd64.zip`** herunterladen.
2. Entpacken und **`mailpit.exe`** doppelklicken. Bei «Der Computer wurde durch Windows geschützt»: **«Weitere Informationen» → «Trotzdem ausführen»**. Fragt die Firewall, genügt **«Abbrechen»**.
3. Das schwarze Fenster **offen lassen**, solange die Anwendung läuft.

## 5. Terminal öffnen und Einstellungen setzen

1. Den Projektordner im Explorer öffnen, in einen leeren Bereich **rechtsklicken** → **«Im Terminal öffnen»**.
2. Diesen Block einfügen und mit **Enter** bestätigen. Vorher in der **ersten Zeile** `IHR-PASSWORT` durch das Passwort aus Schritt 3 ersetzen; die übrigen Zeilen übernehmen es automatisch:

```powershell
$env:PGPASSWORD = "IHR-PASSWORT"
$env:DATABASE_URL = "postgresql+psycopg://postgres:$($env:PGPASSWORD)@127.0.0.1:5432/polit_demo"
$env:JWT_SECRET_KEY = "local-test-only-change-for-production-2026"
$env:SMTP_HOST = "127.0.0.1"; $env:SMTP_PORT = "1025"; $env:SMTP_STARTTLS = "false"
$env:SMTP_FROM_EMAIL = "demo@example.org"
$env:VERIFICATION_BASE_URL = "http://localhost:8000"; $env:FRONTEND_URL = "http://localhost:8000"
$env:DEMO_MODE = "true"; $env:DEMO_MAILBOX_URL = "http://localhost:8025"
```

Die Einstellungen gelten nur für dieses Fenster. **Das Fenster offen lassen.**

## 6. Einrichten (nur beim ersten Mal, einige Minuten)

Die drei Befehle **nacheinander** einfügen und jeweils warten, bis wieder `PS C:\...>` erscheint. Der erste Befehl findet die installierte PostgreSQL-Version selbst.

```powershell
& (Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\createdb.exe" | Select-Object -Last 1).FullName -U postgres polit_demo
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
```

## 7. Starten

```powershell
.\.venv\Scripts\python.exe -m scripts.demo.start
```

Die Datenbank wird eingerichtet und mit Beispieldaten gefüllt. Die Anwendung ist bereit, sobald `Uvicorn running on http://0.0.0.0:8000` erscheint. Fragt die Firewall, genügt **«Abbrechen»**.

## 8. Öffnen

| Dienst | Adresse |
|---|---|
| Polit-Assistant | [localhost:8000](http://localhost:8000) |
| Testpostfach (Mailpit) | [localhost:8025](http://localhost:8025) |

Weiter mit den [ersten Schritten](erste-schritte.md).

## Beenden und erneut starten

**Beenden:** Im Terminal **Strg + C** drücken, Terminal und Mailpit-Fenster schliessen.

**Erneut starten:** `mailpit.exe` starten, im Projektordner ein Terminal öffnen, den Block aus **Schritt 5** einfügen und **Schritt 7** ausführen. Daten, Registrierungen und Abonnements bleiben erhalten.

## Häufige Probleme

| Meldung oder Verhalten | Lösung |
|---|---|
| `py` wird nicht erkannt | Python mit dem Häkchen «Add python.exe to PATH» neu installieren (Schritt 2), dann ein neues Terminal öffnen und Schritt 5 wiederholen. |
| `password authentication failed` | Passwort im Block aus Schritt 5 prüfen. |
| `database "polit_demo" already exists` | Kann ignoriert werden. |
| `createdb.exe` wird nicht gefunden | PostgreSQL ist nicht unter `C:\Program Files\PostgreSQL` installiert. Schritt 3 wiederholen. |
| `connection refused` bei Port `5432` | In Windows nach **«Dienste»** suchen und den Dienst **postgresql-x64-17** starten. |
| Registrierung meldet einen Fehler beim E-Mail-Versand | Mailpit läuft nicht. `mailpit.exe` starten (Schritt 4). |
| `address already in use` | Ein anderes Programm nutzt Port 8000. Es beenden oder den Computer neu starten. |

## Entfernen

Python und PostgreSQL unter **Einstellungen → Apps** deinstallieren, Projekt- und Mailpit-Ordner löschen.
