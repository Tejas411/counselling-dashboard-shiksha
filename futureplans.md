# Future Plans

---

## Plan 1: Excel → Parquet sync for faster dashboard loading

### Context

The dashboard currently reads all data from Excel files at server startup via `data.py`. Excel is slow for pandas (especially as files grow). The goal is to use Parquet for dashboarding (10–50× faster reads) while keeping Excel as the source of truth for manual inspection. Parquet files must always stay in sync with Excel — synced whenever Excel is updated (end of `update_data.py`) and whenever the server starts (`app.py`).

### Excel → Parquet mapping

| Excel (data-store/) | Parquet (data-store/) |
|---|---|
| `counselling_application_sold_report.xlsx` | `applications.parquet` |
| `call_logs.xlsx` | `call_logs.parquet` |
| `counsellor-TL-mapping.xlsx` | `tl_mapping.parquet` |
| `Responses_Created_By_Counsellors.xlsx` | `responses_created.parquet` |
| `edit-shortlist-responses.xlsx` | `responses_shortlist.parquet` |
| latest `*_first_call_byDSDB.xlsx` (glob) | `fresh_leads.parquet` |

### Files to create / modify

**1. CREATE `data_scripts/sync_parquet.py`**

One public function `sync_all()`. Internally uses `_sync(excel_path, parquet_path, label)` which:
- Skips with a warning if Excel file doesn't exist
- Skips with `OK (up-to-date)` if parquet exists and its mtime ≥ Excel mtime (avoids redundant work on startup)
- Otherwise: `pd.read_excel` → `df.to_parquet(index=False)` → prints `synced N rows`

Fresh leads handled by `_sync_fresh_leads()`: globs `data-store/*_first_call_byDSDB.xlsx`, picks latest file, applies same mtime check against `fresh_leads.parquet`.

**2. MODIFY `data.py`**

Replace every `pd.read_excel(...)` with `pd.read_parquet(...)` using the mapped parquet paths. All post-load transformations (datetime parsing, `dur_sec` derivation, `TL_name` mapping, etc.) stay exactly as-is.

Fresh leads: keep glob only to derive `_fl_date` (date label in UI). Read actual data from `fresh_leads.parquet`. Fall back to empty DataFrame if parquet doesn't exist.

**3. MODIFY `app.py`**

Call `sync_all()` before any project data imports:

```python
from data_scripts.sync_parquet import sync_all
sync_all()                         # Excel → Parquet sync

from data import adf, cdf, rdf    # now reads from parquet
from theme import navbar
import pages.applications as applications
# ... rest unchanged
```

**4. MODIFY `update_data.py`**

Add `sync_all()` at the end of `main()`, after all 4 update steps:

```python
    _run("Step 4: Updating Fresh Leads", update_fresh_leads)

    print("\n=== Syncing Parquet files ===")
    from data_scripts.sync_parquet import sync_all
    sync_all()
```

### New dependency

```bash
pip install pyarrow
```

### Verification

1. `python update_data.py` — should print sync status after Step 4
2. `python app.py` — should print sync status (all "up-to-date"), then start server
3. Open `http://localhost:8050` — all 5 tabs load correctly
4. On next startup without running `update_data.py` — all files show `OK (up-to-date)`, startup is fast
