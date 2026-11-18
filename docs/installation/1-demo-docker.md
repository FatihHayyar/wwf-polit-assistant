# Demo mit Docker

Startet die Anwendung mit einem **Datenausschnitt** (die Geschäfte, Sitzungen, Abstimmungen und Dokumente des letzten Jahres, Dokumenttexte gekürzt) und einem lokalen Testpostfach für E-Mails.

| | |
|---|---|
| **Benötigt** | Docker Desktop, Internetverbindung |
| **Freier Speicher** | ca. 3 GB |
| **Dauer** | ca. 15–20 Minuten beim ersten Mal |

> Die Demo enthält nur einen Ausschnitt der Daten. Ältere Geschäfte und vollständige Dokumenttexte fehlen. Ohne Docker: [Demo ohne Docker und Git](2-demo-ohne-docker.md). Alle Daten: [vollständige Installation](3-vollinstallation.md).

## 1. Docker Desktop installieren

1. [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) öffnen, Docker Desktop für das eigene Betriebssystem herunterladen und installieren. Falls verlangt, den Computer neu starten.
2. Docker Desktop starten und die Nutzungsbedingungen akzeptieren. Eine Anmeldung ist nicht nötig («Skip»).
3. Warten, bis unten links **«Engine running»** angezeigt wird.

Docker Desktop muss laufen, solange die Anwendung genutzt wird.

## 2. Projekt herunterladen

1. [github.com/FatihHayyar/wwf-polit-assistant](https://github.com/FatihHayyar/wwf-polit-assistant) öffnen.
2. Auf den grünen Button **«Code»** klicken und **«Download ZIP»** wählen.
3. Die ZIP-Datei mit Rechtsklick → **«Alle extrahieren…»** entpacken.

Der Ordner `wwf-polit-assistant-main` mit den Ordnern `app`, `scripts` und der Datei `README.md` ist der **Projektordner**.

*Mit Git:* `git clone https://github.com/FatihHayyar/wwf-polit-assistant.git`

## 3. Anwendung starten

1. Den Projektordner im Explorer öffnen, in einen leeren Bereich **rechtsklicken** → **«Im Terminal öffnen»** (macOS: Terminal öffnen und mit `cd` in den Ordner wechseln).
2. Diesen Befehl einfügen und mit **Enter** bestätigen:

```sh
docker compose -f docker-compose.demo.yml up --build -d
```

Beim ersten Start lädt Docker die benötigten Komponenten herunter und füllt die Datenbank mit den Beispieldaten. Das dauert einige Minuten. Den Fortschritt zeigt:

```sh
docker compose -f docker-compose.demo.yml logs -f app
```

Die Anwendung ist bereit, sobald `Uvicorn running on http://0.0.0.0:8000` erscheint. **Strg + C** beendet nur die Anzeige, nicht die Anwendung.

## 4. Öffnen

| Dienst | Adresse |
|---|---|
| Polit-Assistant | [localhost:8081](http://localhost:8081) |
| Testpostfach (Mailpit) | [localhost:8025](http://localhost:8025) |

Weiter mit den [ersten Schritten](erste-schritte.md).

## Beenden und erneut starten

```sh
docker compose -f docker-compose.demo.yml down
```

```sh
docker compose -f docker-compose.demo.yml up -d
```

Daten, Registrierungen und Abonnements bleiben erhalten. `down -v` statt `down` löscht die Demo-Datenbank und setzt die Demo zurück.

## Häufige Probleme

| Meldung oder Verhalten | Lösung |
|---|---|
| `docker` wird nicht erkannt / `cannot connect to the Docker daemon` | Docker Desktop starten und warten, bis «Engine running» erscheint. Danach ein neues Terminal öffnen. |
| `no configuration file provided` | Das Terminal ist nicht im Projektordner. Schritt 3.1 wiederholen. |
| `port is already allocated` | Eine andere Variante oder ein anderes Programm nutzt Port 8081 oder 8025. Andere Variante mit `down` beenden (siehe deren Anleitung). |
| Seite lädt nicht | Mit dem `logs`-Befehl prüfen, ob `Uvicorn running …` erschienen ist. |

## Alles entfernen

Nach dem Test löscht dieser Befehl die Demo vollständig: Container, Demo-Datenbank und Anwendungsabbild.

```sh
docker compose -f docker-compose.demo.yml down -v --rmi local
```

Danach kann der Projektordner gelöscht und Docker Desktop bei Bedarf unter **Einstellungen → Apps** deinstalliert werden.
