import pandas as pd
from datetime import datetime, date, time
from dotenv import load_dotenv
from .dbconnections import get_db_handle
from . import find_file

load_dotenv()

CALL_LOGS_QUERY = """
    SELECT
        log.id            AS call_id,
        log.user_id,
        log.counsellor_id,
        rms.counsellor_name,
        team.team_id,
        team.team_name,
        log.file_name,
        log.duration,
        log.file_creation_date,
        log.created_on    AS created_on
    FROM counselling.sa_counsellor_call_log log
    JOIN counselling.RMS_counsellor rms
        ON rms.counsellor_id = log.counsellor_id
       AND rms.status IN ('live', 'deleted')
       AND rms.platform = 'domestic'
    JOIN counselling.sa_team team
        ON team.team_id = rms.team_id
       AND team.status = 'live'
    WHERE log.created_on > %s AND log.created_on < %s
"""


def update_call_logs():
    path = find_file("call_logs.xlsx", "call logs")
    existing = pd.read_excel(path)
    existing["created_on"] = pd.to_datetime(existing["created_on"])

    if existing.empty:
        print("  ABORT: existing file is empty — will not overwrite with partial fetch.")
        return

    max_date = existing["created_on"].max()
    today_start = datetime.combine(date.today(), time.min)
    print(f"  Existing rows: {len(existing)}  |  Latest date: {max_date}")

    conn = get_db_handle("counselling", mysqldb=8)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(CALL_LOGS_QUERY, (max_date, today_start))
    new_df = pd.DataFrame(cursor.fetchall())
    cursor.close()
    conn.close()

    if new_df.empty:
        print("  No new rows found. File unchanged.")
        return

    new_df["created_on"] = pd.to_datetime(new_df["created_on"])
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.drop_duplicates(subset=["call_id"], keep="last", inplace=True)
    combined.sort_values("created_on", inplace=True)

    if len(combined) < len(existing):
        print(f"  ABORT: combined row count ({len(combined)}) is less than existing ({len(existing)}). File unchanged.")
        return

    combined.to_excel(path, index=False)
    print(f"  Appended {len(new_df)} rows. Total: {len(combined)}. Saved to {path}")
