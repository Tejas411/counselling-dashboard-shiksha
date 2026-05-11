from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

from theme import (BG, SURFACE, MUTED, TEXT, ACCENT, CHART, AXIS, AXIS_GRID,
                   CARD, DROP_STYLE, CALL_BLUE, CALL_INDIGO, CALL_TEAL, CALL_PURPLE, CALL_SKY,
                   flabel, kpi_card, slabel, fmt_duration, navbar)
from data import cdf, c_teams, c_tls, c_counsellors, DUR_ORDER


def layout():
    return html.Div([
        navbar("calls"),
        dbc.Container(fluid=True,
            style={"backgroundColor": BG, "minHeight": "100vh", "padding": "32px 28px"},
            children=[
                dbc.Row([
                    dbc.Col([flabel("From"), dcc.DatePickerSingle(
                        id="c-date-from",
                        date=(date.today() - timedelta(days=15)).isoformat(),
                        display_format="DD MMM YYYY",
                        style={"width": "100%"},
                    )], width=2),
                    dbc.Col([flabel("To"), dcc.DatePickerSingle(
                        id="c-date-to",
                        date=(date.today() - timedelta(days=1)).isoformat(),
                        display_format="DD MMM YYYY",
                        style={"width": "100%"},
                    )], width=2),
                    dbc.Col([flabel("Team"), dcc.Dropdown(id="c-team",
                        options=[{"label": t, "value": t} for t in c_teams],
                        multi=True, placeholder="All Teams", style=DROP_STYLE)], width=3),
                    dbc.Col([flabel("Team Lead"), dcc.Dropdown(id="c-tl",
                        options=[{"label": t, "value": t} for t in c_tls],
                        multi=True, placeholder="All TLs", style=DROP_STYLE)], width=2),
                    dbc.Col([flabel("Counsellor"), dcc.Dropdown(id="c-counsellor",
                        options=[{"label": c, "value": c} for c in c_counsellors],
                        multi=True, placeholder="All Counsellors", style=DROP_STYLE)], width=3),
                ], style={"marginBottom": "28px"}),
                dbc.Row(id="c-kpi-row", className="g-3", style={"marginBottom": "20px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Daily Call Volume"),
                        dcc.Graph(id="c-g-daily", config={"displayModeBar": False})], style=CARD), width=8),
                    dbc.Col(html.Div([slabel("Call Duration Buckets"),
                        dcc.Graph(id="c-g-dur", config={"displayModeBar": False})], style=CARD), width=4),
                ], className="g-3"),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Daily Unique Active Counsellors"),
                        dcc.Graph(id="c-g-daily-active", config={"displayModeBar": False})], style=CARD), width=6),
                    dbc.Col(html.Div([slabel("Daily Avg Talk Time per Counsellor"),
                        dcc.Graph(id="c-g-daily-tt", config={"displayModeBar": False})], style=CARD), width=6),
                ], className="g-3", style={"marginTop": "16px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Calls by Team"),
                        dcc.Graph(id="c-g-team", config={"displayModeBar": False})], style=CARD), width=6),
                    dbc.Col(html.Div([slabel("Calls by Team Lead"),
                        dcc.Graph(id="c-g-tl", config={"displayModeBar": False})], style=CARD), width=6),
                ], className="g-3", style={"marginTop": "16px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Top 15 Counsellors — Call Count"),
                        dcc.Graph(id="c-g-count", config={"displayModeBar": False})], style=CARD), width=6),
                    dbc.Col(html.Div([slabel("Top 15 Counsellors — Total Talk Time"),
                        dcc.Graph(id="c-g-dur-top", config={"displayModeBar": False})], style=CARD), width=6),
                ], className="g-3", style={"marginTop": "16px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Top 15 Counsellors — Avg Call Duration"),
                        dcc.Graph(id="c-g-avg", config={"displayModeBar": False})], style=CARD), width=6),
                    dbc.Col(html.Div([slabel("Call Volume by Hour"),
                        dcc.Graph(id="c-g-heat", config={"displayModeBar": False})], style=CARD), width=6),
                ], className="g-3", style={"marginTop": "16px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Talk Time by Team Lead"),
                        dcc.Graph(id="c-g-tt-tl", config={"displayModeBar": False})], style=CARD), width=5),
                    dbc.Col(html.Div([slabel("Top 15 Counsellors — Talk Time"),
                        dcc.Graph(id="c-g-tt-cslr", config={"displayModeBar": False})], style=CARD), width=7),
                ], className="g-3", style={"marginTop": "16px"}),
            ])
    ])


def register_callbacks(app):
    @app.callback(
        Output("c-kpi-row",        "children"),
        Output("c-g-daily",        "figure"),
        Output("c-g-dur",          "figure"),
        Output("c-g-team",         "figure"),
        Output("c-g-tl",           "figure"),
        Output("c-g-count",        "figure"),
        Output("c-g-dur-top",      "figure"),
        Output("c-g-avg",          "figure"),
        Output("c-g-heat",         "figure"),
        Output("c-g-tt-tl",        "figure"),
        Output("c-g-tt-cslr",      "figure"),
        Output("c-g-daily-active", "figure"),
        Output("c-g-daily-tt",     "figure"),
        Input("c-date-from",  "date"),
        Input("c-date-to",    "date"),
        Input("c-team",       "value"),
        Input("c-tl",         "value"),
        Input("c-counsellor", "value"),
    )
    def update_calls(date_from, date_to, sel_teams, sel_tls, sel_counsellors):
        d = cdf.copy()
        if date_from:
            d = d[d["created_on"].dt.date >= pd.to_datetime(date_from).date()]
        if date_to:
            d = d[d["created_on"].dt.date <= pd.to_datetime(date_to).date()]
        if sel_teams:       d = d[d["team_name"].isin(sel_teams)]
        if sel_tls:         d = d[d["TL_name"].isin(sel_tls)]
        if sel_counsellors: d = d[d["counsellor_name"].isin(sel_counsellors)]

        total_calls   = len(d)
        avg_dur_sec   = d["dur_sec"].mean() if total_calls else 0
        uniq_students = d["user_id"].dropna().nunique()
        counsellors   = d["counsellor_id"].dropna().nunique()

        conn = d[d["dur_sec"] > 0].copy()
        conn["date"] = conn["created_on"].dt.date

        if len(conn):
            _daily = conn.groupby("date").agg(
                total_dur=("dur_sec", "sum"),
                active_counsellors=("counsellor_id", "nunique")
            )
            _daily["daily_tt"] = _daily["total_dur"] / _daily["active_counsellors"]
            avg_talk_time = _daily["daily_tt"].mean()
        else:
            avg_talk_time = 0

        kpis = [
            kpi_card("Talk Time",        fmt_duration(avg_talk_time), ACCENT,      "avg per counsellor / day", width=3),
            kpi_card("Total Calls",      f"{total_calls:,}",          CALL_BLUE,   width=2),
            kpi_card("Avg Duration",     fmt_duration(avg_dur_sec),   CALL_INDIGO, width=2),
            kpi_card("Students Reached", f"{uniq_students:,}",        CALL_PURPLE, width=3),
            kpi_card("Counsellors",      counsellors,                 CALL_SKY,    width=2),
        ]

        day_order = d.sort_values("created_on")["date_str"].unique().tolist()
        daily = d.groupby("date_str").size().reset_index(name="n")
        fig_daily = px.bar(daily, x="date_str", y="n",
            category_orders={"date_str": day_order}, labels={"date_str":"","n":""})
        fig_daily.update_traces(marker_color=CALL_BLUE, marker_line_width=0)
        fig_daily.update_layout(**CHART, height=260, showlegend=False)
        fig_daily.update_xaxes(**AXIS, tickfont=dict(color=MUTED, size=11))
        fig_daily.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))

        dur_counts = d["dur_bucket"].value_counts().reindex(DUR_ORDER).fillna(0).reset_index()
        dur_counts.columns = ["bucket","n"]
        fig_dur = px.bar(dur_counts, x="bucket", y="n",
            category_orders={"bucket": DUR_ORDER}, labels={"bucket":"","n":""})
        fig_dur.update_traces(marker_color=CALL_TEAL, marker_line_width=0)
        fig_dur.update_layout(**CHART, height=260, showlegend=False)
        fig_dur.update_xaxes(**AXIS, tickfont=dict(color=TEXT, size=11))
        fig_dur.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))

        team_counts = d.groupby("team_name").size().sort_values(ascending=False).reset_index(name="n")
        fig_team = px.bar(team_counts, x="n", y="team_name",
            category_orders={"team_name": team_counts["team_name"].tolist()},
            labels={"team_name":"","n":""}, orientation="h")
        fig_team.update_traces(marker_color=CALL_BLUE, marker_line_width=0)
        fig_team.update_layout(**CHART, height=320, showlegend=False)
        fig_team.update_xaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_team.update_yaxes(**AXIS, tickfont=dict(color=TEXT, size=11))

        tl_counts = d.groupby("TL_name").size().sort_values(ascending=False).reset_index(name="n")
        fig_tl = px.bar(tl_counts, x="TL_name", y="n",
            category_orders={"TL_name": tl_counts["TL_name"].tolist()},
            labels={"TL_name":"","n":""})
        fig_tl.update_traces(marker_color=CALL_INDIGO, marker_line_width=0)
        fig_tl.update_layout(**CHART, height=320, showlegend=False)
        fig_tl.update_xaxes(**AXIS, tickfont=dict(color=TEXT, size=12))
        fig_tl.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))

        top_count = d.groupby("counsellor_name").size().nlargest(15).sort_values(ascending=False).reset_index(name="n")
        fig_count = px.bar(top_count, x="n", y="counsellor_name",
            category_orders={"counsellor_name": top_count["counsellor_name"].tolist()},
            labels={"counsellor_name":"","n":""}, orientation="h")
        fig_count.update_traces(marker_color=CALL_BLUE, marker_line_width=0)
        fig_count.update_layout(**CHART, height=420, showlegend=False)
        fig_count.update_xaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_count.update_yaxes(**AXIS, tickfont=dict(color=TEXT, size=11))

        top_dur = (d.groupby("counsellor_name")["dur_sec"].sum()
                   .nlargest(15).sort_values(ascending=False) / 60).reset_index()
        top_dur.columns = ["counsellor_name","dur_min"]
        top_dur["label"] = top_dur["dur_min"].apply(
            lambda m: f"{int(m//60)}h {int(m%60)}m" if m >= 60 else f"{int(m)}m")
        fig_dur_top = px.bar(top_dur, x="dur_min", y="counsellor_name",
            category_orders={"counsellor_name": top_dur["counsellor_name"].tolist()},
            labels={"counsellor_name":"","dur_min":"Minutes"},
            orientation="h", custom_data=["label"])
        fig_dur_top.update_traces(marker_color=CALL_TEAL, marker_line_width=0,
            hovertemplate="%{y}<br>%{customdata[0]}<extra></extra>")
        fig_dur_top.update_layout(**CHART, height=420, showlegend=False)
        fig_dur_top.update_xaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_dur_top.update_yaxes(**AXIS, tickfont=dict(color=TEXT, size=11))

        avg_dur = (d.groupby("counsellor_name")["dur_sec"]
                   .mean().nlargest(15).sort_values(ascending=False) / 60).reset_index()
        avg_dur.columns = ["counsellor_name","avg_min"]
        fig_avg = px.bar(avg_dur, x="avg_min", y="counsellor_name",
            category_orders={"counsellor_name": avg_dur["counsellor_name"].tolist()},
            labels={"counsellor_name":"","avg_min":"Avg (min)"}, orientation="h")
        fig_avg.update_traces(marker_color=CALL_PURPLE, marker_line_width=0)
        fig_avg.update_layout(**CHART, height=420, showlegend=False)
        fig_avg.update_xaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_avg.update_yaxes(**AXIS, tickfont=dict(color=TEXT, size=11))

        d2 = d.copy()
        d2["hour"] = d2["created_on"].dt.hour
        d2["day"]  = d2["created_on"].dt.strftime("%a %d %b")
        day_o  = d2.sort_values("created_on")["day"].unique().tolist()
        heat   = d2.groupby(["day","hour"]).size().reset_index(name="n")
        pivot  = heat.pivot(index="day", columns="hour", values="n").reindex(day_o).fillna(0)
        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values, x=[f"{h:02d}h" for h in pivot.columns], y=pivot.index,
            colorscale=[[0,"#EFF6FF"],[1, CALL_BLUE]], showscale=False,
            hovertemplate="%{y}  %{x}<br>%{z} calls<extra></extra>"))
        fig_heat.update_layout(**CHART, height=260)
        fig_heat.update_xaxes(**AXIS, tickfont=dict(color=MUTED, size=10))
        fig_heat.update_yaxes(**AXIS, tickfont=dict(color=MUTED, size=10))

        day_order_conn = conn.sort_values("created_on")["date_str"].unique().tolist()
        daily_active = conn.groupby("date_str")["counsellor_id"].nunique().reset_index(name="n")
        fig_daily_active = px.bar(daily_active, x="date_str", y="n",
            category_orders={"date_str": day_order_conn}, labels={"date_str": "", "n": ""})
        fig_daily_active.update_traces(marker_color=CALL_TEAL, marker_line_width=0)
        fig_daily_active.update_layout(**CHART, height=260, showlegend=False)
        fig_daily_active.update_xaxes(**AXIS, tickfont=dict(color=MUTED, size=11))
        fig_daily_active.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))

        daily_tt_df = conn.groupby("date").agg(
            total_dur=("dur_sec", "sum"),
            active=("counsellor_id", "nunique")
        ).reset_index()
        daily_tt_df["avg_tt_min"] = daily_tt_df["total_dur"] / daily_tt_df["active"] / 60
        daily_tt_df["date_str2"]  = pd.to_datetime(daily_tt_df["date"]).dt.strftime("%d %b")
        daily_tt_df = daily_tt_df.sort_values("date")
        fig_daily_tt = px.bar(daily_tt_df, x="date_str2", y="avg_tt_min",
            category_orders={"date_str2": daily_tt_df["date_str2"].tolist()},
            labels={"date_str2": "", "avg_tt_min": "avg min"})
        fig_daily_tt.update_traces(marker_color=ACCENT, marker_line_width=0)
        fig_daily_tt.update_layout(**CHART, height=260, showlegend=False)
        fig_daily_tt.update_xaxes(**AXIS, tickfont=dict(color=MUTED, size=11))
        fig_daily_tt.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))

        tl_daily = conn.groupby(["TL_name", "date"]).agg(
            total_dur=("dur_sec", "sum"),
            active=("counsellor_id", "nunique")
        ).reset_index()
        tl_daily["daily_tt"] = tl_daily["total_dur"] / tl_daily["active"]
        tl_tt = tl_daily.groupby("TL_name")["daily_tt"].mean().sort_values(ascending=False).reset_index()
        tl_tt.columns = ["TL_name", "avg_tt_sec"]
        tl_tt["avg_tt_min"] = tl_tt["avg_tt_sec"] / 60
        fig_tt_tl = px.bar(tl_tt, x="TL_name", y="avg_tt_min",
            category_orders={"TL_name": tl_tt["TL_name"].tolist()},
            labels={"TL_name": "", "avg_tt_min": "avg min / day"})
        fig_tt_tl.update_traces(marker_color=ACCENT, marker_line_width=0)
        fig_tt_tl.update_layout(**CHART, height=320, showlegend=False)
        fig_tt_tl.update_xaxes(**AXIS, tickfont=dict(color=TEXT, size=12))
        fig_tt_tl.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))

        cslr_daily = conn.groupby(["counsellor_name", "date"])["dur_sec"].sum().reset_index()
        cslr_tt = (cslr_daily.groupby("counsellor_name")["dur_sec"]
                   .mean().nlargest(15).sort_values(ascending=False).reset_index())
        cslr_tt.columns = ["counsellor_name", "avg_tt_sec"]
        cslr_tt["avg_tt_min"] = cslr_tt["avg_tt_sec"] / 60
        fig_tt_cslr = px.bar(cslr_tt, x="avg_tt_min", y="counsellor_name",
            orientation="h",
            category_orders={"counsellor_name": cslr_tt["counsellor_name"].tolist()},
            labels={"counsellor_name": "", "avg_tt_min": "avg min / day"})
        fig_tt_cslr.update_traces(marker_color=ACCENT, marker_line_width=0)
        fig_tt_cslr.update_layout(**CHART, height=420, showlegend=False)
        fig_tt_cslr.update_xaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_tt_cslr.update_yaxes(**AXIS, tickfont=dict(color=TEXT, size=11))

        return (kpis, fig_daily, fig_dur,
                fig_team, fig_tl,
                fig_count, fig_dur_top, fig_avg, fig_heat,
                fig_tt_tl, fig_tt_cslr,
                fig_daily_active, fig_daily_tt)
