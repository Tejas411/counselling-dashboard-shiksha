"""
fresh_leads_data.py
--------------------
Fetch allocated leads for today-2, join with first attempted/connected notes,
and export a raw user-level Excel to data-store/.

Run standalone:
    python data_scripts/fresh_leads_data.py
"""

import sys
import os
import logging
from collections import defaultdict
from datetime import datetime, timedelta

_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
_DATA_STORE  = os.path.join(_PROJECT_DIR, "data-store")

# Ensure dbconnections.py (in this folder) is importable when run standalone
sys.path.insert(0, _SCRIPT_DIR)

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

_VOICE_BOT_IDS_INT = (98378484, 99132516, 99777644, 100664878, 101977480, 101977682, 100872980, 100080242, 103884168, 104230610, 105461428)
_VOICE_BOT_IDS_STR = ("'98378484'", "'99132516'", "'99777644'", "'42629709'", "'100872980'", "'100080242'", "'100664878'", "'101977480'", "'101977682'", "'103884168'", "'104230610'", "'105461428'")

_VOICE_BOT_IDS_INT_SQL = ",".join(str(c) for c in _VOICE_BOT_IDS_INT)
_VOICE_BOT_IDS_STR_SQL = ",".join(_VOICE_BOT_IDS_STR)

_NOTE_IDS_ATTEMPTED     = (19,20,21,22,23,24,25,27,28,30,31,37,38,43,44,45,46,58,60,62,64,66,68,70,72,74,76,78,80,82,84,86,88,90,92,94,96,98,100)
_NOTE_IDS_ATTEMPTED_SQL = ",".join(str(n) for n in _NOTE_IDS_ATTEMPTED)

_NOTE_IDS_CONNECTED     = (20,21,22,23,24,25,27,31,38,42,43,44,46,58,60,62,64,66,68,70,72,74,76,78,80,82,84,86,88,90,92,94,96,98,100)
_NOTE_IDS_CONNECTED_SQL = ",".join(str(n) for n in _NOTE_IDS_CONNECTED)


def _target_day():
    return datetime.now() - timedelta(days=2)


def _alloc_hour_bucket(alloc_dt):
    if alloc_dt is None:
        return "rest hrs"
    h = alloc_dt.hour
    if 9 <= h < 12:
        return "9-12"
    if 12 <= h < 15:
        return "12-15"
    if 15 <= h < 18:
        return "15-18"
    return "rest hrs"


def _export_excel(alloc_map, first_attempts, first_connected, target_day, cslr_map):
    import pandas as pd
    records = []
    for uid, info in alloc_map.items():
        ds      = info["ds_score"]
        bucket  = int(ds // 10) * 10 if ds is not None else None
        alloc_t = info["allocation_time"]
        attempt = first_attempts.get(uid)
        call_t  = attempt["first_call_time"] if attempt else None
        note_id = attempt["first_note_id"]   if attempt else None

        attempted = 0
        delta_hrs = None
        if call_t and alloc_t and (call_t - alloc_t).total_seconds() >= 0:
            attempted = 1
            delta_hrs = round((call_t - alloc_t).total_seconds() / 3600, 2)

        conn_t    = first_connected.get(uid)
        connected = 1 if conn_t and alloc_t and (conn_t - alloc_t).total_seconds() >= 0 else 0

        cslr_id   = info.get("counsellor_id")
        cslr_info = cslr_map.get(cslr_id, {})

        lct = info.get("lead_conversion_type")

        records.append({
            "user_id":              uid,
            "counsellor_id":        cslr_id,
            "counsellor_name":      cslr_info.get("counsellor_name"),
            "team_name":            cslr_info.get("team_name"),
            "lead_conversion_type": lct,
            "allocation_source":    "Request a callback" if lct == "requestCallback" else "other",
            "allocation_time":      alloc_t,
            "alloc_hour_bucket":    _alloc_hour_bucket(alloc_t),
            "ds_score":             ds,
            "ds_bucket":            f"{bucket}-{bucket+9}" if bucket is not None else "no_ds",
            "first_call_time":      call_t,
            "first_note_id":        note_id,
            "attempted":            attempted,
            "connected":            connected,
            "time_to_call_hrs":     delta_hrs,
        })

    os.makedirs(_DATA_STORE, exist_ok=True)
    out_path = os.path.join(
        _DATA_STORE,
        f"{target_day.strftime('%Y-%m-%d')}_first_call_byDSDB.xlsx",
    )
    import pandas as pd
    df = pd.DataFrame(records, columns=[
        "user_id", "counsellor_id", "counsellor_name", "team_name",
        "lead_conversion_type", "allocation_source",
        "allocation_time", "alloc_hour_bucket", "ds_score", "ds_bucket",
        "first_call_time", "first_note_id", "attempted", "connected", "time_to_call_hrs",
    ])
    df.sort_values(["ds_bucket", "allocation_time"], inplace=True, ignore_index=True)
    df.to_excel(out_path, index=False)
    log.info(f"Exported {len(df)} rows → {out_path}")


def fetch():
    target_day  = _target_day()
    alloc_start = target_day.strftime("%Y-%m-%d 00:00:00")
    alloc_end   = target_day.strftime("%Y-%m-%d 23:59:59")
    log.info(f"Target day: {alloc_start[:10]}")

    expected_file = os.path.join(_DATA_STORE, f"{target_day.strftime('%Y-%m-%d')}_first_call_byDSDB.xlsx")
    if os.path.exists(expected_file):
        log.info(f"Already up to date: {expected_file}. Skipping.")
        return

    from dbconnections import get_db_handle
    db_conn = get_db_handle(database="counselling", mysqldb=8)
    cursor  = db_conn.cursor(dictionary=True)
    cursor.execute("SET SESSION MAX_EXECUTION_TIME=90000")

    sql_alloc = f"""
        SELECT
            slad.user_id,
            slad.allocation_time,
            slad.ds_score,
            slad.lead_conversion_type,
            rmc.counsellor_id
        FROM counselling.sd_lead_allocation_details slad
        JOIN counselling.sa_rmc_user rmc
            ON  rmc.user_id       = slad.user_id
            AND rmc.platform      = 'domestic'
            AND rmc.status        IN ('live', 'dropoff')
            AND rmc.created_on    > '2026-01-01 00:00:00'
            AND rmc.counsellor_id NOT IN ({_VOICE_BOT_IDS_INT_SQL})
        WHERE slad.status          IN ('live', 'dropoff')
          AND slad.allocation_time >= %s
          AND slad.allocation_time <= %s
    """
    log.info("Running alloc query...")
    cursor.execute(sql_alloc, (alloc_start, alloc_end))
    alloc_rows = cursor.fetchall()
    log.info(f"{len(alloc_rows)} leads fetched")

    if not alloc_rows:
        cursor.close()
        db_conn.close()
        log.info("No leads allocated on this day. Exiting.")
        return

    sql_cslr = """
        SELECT rms.counsellor_id, rms.counsellor_name,
               rms.team_id, t.team_name
        FROM counselling.RMS_counsellor rms
        JOIN counselling.sa_team t
            ON t.team_id = rms.team_id AND t.status = 'live'
        WHERE rms.status   IN ('live','deleted')
          AND rms.platform = 'domestic'
    """
    cursor.execute(sql_cslr)
    cslr_map = {
        row["counsellor_id"]: {
            "counsellor_name": row.get("counsellor_name"),
            "team_name":       row.get("team_name"),
        }
        for row in cursor.fetchall()
    }

    alloc_map = {}
    for row in alloc_rows:
        uid = row["user_id"]
        if uid not in alloc_map:
            alloc_map[uid] = {
                "allocation_time":      row["allocation_time"],
                "ds_score":             row["ds_score"],
                "lead_conversion_type": row.get("lead_conversion_type"),
                "counsellor_id":        row.get("counsellor_id"),
            }

    user_ids_sql = ",".join(str(u) for u in alloc_map.keys())

    sql_notes = f"""
        SELECT
            note.user_id,
            MIN(note.added_on) AS first_call_time,
            CAST(SUBSTRING_INDEX(
                GROUP_CONCAT(note.note_id ORDER BY note.added_on ASC), ',', 1
            ) AS UNSIGNED) AS first_note_id
        FROM counselling.sa_rmc_user_notes note
        WHERE note.user_id       IN ({user_ids_sql})
          AND note.note_id       IN ({_NOTE_IDS_ATTEMPTED_SQL})
          AND note.added_on      >= %s
          AND note.counsellor_id NOT IN ({_VOICE_BOT_IDS_STR_SQL})
        GROUP BY note.user_id
    """
    log.info("Running notes query...")
    cursor.execute(sql_notes, (alloc_start,))
    first_attempts = {
        row["user_id"]: {
            "first_call_time": row["first_call_time"],
            "first_note_id":   row.get("first_note_id"),
        }
        for row in cursor.fetchall()
    }

    sql_connected = f"""
        SELECT
            note.user_id,
            MIN(note.added_on) AS first_connected_time
        FROM counselling.sa_rmc_user_notes note
        WHERE note.user_id       IN ({user_ids_sql})
          AND note.note_id       IN ({_NOTE_IDS_CONNECTED_SQL})
          AND note.added_on      >= %s
          AND note.counsellor_id NOT IN ({_VOICE_BOT_IDS_STR_SQL})
        GROUP BY note.user_id
    """
    log.info("Running connected query...")
    cursor.execute(sql_connected, (alloc_start,))
    first_connected = {row["user_id"]: row["first_connected_time"] for row in cursor.fetchall()}
    cursor.close()
    db_conn.close()

    _export_excel(alloc_map, first_attempts, first_connected, target_day, cslr_map)


if __name__ == "__main__":
    fetch()
