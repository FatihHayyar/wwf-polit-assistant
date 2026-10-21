# Benutzerhandbuch

## Recherche

Alle Inhalte sind ohne Konto zugänglich. Links einen der neun Bereiche auswählen und Suchbegriff, Thema, Unterthema, Kanton, Geschäftstyp (nur bei Geschäften, z. B. Motion oder Postulat) oder Datum setzen. Die Ergebnisse werden seitenweise geladen. Beim Bereichswechsel bleiben die jeweiligen Filter erhalten.

Themenetiketten zeigen Hauptthema und Unterthema, etwa **Klima & Energie / Sonstiges**. Dieser Treffer gehört zum Klimabereich, besitzt aber kein spezifisch erkanntes Unterthema. Globales **Sonstiges** ohne Hauptthema bedeutet keine erkannte WWF-Zuordnung. Ein Hauptthemenfilter umfasst auch seine lokale Sonstiges-Unterkategorie.

Geschäfte mit gleichem normalisiertem Titel, gleicher Körperschaft und gleichem Kalendertag erscheinen als eine Karte. Die getrennten Quellaufzeichnungen, etwa **Message** und **Projet de loi**, sind über ihre Schaltflächen erreichbar. Es werden keine Quelldaten gelöscht. Trefferzahl und Seiten zählen diese Gruppen; diese Darstellung beweist nicht, dass die Quellen fachlich identisch sind.

Ein Klick auf einen Treffer öffnet die Detailansicht mit Quellenlinks und vorhandenen Beziehungen. Die Schliessen-Schaltfläche bleibt sichtbar, während der Inhalt gescrollt wird. Einzelne Inhalte werden im Bereich **Abonnements verwalten** zum Monitoring hinzugefügt.

Die Sprache lässt sich oben zwischen Deutsch, Französisch, Italienisch und Englisch wechseln. Originaltexte werden in einer verfügbaren Quellsprache angezeigt und nicht automatisch übersetzt.

## Fragen stellen

Im Feld **Frage stellen** über den Filtern lässt sich eine Frage in Deutsch, Französisch, Italienisch oder Englisch eingeben, zum Beispiel:

- «Motionen zum Wolf im Wallis seit 2024»
- «Welche Abstimmungen zum Klima gab es letztes Jahr?»
- «Séances au Grand Conseil de Genève le mois dernier»
- «Was gibt es zu "Fernwärme" im Kanton BE?» (Anführungszeichen erzwingen einen Suchbegriff)

Die Antwort zeigt unter **Verstanden**, welche Teile erkannt wurden (Bereich, Thema, Kanton, Geschäftstyp, Zeitraum, Suchbegriff), und nennt die Anzahl Treffer. Die Filter werden ins Suchformular übernommen und lassen sich dort anpassen. Frühere Fragen bleiben darunter sichtbar. Mit **Als Abonnement speichern** wird die Frage nach der Anmeldung zu einem Abonnement.

Die Erkennung arbeitet mit festen Regeln: Sie beantwortet keine inhaltlichen Fragen und erfindet keine Inhalte, sondern sucht passende parlamentarische Datensätze.

## Konto und Anmeldung

Für E-Mail-Benachrichtigungen zuerst registrieren, den Link in der E-Mail öffnen und auf der folgenden Seite **Registrierung bestätigen** klicken. Bereits registrierte Nutzer wählen **Anmelden** und bestätigen den Anmeldelink ebenso mit einem Klick. Aus Datenschutzgründen zeigt die Anwendung immer dieselbe Meldung, unabhängig davon, ob ein Konto existiert. Wer mehrmals kurz hintereinander einen Link anfordert, muss etwas warten. In der lokalen Docker-Demo befinden sich diese Nachrichten in Mailpit unter `http://localhost:8025`.

Wenn Google vom Betreiber eingerichtet wurde, steht die direkte Google-Anmeldung zur Verfügung. Bei bestimmten bestehenden Konten ist zur sicheren Zuordnung weiterhin die Anmeldung per E-Mail erforderlich. Andere externe Anmeldeanbieter sind derzeit nicht implementiert.

## Abonnements verwalten

Nach der Anmeldung die Abonnementverwaltung öffnen. Ein Konto kann **bis zu zehn Abonnements** führen, jedes mit eigenem Namen, etwa «Energie in Bern» und «Biodiversität in Zürich».

1. **Neues Abonnement** wählen und einen Namen vergeben.
2. Themen, Kantone, Geschäftstypen, Datenbereiche und Suchbegriffe (einer pro Zeile) auswählen.
3. **Abonnement speichern.**

Innerhalb eines Abonnements gelten mehrere Werte derselben Gruppe als Alternativen; verschiedene Gruppen müssen gemeinsam passen. Ein Hauptthema umfasst seine Unterthemen. Ein Abonnement ohne Themen, Kantone, Geschäftstypen und Suchbegriffe ist **pausiert**; eine alleinige Auswahl von Datenbereichen aktiviert es nicht. Mit dem Häkchen **Aktiv** lässt sich ein Abonnement auch bewusst pausieren. **Bearbeiten** und **Löschen** stehen auf jeder Abonnementkarte.

Eine Benachrichtigung genügt, wenn **eines** der aktiven Abonnements passt; passen mehrere, kommt trotzdem nur eine Nachricht. Nach jeder Änderung bestätigt eine E-Mail die gespeicherte Auswahl.

Beobachtete Einzelinhalte sind unabhängig von den Abonnements aktiv. Sie werden mit Bereich und Datensatz-ID hinzugefügt; bei Dokumenten gilt die lokale ID aus der API, nicht die externe Quell-ID.

Als Benachrichtigungsziel kann das Anmeldekonto oder eine Auswahl von insgesamt bis zu zehn E-Mail-Adressen dienen. Andere Adressen müssen über einen Bestätigungslink verifiziert werden. Bis zur ersten eigenen Auswahl verwenden bestehende Konten ihre Anmeldeadresse; **Adressen speichern** übernimmt eine geänderte Auswahl.

**Abmelden** und **Alle Benachrichtigungen beenden** bleiben am unteren Rand des Dialogs erreichbar. «Alle Benachrichtigungen beenden» löscht alle Abonnements und beobachteten Inhalte. **Konto löschen** befindet sich am Ende der Verwaltung und entfernt die kontobezogenen Einstellungen. Abmelden beendet alle Sitzungen des Kontos, auch auf anderen Geräten, beendet aber keine Abonnements.

## Benachrichtigungen

Relevante neue Inhalte und Änderungen werden nach der täglichen Synchronisierung (Standard 04:30 Uhr) geprüft und per E-Mail zusammengefasst. Technische Metadaten und bestimmte geringfügige Änderungen lösen keine Nachricht aus. Die Zusammenfassung erfolgt pro Nutzer und Geschäft beziehungsweise eigenständigem Inhalt; es gibt keine Garantie auf genau eine tägliche Nachricht.

Ein erfolgreich gespeichertes Abonnement allein erzeugt noch keine parlamentarische Update-Nachricht. Dazu muss eine passende relevante Änderung auftreten. Bei fehlenden Nachrichten hilft die [Fehlerbehebung](../troubleshooting.md).

## Benachrichtigung in der Demo ausprobieren

In der Docker-Demo zeigt die Startseite die Schritte an. Zuerst ein Abonnement anlegen. Unter **Benachrichtigung testen (Demo)** steht dann ein Thema zur Auswahl. **Testgeschäft erstellen und benachrichtigen** legt ein fiktives neues Geschäft an (Geschäftstyp und Suchbegriff aus dem passenden Abonnement) und schickt die Benachrichtigung über den regulären Ablauf an das eigene Konto. Die Nachricht erscheint in Mailpit; **Testgeschäft ansehen** öffnet das erzeugte Geschäft. Passt es zu keinem Abonnement, erklärt die Oberfläche den Grund. In einer produktiven Installation gibt es diese Funktion nicht.
