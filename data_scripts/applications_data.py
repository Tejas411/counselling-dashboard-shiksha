import pandas as pd
from datetime import datetime, date, time
from dotenv import load_dotenv
from .dbconnections import get_db_handle
from . import find_file

load_dotenv()

START_DATE = "2026-05-01"

APP_SOLD_QUERY = """
    SELECT
        id, counsellor_id, team_lead_id, student_user_id,
        institute_id, base_course_id,
        application_screenshot_path, payment_screenshot_path,
        call_recording_id, last_call_date, application_submission_date,
        assisted_by_counsellor, lead_source, attribution, remarks,
        creation_date, updation_date, updated_by, status, rejection_reason
    FROM counselling.application_sold_by_counsellor
    WHERE creation_date >= %s AND creation_date < %s
    ORDER BY 1 DESC
"""

COUNSELLOR_QUERY = """
    SELECT counsellor_id, counsellor_name, counsellor_email, rms.team_id, t.team_name
    FROM counselling.RMS_counsellor rms
    JOIN counselling.sa_team t ON t.team_id = rms.team_id AND t.status = 'live'
    WHERE rms.status IN ('live', 'deleted') AND rms.platform = 'domestic'
"""

BASE_COURSE_QUERY = """
    SELECT bc.base_course_id, bc.name AS base_course_name
    FROM baseentities.base_courses bc
    WHERE status = 'live'
"""


def update_app_sold():
    path = find_file("counselling_application_sold_report.xlsx", "applications sold")
    today_start = datetime.combine(date.today(), time.min)

    conn8 = get_db_handle("counselling", mysqldb=8)
    cursor = conn8.cursor(dictionary=True)
    cursor.execute(APP_SOLD_QUERY, (START_DATE, today_start))
    df = pd.DataFrame(cursor.fetchall())
    cursor.close()

    if df.empty:
        conn8.close()
        print("  No application records found.")
        return

    print(f"  Fetched {len(df)} application records.")

    cursor2 = conn8.cursor(dictionary=True)
    cursor2.execute(COUNSELLOR_QUERY)
    df_counsellors = pd.DataFrame(cursor2.fetchall())
    cursor2.close()

    cursor3 = conn8.cursor(dictionary=True)
    cursor3.execute(BASE_COURSE_QUERY)
    df_courses = pd.DataFrame(cursor3.fetchall())
    cursor3.close()
    conn8.close()

    df = df.merge(df_counsellors, on="counsellor_id", how="left")

    df_tl = df_counsellors[["counsellor_id", "counsellor_name"]].rename(
        columns={"counsellor_id": "team_lead_id", "counsellor_name": "TL_name"}
    )
    df = df.merge(df_tl, on="team_lead_id", how="left")

    if not df_courses.empty:
        df = df.merge(df_courses, on="base_course_id", how="left")

    institute_ids = [int(i) for i in df["institute_id"].dropna().unique().tolist()]

    if institute_ids:
        conn5 = get_db_handle("shiksha", mysqldb=5)
        cursor5 = conn5.cursor(dictionary=True)
        placeholders = ", ".join(["%s"] * len(institute_ids))

        cursor5.execute(
            f"SELECT listing_id, name AS college_name FROM shiksha.shiksha_institutes"
            f" WHERE status = 'live' AND listing_id IN ({placeholders})",
            institute_ids,
        )
        df_colleges = pd.DataFrame(cursor5.fetchall())
        df = df.merge(
            df_colleges.rename(columns={"listing_id": "institute_id"}),
            on="institute_id",
            how="left",
        )

        cursor5.execute(
            f"SELECT listing_type_id AS institute_id, username AS client_id"
            f" FROM shiksha.listings_main"
            f" WHERE listing_type IN ('institute', 'university_national')"
            f"   AND status = 'live' AND domain = 'national'"
            f"   AND listing_type_id IN ({placeholders})",
            institute_ids,
        )
        df_clients = pd.DataFrame(cursor5.fetchall())
        if not df_clients.empty:
            df = df.merge(df_clients, on="institute_id", how="left")

        cursor5.close()
        conn5.close()

    # Paid form mapping from application-form-fees.xlsx
    fees_path = find_file("application-form-fees.xlsx", "form fees")
    df_fees = pd.read_excel(fees_path, usecols=["client_id", "Paid form"])
    df_fees["client_id"] = df_fees["client_id"].astype(str)
    if "client_id" in df.columns:
        df["client_id"] = df["client_id"].astype(str)
        df = df.merge(df_fees, on="client_id", how="left")
        df["Paid form"] = df["Paid form"].map({1: "Paid form", 0: "Free form"}).fillna("NA")

    df["creation_date"] = pd.to_datetime(df["creation_date"])
    df.drop_duplicates(subset=["id"], keep="last", inplace=True)
    df.sort_values("creation_date", inplace=True)
    df.to_excel(path, index=False)
    print(f"  Saved {len(df)} rows to {path}")
