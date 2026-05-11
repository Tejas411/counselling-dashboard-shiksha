import os
import glob as _glob
import pandas as pd

# ── Applications ───────────────────────────────────────────────────────────────
adf = pd.read_excel("data-store/counselling_application_sold_report.xlsx")
adf["creation_date"]               = pd.to_datetime(adf["creation_date"])
adf["application_submission_date"] = pd.to_datetime(adf["application_submission_date"])
adf["date_str"]                    = adf["creation_date"].dt.strftime("%d %b")
adf["sub_date_str"]                = adf["application_submission_date"].dt.strftime("%d %b")
adf["lead_source_clean"]           = adf["lead_source"].str.split(",").str[0].str.strip()

# ── Calls ──────────────────────────────────────────────────────────────────────
cdf = pd.read_excel("data-store/call_logs.xlsx")
cdf["created_on"]         = pd.to_datetime(cdf["created_on"])
cdf["file_creation_date"] = pd.to_datetime(cdf["file_creation_date"])
cdf["date_str"]           = cdf["created_on"].dt.strftime("%d %b")
cdf["dur_sec"]            = pd.to_numeric(cdf["duration"], errors="coerce").fillna(0).clip(lower=0)
cdf["dur_min"]            = cdf["dur_sec"] / 60

tl_df = pd.read_excel("data-store/counsellor-TL-mapping.xlsx")
tl_map = tl_df.drop_duplicates("counsellor_id").set_index("counsellor_id")["TL_name"]
cdf["TL_name"] = cdf["counsellor_id"].map(tl_map).fillna("Unmapped")

DUR_ORDER = ["< 1 min", "1 – 2 min", "2 – 5 min", "5 – 10 min", "> 10 min"]

def dur_bucket(s):
    if s < 60:  return "< 1 min"
    if s < 120: return "1 – 2 min"
    if s < 300: return "2 – 5 min"
    if s < 600: return "5 – 10 min"
    return "> 10 min"

cdf["dur_bucket"] = cdf["dur_sec"].apply(dur_bucket)

# ── Responses ──────────────────────────────────────────────────────────────────
_rdf1 = pd.read_excel("data-store/Responses_Created_By_Counsellors.xlsx")
_rdf1["created_on"] = pd.to_datetime(_rdf1["created_on"])
_rdf2 = pd.read_excel("data-store/edit-shortlist-responses.xlsx")
rdf = pd.concat([
    _rdf1[["user_id","counsellor_id","is_client","uilp_id","base_course","created_on"]].assign(source="Counsellor Created"),
    _rdf2.assign(source="Edit Shortlist"),
], ignore_index=True)
rdf["created_on"] = pd.to_datetime(rdf["created_on"])

_a_cnames = adf[["counsellor_id","counsellor_name"]].dropna().drop_duplicates("counsellor_id")
_c_cnames = cdf[["counsellor_id","counsellor_name"]].dropna().drop_duplicates("counsellor_id")
_r_cname_map = (pd.concat([_a_cnames, _c_cnames])
                .drop_duplicates("counsellor_id")
                .set_index("counsellor_id")["counsellor_name"])

rdf["counsellor_name"] = rdf["counsellor_id"].map(_r_cname_map).fillna(rdf["counsellor_id"].astype(str))
rdf["TL_name"]         = rdf["counsellor_id"].map(tl_map).fillna("Unmapped")
rdf["client_label"]    = rdf["is_client"].map({1: "Client", 0: "Non-Client"})
rdf["date_str"]        = rdf["created_on"].dt.strftime("%d %b")

_bc_map_path = "data-store/base_course_mapping.xlsx"
if os.path.exists(_bc_map_path):
    _bc_df  = pd.read_excel(_bc_map_path)
    _bc_map = _bc_df.set_index("base_course_id")["base_course_name"]
else:
    _bc_map = (adf[["base_course_id", "base_course_name"]].dropna()
               .drop_duplicates("base_course_id")
               .set_index("base_course_id")["base_course_name"])

rdf["base_course_name"] = rdf["base_course"].map(_bc_map).fillna("Course " + rdf["base_course"].astype(str))

# ── Fresh Leads ────────────────────────────────────────────────────────────────
_fl_files = sorted(f for f in _glob.glob("data-store/*_first_call_byDSDB.xlsx")
                   if not os.path.basename(f).startswith("~$"))
if _fl_files:
    fldf = pd.read_excel(_fl_files[-1])
    fldf["allocation_time"]  = pd.to_datetime(fldf["allocation_time"])
    fldf["time_to_call_hrs"] = pd.to_numeric(fldf["time_to_call_hrs"], errors="coerce")
    _fl_date = os.path.basename(_fl_files[-1])[:10]
else:
    fldf     = pd.DataFrame(columns=["alloc_hour_bucket","ds_bucket","team_name","attempted","connected","time_to_call_hrs"])
    _fl_date = "N/A"

_SLOT_ORDER = ["9-12", "12-15", "15-18", "rest hrs"]
_fl_slots   = [s for s in _SLOT_ORDER if len(fldf) and s in fldf["alloc_hour_bucket"].values]
_fl_teams   = sorted(fldf["team_name"].dropna().unique()) if len(fldf) and "team_name" in fldf.columns else []
_DS_ORDER   = [f"{i*10}-{i*10+9}" for i in range(10)] + ["no_ds"]

_FL_COLS = [
    {"name": "DS Bucket",  "id": "ds_bucket"},
    {"name": "Allocated",  "id": "allocated",  "type": "numeric"},
    {"name": "Attempted",  "id": "attempted",  "type": "numeric"},
    {"name": "Connected",  "id": "connected",  "type": "numeric"},
    {"name": "Connect %",  "id": "connect_pct"},
    {"name": "≤ 30 min %", "id": "w30_pct"},
    {"name": "≤ 60 min %", "id": "w60_pct"},
]

def _build_fl_table(d):
    rows = []
    tot_alloc = tot_att = tot_conn = tot_w30 = tot_w60 = 0
    for bucket in _DS_ORDER:
        sub = d[d["ds_bucket"] == bucket]
        if len(sub) == 0:
            continue
        alloc = len(sub)
        att   = int(sub["attempted"].sum())
        conn  = int(sub["connected"].sum())
        w30   = int(((sub["time_to_call_hrs"] >= 0) & (sub["time_to_call_hrs"] <= 0.5)).sum())
        w60   = int(((sub["time_to_call_hrs"] >= 0) & (sub["time_to_call_hrs"] <= 1.0)).sum())
        tot_alloc += alloc; tot_att += att; tot_conn += conn
        tot_w30 += w30; tot_w60 += w60
        rows.append({
            "ds_bucket":   bucket,
            "allocated":   alloc,
            "attempted":   att,
            "connected":   conn,
            "connect_pct": f"{conn/alloc*100:.1f}%" if alloc else "—",
            "w30_pct":     f"{w30/alloc*100:.1f}%" if alloc else "—",
            "w60_pct":     f"{w60/alloc*100:.1f}%" if alloc else "—",
        })
    rows.append({
        "ds_bucket":   "TOTAL",
        "allocated":   tot_alloc,
        "attempted":   tot_att,
        "connected":   tot_conn,
        "connect_pct": f"{tot_conn/tot_alloc*100:.1f}%" if tot_alloc else "—",
        "w30_pct":     f"{tot_w30/tot_alloc*100:.1f}%" if tot_alloc else "—",
        "w60_pct":     f"{tot_w60/tot_alloc*100:.1f}%" if tot_alloc else "—",
    })
    return rows

# ── Filter options ─────────────────────────────────────────────────────────────
a_teams       = sorted(adf["team_name"].dropna().unique())
a_tls         = sorted(adf["TL_name"].dropna().unique())
a_statuses    = sorted(adf["status"].dropna().unique())
a_counsellors = sorted(adf["counsellor_name"].dropna().unique())
c_teams       = sorted(cdf["team_name"].dropna().unique())
c_tls         = sorted(cdf["TL_name"].dropna().unique())
c_counsellors = sorted(cdf["counsellor_name"].dropna().unique(), key=str)
r_tls         = sorted(rdf["TL_name"].dropna().unique())
r_counsellors = sorted(rdf["counsellor_name"].dropna().unique())
r_last_date   = rdf["created_on"].max().date()
r_default_start = r_last_date - pd.Timedelta(days=14)
