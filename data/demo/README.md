# Demo-Daten

Quelle: [OpenParlData.ch](https://openparldata.ch/), **CC BY 4.0**.
Auszug aus dem lokalen Datenbestand vom **11. Oktober 2026**.

`sample.json.gz` enthält 500 Beispiele pro Dataset sowie zusätzliche
verknüpfte Referenzdaten und die vorhandenen regelbasierten Klassifikationen.
Die Auswahl ist eine Demonstrationsstichprobe, kein vollständiger Datenbestand.
Benutzerkonten, Abonnements, E-Mail-Tokens und Benachrichtigungen sind ausgeschlossen.
E-Mail-Adressen parlamentarischer Personen wurden aus der Stichprobe entfernt.

Entwickler können die Stichprobe mit `python -m scripts.demo.export` aus einer
konfigurierten Quelldatenbank erneuern. Der Export liest die Datenbank ausschliesslich.
