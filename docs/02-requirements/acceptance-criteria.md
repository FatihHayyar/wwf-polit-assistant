# Akzeptanzkriterien

Die folgenden Kriterien konkretisieren die Anforderungen. Sie sind Prüfdefinitionen und keine bereits erteilte WWF-Abnahme. Numerische Leistungsschwellen und Klassifikationsziele werden vor Messung vereinbart.

| ID | Bezug | Kriterium | Nachweisart |
|---|---|---|---|
| AC01 | R01/R02 | Bekannte Quellbeispiele werden korrekt abgebildet; Beziehungen nachvollziehbar | Mappingtests plus unabhängige Quellstichprobe |
| AC02 | R01 | Fehlerhafte Stufe meldet Ursache; abgeschlossene Batches bleiben fortsetzbar | Fehlerszenario und Wiederanlauf |
| AC03 | R03/R16 | Freigegebene Themen, positive/negative Beispiele und regelbasierte Evidenz | WWF-Freigabe und annotierte Stichprobe |
| AC04 | R04/R10 | Kombinierte Recherche liefert die erwarteten Beispieltreffer | API/UI und WWF-Aufgabendurchlauf |
| AC05 | R05/R06 | Passende relevante Änderung erreicht die Auswahl, unpassende nicht | Matcher-/Policytests und kontrollierte Integration |
| AC06 | R07 | Bestehender Watch erhält relevante verbundene Entwicklung | Reproduzierbarer Updatefall |
| AC07 | R08/R17 | Verifizierte Ziele erhalten Nachrichten; unbestätigte nicht | Mailpit-Test plus Organisations-SMTP-Prüfung |
| AC08 | R09 | OpenAPI entspricht dem übergebenen Stand; geschützte Routen bleiben geschützt | Generierte Spezifikation und Zugriffsprüfung |
| AC09 | R10 | Lange Details und Formulare bleiben auf Desktop/Mobil bedienbar | Browserdurchlauf und Praxisfeedback |
| AC10 | R11 | Neue Umgebung startet anhand Dokumentation, Grenzen sind bekannt | Unabhängiger Demostart und Handover |
| AC11 | R12 | Tatsächliche WWF-Beobachtung, Abweichungen und Entscheid dokumentiert | Abnahmeformular; derzeit offen |
| AC12 | R14 | Container, Schnittstellen, Konfiguration und Betriebsanforderungen für WWF dokumentiert | Technischer Handover; tatsächlicher Azure-Betrieb ist eine spätere WWF-Integrationsaufgabe |
| AC13 | R19 | Mehrere Abonnements werden unabhängig gespeichert; jedes passende aktive Abonnement löst eine (einzige) Nachricht aus, pausierte nicht | API- und Matchertests, Demo-Durchlauf |
| AC14 | R20 | Beispielfragen in vier Sprachen ergeben die erwarteten Filter; Erkanntes ist sichtbar | Interpretertests, Browser-Durchlauf |

Ein Implementierungs-Issue kann geschlossen sein, während das zugehörige fachliche oder betriebliche Prüf-Issue offen bleibt. Dieses Vorgehen verhindert eine pauschale Erfolgserklärung durch technischen Abschluss.
