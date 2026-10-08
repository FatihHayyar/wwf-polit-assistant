# WWF Polit-Assistant

A political monitoring assistant for WWF Switzerland based on Swiss parliamentary open data.

Developed as part of the **Wirtschaftsprojekt (WIPRO)** in the BSc Informatik program at Hochschule Luzern (HSLU).

## Project Goal

The goal is to develop a functional MVP that helps WWF Switzerland search, classify and monitor politically relevant parliamentary activities.

The platform combines OpenParlData, WWF-specific topic classification, canton filtering, email-based subscriptions and automated synchronization.

AI-based functionality is optional and is not required for the initial MVP.

## Current Status — 8 October 2026

The FastAPI backend, PostgreSQL integration, initial data import, classification pipeline, affair search and subscription infrastructure are implemented.

The following functionality is available:

- OpenParlData bulk download and validated snapshot import
- PostgreSQL raw staging and normalized parliamentary data
- Rule-based hierarchical WWF classification
- Affair search, filtering, pagination and detail API
- Email-based registration and passwordless login
- Email verification and JWT authentication
- Theme and canton subscription management
- Change-event and notification creation for affairs
- SMTP email notification delivery
- Incremental synchronization for seven datasets
- API-triggered synchronization with concurrency protection
- Structured synchronization results and technical logs

**Verified tests:**

- All seven synchronization modules completed successfully in a manual run.
- A Bern affair classified under *Erneuerbarer Strom* matched a *Klima & Energie* subscription.
- A notification was created for the matching subscriber.
- A real notification email was successfully received.

**Important limitation:** Changes in related datasets such as agendas, meetings, votings, documents, events and texts are not yet fully connected to affair-based notifications.

## Architecture

```text
OpenParlData
      |
      v
Bulk Import / Incremental Sync
      |
      v
PostgreSQL
      |
      v
Normalized Parliamentary Data
      |
      v
WWF Classification
      |
      +----------------------+
      |                      |
      v                      v
Search & Detail API     Change Events
                             |
                             v
                     Subscription Matching
                             |
                             v
                     Notification Queue
                             |
                             v
                         SMTP Email
```

The initial bulk import and ongoing incremental synchronization are separate processes.

## Technology Stack

- Python 3.13
- FastAPI and Pydantic
- SQLAlchemy and Psycopg
- PostgreSQL 17
- Alembic
- Docker and Docker Compose
- OpenAPI / Swagger
- SMTP email delivery

## OpenParlData Bootstrap

The initial development snapshot is dated **2026-10-06**.

| Dataset | Initial records |
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

The initial import consists of approximately 126 compressed files and 5.91 GB of data.

These figures describe the initial bootstrap snapshot, not necessarily the current database totals.

Individual parliamentary votes are not included in the full local mirror. Aggregate voting information is available through the votings dataset.

## WWF Classification

The MVP uses configurable rule-based classification.

It supports hierarchical topics, subcategories, multilingual rules, weights, scores, confidence values, classification evidence and fallback classification.

Main topic areas:

- Climate & Energy
- Biodiversity & Landscape
- Sustainable Economy & Consumption
- Environment & Policy
- Other (fallback)

For the initial bootstrap, all 325,691 affairs were classified.

The original classification baseline included 325,824 classification rows, 7,111 evidence rows and 320,121 fallback rows.

The rule-based approach is retained for the MVP. AI-assisted classification may be introduced later.

## Search and Filtering

The affair search endpoint is:

```http
GET /api/v1/affairs
```

Supported filters include keyword, canton, WWF category, subcategory, year, month and parliamentary affair type.

Filters can be combined using AND semantics. Multilingual keyword matching uses OR semantics across supported title fields.

Search results use server-side pagination, with a default page size of 10.

Example:

```http
GET /api/v1/affairs?q=Photovoltaik&canton=ZH&year=2026&page=1
```

Title-based partial search uses PostgreSQL `pg_trgm` indexes.

Full-text search across complete parliamentary texts and document contents remains planned.

### Affair Details

```http
GET /api/v1/affairs/{affair_id}
```

The detail response includes available parliamentary metadata, WWF classifications, parliamentary texts and official-source links.

Canton filtering resolves the canton through the parliamentary body:

```text
affairs.body_id
      |
      v
bodies.id
      |
      v
bodies.canton_key
```

## Authentication

The backend implements passwordless email authentication.

The supported flow is:

```text
Register email
      |
      v
Receive verification link
      |
      v
Verify email
      |
      v
Authenticated account
      |
      v
Manage subscriptions
```

Returning users can request a one-time email login link.

The backend uses JWT authentication and supports account deletion.

Relevant endpoints:

```http
POST /api/v1/auth/register
GET  /api/v1/auth/verify-email
POST /api/v1/auth/login
GET  /api/v1/auth/verify-login
```

Authentication and subscription management are backend features. The frontend user experience is still under development.

## Subscriptions

Users can subscribe to WWF topics and Swiss cantons.

Subscription matching follows these rules:

- Multiple selected topics use OR semantics.
- Multiple selected cantons use OR semantics.
- Topics and cantons are combined using AND semantics.
- A selected parent topic includes its descendant categories.
- No selected topics means all topics, provided at least one canton is selected.
- No selected cantons means all cantons, provided at least one topic is selected.
- Both selections empty means no active notification subscription.

Examples:

| Topics | Cantons | Meaning |
|---|---|---|
| Klima & Energie | BE | Climate and energy affairs in Bern |
| Klima & Energie | All | Climate and energy affairs in every canton |
| All | ZH | Affairs across all topics in Zürich |

Subscriptions can be added, removed or replaced through the REST API.

The bulk update endpoint is:

```http
PUT /api/v1/subscriptions
```

Example request:

```json
{
  "category_ids": [1],
  "canton_keys": ["BE"]
}
```

The subscription update process also supports email confirmation.

## Incremental Synchronization

The backend contains seven incremental synchronization modules:

| Dataset | Module |
|---|---|
| Affairs | `scripts.sync.incremental_sync` |
| Agendas | `scripts.sync.agendas_sync` |
| Meetings | `scripts.sync.meetings_sync` |
| Votings | `scripts.sync.votings_sync` |
| Events | `scripts.sync.events_sync` |
| Documents | `scripts.sync.docs_sync` |
| Texts | `scripts.sync.texts_sync` |

The synchronization process uses checkpoints to resume incremental processing.

For affairs, fingerprints help distinguish actual record changes from unchanged records.

The combined synchronization runner is:

```powershell
python -m scripts.sync.run_all
```

The application is configured for a daily synchronization at **03:00 Europe/Zurich**.

### Sync API

```http
POST /api/v1/sync/run
GET  /api/v1/sync/status
GET  /api/v1/sync/latest
GET  /api/v1/sync/runs/{run_id}
GET  /api/v1/sync/runs/{run_id}/log
```

`POST /run` starts a background synchronization and requires the configured sync API key.

`GET /status` shows individual dataset checkpoints.

`GET /latest` returns a structured summary including:

- Run status
- Start and finish timestamps
- Execution duration
- Successful and failed dataset counts
- New, changed and unchanged record counts
- Record errors
- Sent and failed notification emails

Run summaries and technical logs are stored locally under `logs/`.

The synchronization runner uses a PostgreSQL advisory lock to prevent overlapping full synchronization runs.

### Verified Synchronization Result

On 8 October 2026, a manual run reported:

```text
Status: completed
Datasets: 7/7 successful
Duration: 24.24 seconds
New records: 0
Changed records: 0
Errors: 0
Emails sent: 0
Emails failed: 0
```

This confirms successful execution of the seven modules for that run. It does not establish that related-dataset notification propagation is complete.

## Change Events and Notifications

For new and changed affairs, the backend supports:

```text
Affair created / updated
          |
          v
      ChangeEvent
          |
          v
   Subscription Match
          |
          v
       Notification
          |
          v
      Pending Queue
          |
          v
       SMTP Email
```

The notification service checks whether the user remains active, verified and subscribed before sending.

Failed email attempts remain pending for retry. Notifications that no longer satisfy the subscription conditions can be cancelled.

The email sender processes a limited batch of pending notifications per run.

### Tested Notification Flow

A test used the existing Bern affair:

```text
Affair ID: 18792
Title: Komplettierung Solaranlage Schiessanlage Weier
Canton: BE
Category: Erneuerbarer Strom
Parent topic: Klima & Energie
```

The subscription matcher successfully created a pending notification for the matching account.

A subsequent controlled test successfully delivered a real email through SMTP.

Temporary test change events and notifications were removed afterward.

### Related-Dataset Monitoring — Planned

The next development phase will connect changes in related parliamentary data to the appropriate affairs.

Examples include:

- A new agenda item for an existing affair
- A new or rescheduled parliamentary meeting
- A newly published document
- A new parliamentary text
- A voting result
- A new event associated with an affair

The intended flow is:

```text
Agenda / Meeting / Voting / Event / Document / Text change
                           |
                           v
                  Resolve related affair(s)
                           |
                           v
                      ChangeEvent
                           |
                           v
                  Subscription Matching
                           |
                           v
                    Email Notification
```

This functionality must be implemented carefully because different datasets have different relationships to affairs.

An affair-level `updated` test alone does not prove that a meeting or agenda change is detected automatically.

## Supporting API Endpoints

```http
GET /health
GET /api/v1/categories
GET /api/v1/cantons
GET /api/v1/affair-types
```

`GET /health` checks application and database availability.

The other endpoints provide data for search filters and category selection.

## Local Development

### Requirements

- Python 3.13+
- Docker and Docker Compose
- PostgreSQL through the provided Docker configuration

### Create and Activate Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

### Environment Configuration

Copy `.env.example` to `.env` and configure the required settings.

The local PostgreSQL database is exposed on port `5433`.

Email and sync credentials must remain private. Do not commit `.env`, JWT secrets, SMTP credentials or sync API keys.

### Start Database

```powershell
docker compose up -d
```

### Apply Migrations

```powershell
python -m alembic upgrade head
```

### Start API

```powershell
python -m uvicorn app.main:app --reload
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### Initial Bootstrap Commands

Inspect planned downloads:

```powershell
python scripts/bootstrap/download_openparldata.py --dry-run
```

Download selected datasets:

```powershell
python scripts/bootstrap/download_openparldata.py --workers 6
```

Inspect exports:

```powershell
python scripts/bootstrap/inspect_exports.py
```

Import raw data:

```powershell
python scripts/bootstrap/import_raw.py all
```

Raw exports and database snapshots should not be committed to Git.

## MVP Roadmap

### Implemented

- Bulk OpenParlData integration
- PostgreSQL raw staging and normalized models
- WWF taxonomy and rule-based classification
- Affair search and detail endpoints
- Keyword and structured filtering
- Email registration and verification
- Passwordless login
- Theme and canton subscriptions
- Subscription matching
- Affair change events and notifications
- SMTP notification delivery
- Seven incremental sync modules
- Sync execution and result APIs

### Next

- Connect agenda changes to related affair notifications
- Connect meeting changes to related affair notifications
- Extend the same mechanism to votings, events, documents and texts
- Include meaningful change details in notification emails
- Reclassify existing affairs when relevant thematic content changes
- Improve synchronization and notification failure recovery
- Implement the frontend for search, affair details and subscription management

### Later / Optional

- Indexed full-text search across parliamentary content
- Additional parliamentary entity APIs
- AI-assisted classification
- Semantic search
- Summarization and natural-language queries

## Known MVP Limitations

- Related-dataset changes are not yet fully propagated to affair notifications.
- Updated affairs are not automatically reclassified in every relevant scenario.
- Notification emails currently provide limited change details.
- Full parliamentary-text and document-content search is not implemented.
- Harmonized affair state coverage is limited.
- The frontend is not yet implemented.
- Local JSON sync results are not a replacement for production-grade job monitoring.
- The system is a development MVP, not a production-ready deployment.

## Azure Compatibility

The architecture is designed with potential integration into WWF's Azure environment in mind.

It prioritizes PostgreSQL, configuration-driven services, container compatibility and minimal infrastructure dependencies.

## Data Source

Parliamentary data is provided by **OpenParlData.ch** under the CC BY 4.0 license.

## Project Context

This project is developed for **WWF Switzerland** as part of the HSLU BSc Informatik Wirtschaftsprojekt.

The goal is a technically sound and testable prototype that can be extended into a broader political monitoring platform.

## License

A project-specific software license has not yet been defined.