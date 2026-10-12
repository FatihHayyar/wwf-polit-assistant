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
| Regeln statt LLM | Regelbasierter MVP gemäss Auftrag, prüfbare Evidenz | Fachgüte noch messen; kein AI-Dienst implementiert |
| SMTP | E-Mail als vereinbarter Benachrichtigungskanal | Organisationsprovider und Limits offen |

Die ursprünglichen M365- und Java-Ansätze werden als Projektkontext dokumentiert. Der aktuelle Code enthält keinen Java-Service und keine M365-/Copilot-Integration. [Entscheidungsregister](../01-project-management/decision-log.md) und [Azure-Abstimmung](azure-integration.md) enthalten weitere Folgen.
