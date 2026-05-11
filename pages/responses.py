import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

from theme import (BG, SURFACE, MUTED, TEXT, CHART, AXIS, AXIS_GRID,
                   CARD, DROP_STYLE, RESP_GREEN, RESP_TEAL, RESP_VIOLET, RESP_SKY,
                   CLIENT_SC, flabel, kpi_card, slabel, navbar)
from data import rdf, r_tls, r_counsellors, r_last_date, r_default_start


def layout():
    return html.Div([
        navbar("responses"),
        dbc.Container(fluid=True,
            style={"backgroundColor": BG, "minHeight": "100vh", "padding": "32px 28px"},
            children=[
                dbc.Row(dbc.Col(html.P(
                    f"{r_default_start.strftime('%d %b')} – {r_last_date.strftime('%d %b %Y')}  ·  Counsellor Responses (Created + Edit Shortlist)",
                    style={"color": MUTED, "fontSize": "13px", "margin": "0 0 24px"}
                ))),
                dbc.Row([
                    dbc.Col([flabel("Date Range"), dcc.DatePickerRange(
                        id="r-date",
                        min_date_allowed=rdf["created_on"].min().date(),
                        max_date_allowed=r_last_date,
                        start_date=r_default_start,
                        end_date=r_last_date,
                        display_format="DD MMM YYYY",
                        style={"fontSize": "12px"},
                    )], width=4),
                    dbc.Col([flabel("Team Lead"), dcc.Dropdown(id="r-tl",
                        options=[{"label": t, "value": t} for t in r_tls],
                        multi=True, placeholder="All TLs", style=DROP_STYLE)], width=2),
                    dbc.Col([flabel("Source"), dcc.Dropdown(id="r-source",
                        options=[{"label": s, "value": s} for s in ["Counsellor Created", "Edit Shortlist"]],
                        multi=True, placeholder="All Sources", style=DROP_STYLE)], width=2),
                    dbc.Col([flabel("Counsellor"), dcc.Dropdown(id="r-counsellor",
                        options=[{"label": c, "value": c} for c in r_counsellors],
                        multi=True, placeholder="All Counsellors", style=DROP_STYLE)], width=4),
                ], style={"marginBottom": "28px"}),
                dbc.Row(id="r-kpi-row", className="g-3", style={"marginBottom": "20px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Daily Response Volume"),
                        dcc.Graph(id="r-g-daily", config={"displayModeBar": False})], style=CARD), width=8),
                    dbc.Col(html.Div([slabel("Client vs Non-Client Split"),
                        dcc.Graph(id="r-g-pie", config={"displayModeBar": False})], style=CARD), width=4),
                ], className="g-3"),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Responses by Source"),
                        dcc.Graph(id="r-g-source", config={"displayModeBar": False})], style=CARD), width=4),
                    dbc.Col(html.Div([slabel("Responses by Team Lead"),
                        dcc.Graph(id="r-g-tl", config={"displayModeBar": False})], style=CARD), width=8),
                ], className="g-3", style={"marginTop": "16px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Top 15 Counsellors — Response Count"),
                        dcc.Graph(id="r-g-counsellor", config={"displayModeBar": False})], style=CARD), width=6),
                    dbc.Col(html.Div([slabel("Top 15 Base Courses"),
                        dcc.Graph(id="r-g-course", config={"displayModeBar": False})], style=CARD), width=6),
                ], className="g-3", style={"marginTop": "16px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Response Volume by Hour"),
                        dcc.Graph(id="r-g-heat", config={"displayModeBar": False})], style=CARD)),
                ], className="g-3", style={"marginTop": "16px"}),
            ])
    ])


def register_callbacks(app):
    @app.callback(
        Output("r-kpi-row",      "children"),
        Output("r-g-daily",      "figure"),
        Output("r-g-pie",        "figure"),
        Output("r-g-source",     "figure"),
        Output("r-g-tl",         "figure"),
        Output("r-g-counsellor", "figure"),
        Output("r-g-course",     "figure"),
        Output("r-g-heat",       "figure"),
        Input("r-date",       "start_date"),
        Input("r-date",       "end_date"),
        Input("r-tl",         "value"),
        Input("r-source",     "value"),
        Input("r-counsellor", "value"),
    )
    def update_responses(start_date, end_date, sel_tls, sel_source, sel_counsellors):
        d = rdf.copy()
        if start_date:
            d = d[d["created_on"] >= pd.to_datetime(start_date)]
        if end_date:
            d = d[d["created_on"] <= pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)]
        if sel_tls:         d = d[d["TL_name"].isin(sel_tls)]
        if sel_source:      d = d[d["source"].isin(sel_source)]
        if sel_counsellors: d = d[d["counsellor_name"].isin(sel_counsellors)]

        total       = len(d)
        n_client    = (d["is_client"] == 1).sum()
        n_nonclient = (d["is_client"] == 0).sum()
        n_students  = d["user_id"].nunique()
        n_cslrs     = d["counsellor_id"].nunique()
        client_pct  = f"Client rate {n_client/total*100:.1f}%" if total else ""

        kpis = [
            kpi_card("Total Responses", f"{total:,}",       RESP_GREEN,  width=3),
            kpi_card("Client",          f"{n_client:,}",    RESP_GREEN,  client_pct, width=2),
            kpi_card("Non-Client",      f"{n_nonclient:,}", "#94A3B8",   width=2),
            kpi_card("Students",        f"{n_students:,}",  RESP_VIOLET, width=3),
            kpi_card("Counsellors",     n_cslrs,            RESP_SKY,    width=2),
        ]

        day_order = d.sort_values("created_on")["date_str"].unique().tolist()
        daily = d.groupby(["date_str","client_label"]).size().reset_index(name="n")
        fig_daily = px.bar(daily, x="date_str", y="n", color="client_label",
            color_discrete_map=CLIENT_SC,
            category_orders={"date_str": day_order, "client_label": ["Client","Non-Client"]},
            labels={"date_str":"","n":"","client_label":""})
        fig_daily.update_layout(**CHART, height=260, showlegend=True)
        fig_daily.update_xaxes(**AXIS, tickfont=dict(color=MUTED, size=11))
        fig_daily.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_daily.update_traces(marker_line_width=0)

        cv = d["client_label"].value_counts().reset_index()
        fig_pie = px.pie(cv, names="client_label", values="count",
            color="client_label", color_discrete_map=CLIENT_SC, hole=0.55)
        fig_pie.update_layout(**CHART, height=260, showlegend=True)
        fig_pie.update_traces(textposition="inside", textinfo="percent",
            textfont=dict(color="#FFFFFF", size=11, family="Inter, sans-serif"),
            marker_line_color=SURFACE, marker_line_width=2)

        src = d.groupby(["source","client_label"]).size().reset_index(name="n")
        fig_source = px.bar(src, x="source", y="n", color="client_label",
            color_discrete_map=CLIENT_SC,
            category_orders={"client_label": ["Client","Non-Client"]},
            labels={"source":"","n":"","client_label":""})
        fig_source.update_layout(**CHART, height=280, showlegend=True)
        fig_source.update_xaxes(**AXIS, tickfont=dict(color=TEXT, size=12))
        fig_source.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_source.update_traces(marker_line_width=0)

        tl_s = d.groupby(["TL_name","client_label"]).size().reset_index(name="n")
        tl_order = d.groupby("TL_name").size().sort_values(ascending=False).index.tolist()
        fig_tl = px.bar(tl_s, x="TL_name", y="n", color="client_label",
            color_discrete_map=CLIENT_SC,
            category_orders={"TL_name": tl_order, "client_label": ["Client","Non-Client"]},
            labels={"TL_name":"","n":"","client_label":""})
        fig_tl.update_layout(**CHART, height=280, showlegend=True)
        fig_tl.update_xaxes(**AXIS, tickfont=dict(color=TEXT, size=12), tickangle=-30)
        fig_tl.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_tl.update_traces(marker_line_width=0)

        top15 = d.groupby("counsellor_name").size().nlargest(15).index
        cs = (d[d["counsellor_name"].isin(top15)]
              .groupby(["counsellor_name","client_label"]).size().reset_index(name="n"))
        # ascending=True so the highest-count counsellor appears at the top of a horizontal bar chart
        c_order = (d[d["counsellor_name"].isin(top15)]
                   .groupby("counsellor_name").size().sort_values(ascending=True).index.tolist())
        fig_cslr = px.bar(cs, x="n", y="counsellor_name", color="client_label",
            color_discrete_map=CLIENT_SC,
            category_orders={"counsellor_name": c_order, "client_label": ["Client","Non-Client"]},
            labels={"counsellor_name":"","n":"","client_label":""},
            orientation="h")
        fig_cslr.update_layout(**CHART, height=420, showlegend=True)
        fig_cslr.update_xaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_cslr.update_yaxes(**AXIS, tickfont=dict(color=TEXT, size=11))
        fig_cslr.update_traces(marker_line_width=0)

        top15c = d.groupby("base_course_name").size().nlargest(15).index
        crs = (d[d["base_course_name"].isin(top15c)]
               .groupby(["base_course_name","client_label"]).size().reset_index(name="n"))
        cr_order = (d[d["base_course_name"].isin(top15c)]
                    .groupby("base_course_name").size().sort_values(ascending=True).index.tolist())
        fig_course = px.bar(crs, x="n", y="base_course_name", color="client_label",
            color_discrete_map=CLIENT_SC,
            category_orders={"base_course_name": cr_order, "client_label": ["Client","Non-Client"]},
            labels={"base_course_name":"","n":"","client_label":""},
            orientation="h")
        fig_course.update_layout(**CHART, height=420, showlegend=True)
        fig_course.update_xaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_course.update_yaxes(**AXIS, tickfont=dict(color=TEXT, size=11))
        fig_course.update_traces(marker_line_width=0)

        d2 = d.copy()
        d2["hour"] = d2["created_on"].dt.hour
        d2["day"]  = d2["created_on"].dt.strftime("%a %d %b")
        day_o  = d2.sort_values("created_on")["day"].unique().tolist()
        heat   = d2.groupby(["day","hour"]).size().reset_index(name="n")
        pivot  = heat.pivot(index="day", columns="hour", values="n").reindex(day_o).fillna(0)
        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values, x=[f"{h:02d}h" for h in pivot.columns], y=pivot.index,
            colorscale=[[0,"#ECFDF5"],[1, RESP_GREEN]], showscale=False,
            hovertemplate="%{y}  %{x}<br>%{z} responses<extra></extra>"))
        fig_heat.update_layout(**CHART, height=420)
        fig_heat.update_xaxes(**AXIS, tickfont=dict(color=MUTED, size=10))
        fig_heat.update_yaxes(**AXIS, tickfont=dict(color=MUTED, size=10))

        return (kpis, fig_daily, fig_pie, fig_source,
                fig_tl, fig_cslr, fig_course, fig_heat)
