# Benutzerhandbuch

## Recherche

Alle Inhalte sind ohne Konto zugänglich. Links einen der neun Bereiche auswählen und Suchbegriff, Thema, Unterthema, Kanton, Geschäftstyp (nur bei Geschäften, z. B. Motion oder Postulat) oder Datum setzen. Die Ergebnisse werden seitenweise geladen. Beim Bereichswechsel bleiben die jeweiligen Filter erhalten.

Themenetiketten zeigen Hauptthema und Unterthema, etwa **Klima & Energie / Sonstiges**. Dieser Treffer gehört zum Klimabereich, besitzt aber kein spezifisch erkanntes Unterthema. Globales **Sonstiges** ohne Hauptthema bedeutet keine erkannte WWF-Zuordnung. Ein Hauptthemenfilter umfasst auch seine lokale Sonstiges-Unterkategorie.

Geschäfte mit gleichem normalisiertem Titel, gleicher Körperschaft und gleichem Kalendertag erscheinen als eine Karte. Die getrennten Quellaufzeichnungen, etwa **Message** und **Projet de loi**, sind über ihre Schaltflächen erreichbar. Es werden keine Quelldaten gelöscht. Trefferzahl und Seiten zählen diese Gruppen; diese Darstellung beweist nicht, dass die Quellen fachlich identisch sind.

Ein Klick auf einen Treffer öffnet die Detailansicht mit Quellenlinks und vorhandenen Beziehungen. Die Schliessen-Schaltfläche bleibt sichtbar, während der Inhalt gescrollt wird. Angemeldete Nutzer verfolgen einen Inhalt mit **☆ Verfolgen** oben in der Detailansicht; **★ Wird verfolgt** beendet das Verfolgen wieder.

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

Für E-Mail-Benachrichtigungen zuerst registrieren, den Link in der E-Mail öffnen und auf der folgenden Seite **Registrierung bestätigen** klicken. Bereits registrierte Nutzer wählen **Anmelden** und bestätigen den Anmeldelink ebenso mit einem Klick. Wer sich mit einer bereits registrierten Adresse registrieren will, erhält den Hinweis, sich anzumelden; wer sich mit einer unbekannten Adresse anmelden will, den Hinweis, sich zuerst zu registrieren. In beiden Fällen wechselt die Auswahl automatisch, ein zweiter Klick sendet den richtigen Link. Pro Adresse kann höchstens einmal pro Minute ein Link angefordert werden; die Meldung nennt die verbleibende Wartezeit. In der lokalen Docker-Demo befinden sich diese Nachrichten in Mailpit unter `http://localhost:8025`.

Wenn Google vom Betreiber eingerichtet wurde, steht die direkte Google-Anmeldung zur Verfügung. Bei bestimmten bestehenden Konten ist zur sicheren Zuordnung weiterhin die Anmeldung per E-Mail erforderlich. Andere externe Anmeldeanbieter sind derzeit nicht implementiert.

## Abonnements verwalten

Nach der Anmeldung **Abonnements ansehen und verwalten** öffnen. Ein Konto kann **bis zu zehn Abonnements** führen, etwa «Energie in Luzern» und «Bioenergie in allen Kantonen». Der Name entsteht automatisch aus der Auswahl.

1. **+ Neues Abonnement** wählen oder bei einem bestehenden **Bearbeiten**.
2. Themen, Kantone, Geschäftstypen und Datenbereiche auswählen.
3. Unten **Abonnement speichern** klicken. Der Dialog schliesst sich und bestätigt das Speichern.

Innerhalb eines Abonnements gelten mehrere Werte derselben Gruppe als Alternativen; verschiedene Gruppen müssen gemeinsam passen. Ein Hauptthema umfasst seine Unterthemen. Ein Abonnement ohne Themen, Kantone und Geschäftstypen ist **pausiert**; eine alleinige Auswahl von Datenbereichen aktiviert es nicht. Mit dem Häkchen **Benachrichtigungen für dieses Abonnement aktiv** lässt es sich auch bewusst pausieren. **Löschen** steht auf jeder Abonnementkarte.

Eine Benachrichtigung genügt, wenn **eines** der aktiven Abonnements passt; passen mehrere – etwa ein Bioenergie-Geschäft aus Luzern bei den beiden Beispielen oben –, kommt trotzdem nur eine Nachricht. Nach jeder Änderung bestätigt eine E-Mail die gespeicherte Auswahl.

Unter **Verfolgte Inhalte** stehen alle mit **☆ Verfolgen** beobachteten Einzelinhalte mit Titel. Ein Klick öffnet den Inhalt, **Verfolgung beenden** entfernt ihn. Verfolgte Inhalte melden sich unabhängig von den Abonnements.

Als Benachrichtigungsziel kann das Anmeldekonto oder eine Auswahl von insgesamt bis zu zehn E-Mail-Adressen dienen. Andere Adressen müssen über einen Bestätigungslink verifiziert werden. Bis zur ersten eigenen Auswahl verwenden bestehende Konten ihre Anmeldeadresse; eine geänderte Auswahl wird mit **Abonnement speichern** übernommen.

**Abonnement speichern**, **Abmelden** und **Alle Benachrichtigungen beenden** bleiben am unteren Rand des Dialogs erreichbar. «Alle Benachrichtigungen beenden» löscht alle Abonnements und verfolgten Inhalte. **Konto löschen** befindet sich am Ende der Verwaltung, entfernt die kontobezogenen Einstellungen und bestätigt die Löschung per E-Mail an die Kontoadresse. Abmelden beendet alle Sitzungen des Kontos, auch auf anderen Geräten, beendet aber keine Abonnements.

## Benachrichtigungen

Relevante neue Inhalte und Änderungen werden nach der täglichen Synchronisierung (Standard 04:30 Uhr) geprüft und per E-Mail zusammengefasst. Technische Metadaten und bestimmte geringfügige Änderungen lösen keine Nachricht aus. Die Zusammenfassung erfolgt pro Nutzer und Geschäft beziehungsweise eigenständigem Inhalt; es gibt keine Garantie auf genau eine tägliche Nachricht.

Ein erfolgreich gespeichertes Abonnement allein erzeugt noch keine parlamentarische Update-Nachricht. Dazu muss eine passende relevante Änderung auftreten. Bei fehlenden Nachrichten hilft die [Fehlerbehebung](../troubleshooting.md).

## Benachrichtigung in der Demo ausprobieren

In der Docker-Demo zeigt die Startseite die Schritte an. Zuerst ein Abonnement mit mindestens einem Thema speichern. Unter **Benachrichtigung testen (Demo)** steht dann ein Thema zur Auswahl. **Testgeschäft erstellen und benachrichtigen** legt ein fiktives neues Geschäft an (Geschäftstyp aus dem Abonnement) und schickt die Benachrichtigung über den regulären Ablauf an das eigene Konto. Die Nachricht erscheint in Mailpit; **Testgeschäft ansehen** öffnet das erzeugte Geschäft. Passt es zu keinem Abonnement, erklärt die Oberfläche den Grund. In einer produktiven Installation gibt es diese Funktion nicht.
