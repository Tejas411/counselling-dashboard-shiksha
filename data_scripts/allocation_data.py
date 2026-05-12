import numpy as np
if not hasattr(np, 'float_'):
    np.float_ = np.float64

import sys
import os
import pandas as pd
from elastic_connections import get_es_client
from dbconnections import get_db_handle
from data_scripts import DATASTORE

BOT_COUNSELLOR_IDS = [
    99132516,   # LQB1 (high priority)
    99777644,   # LQB2 (low priority)
    100080242,  # Application nudge bot
    98378484,   # LQB1 (high priority)
    100664878,  # LQB Incoming
    100872980,  # Shortlist bot
    101977480,  # LQB1 (high priority)
    101977682,  # Shortlist bot
    104230610,  # LQB2 (low priority)
    103884168,  # Counselling bot
    105461428,  # Shortlist bot (low priority)
    12345678,   # Campaigns bot
]

BOT_COUNSELLOR_IDS_SET = set(BOT_COUNSELLOR_IDS)

COLUMNS = [
    'userId', 'leadLabel', 'latestLeadLabel', 'eventType',
    'counsellorId', 'actionTime', 'date', 'allocationEventType',
    'previousCounsellorId', 'actionTakenBy', 'dsScoreES', 'ds_score', 'ds_score_bucket',
    'is_human_transfered', 'bot_transfered',
    'is_attempted', 'number_of_attempted_days', 'first_attempted_at',
    'is_connected', 'number_of_call_days', 'first_connected_at',
    'dialer_attempts', 'dialer_connects'
]

def fetch_ds_scores(user_ids):
    if not user_ids:
        return {}

    db = get_db_handle(database="counselling", mysqldb=8)
    cursor = db.cursor()
    ds_score_map = {}
    batch_size = 1000

    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i : i + batch_size]
        placeholders = ", ".join(["%s"] * len(batch))
        query = (
            f"SELECT user_id, ds_score, FLOOR(ds_score/10)*10 AS ds_score_bucket "
            f"FROM counselling.sd_lead_allocation_details "
            f"WHERE user_id IN ({placeholders}) "
            f"AND status IN ('live', 'dropoff')"
        )
        cursor.execute(query, batch)
        for user_id, ds_score, ds_score_bucket in cursor.fetchall():
            ds_score_map[user_id] = (ds_score, ds_score_bucket)
        print(f"  ds_score batch {i // batch_size + 1}: fetched {len(batch)} users")

    cursor.close()
    db.close()
    print(f"ds_score mapped for {len(ds_score_map)} users out of {len(user_ids)}")
    return ds_score_map


def fetch_attempted_users(es, index, start_date, end_date):
    attempt_query = {
        "bool": {
            "must": [
                {"term": {"eventType": "notePosted"}},
                {"terms": {"currNoteContactedStatus": ["touched_spoken", "touched_not_spoken"]}},
                {"term": {"platform": "domestic"}},
                {
                    "range": {
                        "actionTime": {
                            "gte": f"{start_date}T00:00:00",
                            "lte": f"{end_date}T23:59:59"
                        }
                    }
                }
            ],
            "must_not": [
                {"terms": {"counsellorId": BOT_COUNSELLOR_IDS}}
            ]
        }
    }

    print("Fetching attempted users from ES...")
    page = es.search(index=index, query=attempt_query, scroll="2m", size=1000)
    scroll_id = page["_scroll_id"]
    hits = page["hits"]["hits"]
    total = page["hits"].get("total", {})
    print(f"Total attempt documents: {total.get('value', 0) if isinstance(total, dict) else total}")

    user_dates = {}
    user_first_attempt = {}
    while hits:
        for hit in hits:
            src = hit["_source"]
            uid = src.get("userId")
            action_time = src.get("actionTime", "")
            date = action_time[:10] if action_time else None
            if uid and date:
                user_dates.setdefault(uid, set()).add(date)
                if uid not in user_first_attempt or action_time < user_first_attempt[uid]:
                    user_first_attempt[uid] = action_time

        page = es.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = page["_scroll_id"]
        hits = page["hits"]["hits"]

    es.clear_scroll(scroll_id=scroll_id)
    print(f"Unique attempted users: {len(user_dates)}")
    return user_dates, user_first_attempt


def fetch_connected_users(es, index, start_date, end_date):
    connect_query = {
        "bool": {
            "must": [
                {"term": {"eventType": "notePosted"}},
                {"term": {"currNoteContactedStatus": "touched_spoken"}},
                {"term": {"platform": "domestic"}},
                {
                    "range": {
                        "actionTime": {
                            "gte": f"{start_date}T00:00:00",
                            "lte": f"{end_date}T23:59:59"
                        }
                    }
                }
            ],
            "must_not": [
                {"terms": {"counsellorId": BOT_COUNSELLOR_IDS}}
            ]
        }
    }

    print("Fetching connected users from ES...")
    page = es.search(index=index, query=connect_query, scroll="2m", size=1000)
    scroll_id = page["_scroll_id"]
    hits = page["hits"]["hits"]
    total = page["hits"].get("total", {})
    print(f"Total connected documents: {total.get('value', 0) if isinstance(total, dict) else total}")

    user_dates = {}
    user_first_connect = {}
    while hits:
        for hit in hits:
            src = hit["_source"]
            uid = src.get("userId")
            action_time = src.get("actionTime", "")
            date = action_time[:10] if action_time else None
            if uid and date:
                user_dates.setdefault(uid, set()).add(date)
                if uid not in user_first_connect or action_time < user_first_connect[uid]:
                    user_first_connect[uid] = action_time

        page = es.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = page["_scroll_id"]
        hits = page["hits"]["hits"]

    es.clear_scroll(scroll_id=scroll_id)
    print(f"Unique connected users: {len(user_dates)}")
    return user_dates, user_first_connect


def fetch_dialer_stats(es, index, start_date, end_date):
    dialer_query = {
        "bool": {
            "must": [
                {"terms": {"noteId": [37, 38]}},
                {"term": {"platform": "domestic"}},
                {
                    "range": {
                        "actionTime": {
                            "gte": f"{start_date}T00:00:00",
                            "lte": f"{end_date}T23:59:59"
                        }
                    }
                }
            ],
            "must_not": [
                {"terms": {"counsellorId": BOT_COUNSELLOR_IDS}}
            ]
        }
    }

    print("Fetching dialer stats from ES...")
    page = es.search(index=index, query=dialer_query, scroll="2m", size=1000)
    scroll_id = page["_scroll_id"]
    hits = page["hits"]["hits"]
    total = page["hits"].get("total", {})
    print(f"Total dialer documents: {total.get('value', 0) if isinstance(total, dict) else total}")

    dialer_attempts = {}
    dialer_connects = {}
    while hits:
        for hit in hits:
            src = hit["_source"]
            uid = src.get("userId")
            note_id = src.get("noteId")
            if uid is None:
                continue
            if note_id == 37:
                dialer_attempts[uid] = dialer_attempts.get(uid, 0) + 1
            elif note_id == 38:
                dialer_connects[uid] = dialer_connects.get(uid, 0) + 1

        page = es.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = page["_scroll_id"]
        hits = page["hits"]["hits"]

    es.clear_scroll(scroll_id=scroll_id)
    print(f"Dialer attempted users: {len(dialer_attempts)} | Dialer connected users: {len(dialer_connects)}")
    return dialer_attempts, dialer_connects


def fetch_counselling_allocations(start_date="2026-05-01", end_date="2026-05-11"):
    es = get_es_client()
    if es is None:
        print("Failed to connect to Elasticsearch. Exiting.")
        sys.exit(1)

    year = start_date.split("-")[0]
    index = f"shiksha_user_counselling_events_y{year}"

    es_query = {
        "bool": {
                "must": [
                    {
                        "terms": {
                            "eventType": ["counsellorAllocated", "counsellorChanged"]
                        }
                    },
                    {
                        "range": {
                            "actionTime": {
                                "gte": f"{start_date}T00:00:00",
                                "lte": f"{end_date}T23:59:59"
                            }
                        }
                    },
                    {
                        "term": {
                            "platform": "domestic"
                        }
                    }
                ],
                "must_not": [
                    {
                        "terms": {
                            "counsellorId": BOT_COUNSELLOR_IDS
                        }
                    }
                ]
        }
    }

    print(f"Querying index: {index} for range: {start_date} to {end_date}")

    page = es.search(index=index, query=es_query, scroll="2m", size=1000)
    scroll_id = page["_scroll_id"]
    hits = page["hits"]["hits"]
    total = page["hits"].get("total", {})
    total_count = total.get("value", 0) if isinstance(total, dict) else total
    print(f"Total matching documents: {total_count}")

    records = []

    while hits:
        for hit in hits:
            src = hit["_source"]
            event_type = src.get("eventType", "")
            if isinstance(event_type, list):
                event_type = ", ".join(event_type)

            records.append({
                "userId":               src.get("userId", ""),
                "leadLabel":            src.get("leadLabel", ""),
                "latestLeadLabel":      src.get("latestLeadLabel", ""),
                "eventType":            event_type,
                "counsellorId":         src.get("counsellorId", ""),
                "actionTime":           src.get("actionTime", ""),
                "date":                 src.get("actionTime", "")[:10] if src.get("actionTime") else "",
                "allocationEventType":  src.get("allocationEventType", ""),
                "previousCounsellorId": src.get("previousCounsellorId", ""),
                "actionTakenBy":        src.get("actionTakenBy", ""),
                "dsScoreES":            src.get("dsScore", ""),
                "ds_score":             "",
            })

        page = es.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = page["_scroll_id"]
        hits = page["hits"]["hits"]

    es.clear_scroll(scroll_id=scroll_id)
    print(f"Records fetched: {len(records)}")

    df = pd.DataFrame(records, columns=COLUMNS)
    df = df[df["counsellorId"].notna() & (df["counsellorId"] != "")]
    print(f"Records after dropping missing counsellorId: {len(df)}")

    before = len(df)
    df.drop_duplicates(subset=["userId", "actionTime", "eventType", "counsellorId"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f"Duplicates removed: {before - len(df)} | Unique records: {len(df)}")

    # --- Step 2: enrich ds_score from MySQL in batches of 1000 ---
    user_ids = df["userId"].dropna().astype(int).unique().tolist()
    ds_score_map = fetch_ds_scores(user_ids)
    df["ds_score"]        = df["userId"].map(lambda uid: ds_score_map.get(int(uid), (np.nan, np.nan))[0] if pd.notna(uid) else np.nan)
    df["ds_score_bucket"] = df["userId"].map(lambda uid: ds_score_map.get(int(uid), (np.nan, np.nan))[1] if pd.notna(uid) else np.nan)

    def is_human(val):
        try:
            return pd.notna(val) and val != "" and int(val) not in BOT_COUNSELLOR_IDS_SET
        except (ValueError, TypeError):
            return False

    df["is_human_transfered"] = (
        df["counsellorId"].apply(is_human) & df["previousCounsellorId"].apply(is_human)
    ).astype(int)

    def is_bot(val):
        try:
            return pd.notna(val) and val != "" and int(val) in BOT_COUNSELLOR_IDS_SET
        except (ValueError, TypeError):
            return False

    df["bot_transfered"] = df["previousCounsellorId"].apply(is_bot).astype(int)

    # --- Step 3: attempted users from ES ---
    user_dates, user_first_attempt = fetch_attempted_users(es, index, start_date, end_date)
    df["is_attempted"]             = df["userId"].map(lambda uid: 1 if uid in user_dates else 0)
    df["number_of_attempted_days"] = df["userId"].map(lambda uid: len(user_dates[uid]) if uid in user_dates else 0)
    df["first_attempted_at"]       = df["userId"].map(lambda uid: user_first_attempt.get(uid))

    # --- Step 4: connected users from ES ---
    connect_dates, user_first_connect = fetch_connected_users(es, index, start_date, end_date)
    df["is_connected"]        = df["userId"].map(lambda uid: 1 if uid in connect_dates else 0)
    df["number_of_call_days"] = df["userId"].map(lambda uid: len(connect_dates[uid]) if uid in connect_dates else 0)
    df["first_connected_at"]  = df["userId"].map(lambda uid: user_first_connect.get(uid))

    # --- Step 5: dialer attempts & connects from ES ---
    dialer_attempts, dialer_connects = fetch_dialer_stats(es, index, start_date, end_date)
    df["dialer_attempts"] = df["userId"].map(lambda uid: dialer_attempts.get(uid, 0))
    df["dialer_connects"] = df["userId"].map(lambda uid: dialer_connects.get(uid, 0))

    # --- Step 6: allocation_source (priority-ordered) ---
    prev_is_bot   = df["previousCounsellorId"].apply(is_bot)
    action_is_bot = df["actionTakenBy"].apply(is_bot)
    df["allocation_source"] = np.select(
        [
            df["leadLabel"] == "RCB",
            df["allocationEventType"] == "sdTeamPoolBasedCounsellorAllocationEvent",
            prev_is_bot & ~action_is_bot,
            prev_is_bot & action_is_bot,
        ],
        [
            "Request a callback",
            "Pulled from team pool",
            "TL transferred",
            "Bot transferred",
        ],
        default="Other",
    )

    # Replace empty strings with NaN so cells appear blank in Excel
    df = df.mask(df == "")

    output_file = os.path.join(DATASTORE, "counselling_allocation.xlsx")
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Allocations")
        ws = writer.sheets["Allocations"]
        # Auto-fit column widths
        for col_cells in ws.columns:
            max_len = max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 40)

    print(f"Exported to: {output_file}")


if __name__ == "__main__":
    start = sys.argv[1] if len(sys.argv) > 1 else "2026-05-01"
    end   = sys.argv[2] if len(sys.argv) > 2 else "2026-05-11"
    fetch_counselling_allocations(start, end)
