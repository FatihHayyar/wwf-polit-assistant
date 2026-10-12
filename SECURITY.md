# Sicherheit

Der Polit-Assistant ist ein Entwicklungs-MVP. Es gibt derzeit keine veröffentlichte Supportmatrix für Releases, kein zugesagtes Reaktionszeitfenster und keine abgeschlossene Produktions-Sicherheitsprüfung. Sicherheitskorrekturen sollen im aktuellen Entwicklungsstand überprüft werden.

## Sicherheitsproblem melden

Keine öffentlich ausnutzbaren Details, Zugangsdaten oder personenbezogenen Daten in GitHub-Issues veröffentlichen. Wenn im Repository **Security → Report a vulnerability** verfügbar ist, diesen privaten Meldeweg verwenden. Andernfalls die Projektverantwortlichen über einen bereits bekannten privaten Projektkontakt erreichen; eine separate öffentliche Sicherheitsadresse ist noch nicht eingerichtet.

Betroffenen Commit, Komponente, mögliche Auswirkungen und eine bereinigte Reproduktion angeben. Tests auf eigene beziehungsweise ausdrücklich freigegebene Testumgebungen beschränken. Eine öffentliche Fehlerbeschreibung erst nach Abstimmung zur Offenlegung erstellen.

## Betriebshinweise

Demo-Schlüssel und Datenbankpasswörter sind nur für lokale Nutzung vorgesehen. Echte Secrets über die Umgebung verwalten, HTTPS für öffentliche Kontofunktionen einsetzen und Sync-Schlüssel nur berechtigten Betreibern geben. Bestätigungslinks, JWTs, SMTP-Zugangsdaten und Benutzeradressen aus Screenshots und Logs entfernen.

Bei versehentlich veröffentlichten Secrets die betroffenen Schlüssel widerrufen oder rotieren; das Löschen aus der aktuellen Datei entfernt sie nicht aus der Git-Historie. Weitere Hinweise stehen im [Betriebsleitfaden](docs/deployment.md).
