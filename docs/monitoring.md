# Search, subscriptions and synchronization

The local frontend is served by FastAPI at `/`. Its main navigation contains affairs, meetings, groups and interests. Agendas,
events, votes, documents and texts appear in their related affairs or meetings,
with contextual titles, links and available voting results. All nine datasets
remain synchronized and accessible through the API and related-list links. Search
supports keyword, category/subcategory, canton and date-range filters with
server-side pagination. Affair details include related records, links to browse
the complete related lists, and the latest 100 detected changes.

## Start locally

Configure PostgreSQL, JWT, SMTP and `SYNC_API_KEY` using `.env.example`. Then run:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://localhost:8000`. Registration and passwordless login use email links.
Choose Deutsch, Français, Italiano or English at the top right of the main page.
The browser remembers the selected UI language. Menus, filters, subscription
controls, dates and detail labels follow that language. Source content falls back
to the available original language; no machine translation of long texts is used.
Record details hide technical IDs and duplicate language fields, show one type
and status, collapse long original text, and omit empty related sections.
Agenda cards use their own title, then a linked affair title, then a linked meeting
name when the source has no item title. They show meeting/affair links and the
official source URL when available. Agenda details include the meeting, group and
directly attached documents; meeting details list their agenda items. Agenda
keyword search also searches linked meeting names/descriptions and affair titles.
Public browsing requires no account. A separate stay-informed section offers
registration, login and subscription management. Topics are grouped under their
main themes; selecting a main theme covers all its subtopics. Supporting datasets
are available under an expandable subscription section. Selecting affairs also
covers updates to linked records.

Successful verification redirects to the application and sets an HttpOnly session cookie.
An already open application tab signs in without losing its filters. The email
client controls whether the link opens a new tab; the application attempts to
close that tab after notifying the existing tab, subject to browser restrictions. The API also continues
to accept bearer tokens. SMTP must be configured for login and monitoring emails.

Existing affair classifications remain available to searches of linked records.
To classify existing related records by their own content, including standalone
records, run the following preparation job. It does not create notifications:

```powershell
.venv\Scripts\python.exe -m scripts.classify_entities
```

This job commits batches of 500 and skips classifications at the current classifier
version on restart. Use `--dataset agendas` to process one section, or `--force`
to rebuild its classifications. The taxonomy must already be seeded. New records
and meaningful changes are classified during synchronization; unchanged records
with missing own classifications are also classified when scanned.

## Subscription behavior

Users select categories, cantons, keywords and optionally datasets. Parent categories
include their descendants. Within each selection group, alternatives match with
OR; topic and canton restrictions must both match the same record or linked
affair. An empty topic or canton group is unrestricted. Filter subscriptions pause
when categories, cantons and keywords are all empty. Empty dataset selection means all nine datasets.

Keywords are literal case-insensitive phrases: one per line, up to 20 phrases,
each up to 200 characters. Any phrase matches; keyword, topic and canton filters
apply together. The stored fields searched are the same as in keyword search.
Related records can match their affair's classification alongside their own keywords.

Detail pages offer individual record watches. Affair watches include related
changes; meeting watches include records with that meeting ID. Watches operate
independently of filters and changing classifications. The subscriptions dialog
lists/removes watches. Saving empty filters leaves watches active; "Alle
Benachrichtigungen beenden" clears filters, keywords and watches.

Group details list related meetings. Group watches cover the group record and
its meetings/meeting-linked records. Groups inherit affair classifications through
their meetings. Interest declarations have their own classifications and watches;
they show the declaring person when that person exists in the imported database.
No affair relationship is invented for a person's declaration. A person's other
declarations are browsable using `person_id`; group meetings use `group_id`.
Group date filters use `updated_at` because the existing group model has no
begin date. Interest date filters use `begin_date`; missing dates do not match a
date restriction. Membership synchronization is outside these two source datasets.

Each meaningful source change produces a change event and at most one notification
per matching user. A meeting linked to several affairs creates associations to
all those affairs while sending one notification per user. Current subscription
preferences are checked again before email delivery. Email contains a frontend
link to the affected record.

## Daily and manual synchronization

The existing Docker scheduler and the frontend's manual synchronization button
both use `scripts.sync.run_all`. Manual execution requires `SYNC_API_KEY` and
uses the existing protected sync API. The database lock prevents concurrent
full runs. A failed section is recorded and the remaining sections continue.
JSON results are written to `logs/sync_<run_id>.json`.

```powershell
.venv\Scripts\python.exe -m scripts.sync.run_all
```

This command contacts OpenParlData, modifies records and delivers pending
notification emails. It is separate from the classification preparation job.

Affairs, meetings and documents use timestamp checkpoints. Agendas, votings,
events and texts are fully scanned because their upstream update timestamps
are unavailable or unreliable. Groups and interests also use full scans for
their smaller datasets to check older records and tolerate missing timestamps.
Full scans can be expensive on the initial and
daily runs, but also detect changes to older IDs. The classifier and notification
pipeline run only when content changes, with missing-classification backfill as
described above. Timestamp-only changes do not generate notifications. Repeated
real transitions such as A → B → A each generate a new change event; replaying
unchanged data does not duplicate notifications.

Related changes appear in affair detail/history and match affair subscriptions.
They do not overwrite the affair's source `updated_at` timestamp. Text changes
also rebuild affected affair classifications; affair title changes trigger
reclassification. Other related entities receive their own content classifications.

Documents use the local primary key in frontend URLs and change events because
upstream document IDs can occur in multiple relationship contexts. The original
source ID remains visible. Ambiguous document identities fail the batch instead
of silently updating a different record.

## Verification and limits

```powershell
.venv\Scripts\python.exe -B -m unittest discover -s tests -v
node --check app/web/app.js
node --check app/web/i18n.js
node tests/test_frontend.cjs
```

Tests use SQLite and mock upstream HTTP/SMTP; they do not send real email.
The local frontend and API have HTTP smoke checks. Edge browser checks cover all
four UI languages, the real affair 203543, agenda/meeting links, saved preferences,
mobile width, cross-tab login, grouped topic selection and subscription persistence.
The isolated backend suite contains 31 tests.
A complete live synchronization remains a deployment check. Historical entity
classification requires the preparation job above. Search covers stored fields;
it does not download or extract external PDF/document attachments.

See [WWF requirements review](wwf-requirements.md) for initial taxonomy mappings,
dataset coverage and Azure integration decisions still to agree.

After updating code, restart a locally running API if it was started without
`--reload`. Rebuild an existing Docker scheduler to include the new sync modules:

```powershell
docker compose up -d --build scheduler
```
