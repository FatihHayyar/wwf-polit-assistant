# WWF Polit-Assistant

A political monitoring assistant for WWF Switzerland based on Swiss parliamentary open data.

The project is developed as part of the **Wirtschaftsprojekt (WIPRO)** in the BSc Informatik program at Hochschule Luzern (HSLU).

## Project Goal

The goal of the project is to build an MVP that helps WWF Switzerland identify and monitor politically relevant parliamentary activities.

The system integrates data from OpenParlData and prepares it for:

- structured political data search
- WWF-specific topic classification
- canton-based monitoring
- keyword-based monitoring
- monitoring of new and updated parliamentary items
- email subscriptions and notifications
- a documented REST API
- a simple user interface

The architecture is designed so that AI-based functionality can be added later without making AI a dependency of the initial MVP.

## Current Status

The project is currently under active development.

The following foundation is already available:

- Python / FastAPI project structure
- PostgreSQL database
- Docker-based local database environment
- SQLAlchemy database integration
- Alembic database migrations
- OpenAPI / Swagger through FastAPI
- OpenParlData bulk export downloader
- snapshot-based raw data storage
- download validation using the OpenParlData manifest
- PostgreSQL raw staging layer
- streaming gzip import using PostgreSQL `COPY`
- row-count validation during bootstrap

The initial OpenParlData snapshot currently used for development is:

```text
2026-10-06
```

The selected bootstrap datasets contain approximately:

```text
126 files
5.91 GB compressed data
3,098,065 records
```

## Architecture

The MVP uses a deliberately simple architecture that can later be integrated into WWF's Azure environment.

```text
OpenParlData
     |
     | Bulk Export / REST API
     v
+-------------------------+
| OpenParlData Integration|
+-------------------------+
     |
     | Initial Bootstrap
     v
+-------------------------+
| Raw Snapshot Storage    |
| NDJSON.GZ               |
+-------------------------+
     |
     | Streaming Import
     v
+-------------------------+
| PostgreSQL Raw Staging  |
+-------------------------+
     |
     | Normalize / Process
     v
+-------------------------+
| Application Data Model  |
+-------------------------+
     |
     +-------------------+
     |                   |
     v                   v
Classification       Monitoring
     |                   |
     +---------+---------+
               |
               v
        Search / REST API
               |
        +------+------+
        |             |
        v             v
       UI       Notifications
```

Initial bootstrap and ongoing synchronization are intentionally separated.

### Initial Bootstrap

The initial bootstrap follows this process:

```text
OpenParlData Bulk Export
        |
        v
Parallel Download
        |
        v
Raw NDJSON.GZ Snapshot
        |
        v
PostgreSQL COPY
        |
        v
Raw Staging
        |
        v
Normalization
        |
        v
Relations / Indexes
        |
        v
Classification
        |
        v
Validation
```

Network download and data processing are separated so that processing errors do not require downloading the complete OpenParlData snapshot again.

### Incremental Synchronization

After the initial bootstrap, regular updates will use a different pipeline:

```text
OpenParlData API
        |
        v
Candidate Changes
        |
        v
Fingerprint Comparison
        |
        v
Actual Changes
        |
        v
Database Upsert
        |
        v
Classification / Monitoring
        |
        v
Subscription Matching
        |
        v
Notifications
```

Remote `updated_at` timestamps are not assumed to represent meaningful content changes. Local fingerprints will be used to distinguish actual changes from upstream metadata or bulk-update operations.

## OpenParlData Data

The current bootstrap includes:

| Dataset | Records |
|---|---:|
| Bodies | 2,411 |
| Persons | 26,864 |
| Memberships | 121,456 |
| Groups | 8,885 |
| Interests | 30,343 |
| Affairs | 325,691 |
| Meetings | 33,670 |
| Agendas | 422,971 |
| Events | 915,238 |
| Votings | 77,061 |
| Docs | 907,736 |
| Texts | 225,739 |
| **Total** | **3,098,065** |

Individual parliamentary votes are intentionally not included in the initial full mirror because the OpenParlData export contains more than 75 million individual vote records.

Aggregate voting information is included through the `votings` dataset. Individual votes can later be retrieved on demand when required.

## Technology Stack

### Backend

- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy
- Psycopg
- Alembic

### Database

- PostgreSQL 17

### Infrastructure

- Docker
- Docker Compose

### API

FastAPI automatically provides an OpenAPI specification and interactive Swagger documentation.

During local development:

```text
http://localhost:8000/docs
```

## Project Structure

```text
polit-assistant-python/
|
+-- app/
|   +-- api/
|   +-- classification/
|   +-- core/
|   +-- db/
|   +-- integrations/
|   |   +-- openparldata/
|   +-- models/
|   +-- monitoring/
|   +-- repositories/
|   +-- services/
|   +-- main.py
|
+-- data/
|   +-- raw/
|
+-- migrations/
|
+-- scripts/
|   +-- bootstrap/
|       +-- download_openparldata.py
|       +-- inspect_exports.py
|       +-- import_raw.py
|
+-- tests/
|
+-- docker-compose.yml
+-- pyproject.toml
+-- .env.example
+-- README.md
```

## Local Development

### Requirements

The local development environment requires:

- Python 3.13+
- Docker
- Docker Compose

### Python Environment

Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
```

```powershell
.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```powershell
pip install -e .
```

### Environment Configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

The local development configuration uses a PostgreSQL instance exposed on port `5433`.

### Start PostgreSQL

```powershell
docker compose up -d
```

Check the container:

```powershell
docker compose ps
```

### Database Migrations

Apply all migrations:

```powershell
python -m alembic upgrade head
```

### Start the API

```powershell
python -m uvicorn app.main:app --reload
```

Health endpoint:

```text
GET /health
```

Swagger UI:

```text
http://localhost:8000/docs
```

## OpenParlData Bootstrap

The initial data load uses the official OpenParlData bulk exports.

### Download

Show the planned download without downloading files:

```powershell
python scripts/bootstrap/download_openparldata.py --dry-run
```

Download and verify the selected datasets:

```powershell
python scripts/bootstrap/download_openparldata.py --workers 6
```

Already completed files are detected using their expected manifest size and skipped.

Raw files are stored by snapshot:

```text
data/raw/<snapshot>/
```

For example:

```text
data/raw/2026-10-06/
```

Raw exports are intentionally excluded from Git.

### Inspect Export Structure

The structure of downloaded OpenParlData records can be inspected without modifying the files or database:

```powershell
python scripts/bootstrap/inspect_exports.py
```

### Raw PostgreSQL Import

Import one dataset:

```powershell
python scripts/bootstrap/import_raw.py bodies
```

Import all selected bootstrap datasets:

```powershell
python scripts/bootstrap/import_raw.py all
```

The importer:

- streams compressed `.ndjson.gz` files
- does not extract the complete files to disk
- uses PostgreSQL `COPY`
- stores the original OpenParlData record as JSONB
- validates imported row counts against the export manifest
- skips datasets that are already completely imported
- keeps completed datasets when a later dataset fails

The raw staging layer is an intermediate bootstrap mechanism. It is not intended to be the final application data model.

## Planned Application Data Model

The normalized application model will cover the parliamentary entities required by the WWF use cases, including:

```text
Bodies
  |
  +-- Persons
  |
  +-- Memberships
  |
  +-- Groups
  |
  +-- Affairs
  |     |
  |     +-- Texts
  |     +-- Documents
  |     +-- Events
  |     +-- Votings
  |
  +-- Meetings
        |
        +-- Agendas
             |
             +-- Affairs
```

Relations will be based on the identifiers supplied by OpenParlData rather than inferred from textual content.

## WWF Classification

The classification system will be configurable rather than hard-coded to a permanent topic list.

The initial focus will be on a limited number of WWF-relevant topics and subcategories. The configuration should allow topics, subcategories and keywords to be adjusted as the taxonomy is refined together with WWF experts.

Examples discussed for the area **Energy & Climate** include:

- renewable heating and cooling
- renewable electricity generation
- building efficiency
- electric mobility
- public-sector leadership
- data centres
- large energy consumers

Rule-based classification is the MVP approach. The architecture should allow later AI-assisted classification without requiring it for the initial system.

## Monitoring and Subscriptions

Monitoring is intended to go beyond simple topic subscriptions.

Planned subscription criteria include combinations of:

- canton
- WWF classification
- subcategory
- individual keywords
- parliamentary content type

Users should also be able to follow existing parliamentary items and receive notifications when meaningful changes occur.

Relevant monitored entities may include:

- Affairs
- Meetings
- Agendas
- Documents
- Texts
- Events
- Votings

Change detection will use local state and fingerprints where appropriate to avoid generating notifications solely because an upstream timestamp changed.

## Search

The MVP will provide structured search and filtering over normalized parliamentary data.

PostgreSQL is intended to provide the initial search capabilities, including full-text search where required. Additional search infrastructure such as Elasticsearch is not required for the initial MVP unless a concrete requirement justifies it.

## Azure Compatibility

The solution is designed with future integration into WWF's Azure environment in mind.

The architecture therefore aims to remain:

- container-friendly
- configuration-driven
- stateless at the API layer
- PostgreSQL-based
- compatible with standard Azure deployment approaches
- free of unnecessary infrastructure dependencies

Additional infrastructure components will only be introduced when there is a clear technical requirement and compatibility with the WWF environment has been considered.

## AI

AI is not required for the first working MVP.

The initial system focuses on:

- reliable OpenParlData integration
- structured data
- classification
- search
- monitoring
- subscriptions
- notifications

Possible later extensions include:

- semantic search
- natural-language queries
- summarization
- AI-assisted classification
- conversational access
- retrieval-augmented generation

This separation allows the core political data platform to remain useful even without an AI service.

## Data Source

Parliamentary data is provided by OpenParlData.

Source attribution:

> Source: OpenParlData.ch

OpenParlData data is provided under the CC BY 4.0 license.

## Project Context

This project is developed for **WWF Switzerland** as part of the HSLU BSc Informatik Wirtschaftsprojekt.

The MVP is intended as a technically sound prototype and foundation for further development rather than a production-ready final platform.

## License

A project-specific software license has not yet been defined.