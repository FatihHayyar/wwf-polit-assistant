# Monitoringkonzept

Monitoring kombiniert **neue passende Inhalte** und **Entwicklungen bestehender Inhalte**. Aktive Recherche ist davon getrennt. Die fachliche Grundlage sind Kategorien, Kantone, Keywords, Datenbereiche und die verfügbaren Beziehungen.

## Filterabonnements

Innerhalb einer Filtergruppe gelten Alternativen; verschiedene eingeschränkte Gruppen müssen gemeinsam passen. Elternkategorien schliessen Unterkategorien ein. Bis zu 20 normalisierte, literale Suchbegriffe mit je 1–200 Zeichen werden unterstützt. Leere Dataset-Auswahl umfasst alle Bereiche.

Sind Kategorien, Kantone und Keywords alle leer, pausieren Filterabonnements. Nur Datasets auszuwählen aktiviert sie nicht. Änderungen der allgemeinen Filter löschen nicht automatisch Einzel-Watches.

## Einzel-Watches

Ein Watch bindet sich an Bereich und positive lokale ID. Geschäfts-Watches umfassen relevante zugeordnete Änderungen; Sitzungs-Watches berücksichtigen verfügbare Sitzungsbeziehungen. Gruppen können über ihre Sitzungen zusätzlichen Kontext liefern. Für Interessenbindungen wird keine beliebige direkte Geschäftsbeziehung angenommen.

Die Oberfläche verwaltet Watches im Abonnementdialog. Detailkarten dienen der Recherche. Dokument-Watches verwenden `pk`, weil `source_id` mehrere lokale Zuordnungen besitzen kann.

## Relevanz und Zustellung

Inhaltspersistenz, Relevanzprüfung, Filterabgleich und Versand sind separate Schritte. Eine technisch geänderte Zeile muss keine Benachrichtigung erzeugen. Bei erfolgreichem Gesamtsync werden ausstehende Nachrichten nach erneuter Konto-/Abonnementprüfung verarbeitet. Bei Fehlern bleiben sie ausstehend.

Details zur bereits implementierten Policy und Wiederaufnahme stehen im [technischen Monitoring-Leitfaden](../monitoring.md). Die [API](../api.md) beschreibt die Verwaltung; das [Benutzerhandbuch](../06-handover/user-guide.md) erklärt den Ablauf.
