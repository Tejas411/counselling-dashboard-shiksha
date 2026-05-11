import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

from theme import (BG, SURFACE, MUTED, TEXT, ACCENT, CHART, AXIS, AXIS_GRID,
                   CARD, DROP_STYLE, SC, flabel, kpi_card, slabel, navbar)
from data import adf, a_teams, a_tls, a_statuses, a_counsellors


def layout():
    return html.Div([
        navbar("applications"),
        dbc.Container(fluid=True,
            style={"backgroundColor": BG, "minHeight": "100vh", "padding": "32px 28px"},
            children=[
                dbc.Row(dbc.Col(html.P(
                    f"{adf['creation_date'].min().strftime('%#d %b %Y')}  –  "
                    f"{adf['creation_date'].max().strftime('%#d %b %Y')}  ·  Application Forms Sold",
                    style={"color": MUTED, "fontSize": "13px", "margin": "0 0 24px"}
                ))),
                dbc.Row([
                    dbc.Col([flabel("Team"), dcc.Dropdown(id="a-team",
                        options=[{"label": t, "value": t} for t in a_teams],
                        multi=True, placeholder="All Teams", style=DROP_STYLE)], width=3),
                    dbc.Col([flabel("Team Lead"), dcc.Dropdown(id="a-tl",
                        options=[{"label": t, "value": t} for t in a_tls],
                        multi=True, placeholder="All TLs", style=DROP_STYLE)], width=3),
                    dbc.Col([flabel("Status"), dcc.Dropdown(id="a-status",
                        options=[{"label": s, "value": s} for s in a_statuses],
                        multi=True, placeholder="All Statuses", style=DROP_STYLE)], width=3),
                    dbc.Col([flabel("Counsellor"), dcc.Dropdown(id="a-counsellor",
                        options=[{"label": c, "value": c} for c in a_counsellors],
                        multi=True, placeholder="All Counsellors", style=DROP_STYLE)], width=3),
                ], style={"marginBottom": "28px"}),
                dbc.Row(id="a-kpi-row", className="g-3", style={"marginBottom": "20px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Daily Trend — Entry Date"),
                        dcc.Graph(id="a-g-daily", config={"displayModeBar": False})], style=CARD), width=8),
                    dbc.Col(html.Div([slabel("Status Split"),
                        dcc.Graph(id="a-g-pie", config={"displayModeBar": False})], style=CARD), width=4),
                ], className="g-3"),
                dbc.Row(dbc.Col(html.Div([slabel("Daily Trend — Application Submission Date"),
                    dcc.Graph(id="a-g-appsub", config={"displayModeBar": False})], style=CARD)),
                    className="g-3", style={"marginTop": "16px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("By Team"),
                        dcc.Graph(id="a-g-team", config={"displayModeBar": False})], style=CARD), width=6),
                    dbc.Col(html.Div([slabel("By Team Lead"),
                        dcc.Graph(id="a-g-tl", config={"displayModeBar": False})], style=CARD), width=6),
                ], className="g-3", style={"marginTop": "16px"}),
                dbc.Row(dbc.Col(html.Div([slabel("By Team Lead — Avg Applications per Counsellor"),
                    dcc.Graph(id="a-g-tl-norm", config={"displayModeBar": False})], style=CARD)),
                    className="g-3", style={"marginTop": "16px"}),
                dbc.Row([
                    dbc.Col(html.Div([slabel("Top 15 Counsellors"),
                        dcc.Graph(id="a-g-counsellor", config={"displayModeBar": False})], style=CARD), width=6),
                    dbc.Col(html.Div([slabel("Top 15 Colleges"),
                        dcc.Graph(id="a-g-college", config={"displayModeBar": False})], style=CARD), width=6),
                ], className="g-3", style={"marginTop": "16px"}),
                dbc.Row(dbc.Col(html.Div([slabel("Top 15 Base Courses"),
                    dcc.Graph(id="a-g-course", config={"displayModeBar": False})], style=CARD)),
                    className="g-3", style={"marginTop": "16px"}),
                dbc.Row(dbc.Col(html.Div([slabel("Submission Hours"),
                    dcc.Graph(id="a-g-heatmap", config={"displayModeBar": False})], style=CARD)),
                    className="g-3", style={"marginTop": "16px"}),
            ])
    ])


def register_callbacks(app):
    @app.callback(
        Output("a-kpi-row",      "children"),
        Output("a-g-daily",      "figure"),
        Output("a-g-pie",        "figure"),
        Output("a-g-appsub",     "figure"),
        Output("a-g-team",       "figure"),
        Output("a-g-tl",         "figure"),
        Output("a-g-tl-norm",    "figure"),
        Output("a-g-counsellor", "figure"),
        Output("a-g-college",    "figure"),
        Output("a-g-course",     "figure"),
        Output("a-g-heatmap",    "figure"),
        Input("a-team",       "value"),
        Input("a-tl",         "value"),
        Input("a-status",     "value"),
        Input("a-counsellor", "value"),
    )
    def update_apps(sel_teams, sel_tls, sel_status, sel_counsellors):
        d = adf.copy()
        if sel_teams:       d = d[d["team_name"].isin(sel_teams)]
        if sel_tls:         d = d[d["TL_name"].isin(sel_tls)]
        if sel_status:      d = d[d["status"].isin(sel_status)]
        if sel_counsellors: d = d[d["counsellor_name"].isin(sel_counsellors)]

        total    = len(d)
        accepted = (d["status"] == "ACCEPTED").sum()
        pending  = (d["status"] == "PENDING").sum()
        rejected = (d["status"] == "REJECTED").sum()
        acc_pct  = f"Accept rate {accepted/total*100:.1f}%" if total else ""

        kpis = [
            kpi_card("Total",       total,                          ACCENT),
            kpi_card("Accepted",    accepted,                       "#16A34A", acc_pct),
            kpi_card("Pending",     pending,                        "#D97706"),
            kpi_card("Rejected",    rejected,                       "#DC2626"),
            kpi_card("Counsellors", d["counsellor_name"].nunique(), "#7C3AED"),
            kpi_card("Colleges",    d["college_name"].nunique(),    "#0284C7"),
        ]

        day_order = d.sort_values("creation_date")["date_str"].unique().tolist()
        daily = d.groupby(["date_str", "status"]).size().reset_index(name="n")
        fig_daily = px.bar(daily, x="date_str", y="n", color="status",
            color_discrete_map=SC,
            category_orders={"date_str": day_order, "status": ["ACCEPTED","PENDING","REJECTED"]},
            labels={"date_str":"","n":"","status":""})
        fig_daily.update_layout(**CHART, height=260, showlegend=True)
        fig_daily.update_xaxes(**AXIS, tickfont=dict(color=MUTED, size=11))
        fig_daily.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_daily.update_traces(marker_line_width=0)

        sc = d["status"].value_counts().reset_index()
        fig_pie = px.pie(sc, names="status", values="count",
            color="status", color_discrete_map=SC, hole=0.55)
        fig_pie.update_layout(**CHART, height=260, showlegend=True)
        fig_pie.update_traces(textposition="inside", textinfo="percent",
            textfont=dict(color="#FFFFFF", size=11, family="Inter, sans-serif"),
            marker_line_color=SURFACE, marker_line_width=2)

        dsub = d.dropna(subset=["application_submission_date"]).copy()
        dsub["sub_date_dt"] = dsub["application_submission_date"].dt.normalize()
        sub_order = dsub.sort_values("sub_date_dt")["sub_date_str"].unique().tolist()
        sub_daily = dsub.groupby(["sub_date_str","status"]).size().reset_index(name="n")
        fig_appsub = px.bar(sub_daily, x="sub_date_str", y="n", color="status",
            color_discrete_map=SC,
            category_orders={"sub_date_str": sub_order, "status": ["ACCEPTED","PENDING","REJECTED"]},
            labels={"sub_date_str":"","n":"","status":""})
        fig_appsub.update_layout(**CHART, height=240, showlegend=True)
        fig_appsub.update_xaxes(**AXIS, tickfont=dict(color=MUTED, size=10), tickangle=-45, nticks=30)
        fig_appsub.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_appsub.update_traces(marker_line_width=0)

        def hbar(data, x, y, order, h=300, legend=False, tick_size=11):
            fig = px.bar(data, x=x, y=y, color="status", color_discrete_map=SC,
                category_orders={y: order, "status": ["ACCEPTED","PENDING","REJECTED"]},
                labels={y:"",x:"","status":""}, orientation="h")
            fig.update_layout(**CHART, height=h, showlegend=legend)
            fig.update_xaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
            fig.update_yaxes(**AXIS, tickfont=dict(color=TEXT, size=tick_size))
            fig.update_traces(marker_line_width=0)
            return fig

        ts = d.groupby(["team_name","status"]).size().reset_index(name="n")
        t_order = d.groupby("team_name").size().sort_values(ascending=False).index.tolist()
        fig_team = hbar(ts, "n", "team_name", t_order, 300)

        tl_s = d.groupby(["TL_name","status"]).size().reset_index(name="n")
        tl_order = d.groupby("TL_name").size().sort_values(ascending=False).index.tolist()
        fig_tl = px.bar(tl_s, x="TL_name", y="n", color="status",
            color_discrete_map=SC,
            category_orders={"TL_name": tl_order, "status": ["ACCEPTED","PENDING","REJECTED"]},
            labels={"TL_name":"","n":"","status":""})
        fig_tl.update_layout(**CHART, height=300, showlegend=True)
        fig_tl.update_xaxes(**AXIS, tickfont=dict(color=TEXT, size=12))
        fig_tl.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
        fig_tl.update_traces(marker_line_width=0)

        tl_total  = d.groupby("TL_name").size()
        tl_active = d.groupby("TL_name")["counsellor_name"].nunique()
        tl_norm   = (tl_total / tl_active).sort_values(ascending=False).reset_index()
        tl_norm.columns = ["TL_name", "apps_per_cslr"]
        fig_tl_norm = px.bar(tl_norm, x="TL_name", y="apps_per_cslr",
            category_orders={"TL_name": tl_norm["TL_name"].tolist()},
            labels={"TL_name": "", "apps_per_cslr": "apps / counsellor"})
        fig_tl_norm.update_traces(marker_color=ACCENT, marker_line_width=0)
        fig_tl_norm.update_layout(**CHART, height=300, showlegend=False)
        fig_tl_norm.update_xaxes(**AXIS, tickfont=dict(color=TEXT, size=12))
        fig_tl_norm.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))

        top15c  = d.groupby("counsellor_name").size().nlargest(15).index
        cs      = d[d["counsellor_name"].isin(top15c)].groupby(["counsellor_name","status"]).size().reset_index(name="n")
        c_order = d[d["counsellor_name"].isin(top15c)].groupby("counsellor_name").size().sort_values(ascending=False).index.tolist()
        fig_c = hbar(cs, "n", "counsellor_name", c_order, 420, legend=True)

        top15col  = d.groupby("college_name").size().nlargest(15).index
        cols      = d[d["college_name"].isin(top15col)].groupby(["college_name","status"]).size().reset_index(name="n")
        col_order = d[d["college_name"].isin(top15col)].groupby("college_name").size().sort_values(ascending=False).index.tolist()
        fig_col = hbar(cols, "n", "college_name", col_order, 420)

        top15cr  = d.groupby("base_course_name").size().nlargest(15).index
        crs      = d[d["base_course_name"].isin(top15cr)].groupby(["base_course_name","status"]).size().reset_index(name="n")
        cr_order = d[d["base_course_name"].isin(top15cr)].groupby("base_course_name").size().sort_values(ascending=False).index.tolist()
        fig_course = hbar(crs, "n", "base_course_name", cr_order, 420, legend=True, tick_size=12)

        d2 = d.copy()
        d2["hour"] = d2["creation_date"].dt.hour
        d2["day"]  = d2["creation_date"].dt.strftime("%a %d %b")
        day_o  = d2.sort_values("creation_date")["day"].unique().tolist()
        heat   = d2.groupby(["day","hour"]).size().reset_index(name="n")
        pivot  = heat.pivot(index="day", columns="hour", values="n").reindex(day_o).fillna(0)
        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values, x=[f"{h:02d}h" for h in pivot.columns], y=pivot.index,
            colorscale=[[0,"#FDF6F3"],[1,ACCENT]], showscale=False,
            hovertemplate="%{y}  %{x}<br>%{z} submissions<extra></extra>"))
        fig_heat.update_layout(**CHART, height=280)
        fig_heat.update_xaxes(**AXIS, tickfont=dict(color=MUTED, size=10))
        fig_heat.update_yaxes(**AXIS, tickfont=dict(color=MUTED, size=10))

        return (kpis, fig_daily, fig_pie, fig_appsub,
                fig_team, fig_tl, fig_tl_norm, fig_c, fig_col, fig_course, fig_heat)
