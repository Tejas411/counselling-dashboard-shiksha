from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

from theme import (BG, SURFACE, SURFACE2, BORDER, TEXT, MUTED, ACCENT,
                   CARD, DROP_STYLE, CALL_BLUE, CALL_TEAL, flabel, kpi_card, slabel, navbar)
from data import fldf, _fl_date, _fl_slots, _fl_teams, _build_fl_table, _FL_COLS


def layout():
    slot_opts = [{"label": "All Slots", "value": "all"}] + \
                [{"label": s, "value": s} for s in _fl_slots]
    team_opts = [{"label": t, "value": t} for t in _fl_teams]
    return html.Div([
        navbar("fresh_leads"),
        dbc.Container(fluid=True,
            style={"backgroundColor": BG, "minHeight": "100vh", "padding": "32px 28px"},
            children=[
                dbc.Row(dbc.Col(html.P(
                    f"{_fl_date}  ·  First Call Response by DS Score Bucket",
                    style={"color": MUTED, "fontSize": "13px", "margin": "0 0 24px"}
                ))),
                dbc.Row([
                    dbc.Col([
                        flabel("Allocation Time Slot"),
                        dcc.Dropdown(id="fl-slot", options=slot_opts, value="all",
                                     clearable=False, style=DROP_STYLE),
                    ], width=3),
                    dbc.Col([
                        flabel("Team"),
                        dcc.Dropdown(id="fl-team", options=team_opts,
                                     multi=True, placeholder="All Teams", style=DROP_STYLE),
                    ], width=4),
                ], style={"marginBottom": "28px"}),
                dbc.Row(id="fl-kpi-row", className="g-3", style={"marginBottom": "20px"}),
                dbc.Row(dbc.Col(
                    html.Div([
                        slabel("DS Score Bucket — Allocation & Call Response"),
                        html.Div(id="fl-table", style={"padding": "0 20px 20px"}),
                    ], style=CARD)
                )),
            ])
    ])


def register_callbacks(app):
    @app.callback(
        Output("fl-kpi-row", "children"),
        Output("fl-table",   "children"),
        Input("fl-slot",     "value"),
        Input("fl-team",     "value"),
    )
    def update_fresh_leads(slot, sel_teams):
        d = fldf.copy()
        if slot and slot != "all":
            d = d[d["alloc_hour_bucket"] == slot]
        if sel_teams:
            d = d[d["team_name"].isin(sel_teams)]

        alloc   = len(d)
        att     = int(d["attempted"].sum()) if alloc else 0
        conn    = int(d["connected"].sum()) if alloc else 0
        w30     = int(((d["time_to_call_hrs"] >= 0) & (d["time_to_call_hrs"] <= 0.5)).sum()) if alloc else 0
        att_pct = f"Attempted {att/alloc*100:.1f}%" if alloc else ""
        con_pct = f"Connect {conn/alloc*100:.1f}%" if alloc else ""
        w30_pct = f"{w30/alloc*100:.1f}% of allocated" if alloc else ""

        kpis = [
            kpi_card("Allocated", f"{alloc:,}", ACCENT,    width=3),
            kpi_card("Attempted", f"{att:,}",   CALL_BLUE, att_pct, width=3),
            kpi_card("Connected", f"{conn:,}",  "#16A34A", con_pct, width=3),
            kpi_card("≤ 30 min",  f"{w30:,}",   CALL_TEAL, w30_pct, width=3),
        ]

        if alloc == 0:
            return kpis, html.P("No data for selected slot.", style={"color": MUTED, "padding": "20px"})

        rows  = _build_fl_table(d)
        table = dash_table.DataTable(
            data=rows,
            columns=_FL_COLS,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": BG,
                "color": MUTED,
                "fontSize": "11px",
                "fontWeight": "600",
                "fontFamily": "Inter, sans-serif",
                "textTransform": "uppercase",
                "letterSpacing": "0.06em",
                "border": f"1px solid {BORDER}",
                "borderBottom": f"2px solid {BORDER}",
                "padding": "10px 16px",
            },
            style_cell={
                "fontFamily": "Inter, sans-serif",
                "fontSize": "13px",
                "color": TEXT,
                "border": f"1px solid {BORDER}",
                "padding": "10px 16px",
                "textAlign": "center",
                "fontVariantNumeric": "tabular-nums",
                "minWidth": "90px",
            },
            style_cell_conditional=[
                {"if": {"column_id": "ds_bucket"}, "textAlign": "left",
                 "fontWeight": "600", "minWidth": "110px"},
            ],
            style_data={"backgroundColor": SURFACE},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": SURFACE2},
                {
                    "if": {"filter_query": '{ds_bucket} = "TOTAL"'},
                    "backgroundColor": BG,
                    "fontWeight": "700",
                    "borderTop": f"2px solid {BORDER}",
                },
            ],
            sort_action="none",
            page_action="none",
        )
        return kpis, table
