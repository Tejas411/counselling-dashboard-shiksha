import os
import pandas as pd
from datetime import datetime, date, time
from dotenv import load_dotenv
from .dbconnections import get_db_handle
from . import find_file, DATASTORE

load_dotenv()

RESPONSE_CREATION_QUERY = """
    SELECT userId AS user_id, counsellorId AS counsellor_id, uilpId AS uilp_id,
           baseCourseId AS base_course, isClient AS is_client, createdOn AS created_on
    FROM counselling.sdResponseCreationData srcd
    LEFT JOIN counselling.RMS_counsellor rms
        ON rms.counsellor_id = srcd.counsellorId
       AND rms.status = 'live'
       AND rms.platform = 'domestic'
    LEFT JOIN counselling.sa_team team
        ON team.team_id = rms.team_id
       AND team.status = 'live'
    WHERE srcd.createdOn > %s AND srcd.createdOn < %s
"""

SHORTLIST_RESPONSE_QUERY = """
    SELECT user_id, loggedin_user_id AS counsellor_id, is_paid AS is_client,
           entity_id AS uilp_id, subentity_id AS base_course, usd.created AS created_on
    FROM counselling.user_shortlist_data usd
    LEFT JOIN counselling.RMS_counsellor rms
        ON rms.counsellor_id = usd.loggedin_user_id
       AND rms.status = 'live'
       AND rms.platform = 'domestic'
    LEFT JOIN counselling.sa_team team
        ON team.team_id = rms.team_id
       AND team.status = 'live'
    WHERE loggedin_user_type = 'counsellor'
      AND updated > %s AND updated < %s
      AND usd.status = 'live'
      AND shortlisted = 1
"""


def update_response_creation():
    path = find_file("Responses_Created_By_Counsellors*.xlsx", "response creation data")
    existing = pd.read_excel(path)
    existing.rename(columns={"createdOn": "created_on"}, inplace=True)
    existing["created_on"] = pd.to_datetime(existing["created_on"])

    if existing.empty:
        print("  ABORT: existing file is empty — will not overwrite with partial fetch.")
        return

    max_date = existing["created_on"].max()
    today_start = datetime.combine(date.today(), time.min)
    print(f"  Existing rows: {len(existing)}  |  Latest date: {max_date}")

    conn = get_db_handle("counselling", mysqldb=8)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(RESPONSE_CREATION_QUERY, (max_date, today_start))
    new_df = pd.DataFrame(cursor.fetchall())
    cursor.close()
    conn.close()

    if new_df.empty:
        print("  No new rows found. File unchanged.")
        return

    new_df["created_on"] = pd.to_datetime(new_df["created_on"])
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.drop_duplicates(subset=["user_id", "uilp_id", "base_course", "created_on"], keep="last", inplace=True)
    combined.sort_values("created_on", inplace=True)

    if len(combined) < len(existing):
        print(f"  ABORT: combined row count ({len(combined)}) is less than existing ({len(existing)}). File unchanged.")
        return

    combined.to_excel(path, index=False)
    print(f"  Appended {len(new_df)} rows. Total: {len(combined)}. Saved to {path}")


def update_shortlist_responses():
    path = find_file("edit-shortlist-responses*.xlsx", "shortlist responses")
    existing = pd.read_excel(path)
    existing.rename(columns={"is_paid": "is_client"}, inplace=True)
    existing["created_on"] = pd.to_datetime(existing["created_on"])

    if existing.empty:
        print("  ABORT: existing file is empty — will not overwrite with partial fetch.")
        return

    max_date = existing["created_on"].max()
    today_start = datetime.combine(date.today(), time.min)
    print(f"  Existing rows: {len(existing)}  |  Latest date: {max_date}")

    conn = get_db_handle("counselling", mysqldb=8)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(SHORTLIST_RESPONSE_QUERY, (max_date, today_start))
    new_df = pd.DataFrame(cursor.fetchall())
    cursor.close()
    conn.close()

    if new_df.empty:
        print("  No new rows found. File unchanged.")
        return

    new_df["created_on"] = pd.to_datetime(new_df["created_on"])
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.drop_duplicates(subset=["user_id", "uilp_id", "base_course"], keep="last", inplace=True)
    combined.sort_values("created_on", inplace=True)

    if len(combined) < len(existing):
        print(f"  ABORT: combined row count ({len(combined)}) is less than existing ({len(existing)}). File unchanged.")
        return

    combined.to_excel(path, index=False)
    print(f"  Appended {len(new_df)} rows. Total: {len(combined)}. Saved to {path}")


BASE_COURSE_MAPPING_QUERY = """
    SELECT bc.base_course_id, bc.name AS base_course_name
    FROM baseentities.base_courses bc
    WHERE status = 'live'
"""


def update_base_course_mapping():
    out_path = os.path.join(DATASTORE, "base_course_mapping.xlsx")
    conn = get_db_handle("counselling", mysqldb=8)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(BASE_COURSE_MAPPING_QUERY)
    df = pd.DataFrame(cursor.fetchall())
    cursor.close()
    conn.close()

    if df.empty:
        print("  No base course data returned. File unchanged.")
        return

    df.to_excel(out_path, index=False)
    print(f"  Saved {len(df)} base courses to {out_path}")
