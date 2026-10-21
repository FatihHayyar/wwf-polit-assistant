# Technologieentscheidungen

| Baustein | Entscheidung und Begründung | Grenze |
|---|---|---|
| Python/FastAPI | Nähe zur WWF-Python-Landschaft und API-zentrierter MVP | Kein vergleichender Framework-Benchmark |
| PostgreSQL | Relationaler Bestand mit Beziehungen und Sync-Koordination | Schema-/Indexmigrationen und Betrieb benötigen Prüfung |
| SQLAlchemy/Psycopg | Modelle, Datenzugriff und Importpfade | ORM ersetzt keine Datenintegritätsprüfung |
| Alembic | Versionierte Schemaänderungen | Migration kann auf grossen Tabellen lange dauern |
| Docker | Paketierung und reproduzierbare Demo | Lokale Compose-Dateien sind keine Produktionsplattform |
| HTML/CSS/JavaScript | Einfache, von FastAPI ausgelieferte Oberfläche | Streamlit wurde als vorhandenes WWF-Werkzeug genannt, nicht als Pflicht |
| OpenAPI | Generierte Schnittstellenbeschreibung | Nur installierten Codevertrag prüfen, keine fachliche Abnahme |
| Regeln statt LLM | Regelbasierter MVP gemäss Auftrag, prüfbare Evidenz; lokale Ollama-Versuche erreichten die Regelgenauigkeit nicht | Recall 0.667 auf unabhängigem Prüfset; kein AI-Dienst implementiert, Schnittstellen vorhanden |
| Regelbasierte Fragenerkennung | Dialogorientierte Abfrage ohne Modellbetrieb, nutzt dieselben Themenregeln | Versteht nur bekannte Muster; Erkanntes wird angezeigt |
| JSON-Listen für Abonnementfilter | Ein Abonnement ist eine Zeile; einfache Migration und Abfrage bei höchstens zehn Abonnements je Konto | Keine Fremdschlüssel auf Kategorien; Ersetzungen über `replaces` |
| SMTP | E-Mail als vereinbarter Benachrichtigungskanal | Organisationsprovider und Limits offen |

Die ursprünglichen M365- und Java-Ansätze werden als Projektkontext dokumentiert. Der aktuelle Code enthält keinen Java-Service und keine M365-/Copilot-Integration. [Entscheidungsregister](../01-project-management/decision-log.md) und [Azure-Abstimmung](azure-integration.md) enthalten weitere Folgen.
