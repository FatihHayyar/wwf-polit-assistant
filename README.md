# WWF Polit-Assistant

A political monitoring assistant for WWF Switzerland based on Swiss parliamentary open data.

The project is developed as part of the **Wirtschaftsprojekt (WIPRO)** in the BSc Informatik program at Hochschule Luzern (HSLU).

## Project Goal

The goal of the project is to build a functional MVP that helps WWF Switzerland identify, search and monitor politically relevant parliamentary activities.

The system integrates data from OpenParlData and prepares it for:

- structured political data search
- WWF-specific topic classification
- canton-based filtering and monitoring
- keyword-based filtering and monitoring
- monitoring of new and updated parliamentary items
- email subscriptions and notifications
- a documented REST API
- a simple user interface

The architecture is designed so that AI-based functionality can be added later without making AI a dependency of the initial MVP.

---

## Current Status

The project is currently under active development.

The data integration, normalization, WWF classification and first search/detail API foundation are implemented.

The following components are currently available:

- Python / FastAPI backend
- PostgreSQL database
- Docker-based local database environment
- SQLAlchemy database integration
- Alembic database migrations
- OpenAPI / Swagger documentation through FastAPI
- OpenParlData bulk export downloader
- snapshot-based raw data storage
- download validation using the OpenParlData manifest
- PostgreSQL raw staging layer
- streaming gzip import using PostgreSQL `COPY`
- normalized parliamentary application data
- WWF rule-based classification
- affair search and filtering
- pagination
- category and subcategory discovery API
- canton discovery API
- parliamentary affair type discovery API
- affair detail API
- parliamentary text retrieval for individual affairs
- official-source links for parliamentary affairs

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

### Current Affair Dataset

```text
325,691 parliamentary affairs
```

All imported affairs have been processed by the current WWF classification pipeline.

Current classification coverage:

```text
Affairs:                  325,691
Classified affairs:       325,691
Missing classifications:        0
Classification rows:      325,824
Evidence rows:              7,111
Fallback rows:            320,121
```

The current rule-based classification result is treated as a stable MVP baseline while development continues on search, monitoring, subscriptions and the user interface.

---

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
     v
+-------------------------+
| Raw Snapshot Storage    |
| NDJSON.GZ               |
+-------------------------+
     |
     v
+-------------------------+
| PostgreSQL Raw Staging  |
+-------------------------+
     |
     v
+-------------------------+
| Normalized Data Model   |
+-------------------------+
     |
     v
+-------------------------+
| WWF Classification      |
+-------------------------+
     |
     v
+-------------------------+
| Affair Query Service    |
+-------------------------+
     |
     +--------------------+
     |                    |
     v                    v
 Search REST API     Subscription Matcher
     |                    |
     v                    v
    UI               Monitoring
                          |
                          v
                    Notifications
```

Initial bootstrap and ongoing synchronization are intentionally separated.

---

## Initial Bootstrap

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
WWF Classification
        |
        v
Validation
```

Network download and data processing are separated so that processing errors do not require downloading the complete OpenParlData snapshot again.

---

## Incremental Synchronization

After the initial bootstrap, regular updates are intended to use a different pipeline:

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

Remote `updated_at` timestamps should not automatically be interpreted as meaningful content changes.

Local state and fingerprints can be used to distinguish actual changes from upstream metadata updates or bulk-update operations.

Incremental synchronization and automatic monitoring are not yet complete.

---

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

Aggregate voting information is included through the `votings` dataset.

Individual votes can later be retrieved on demand when required.

---

## Normalized Application Data

The OpenParlData raw staging layer is transformed into a normalized application model.

Relevant entities include:

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

Relations are based on identifiers supplied by OpenParlData rather than inferred from textual content.

This normalized model is used by the API, WWF classification, search and future monitoring components.

---

## WWF Classification

The MVP uses a configurable rule-based WWF classification system.

The classification pipeline has been executed over all currently imported parliamentary affairs.

```text
325,691 / 325,691 affairs classified
```

The classification system supports:

- hierarchical WWF topics
- subcategories
- multilingual rules
- rule weights
- classification scores
- confidence values
- classification evidence
- fallback classification

### Current Topic Structure

The current taxonomy contains the following main areas:

```text
Climate & Energy
Biodiversity & Landscape
Sustainable Economy & Consumption
Environment & Policy
Other
```

### Climate & Energy

Current subcategories include:

- renewable electricity
- renewable heating and cooling
- building efficiency
- sustainable mobility
- grids and storage
- fossil energy
- large consumers and data centres

### Biodiversity & Landscape

Current subcategories include:

- species and habitats
- protected areas
- forest
- waters
- soil and spatial planning
- agriculture and biodiversity

### Sustainable Economy & Consumption

Current subcategories include:

- circular economy
- resources and raw materials
- sustainable finance
- companies and supply chains
- food and consumption

### Environment & Policy

Current subcategories include:

- environmental law
- public sector
- environmental funding
- international environment
- environmental research and education

### Fallback Classification

Affairs that do not match a specific WWF topic receive the fallback category:

```text
other
```

The fallback category ensures that every imported affair has a classification result.

Rule-based classification is the MVP approach.

The architecture allows AI-assisted classification to be introduced later without replacing the current deterministic classification pipeline.

---

## Search API

The first affair search API is implemented.

Main endpoint:

```text
GET /api/v1/affairs
```

The endpoint returns a paginated affair list.

Default page size:

```text
10 affairs
```

Results are currently ordered by newest parliamentary affairs first.

### Supported Filters

The search API currently supports:

- keyword
- canton
- WWF main category
- WWF subcategory
- year
- month
- parliamentary affair type
- pagination

Filters can be combined.

For example:

```text
GET /api/v1/affairs?q=Photovoltaik&canton=ZH&category=climate_energy&year=2026&page=1
```

Filter combinations use AND semantics.

For multilingual keyword fields, matching uses OR semantics across the supported title fields.

---

## Keyword Search

The current MVP keyword search covers:

- German title
- French title
- Italian title
- German long title
- French long title
- Italian long title
- affair number

PostgreSQL `pg_trgm` indexes are used for efficient partial title matching.

Full parliamentary-text and document-content search is intentionally deferred.

A first direct `%ILIKE%` approach over large text/document content was not sufficiently efficient for the dataset size.

A later implementation should use an appropriate PostgreSQL full-text search and indexing strategy.

---

## Canton Filtering

Affairs are connected to parliamentary bodies.

Canton filtering therefore uses:

```text
affairs.body_id
        |
        v
bodies.id
        |
        v
bodies.canton_key
```

This is necessary because an affair's `body_key` is not guaranteed to be a canton code.

Municipal and other parliamentary bodies can have different body identifiers while still belonging to a canton.

---

## WWF Topic Filtering

The API supports hierarchical WWF filtering.

When a main category is selected without a subcategory:

```text
Main category
+
all direct subcategories
```

are included.

When a subcategory is selected:

```text
exact selected subcategory
```

is used.

This allows the frontend to provide:

```text
Hauptthema
    |
    +-- Unterthema
```

dropdowns.

---

## Affair Type Filtering

The API supports filtering by harmonized parliamentary affair type.

Examples may include:

```text
Motion
Postulat
Interpellation
Anfrage
Regierungsgeschäft
```

The filter is case-insensitive.

For example:

```text
GET /api/v1/affairs?affair_type=motion
```

can match:

```text
Motion
```

Available affair types are read from the database instead of being hard-coded in the frontend.

---

## Affair Detail API

Individual affairs can be retrieved through:

```text
GET /api/v1/affairs/{affair_id}
```

The detail response can contain:

- affair number
- multilingual titles
- long titles
- affair type
- state, where available
- begin date
- end date
- active status
- parliamentary body
- canton
- WWF classifications
- classification confidence and score
- parliamentary texts
- official source URL

Example:

```text
GET /api/v1/affairs/340682
```

The API retrieves parliamentary texts only for the selected affair.

It does not scan the complete text or document datasets when loading an affair detail page.

This makes detail retrieval independent from the later full-text search implementation.

---

## Planned Affair Detail UI

The user interface is intended to show only essential information on the main search page.

Each page will contain up to 10 affairs.

A user can select an affair to open its detail view.

The detail page is intended to provide:

```text
Back to overview

Affair title
Affair number

Affair type
Parliament / body
Canton
Date
WWF topic / subcategory

Parliamentary text preview

[Read more]

[Open original source]
```

For long parliamentary texts, the frontend can initially display only a preview.

The user can then expand the complete text using:

```text
Weiterlesen
```

and optionally collapse it again.

If no parliamentary text is available, the official source URL can still be provided.

Parliamentary texts may contain HTML markup from the source system. The frontend must sanitize such content before rendering it as HTML.

---

## Supporting API Endpoints

### Health

```text
GET /health
```

The endpoint verifies that the API and PostgreSQL connection are available.

### Categories

```text
GET /api/v1/categories
```

Returns active WWF main categories and their subcategories.

The fallback `other` category is not intended as a normal search dropdown option.

### Cantons

```text
GET /api/v1/cantons
```

Returns canton codes currently available through parliamentary bodies.

### Affair Types

```text
GET /api/v1/affair-types
```

Returns harmonized affair types currently available in the database.

This allows the frontend to populate filters dynamically instead of maintaining hard-coded lists.

---

## State / Status Filtering

The normalized affair model contains a harmonized state field.

However, current OpenParlData coverage for this field is very limited.

Current data:

```text
Total affairs:        325,691
Affairs with state:       278
Affairs without state: 325,413
```

Available harmonized states currently include:

```text
Abgeschlossen
Eingereicht
Traktandiert
```

Because the field is populated for only a very small fraction of the dataset, state filtering is not currently intended as a primary MVP user-interface filter.

The field remains available in the data model and can be reconsidered if future OpenParlData synchronization provides better coverage.

---

## Pagination

Affair search uses server-side pagination.

Current page size:

```text
10
```

The API response contains:

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 0,
    "total_pages": 0
  }
}
```

The frontend can therefore implement previous/next navigation without loading the complete affair dataset.

---

## Monitoring and Subscriptions

Monitoring and subscriptions are the next major backend phase.

The intended subscription model should support combinations of:

- canton
- WWF classification
- WWF subcategory
- individual keywords
- parliamentary affair type

The same filter logic used by affair search should be reusable by subscription matching.

This avoids maintaining separate search and subscription semantics.

### Planned Email-Based Subscription Flow

The planned MVP user flow does not require a traditional username/password account.

A user can enter an email address to subscribe to WWF monitoring channels or saved filter combinations.

The intended flow is:

```text
User selects topic / filters
        |
        v
Subscribe
        |
        v
Enter email address
        |
        v
Activation email
        |
        v
Activation link
        |
        v
Email verified
        |
        v
Manage subscriptions
```

After successful email verification, the user should remain verified for the current session.

A verified email address can have multiple subscriptions.

Examples:

```text
Subscription 1
Canton: ZH
WWF Topic: Climate & Energy
Keyword: Photovoltaik

Subscription 2
Canton: BE
WWF Topic: Biodiversity & Landscape

Subscription 3
Affair Type: Motion
WWF Subcategory: Sustainable Mobility
```

Users should be able to:

- add subscriptions
- remove individual subscriptions
- change existing subscriptions
- manage multiple monitoring channels
- unsubscribe completely from the system

If an email address is already registered, the application should inform the user appropriately instead of creating duplicate user identities.

If an email address is not registered when attempting account/subscription management, the application should also communicate that state clearly.

Email verification and subscription management are planned work and are not yet implemented.

---

## Monitoring Existing Affairs

Subscriptions are not limited to discovering new matching affairs.

The system should also support monitoring already known parliamentary objects for meaningful updates.

Relevant monitored entities may include:

- Affairs
- Meetings
- Agendas
- Documents
- Texts
- Events
- Votings

The intended monitoring flow is:

```text
OpenParlData update
        |
        v
Local synchronization
        |
        v
Change detection
        |
        +----------------------+
        |                      |
        v                      v
New affair              Existing affair changed
        |                      |
        v                      v
Subscription match      Monitoring match
        |                      |
        +-----------+----------+
                    |
                    v
              Notification
```

Change detection should use local state and fingerprints where appropriate to avoid notifications caused only by irrelevant upstream timestamp changes.

---

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

---

## Project Structure

```text
polit-assistant-python/
|
+-- app/
|   +-- api/
|   |   +-- routes/
|   |
|   +-- classification/
|   +-- core/
|   +-- db/
|   +-- integrations/
|   |   +-- openparldata/
|   |
|   +-- models/
|   +-- monitoring/
|   +-- repositories/
|   +-- schemas/
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

---

## Local Development

### Requirements

The local development environment requires:

- Python 3.13+
- Docker
- Docker Compose

### Python Environment

Create a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Install project dependencies:

```powershell
pip install -e .
```

---

## Environment Configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

The local development configuration uses a PostgreSQL instance exposed on port:

```text
5433
```

---

## Start PostgreSQL

```powershell
docker compose up -d
```

Check the container:

```powershell
docker compose ps
```

---

## Database Migrations

Apply all migrations:

```powershell
python -m alembic upgrade head
```

---

## Start the API

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

---

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

---

## Inspect Export Structure

The structure of downloaded OpenParlData records can be inspected without modifying the files or database:

```powershell
python scripts/bootstrap/inspect_exports.py
```

---

## Raw PostgreSQL Import

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

The raw staging layer is an intermediate bootstrap mechanism.

Application queries use the normalized data model.

---

## Search Performance

The parliamentary dataset contains hundreds of thousands of affairs and large document/text collections.

Search implementation therefore needs to avoid unindexed scans over large text fields.

Current title-based partial search uses PostgreSQL trigram indexing.

The PostgreSQL extension used is:

```text
pg_trgm
```

Trigram GIN indexes are used for multilingual affair title and long-title fields.

Full parliamentary-content search is planned separately using a suitable indexed full-text search strategy.

The initial MVP does not require Elasticsearch.

PostgreSQL remains the preferred search backend unless a concrete future requirement justifies additional infrastructure.

---

## Azure Compatibility

The solution is designed with future integration into WWF's Azure environment in mind.

The architecture therefore aims to remain:

- container-friendly
- configuration-driven
- stateless at the API layer
- PostgreSQL-based
- compatible with standard Azure deployment approaches
- free of unnecessary infrastructure dependencies

Additional infrastructure components should only be introduced when there is a clear technical requirement and compatibility with the WWF environment has been considered.

---

## AI

AI is not required for the first working MVP.

The initial system focuses on:

- reliable OpenParlData integration
- normalized structured data
- WWF classification
- search
- filtering
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

---

## MVP Roadmap

### Completed / Working Foundation

- OpenParlData bulk download
- raw PostgreSQL staging
- normalized parliamentary data
- SQLAlchemy models
- WWF taxonomy
- rule-based WWF classification
- full affair classification run
- classification validation
- FastAPI application
- PostgreSQL health check
- affair list API
- pagination
- keyword title search
- canton filtering
- WWF category filtering
- WWF subcategory filtering
- year filtering
- month filtering
- affair type filtering
- categories API
- cantons API
- affair-types API
- affair detail API
- parliamentary text retrieval
- official source links

### Next

- email identity / activation flow
- subscription persistence
- multiple subscriptions per verified email
- subscription management
- complete unsubscribe flow
- reuse affair filters for subscription matching
- incremental OpenParlData synchronization
- new-affair detection
- existing-affair change detection
- email notifications
- simple frontend
- search results page
- affair detail page
- text preview / expand interaction

### Later / Optional

- indexed parliamentary-content full-text search
- advanced monitoring
- meetings / agendas API
- voting API
- political groups API
- interests API
- AI-assisted functionality
- semantic search
- summarization

---

## Known MVP Limitations

Current known limitations include:

- full parliamentary-text search is not yet implemented
- document-content search is not yet implemented
- harmonized affair state coverage is very limited
- subscriptions are not yet implemented
- email verification is not yet implemented
- notifications are not yet implemented
- incremental synchronization is not yet complete
- frontend is not yet implemented
- AI functionality is intentionally deferred

These limitations are part of the current development state and do not prevent the existing data, classification and search/detail API foundation from being tested.

---

## Data Source

Parliamentary data is provided by OpenParlData.

Source attribution:

> Source: OpenParlData.ch

OpenParlData data is provided under the CC BY 4.0 license.

---

## Project Context

This project is developed for **WWF Switzerland** as part of the HSLU BSc Informatik Wirtschaftsprojekt.

The MVP is intended as a technically sound, testable prototype and foundation for further development rather than a production-ready final platform.

The implementation prioritizes:

```text
Data Integration
        |
        v
WWF Classification
        |
        v
Search & Filtering
        |
        v
Monitoring
        |
        v
Subscriptions & Notifications
        |
        v
User Interface
```

AI-based functionality remains an optional extension after the core MVP functionality.

---

## License

A project-specific software license has not yet been defined.