# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Constraints

- **Do not make any changes to files or scripts outside this project folder.**

## Running the dashboard

```bash
python app.py          # starts Dash server at http://localhost:8050
```

To incrementally sync MySQL data into the Excel files in `data-store/`:

```bash
python update_data.py
```

## Installing dependencies

The current dashboard (`app.py`) requires:

```bash
pip install dash dash-bootstrap-components plotly pandas openpyxl python-dotenv mysql-connector-python
```

> `requirements.txt` is stale — it lists `streamlit` and `duckdb` from the old architecture and does not include `dash` or `dash-bootstrap-components`.

## Project structure

```
counselling-dashboard/
├── app.py                          # Entry point — Dash app, routing, callback registration
├── data.py                         # Loads all DataFrames at startup from data-store/
├── theme.py                        # Design tokens, shared UI helpers (navbar, kpi_card, etc.)
├── update_data.py                  # Orchestrator — calls data_scripts/* to sync MySQL → Excel
│
├── pages/                          # One module per dashboard tab
│   ├── applications.py             # /  (Applications tab)
│   ├── calls.py                    # /calls
│   ├── responses.py                # /responses
│   ├── fresh_leads.py              # /fresh-leads
│   └── leaderboard.py              # /leaderboard
│
├── data_scripts/                   # MySQL → Excel fetch logic, split by data source
│   ├── __init__.py                 # Shared: DATASTORE constant + find_file() helper
│   ├── dbconnections.py            # MySQL connection factory (DB5 / DB8)
│   ├── calls_data.py               # Fetches call logs (uses update.py for DB handle)
│   ├── applications_data.py        # Fetches applications sold
│   ├── responses_data.py           # Fetches response creation + shortlist responses
│   └── fresh_leads_data.py         # Fetches fresh lead allocations → exports daily Excel
│
├── data-store/                     # Excel files read by data.py at startup
├── assets/                         # style.css — Dash auto-serves this
├── cache/                          # JSON cache written by fresh_leads_data.py
│
├── update.py                       # DB connection factory used by data_scripts (calls/apps/responses)
├── schema.md                       # Full MySQL table schemas for reference
└── .claude/                        # Claude Code settings (settings.json, settings.local.json)
```

## Architecture

### Excel → Dash (current `app.py`)
`app.py` reads directly from Excel files at startup (via `data.py`), cleans them in-memory with pandas, and serves a multi-page Plotly Dash dashboard (five tabs: **Applications** at `/`, **Calls** at `/calls`, **Responses** at `/responses`, **Fresh Leads** at `/fresh-leads`, and **Leaderboard** at `/leaderboard`). Routing is handled by `dcc.Location` + a top-level callback; `suppress_callback_exceptions=True` is set because each page has its own callback.

**Data files loaded at startup** (all in `data-store/`):
- `counselling_application_sold_report.xlsx` — applications data (`adf`)
- `call_logs.xlsx` — call logs data (`cdf`)
- `counsellor-TL-mapping.xlsx` — maps `counsellor_id` → `TL_name` for the calls tab
- `Responses_Created_By_Counsellors.xlsx` + `edit-shortlist-responses.xlsx` — responses data (`rdf`)
- `*_first_call_byDSDB.xlsx` — fresh leads data (`fldf`), most recent file used

Each page module in `pages/` exports `layout()` and `register_callbacks(app)`. Leaderboard is the exception: `register_callbacks(app, adf, cdf, rdf)` receives DataFrames explicitly. `app.py` calls all register functions at startup and routes to each layout via URL.

Global design tokens (colors, chart dicts, card style) are in `theme.py` and imported by all page modules. CSS overrides for Dash dropdowns and scrollbars live in `assets/style.css`.

**Key metric — Talk Time** (calls tab): avg daily talk time per counsellor = mean over days of (total connected duration / unique active counsellors that day). A "connected call" is any call with `dur_sec > 0`.

**Leaderboard tab** (`/leaderboard`, `pages/leaderboard.py`):
- Filters: Date From / To (default: 1st of current month → yesterday), Team (multi), Team Lead (multi)
- Eligibility: only counsellors with ≥ 1 connected call (`dur_sec > 0`) in the selected period appear
- Ranked by Applications (ACCEPTED + PENDING) descending; Connected Calls as tiebreaker
- Table columns: Rank | Counsellor | Applications | Active Days | Call-to-App % | Connected Calls | Total Talk Time | Avg. Talk Time / Active Day | Client Responses
- **Avg. Talk Time / Active Day** (per counsellor): mean of that counsellor's daily `dur_sec` sums across their active days
- **Client Responses**: count of `rdf` rows where `is_client == 1` for the counsellor in the period
- Top 3 rows get gold / silver / bronze left-border accent styling

### MySQL → Excel sync (`update_data.py`)
Thin orchestrator that imports and calls one function per data source from `data_scripts/`:
- `data_scripts/calls_data.py` — call logs via DB8
- `data_scripts/applications_data.py` — applications sold via DB8 + DB5 (college names)
- `data_scripts/responses_data.py` — response creation + shortlist responses via DB8
- `data_scripts/fresh_leads_data.py` — fresh lead allocations via DB8, exports dated Excel to `data-store/`

DB connections: `data_scripts/dbconnections.py` is used by `fresh_leads_data.py`; the other three use `update.py` at the project root.

### Legacy one-shot script (`counselling_application_sold_report.py`)
Original script used to generate the applications Excel from scratch. Superseded by `update_data.py`. Note: it imports from root-level `dbconnections` which has been moved to `data_scripts/dbconnections.py` — update the import if this script needs to be run.
