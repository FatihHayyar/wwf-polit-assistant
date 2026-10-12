# Search, subscriptions and synchronization

Current setup and user documentation is available in German in the [documentation index](README.md).

The local frontend is served by FastAPI at `/`. All nine public datasets have their own navigation entries and remain available through the API and related-list links. Search
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
Public browsing requires no account. A stay-informed section above the results offers
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

Subscription management offers individual record watches. Affair watches include related
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

The Docker scheduler and protected development API both use `scripts.sync.run_all`.
Synchronization controls are absent from the public frontend. Manual execution
requires `SYNC_API_KEY` in the `X-Sync-API-Key` header. The database lock prevents concurrent
full runs. A failed section is recorded and the remaining sections continue. Email delivery
starts only after every section succeeds; otherwise pending notifications are
retained until a successful resume.
JSON results are written to `logs/sync_<run_id>.json`.

```powershell
.venv\Scripts\python.exe -m scripts.sync.run_all
```

This command contacts OpenParlData, modifies records and delivers pending
notification emails. It is separate from the classification preparation job.

Affairs, meetings and documents use timestamp checkpoints.
Before trusting a timestamp checkpoint, the first API page's source count is
compared with the local record count (distinct identities for other datasets,
rows including relationship variants for Documents). A source count
gap triggers source identity reconciliation, including records older than the
checkpoint. This reconciliation mode is saved with committed batches so a
resumed job continues checking historical records. When Documents has no timestamps newer
than its cursor, all missing identities and the latest live page are hydrated.
Use `--recheck` for a full content audit
even when identity counts match; matching counts do not prove identical IDs
or detect historical edits that do not advance the upstream timestamp.
Documents also checks the highest live source ID, detecting backdated new
documents even when upstream deletions keep the total record count unchanged.

Agendas, votings,
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
The isolated backend suite contains 71 tests (12 October 2026). See the [test guide](testing.md) for current commands and prerequisites.
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

## Development sync control

Use `/docs` to call the following endpoints with `X-Sync-API-Key`, or use an
API client. Keep the key out of public frontend code.

- `POST /api/v1/sync/run`: starts the background process and returns its run ID.
- `GET /api/v1/sync/runs/{run_id}`: status, current dataset and completed dataset totals.
- `GET /api/v1/sync/runs/{run_id}/log`: worker output for progress within a dataset.
- `GET /api/v1/sync/status`: dataset checkpoints (also requires the key).
- `POST /api/v1/sync/runs/{run_id}/cancel`: requests cancellation. Check status
  until it becomes `cancelled`; acceptance alone does not confirm it stopped.

Cancellation support applies to workers started with the updated code. The runner
checks once per second while a dataset subprocess is running and terminates that
subprocess, releasing its connections and the runner lock. Already committed
batches remain stored; a later sync can replay unchanged records safely. During
the notification phase, cancellation is checked before each email; an email
already being sent cannot be recalled. Older running workers return
409 for cancellation and must finish or be stopped separately by an operator.
Restart the API and rebuild the scheduler image to load these changes.
The public page makes no sync-status polling requests. Development clients can
request status manually or poll at a deliberate interval (for example 15 seconds).

### PowerShell example

Start the local API first. Run in another terminal (the key is read without echo):

```powershell
$syncBase = "http://localhost:8000/api/v1/sync"
$syncSecret = Read-Host "SYNC_API_KEY" -AsSecureString
$syncHeaders = @{ "X-Sync-API-Key" = ([System.Net.NetworkCredential]::new("", $syncSecret)).Password }
$syncRun = Invoke-RestMethod -Method Post -Uri "$syncBase/run" -Headers $syncHeaders
$syncRunId = $syncRun.run_id
$syncRun
```

Check status and worker output on demand:

```powershell
Invoke-RestMethod -Uri "$syncBase/runs/$syncRunId" -Headers $syncHeaders | ConvertTo-Json -Depth 5
(Invoke-RestMethod -Uri "$syncBase/runs/$syncRunId/log" -Headers $syncHeaders).log
```

To monitor an existing run, set `$syncRunId` to its returned ID instead of starting
another run. Starting while another worker holds the lock returns HTTP 409.

Request cancellation and then check status for confirmation:

```powershell
Invoke-RestMethod -Method Post -Uri "$syncBase/runs/$syncRunId/cancel" -Headers $syncHeaders
Invoke-RestMethod -Uri "$syncBase/runs/$syncRunId" -Headers $syncHeaders
```

## Type normalization and notification queue

Sync compares text fields after converting API values to their database text
representation. For example, numeric agenda `item_number=1` equals stored `"1"`,
while a change to `2` still produces an event. Timestamp-only differences remain
excluded. Related dataset checkpoint counters are persisted after each batch.

The sender has no total 100-message cap. By default it groups the pending queue
present at the start into summaries; individual delivery is also available. Each notification is attempted
at most once per invocation; failed sends remain pending for a subsequent run.
New queue entries arriving during delivery wait for the next invocation. Optional
`limit` still allows an operator to request bounded delivery. Sent/failed totals
are saved periodically and retained when cancellation interrupts delivery.

`python -m scripts.quarantine_agenda_type_events RUN_ID` previews item-number-only
agenda event candidates from a confirmed cancelled run. `--apply` writes an audit
copy under `logs/`, marks these events `ignored` and cancels their pending
notifications. New records and events with any other changed field are preserved.
Previous field values were not stored, so these candidates cannot all be proven
false retrospectively; quarantine retains them for inspection instead of deleting
them. Ignored events are excluded from public affair history and email delivery.

## Resuming an interrupted job

`POST /api/v1/sync/runs/{run_id}/resume` (same API-key header) starts a new
background attempt of the same job and returns a new run ID. Its summary includes
`job_id`, `resume_of` and `dataset_results` for completed, running and failed
sections. Completed sections are skipped; a fresh `POST /sync/run` creates a
new daily/manual job and checks every section again.

```powershell
$syncRun = Invoke-RestMethod -Method Post -Uri "$syncBase/runs/$syncRunId/resume" -Headers $syncHeaders
$syncRunId = $syncRun.run_id
Invoke-RestMethod -Uri "$syncBase/runs/$syncRunId" -Headers $syncHeaders | ConvertTo-Json -Depth 8
```

Full scans read the official bulk export **as an ID inventory only**, including
split exports, then hydrate batches of IDs from the live API with `offset=0`.
The API ID filter is checked; an ignored filter or truncated batch fails rather
than silently skipping data. This avoids the upstream 100,000 offset cap and
avoids overwriting live values with an older export. New higher IDs since the
export are included before the inventory is fixed. Incremental sections retain
their successful update checkpoint, falling back to an ID inventory if the
API depth cap is reached. The original upper update cursor bounds that job;
updates made after it are checked by a later fresh job.

Progress is stored under `logs/sync_jobs/JOB_ID/` after each database batch
commit. With inventory-based scans, resume skips committed inventory batches;
a crash between database commit and progress save replays the last batch safely.
Incremental API scans restart from their successful checkpoint on resume because
reusing an offset against a changing sort order is unsafe. Successful section
completion is persisted before the runner moves to the next section. Each of
the nine sections prints its result counters, duration and checkpoint outcome.

Legacy cancelled jobs can resume by recognizing explicit `OK` lines in their
logs. Their unfinished sections have no stable batch manifest, so those sections
are rechecked from the beginning once. Existing data and notifications are
retained. Preserve the job directory and logs across restarts; API and worker
containers must share this storage for resume to work. Bulk inventories require
network/disk space: the current texts export is split across files, while a rare
full Documents fallback can require several GB. No source deletions are inferred
from missing export/API IDs.

## Meaningful notification rules

All source changes are still stored as events. Notification eligibility is
independent and recorded with policy version `meaningful-v1`; future update events
preserve before/after values. Whitespace, common HTML markup, Unicode presentation
and entity-encoding differences do not generate notifications. Empty and null
text are equivalent. Technical URL, source-ID, ordering and language metadata
updates remain stored without email. Record creation is eligible in every dataset.

| Dataset | Update fields eligible for email |
| --- | --- |
| Affairs | Titles/long titles, original status labels, active flag, start/end dates |
| Agendas | Title, description, status, result, date, meeting |
| Meetings | Name, description, dates, status, location |
| Votings | Date, title/question, decision, results and meanings of yes/no |
| Events | Date, original title, actor and explanatory text; not position/last flags |
| Documents | Name, date, extracted text or file hash; not URL/size/format alone |
| Texts | Text content in available languages, date; not format/type metadata alone |
| Groups | Name and active flag; not abbreviation or harmonized type alone |
| Interests | Organization/name, role, person, dates, ex-officio flag |

Matching subscription filters and record watches are applied after this policy
gate and rechecked before delivery. `python -m scripts.reapply_notification_policy`
previews cancellations in the pending queue; `--apply` stores an audit and applies
them. Legacy events lack previous values: only their recorded changed-field names
can be evaluated, so historical formatting differences cannot all be reconstructed.
Events are retained even when their notifications are cancelled.

The default sender groups pending notifications by user and related affair, or
by standalone record when there is no affair. A successful summary marks every
included notification sent. Failed groups remain pending and are attempted once
per invocation. There is no total 100-message cap. Up to 30 changes are listed in
a summary, with links to the full record/history for further changes. An optional
`limit` bounds the number of summaries; `digest=False` retains the individual
delivery mode for explicit operator use.

Texts uses a special source strategy: its API ignores the `id` filter and reports
global pagination metadata. The bulk inventory supplies stable affair groups,
then the live API is read using supported `affair_id` filters and actual page
length. Orphan text IDs use the detail endpoint. Progress is committed per group
batch, which may contain more than 500 text records. Fresh bulk contents never
overwrite newer live text values.


### Notification email presentation and SMTP failures

Notification emails use German display names for all nine datasets and contain both plain text and HTML. Related events, documents, votes and texts remain grouped under their affair; the subject and body list the included dataset types. Legacy changes without snapshots show the current value rather than inventing an old value. Detailed before/after values are shown where snapshots exist. Record links use `VERIFICATION_BASE_URL`; configure a reachable deployment URL outside local development.

Delivery stops after three consecutive failures. Successful messages remain sent; failed and unattempted notifications remain pending. SMTP response codes and the failing connection stage are preserved. Resume the completed job after resolving the SMTP problem to retry pending emails without scanning completed datasets again. A failure during authentication requires checking the SMTP provider/account; restarting the data scan does not resolve it.


The 2026-10-11 change-quality audit found 1,251 formatting-only changes among 1,329 Texts updates with snapshots (78 had different visible content, including spelling corrections). Policy `meaningful-v2` parses visible HTML text, ignores inline wrappers and equivalent quotation marks, and ignores whitespace around punctuation. Numeric signs, changed amounts and negation remain significant. Earlier change events without snapshots cannot be conclusively assessed for formatting changes. Detailed local audit: `logs/change_quality_audit_20261011.json`.


### Current notification policy: meaningful-v3

All source changes continue to update the database, classification and change history. Email eligibility is independent. This policy supersedes the earlier broader field rules above.

| Dataset | Notifications for new records and these updates |
| --- | --- |
| Affairs | Actual status changes and active/inactive transitions; title and standalone begin/end-date corrections are silent |
| Agendas | Schedule date, status and result; title, description, numbering and relationship corrections are silent |
| Meetings | Schedule dates, status and location |
| Votings | Decisions and vote counts/results; title corrections are silent |
| Events | Event date and substantive details; actor, sort and relationship corrections are silent |
| Documents | New document or changed extracted text; hash, filename, date and URL changes alone are silent because they do not prove visible-content change |
| Texts | New text or substantive visible text changes; format/type/date-only updates are silent |
| Groups | Active status (and lifecycle dates if supplied); renaming is silent |
| Interests | Person, role, lifecycle dates and ex-officio status; name/URL corrections are silent |

Whitespace, HTML wrappers, equivalent quotation marks, capitalization-only changes and isolated one-character spelling corrections in alphabetic words of at least six characters are silent. Numeric changes, negation, inserted/deleted words and larger replacements remain eligible. This is a deterministic conservative rule, not a guarantee of political significance; complex rewrites can still be editorial. New records remain subject to the current theme/canton/keyword/watch filters.

Historical updated events without before/after snapshots are not emailed: field names alone cannot establish substantive change. Existing cancelled notifications remain cancelled. No old notifications are recreated. Under this policy, 77 of the 1,329 Texts snapshots from the latest run remain eligible (read-only evaluation; no emails sent).
