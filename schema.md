# SQL Table Schemas

Tables referenced by `update_data.py`. All connections are managed via `update.py:get_db_handle()` using `.env` credentials.

---

## DB8 — `counselling` database (MySQL 8)

### `counselling.sa_counsellor_call_log`
Call records logged by counsellors.

| Column | Type | Notes |
|---|---|---|
| `id` | int | Primary key → aliased as `call_id` in query |
| `user_id` | int | Student/user who was called |
| `counsellor_id` | int | FK → `RMS_counsellor.counsellor_id` |
| `file_name` | varchar | Name of the call recording file |
| `duration` | int/float | Call duration in seconds |
| `file_creation_date` | datetime | When the recording file was created |
| `created_on` | datetime | When the call log row was created; used as the incremental cursor |

**Filters applied:** `created_on > <max_date_in_file> AND created_on < <midnight_today>`
**Joined with:** `RMS_counsellor` (on `counsellor_id`), `sa_team` (on `team_id`)

---

### `counselling.RMS_counsellor`
Counsellor master data.

| Column | Type | Notes |
|---|---|---|
| `counsellor_id` | int | Primary key |
| `counsellor_name` | varchar | Display name |
| `counsellor_email` | varchar | Email address |
| `team_id` | int | FK → `sa_team.team_id` |
| `status` | enum | `'live'` or `'deleted'`; both included in queries |
| `platform` | varchar | Filtered to `'domestic'` only |

**Used in:** call logs join, application sold enrichment, TL name resolution (self-join on `counsellor_id = team_lead_id`), responses joins
**Note on `status` filter:** call logs + application sold use `status IN ('live', 'deleted')`; response queries use `status = 'live'` only

---

### `counselling.sa_team`
Team master data.

| Column | Type | Notes |
|---|---|---|
| `team_id` | int | Primary key |
| `team_name` | varchar | Display name |
| `status` | enum | Filtered to `'live'` only |

---

### `counselling.application_sold_by_counsellor`
Application form sales records.

| Column | Type | Notes |
|---|---|---|
| `id` | int | Primary key; used for deduplication on incremental sync |
| `creation_date` | datetime | When the application was created; used as the incremental cursor |
| `counsellor_id` | int | FK → `RMS_counsellor.counsellor_id` |
| `team_lead_id` | int | FK → `RMS_counsellor.counsellor_id` (TL lookup via self-join) |
| `institute_id` | int | FK → `shiksha.shiksha_institutes.listing_id` |
| `status` | varchar | `ACCEPTED`, `PENDING`, or `REJECTED` |
| `application_submission_date` | datetime | When the student submitted the application |
| `base_course_name` | varchar | Course name |
| `lead_source` | varchar | Comma-separated; first token used as `lead_source_clean` in `app.py` |
| *(other columns)* | | `SELECT *` — all columns fetched |

**Filters applied:** `creation_date > <max_date_in_file> AND creation_date < <midnight_today>`
**Enriched with:** counsellor name + team (DB8 `RMS_counsellor`/`sa_team`), TL name (self-join), college name (DB5)

---

### `counselling.sdResponseCreationData`
Counsellor-created SD responses (shortlisting/recommendation events).

| Column | Type | Notes |
|---|---|---|
| `userId` | int | Student user ID |
| `counsellorId` | int | FK → `RMS_counsellor.counsellor_id` |
| `uilpId` | int | University/institute-level programme ID |
| `baseCourseId` | int | Base course ID → saved as `base_course` in Excel |
| `isClient` | tinyint | `1` = paid client, `0` = non-client |
| `createdOn` | datetime | When the response was created; used as the incremental cursor |

**Filters applied:** `createdOn > <max_date_in_file> AND createdOn < <midnight_today>`
**Joined with:** `RMS_counsellor` (LEFT, `status = 'live'`, `platform = 'domestic'`), `sa_team` (LEFT, `status = 'live'`)
**Dedup key:** `(userId, uilpId, baseCourseId, createdOn)`
**Saves to:** `data-store/Responses_Created_By_Counsellors.xlsx`

---

### `counselling.user_shortlist_data`
Edit-shortlist response events — records when a counsellor shortlists a programme for a user.

| Column | Type | Notes |
|---|---|---|
| `user_id` | int | Student user ID |
| `loggedin_user_id` | int | Counsellor who performed the action → aliased as `counsellor_id` |
| `loggedin_user_type` | varchar | Filtered to `'counsellor'` only |
| `entity_id` | int | UILP ID → aliased as `uilp_id` |
| `subentity_id` | int | Base course ID → aliased as `base_course` |
| `is_paid` | tinyint | Whether the student is a paid client |
| `created_on` | datetime | When the shortlist record was created |
| `updated` | datetime | Last-modified timestamp; used as the incremental cursor (catches re-shortlisted records) |
| `status` | enum | Filtered to `'live'` only |
| `shortlisted` | tinyint | Filtered to `1` only |

**Filters applied:** `loggedin_user_type = 'counsellor' AND updated > <max_date_in_file> AND updated < <midnight_today> AND status = 'live' AND shortlisted = 1`
**Joined with:** `RMS_counsellor` (LEFT, `status = 'live'`, `platform = 'domestic'`), `sa_team` (LEFT, `status = 'live'`)
**Dedup key:** `(user_id, uilp_id, base_course)`
**Saves to:** `data-store/edit-shortlist-responses.xlsx`

---

## DB5 — `shiksha` database (MySQL 5)

### `shiksha.shiksha_institutes`
College/institute master data.

| Column | Type | Notes |
|---|---|---|
| `listing_id` | int | Primary key → maps to `application_sold_by_counsellor.institute_id` |
| `name` | varchar | College display name → aliased as `college_name` |
| `status` | enum | Filtered to `'live'` only |

**Fetched with:** `WHERE listing_id IN (<ids from new applications>)`

---

## Environment Variables (`.env`)

| Variable | DB |
|---|---|
| `DB5_HOST`, `DB5_USER`, `DB5_PASSWORD`, `DB5_PORT` | MySQL 5 (shiksha) |
| `DB8_HOST`, `DB8_USER`, `DB8_PASSWORD`, `DB8_PORT` | MySQL 8 (counselling) |