# Azure-Integration

**Status: vorbereitet, nicht deployt oder validiert.** Python, Docker, PostgreSQL, OpenAPI und Umgebungsvariablen sind Anschlussbausteine. Kein konkreter Azure-Dienst oder Organisationszugang ist als beschlossen eingetragen.

| Bereich | Abstimmung / Prüfung |
|---|---|
| API | Container-Hosting, HTTPS, Netzwerk und Skalierung |
| PostgreSQL | Zielservice, Version, TLS, Netzfreigaben und Restore |
| Scheduler | Eine verantwortliche Jobinstanz, Laufzeit und Zeitzone |
| Jobzustand | Gemeinsamer persistenter Speicher für lokale Manifeste/Exporte oder anderes Statussystem |
| Secrets | Verwaltung von DB-, JWT-, Sync-, SMTP- und optional OAuth-Werten |
| Authentifizierung | Organisatorische Anforderungen; Google ist kein Entra-SSO |
| E-Mail | Zugelassener Provider, Absender, Limits und ausgehende Verbindung |
| Monitoring | Letzter erfolgreicher Sync, Fehleralarmierung, zentrale Logs |
| Datenschutz | Empfängeradressen, Zugriff, Aufbewahrung und Kontolöschung |

Die API kann mit `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` aus dem Image starten. Dessen Standardbefehl ist der Scheduler. Migrationen vor der neuen Anwendungsversion koordiniert ausführen. Lokaler `/health`-Erfolg belegt nur die DB-Verbindung und ersetzt keinen Cloudtest.

Abschlussnachweis: tatsächliche Testbereitstellung, erfolgreiche API-/Job-/SMTP-Prüfung, Fehler-/Wiederaufnahmeszenario und Wiederherstellung einer Sicherung. Siehe [Deployment](../06-handover/deployment-guide.md) und [Betrieb](../06-handover/operations-guide.md).
