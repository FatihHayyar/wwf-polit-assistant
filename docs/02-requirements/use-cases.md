# Anwendungsfälle

| ID | Person / Ziel | Ablauf | Erwartung |
|---|---|---|---|
| UC01 | Recherche ohne Konto | Bereich wählen, Thema/Kanton/Keyword filtern, Detail öffnen | Passende Ergebnisse und verfügbare Quellen/Beziehungen |
| UC02 | Neue relevante Inhalte abonnieren | Konto bestätigen, kombinierte Filter speichern | Passende relevante Änderungen auswählen, andere ausschliessen |
| UC03 | Bestehendes Geschäft beobachten | In Abonnementverwaltung Bereich und lokale ID hinzufügen | Relevante Updates einschliesslich verfügbarer verknüpfter Inhalte |
| UC04 | Sitzung verstehen | Sitzung und verknüpfte Traktanden/Unterlagen öffnen | Zusammenhang korrekt, fehlende Beziehungen nicht erfunden |
| UC05 | Weitere Datenbereiche nutzen | Abstimmungen, Gruppen und Interessen recherchieren | Eigenständige Listen und vorhandener Kontext |
| UC06 | Empfänger verwalten | Eigene und fremde Adresse hinterlegen, fremde bestätigen | Monitoring nur an bestätigte Ziele |
| UC07 | Benachrichtigungen beenden | Filter pausieren, Watches entfernen oder alles beenden | Keine weiterhin aktive unbeabsichtigte Auswahl |
| UC08 | Kontodaten entfernen | Konto löschen | Kontobezogene Einstellungen entfernt |
| UC09 | Betrieb prüfen | Job starten/status prüfen, Fehler fortsetzen | Checkpoints nachvollziehbar, kein paralleler Runner |

Voraussetzungen, konkrete IDs, Datenstand und Ergebnisse werden in der [Testplanung](../05-testing/test-plan.md) und im [Evaluationsbericht](../07-academic/evaluation-report.md) festgehalten. Für künstliche Updatefälle eine isolierte Datenbank und Mailpit verwenden. Bei Dokumenten ist die lokale `pk` gemeint, nicht die externe `source_id`.
