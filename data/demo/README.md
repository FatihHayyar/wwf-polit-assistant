# Demo-Daten

Quelle: [OpenParlData.ch](https://openparldata.ch/), **CC BY 4.0**.
Auszug aus dem lokalen Datenbestand vom **18. November 2026**.

`sample.json.gz` enthält alle Geschäfte, Traktanden, Sitzungen, Abstimmungen,
Ereignisse, Dokumente und Texte des **letzten Jahres** (ab 18. November 2025,
nach dem Datum des jeweiligen Eintrags), rund 200'000 Einträge. Von Gruppen und
Interessenbindungen, die kein solches Datum haben, sind die 500 neuesten
enthalten. Zusätzlich kommen je Unterthema die drei neuesten klassifizierten
Einträge hinzu, sodass Themenfilter in jedem Bereich Treffer liefern, soweit der
vollständige Bestand solche Einträge enthält. Dazu kommen verknüpfte
Referenzdaten und die vorhandenen regelbasierten Klassifikationen.

Dokumenttexte sind auf die ersten 2'000 Zeichen gekürzt, damit die Datei unter
50 MB bleibt. Die Volltextsuche in Dokumenten erfasst deshalb nur deren Anfang.

Die Auswahl ist eine Demonstrationsstichprobe, kein vollständiger Datenbestand.
Benutzerkonten, Abonnements, E-Mail-Tokens, Benachrichtigungen und fiktive
Demo-Geschäfte sind ausgeschlossen. E-Mail-Adressen parlamentarischer Personen
wurden aus der Stichprobe entfernt.

Entwickler können die Stichprobe mit `python -m scripts.demo.export` aus einer
konfigurierten Quelldatenbank erneuern. Der Export liest die Datenbank ausschliesslich.
