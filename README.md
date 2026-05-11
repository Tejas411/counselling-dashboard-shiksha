# Counselling Dashboard

A Plotly Dash dashboard showing counsellor performance across Applications, Calls, Responses, Fresh Leads, and a Leaderboard.

## Setup

Install dependencies:

```bash
pip install dash dash-bootstrap-components plotly pandas openpyxl python-dotenv mysql-connector-python
```

## Updating data

Run this once a day (or on demand) to pull the latest records from MySQL into the local Excel files:

```bash
python update_data.py
```

What it does:
- **Step 1** — Appends new call log rows to `data-store/call_logs.xlsx`
- **Step 2** — Appends new application sold rows to `data-store/counselling_application_sold_report.xlsx`
- **Step 3.1** — Appends new response creation rows to `data-store/Responses_Created_By_Counsellors.xlsx`
- **Step 3.2** — Appends new shortlist response rows to `data-store/edit-shortlist-responses.xlsx`

Each step fetches only rows newer than the latest date already in the file (incremental sync). Run from the project root — requires VPN/network access to the MySQL servers.

## Starting the dashboard

```bash
python app.py
```

Then open your browser and go to:

```
http://localhost:8050
```

The dashboard loads all Excel files from `data-store/` at startup. To see updated data after running `update_data.py`, restart the server.

## Tabs

| URL | Tab |
|-----|-----|
| `/` | Applications |
| `/calls` | Calls |
| `/responses` | Responses |
| `/fresh-leads` | Fresh Leads |
| `/leaderboard` | Leaderboard |

## Project layout

```
app.py              # Dash entry point
update_data.py      # Daily data sync orchestrator
data.py             # Loads DataFrames from data-store/ at startup
theme.py            # Shared colors and UI components

pages/              # One file per dashboard tab
data_scripts/       # MySQL fetch logic, split by data source
data-store/         # Excel files (source of truth for the dashboard)
assets/             # CSS overrides (auto-loaded by Dash)
cache/              # JSON cache for fresh_leads_data
```
