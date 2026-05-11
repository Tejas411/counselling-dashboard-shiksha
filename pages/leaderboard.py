from dash import html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import date, timedelta

from theme import (BG, SURFACE, SURFACE2, BORDER, TEXT, MUTED, ACCENT,
                   CARD, DROP_STYLE, flabel, kpi_card)

_fmt_duration = lambda s: (lambda h, m: f"{h}h {m}m" if h else f"{m}m")(
    max(0, int(s)) // 3600, (max(0, int(s)) % 3600) // 60)

def _kpi_card(title, value, color, sub="", width=2):
    return dbc.Col(html.Div([
        html.Div(style={"height": "3px", "backgroundColor": color,
                        "borderRadius": "12px 12px 0 0", "marginBottom": "16px"}),
        html.P(title, style={"color": MUTED, "fontSize": "10px", "fontWeight": "600",
                              "letterSpacing": "0.08em", "textTransform": "uppercase",
                              "margin": "0 0 6px"}),
        html.Div(str(value), style={"color": TEXT, "fontSize": "24px", "fontWeight": "700",
                                    "fontFamily": "Inter, sans-serif",
                                    "letterSpacing": "-0.02em"}),
        html.P(sub, style={"color": color, "fontSize": "11px", "margin": "4px 0 0"}),
    ], style={**CARD, "padding": "0 20px 18px", "borderTop": "none"}), width=width)


def leaderboard_content(adf, cdf, rdf):
    today       = date.today()
    yesterday   = today - timedelta(days=1)
    month_start = today.replace(day=1)

    teams = sorted(cdf["team_name"].dropna().unique())
    tls   = sorted(cdf["TL_name"].dropna().unique())

    return dbc.Container(fluid=True,
        style={"backgroundColor": BG, "minHeight": "100vh", "padding": "32px 28px"},
        children=[
            dbc.Row([
                dbc.Col([flabel("From"),
                    dcc.DatePickerSingle(
                        id="lb-date-from", date=month_start.isoformat(),
                        display_format="DD MMM YYYY",
                        style={"width": "100%"})], width=2),
                dbc.Col([flabel("To"),
                    dcc.DatePickerSingle(
                        id="lb-date-to", date=yesterday.isoformat(),
                        display_format="DD MMM YYYY",
                        style={"width": "100%"})], width=2),
                dbc.Col([flabel("Team"),
                    dcc.Dropdown(id="lb-team",
                        options=[{"label": t, "value": t} for t in teams],
                        multi=True, placeholder="All Teams", style=DROP_STYLE)], width=4),
                dbc.Col([flabel("Team Lead"),
                    dcc.Dropdown(id="lb-tl",
                        options=[{"label": t, "value": t} for t in tls],
                        multi=True, placeholder="All TLs", style=DROP_STYLE)], width=4),
            ], style={"marginBottom": "28px"}),

            dbc.Row(id="lb-kpi-row", className="g-3", style={"marginBottom": "20px"}),

            dbc.Row([
                dbc.Col([
                    flabel("Search Counsellor"),
                    dcc.Input(
                        id="lb-search", type="text",
                        placeholder="Type a name...", debounce=True,
                        style={
                            "width": "100%", "padding": "8px 12px", "fontSize": "13px",
                            "border": f"1px solid {BORDER}", "borderRadius": "8px",
                            "fontFamily": "Inter, sans-serif", "outline": "none",
                            "backgroundColor": SURFACE, "color": TEXT,
                        }),
                ], width=4),
            ], style={"marginBottom": "20px"}),

            html.Div(id="lb-table-container"),
        ])


def register_callbacks(app, adf, cdf, rdf):
    @app.callback(
        Output("lb-kpi-row",         "children"),
        Output("lb-table-container", "children"),
        Input("lb-date-from", "date"),
        Input("lb-date-to",   "date"),
        Input("lb-team",      "value"),
        Input("lb-tl",        "value"),
        Input("lb-search",    "value"),
    )
    def update_leaderboard(date_from, date_to, sel_teams, sel_tls, search):
        c = cdf.copy()
        if date_from:
            c = c[c["created_on"].dt.date >= pd.to_datetime(date_from).date()]
        if date_to:
            c = c[c["created_on"].dt.date <= pd.to_datetime(date_to).date()]
        if sel_teams:
            c = c[c["team_name"].isin(sel_teams)]
        if sel_tls:
            c = c[c["TL_name"].isin(sel_tls)]

        conn     = c[c["dur_sec"] > 0].copy()
        eligible = set(conn["counsellor_name"].dropna().unique())

        empty_kpis = [
            _kpi_card("Counsellors",     0,   ACCENT,    width=2),
            _kpi_card("Applications",    0,   "#16A34A", width=2),
            _kpi_card("Connected Calls", 0,   "#2563EB", width=2),
            _kpi_card("Avg Talk Time",   "—", "#7C3AED",
                      sub="avg / active day / counsellor", width=3),
            _kpi_card("Client Responses",0,   "#D97706", width=3),
        ]

        if not eligible:
            msg = html.P("No counsellors with connected calls in this period.",
                         style={"color": MUTED, "padding": "60px",
                                "textAlign": "center", "fontSize": "14px"})
            return empty_kpis, msg

        conn["_date"] = conn["created_on"].dt.date
        grp             = conn.groupby("counsellor_name")
        connected_calls = grp["dur_sec"].count().rename("connected_calls")
        total_talk_sec  = grp["dur_sec"].sum().rename("total_talk_sec")
        active_days     = grp["_date"].nunique().rename("active_days")
        avg_tt_per_day_sec = (
            conn.groupby(["counsellor_name", "_date"])["dur_sec"]
                .sum()
                .groupby(level="counsellor_name")
                .mean()
                .rename("avg_tt_per_day_sec")
        )

        a = adf.copy()
        if date_from:
            a = a[a["creation_date"].dt.date >= pd.to_datetime(date_from).date()]
        if date_to:
            a = a[a["creation_date"].dt.date <= pd.to_datetime(date_to).date()]
        a = a[a["counsellor_name"].isin(eligible)]
        apps = (a[a["status"].isin(["ACCEPTED", "PENDING"])]
                .groupby("counsellor_name").size()
                .rename("applications"))

        r = rdf.copy()
        if date_from:
            r = r[r["created_on"].dt.date >= pd.to_datetime(date_from).date()]
        if date_to:
            r = r[r["created_on"].dt.date <= pd.to_datetime(date_to).date()]
        r = r[r["counsellor_name"].isin(eligible)]
        client_resp = (r[r["is_client"] == 1]
                       .groupby("counsellor_name").size()
                       .rename("client_responses"))

        df = (pd.DataFrame(index=pd.Index(sorted(eligible), name="counsellor_name"))
              .join(connected_calls).join(total_talk_sec).join(active_days)
              .join(avg_tt_per_day_sec).join(apps).join(client_resp)
              .fillna(0))

        df["connected_calls"]  = df["connected_calls"].astype(int)
        df["active_days"]      = df["active_days"].astype(int)
        df["applications"]     = df["applications"].astype(int)
        df["client_responses"] = df["client_responses"].astype(int)
        df["call_to_app_pct"]  = (
            df["applications"] / df["connected_calls"].replace(0, 1) * 100
        ).round(1)

        df.sort_values(["applications", "connected_calls"], ascending=[False, False], inplace=True)
        df.insert(0, "Rank", range(1, len(df) + 1))
        df["Total Talk Time"]             = df["total_talk_sec"].apply(_fmt_duration)
        df["Avg. Talk Time / Active Day"] = df["avg_tt_per_day_sec"].apply(_fmt_duration)
        df["Call-to-App %"]               = df["call_to_app_pct"].apply(lambda x: f"{x:.1f}%")

        avg_tt = df["avg_tt_per_day_sec"].mean() if len(df) else 0
        kpi_children = [
            _kpi_card("Counsellors",     len(df),                         ACCENT,    width=2),
            _kpi_card("Applications",    int(df["applications"].sum()),    "#16A34A", width=2),
            _kpi_card("Connected Calls", int(df["connected_calls"].sum()), "#2563EB", width=2),
            _kpi_card("Avg Talk Time",   _fmt_duration(avg_tt),            "#7C3AED",
                      sub="avg / active day / counsellor", width=3),
            _kpi_card("Client Responses",int(df["client_responses"].sum()),"#D97706", width=3),
        ]

        display_df = df.reset_index()[[
            "Rank", "counsellor_name", "applications", "active_days",
            "Call-to-App %", "connected_calls",
            "Total Talk Time", "Avg. Talk Time / Active Day", "client_responses",
        ]].rename(columns={
            "counsellor_name":  "Counsellor",
            "applications":     "Applications",
            "active_days":      "Active Days",
            "connected_calls":  "Connected Calls",
            "client_responses": "Client Responses",
        })

        if search and search.strip():
            mask = display_df["Counsellor"].str.contains(search.strip(), case=False, na=False)
            display_df = display_df[mask]

        if display_df.empty:
            return kpi_children, html.P(
                f'No counsellors matching "{search}".',
                style={"color": MUTED, "padding": "40px", "textAlign": "center",
                       "fontSize": "14px"})

        table = dash_table.DataTable(
            data=display_df.to_dict("records"),
            columns=[{"name": col, "id": col} for col in display_df.columns],
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": BG,
                "color": MUTED,
                "fontFamily": "Inter, sans-serif",
                "fontSize": "10px",
                "fontWeight": "600",
                "letterSpacing": "0.08em",
                "textTransform": "uppercase",
                "border": f"1px solid {BORDER}",
                "padding": "12px 16px",
                "textAlign": "center",
                "cursor": "pointer",
            },
            style_cell={
                "fontFamily": "Inter, sans-serif",
                "fontSize": "13px",
                "color": TEXT,
                "border": f"1px solid {BORDER}",
                "padding": "10px 16px",
                "textAlign": "center",
                "backgroundColor": SURFACE,
            },
            style_cell_conditional=[
                {"if": {"column_id": "Counsellor"},
                 "textAlign": "left", "minWidth": "180px", "fontWeight": "500"},
                {"if": {"column_id": "Rank"},
                 "fontWeight": "700", "width": "60px", "minWidth": "60px"},
            ],
            style_data={"backgroundColor": SURFACE},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": SURFACE2},
                {"if": {"filter_query": "{Rank} = 1"},
                 "borderLeft": "4px solid #C9A84C", "backgroundColor": "#FFFCF0"},
                {"if": {"filter_query": "{Rank} = 1", "column_id": "Rank"},
                 "color": "#C9A84C", "fontSize": "15px"},
                {"if": {"filter_query": "{Rank} = 2"},
                 "borderLeft": "4px solid #A8A9AD", "backgroundColor": "#FAFAFA"},
                {"if": {"filter_query": "{Rank} = 2", "column_id": "Rank"},
                 "color": "#A8A9AD", "fontSize": "15px"},
                {"if": {"filter_query": "{Rank} = 3"},
                 "borderLeft": "4px solid #B87333", "backgroundColor": "#FDF6F0"},
                {"if": {"filter_query": "{Rank} = 3", "column_id": "Rank"},
                 "color": "#B87333", "fontSize": "15px"},
            ],
            sort_action="native",
            page_action="none",
        )

        return kpi_children, html.Div([table], style=CARD)
