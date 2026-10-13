# Benutzerhandbuch

## Recherche

Alle Inhalte sind ohne Konto zugänglich. Links einen der neun Bereiche auswählen und Suchbegriff, Thema, Unterthema, Kanton oder Datum setzen. Die Ergebnisse werden seitenweise geladen. Beim Bereichswechsel bleiben die jeweiligen Filter erhalten.

Themenetiketten zeigen Hauptthema und Unterthema, etwa **Klima & Energie / Sonstiges**. Dieser Treffer gehört zum Klimabereich, besitzt aber kein spezifisch erkanntes Unterthema. Globales **Sonstiges** ohne Hauptthema bedeutet keine erkannte WWF-Zuordnung. Ein Hauptthemenfilter umfasst auch seine lokale Sonstiges-Unterkategorie.

Geschäfte mit gleichem normalisiertem Titel, gleicher Körperschaft und gleichem Kalendertag erscheinen als eine Karte. Die getrennten Quellaufzeichnungen, etwa **Message** und **Projet de loi**, sind über ihre Schaltflächen erreichbar. Es werden keine Quelldaten gelöscht. Trefferzahl und Seiten zählen diese Gruppen; diese Darstellung beweist nicht, dass die Quellen fachlich identisch sind.

Ein Klick auf einen Treffer öffnet die Detailansicht mit Quellenlinks und vorhandenen Beziehungen. Die Schliessen-Schaltfläche bleibt sichtbar, während der Inhalt gescrollt wird. Einzelne Inhalte werden im Bereich **Abonnements verwalten** zum Monitoring hinzugefügt.

Die Sprache lässt sich oben zwischen Deutsch, Französisch, Italienisch und Englisch wechseln. Originaltexte werden in einer verfügbaren Quellsprache angezeigt und nicht automatisch übersetzt.

## Konto und Anmeldung

Für E-Mail-Benachrichtigungen zuerst registrieren und den Bestätigungslink öffnen. Bereits registrierte Nutzer wählen **Anmelden**. In der lokalen Docker-Demo befinden sich diese Nachrichten in Mailpit unter `http://localhost:8025`.

Wenn Google vom Betreiber eingerichtet wurde, steht die direkte Google-Anmeldung zur Verfügung. Bei bestimmten bestehenden Konten ist zur sicheren Zuordnung weiterhin die Anmeldung per E-Mail erforderlich. Andere externe Anmeldeanbieter sind derzeit nicht implementiert.

## Abonnements verwalten

Nach der Anmeldung die Abonnementverwaltung öffnen. Themen, Kantone, Suchbegriffe und Datenbereiche lassen sich kombinieren. Ein Hauptthema umfasst seine Unterthemen. Mehrere Werte derselben Gruppe gelten als Alternativen; verschiedene Gruppen müssen gemeinsam passen.

Leere Themen-, Kantons- und Suchbegriffgruppen pausieren die Filterabonnements. Eine alleinige Auswahl von Datenbereichen aktiviert sie nicht. Beobachtete Einzelinhalte bleiben davon unabhängig aktiv. Einzelinhalte werden mit Bereich und Datensatz-ID hinzugefügt; bei Dokumenten gilt die lokale ID aus der API, nicht die externe Quell-ID.

Als Benachrichtigungsziel kann das Anmeldekonto oder eine Auswahl von insgesamt bis zu zehn E-Mail-Adressen dienen. Andere Adressen müssen über einen Bestätigungslink verifiziert werden. Bis zur ersten eigenen Auswahl verwenden bestehende Konten ihre Anmeldeadresse.

**Änderungen speichern**, **Abmelden** und **Alle Abonnements beenden** bleiben im Verwaltungsdialog auch beim Scrollen erreichbar. Nach erfolgreichem Speichern erscheint eine Bestätigung. **Konto löschen** befindet sich am Ende der Verwaltung und entfernt die kontobezogenen Einstellungen. Abmelden beendet die aktuelle Sitzung, beendet aber keine Abonnements.

## Benachrichtigungen

Relevante neue Inhalte und Änderungen werden nach einem erfolgreichen Sync geprüft und per E-Mail zusammengefasst. Technische Metadaten und bestimmte geringfügige Änderungen lösen keine Nachricht aus. Die Zusammenfassung erfolgt pro Nutzer und Geschäft beziehungsweise eigenständigem Inhalt; es gibt keine Garantie auf genau eine tägliche Nachricht.

Ein erfolgreich gespeichertes Abonnement allein erzeugt noch keine parlamentarische Update-Nachricht. Dazu muss eine passende relevante Änderung auftreten. Bei fehlenden Nachrichten hilft die [Fehlerbehebung](../troubleshooting.md).
