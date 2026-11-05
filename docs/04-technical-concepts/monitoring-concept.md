# Monitoringkonzept

Monitoring kombiniert **neue passende Inhalte** und **Entwicklungen bestehender Inhalte**. Aktive Recherche ist davon getrennt. Die fachliche Grundlage sind Kategorien, Kantone, Geschäftstypen, Datenbereiche und die verfügbaren Beziehungen.

## Abonnements

Ein Konto führt bis zu zehn Abonnements; Namen werden aus den Filtern erzeugt. Innerhalb eines Abonnements gelten in einer Filtergruppe Alternativen; verschiedene eingeschränkte Gruppen müssen gemeinsam passen. Zwischen den Abonnements gilt ODER: Ein passendes aktives Abonnement genügt, und mehrere passende Abonnements erzeugen trotzdem nur eine Benachrichtigung. Elternkategorien schliessen Unterkategorien ein. Der Geschäftstyp gilt auch für verknüpfte Datensätze über ihr Geschäft. Leere Dataset-Auswahl umfasst alle Bereiche. Individuelle Suchbegriffe gehören zur Recherche, nicht zu Abonnements (Entscheid D15).

Sind Kategorien, Kantone und Geschäftstypen alle leer oder ist das Abonnement als inaktiv markiert, ist es pausiert. Nur Datasets auszuwählen aktiviert es nicht. Änderungen oder Löschungen von Abonnements entfernen keine Einzel-Watches.

## Einzel-Watches

Ein Watch bindet sich an Bereich und positive lokale ID. Geschäfts-Watches umfassen relevante zugeordnete Änderungen; Sitzungs-Watches berücksichtigen verfügbare Sitzungsbeziehungen. Gruppen können über ihre Sitzungen zusätzlichen Kontext liefern. Für Interessenbindungen wird keine beliebige direkte Geschäftsbeziehung angenommen.

Die Detailansicht bietet **☆ Verfolgen** zum An- und Abschalten; der Abonnementdialog listet Watches mit Titel und entfernt sie. Dokument-Watches verwenden `pk`, weil `source_id` mehrere lokale Zuordnungen besitzen kann.

## Relevanz und Zustellung

Inhaltspersistenz, Relevanzprüfung, Filterabgleich und Versand sind separate Schritte. Eine technisch geänderte Zeile muss keine Benachrichtigung erzeugen. Bei erfolgreichem Gesamtsync werden ausstehende Nachrichten nach erneuter Konto-/Abonnementprüfung verarbeitet. Bei Fehlern bleiben sie ausstehend.

Details zur bereits implementierten Policy und Wiederaufnahme stehen im [technischen Monitoring-Leitfaden](../monitoring.md). Die [API](../api.md) beschreibt die Verwaltung; das [Benutzerhandbuch](../06-handover/user-guide.md) erklärt den Ablauf.
