import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd

from theme import (BG, MUTED, ACCENT, CHART, AXIS, AXIS_GRID, CARD,
                   SURFACE, SURFACE2, BORDER, TEXT, SUBTLE, GRID_COLOR,
                   kpi_card, slabel, navbar)

_BAR_BLUE  = "#7BAFD4"
_BAR_TEAL  = "#66B2A8"
_LINE_CLR  = ACCENT
from data import allodf, _alloc_date_range


def _build_ds_daywise_table(d):
    days = sorted(d["date"].dropna().unique())[-3:]
    if not days:
        return html.P("No data available", style={"color": MUTED, "padding": "20px", "textAlign": "center"})

    day_labels = [pd.Timestamp(dt).strftime("%d %b") for dt in days]

    bucket_vals = sorted([v for v in d["ds_score_bucket"].unique() if pd.notna(v)])
    has_no_ds   = d["ds_score_bucket"].isna().any()

    _base = {"padding": "6px 10px", "fontSize": "12px", "whiteSpace": "nowrap",
             "fontFamily": "Inter, sans-serif"}

    th_main = {**_base, "backgroundColor": SURFACE2, "color": MUTED, "fontWeight": "600",
               "textAlign": "left", "verticalAlign": "middle", "minWidth": "72px",
               "borderBottom": f"2px solid {BORDER}", "fontSize": "10px",
               "textTransform": "uppercase", "letterSpacing": "0.06em"}

    th_day  = {**_base, "backgroundColor": SURFACE, "color": ACCENT, "fontWeight": "600",
               "textAlign": "center", "borderBottom": f"1px solid {BORDER}",
               "borderLeft": f"2px solid {BORDER}", "fontSize": "11px"}

    th_sub  = {**_base, "backgroundColor": SURFACE2, "color": MUTED, "fontWeight": "600",
               "textAlign": "right", "borderBottom": f"2px solid {BORDER}",
               "fontSize": "10px", "textTransform": "uppercase", "letterSpacing": "0.04em"}

    th_sub0 = {**th_sub, "borderLeft": f"2px solid {BORDER}"}

    td_label = {**_base, "color": TEXT, "fontWeight": "500", "textAlign": "left",
                "borderBottom": f"1px solid {GRID_COLOR}", "minWidth": "72px"}

    td_num   = {**_base, "color": TEXT, "textAlign": "right",
                "borderBottom": f"1px solid {GRID_COLOR}"}

    td_pct   = {**_base, "color": ACCENT, "textAlign": "right",
                "borderBottom": f"1px solid {GRID_COLOR}"}

    td_zero  = {**_base, "color": SUBTLE, "textAlign": "right",
                "borderBottom": f"1px solid {GRID_COLOR}"}

    td_tot_label = {**_base, "color": MUTED, "fontWeight": "700", "textAlign": "left",
                    "borderTop": f"2px solid {BORDER}", "backgroundColor": SURFACE2,
                    "fontSize": "10px", "textTransform": "uppercase", "letterSpacing": "0.06em"}

    td_tot_num   = {**_base, "color": TEXT, "fontWeight": "700", "textAlign": "right",
                    "borderTop": f"2px solid {BORDER}", "backgroundColor": SURFACE2}

    td_tot_pct   = {**_base, "color": ACCENT, "fontWeight": "700", "textAlign": "right",
                    "borderTop": f"2px solid {BORDER}", "backgroundColor": SURFACE2}

    def _stats(sub):
        alloc = len(sub)
        att  = int(sub["is_attempted"].sum()) if alloc and "is_attempted" in sub.columns else 0
        conn = int(sub["is_connected"].sum()) if alloc and "is_connected" in sub.columns else 0
        pct_att    = f"{att  / alloc * 100:.0f}%" if alloc else "—"
        pct_pickup = f"{conn / att   * 100:.0f}%" if att   else "—"
        pct_conn   = f"{conn / alloc * 100:.0f}%" if alloc else "—"
        return alloc, att, conn, pct_att, pct_pickup, pct_conn

    def _day_cells(alloc, att, conn, pct_att, pct_pickup, pct_conn, is_total=False, sep=False):
        n = td_tot_num if is_total else td_num
        p = td_tot_pct if is_total else td_pct
        border = {"borderLeft": f"2px solid {BORDER}"} if sep else {}
        return [
            html.Td(f"{alloc:,}" if alloc else "—", style={**n, **border}),
            html.Td(f"{att:,}"   if att   else "—", style=n),
            html.Td(f"{conn:,}"  if conn  else "—", style=n),
            html.Td(pct_att,                        style=p),
            html.Td(pct_pickup,                     style=p),
            html.Td(pct_conn,                       style=p),
        ]

    def _zero_cells(sep=False):
        border = {"borderLeft": f"2px solid {BORDER}"} if sep else {}
        return [html.Td("—", style={**td_zero, **border})] + [html.Td("—", style=td_zero)] * 5

    # ── Headers ──────────────────────────────────────────────────────────────────
    header1 = [html.Th("DS Bucket", rowSpan=2, style=th_main)]
    for lbl in day_labels:
        header1.append(html.Th(lbl, colSpan=6, style=th_day))

    header2 = []
    for i, _ in enumerate(day_labels):
        header2.append(html.Th("Alloc", style=th_sub0 if i > 0 else th_sub))
        for lbl in ("Att", "Conn", "% Att", "% Pickup", "% Conn"):
            header2.append(html.Th(lbl, style=th_sub))

    # ── Data rows ────────────────────────────────────────────────────────────────
    rows = []
    all_buckets = [(v, f"{int(v)}–{int(v)+9}", False) for v in bucket_vals]
    if has_no_ds:
        all_buckets.append((None, "No DS", True))

    for bucket_val, bucket_label, is_no_ds in all_buckets:
        cells = [html.Td(bucket_label, style=td_label)]
        for i, day in enumerate(days):
            day_d = d[d["date"] == day]
            sub   = day_d[day_d["ds_score_bucket"].isna()] if is_no_ds \
                    else day_d[day_d["ds_score_bucket"] == bucket_val]
            alloc, att, conn, pct_att, pct_pickup, pct_conn = _stats(sub)
            cells += _day_cells(alloc, att, conn, pct_att, pct_pickup, pct_conn, sep=(i > 0)) \
                     if alloc else _zero_cells(sep=(i > 0))
        rows.append(html.Tr(cells))

    # ── Total row ────────────────────────────────────────────────────────────────
    tot_cells = [html.Td("Total", style=td_tot_label)]
    for i, day in enumerate(days):
        alloc, att, conn, pct_att, pct_pickup, pct_conn = _stats(d[d["date"] == day])
        tot_cells += _day_cells(alloc, att, conn, pct_att, pct_pickup, pct_conn, is_total=True, sep=(i > 0))
    rows.append(html.Tr(tot_cells))

    table = html.Table(
        [html.Thead([html.Tr(header1), html.Tr(header2)]), html.Tbody(rows)],
        style={"width": "100%", "borderCollapse": "collapse"},
    )
    return html.Div(table, style={"overflowX": "auto", "padding": "0 4px 16px"})


_SOURCE_ORDER = [
    "Request a callback",
    "Pulled from team pool",
    "TL transferred",
    "Bot transferred",
    "Other",
]


def _build_source_bucket_table(d):
    if "allocation_source" not in d.columns:
        return html.P(
            "allocation_source column not available — re-run update_data.py to populate it.",
            style={"color": MUTED, "padding": "20px", "textAlign": "center", "fontSize": "12px"},
        )

    present  = set(d["allocation_source"].dropna().unique())
    sources  = [s for s in _SOURCE_ORDER if s in present] + sorted(present - set(_SOURCE_ORDER))

    if not sources:
        return html.P("No data", style={"color": MUTED, "padding": "20px", "textAlign": "center"})

    bucket_vals = sorted([v for v in d["ds_score_bucket"].unique() if pd.notna(v)])
    has_no_ds   = d["ds_score_bucket"].isna().any()

    _base = {"padding": "6px 10px", "fontSize": "12px", "whiteSpace": "nowrap",
             "fontFamily": "Inter, sans-serif"}

    th_label = {**_base, "backgroundColor": SURFACE2, "color": MUTED, "fontWeight": "600",
                "textAlign": "left", "borderBottom": f"2px solid {BORDER}",
                "fontSize": "10px", "textTransform": "uppercase", "letterSpacing": "0.06em",
                "minWidth": "72px"}

    th_src   = {**_base, "backgroundColor": SURFACE2, "color": MUTED, "fontWeight": "600",
                "textAlign": "right", "borderBottom": f"2px solid {BORDER}", "fontSize": "11px"}

    th_total = {**th_src, "color": ACCENT, "fontSize": "10px",
                "textTransform": "uppercase", "letterSpacing": "0.06em"}

    td_label    = {**_base, "color": TEXT, "fontWeight": "500", "textAlign": "left",
                   "borderBottom": f"1px solid {GRID_COLOR}", "minWidth": "72px"}
    td_num      = {**_base, "color": TEXT, "textAlign": "right",
                   "borderBottom": f"1px solid {GRID_COLOR}"}
    td_zero     = {**_base, "color": SUBTLE, "textAlign": "right",
                   "borderBottom": f"1px solid {GRID_COLOR}"}
    td_row_tot  = {**_base, "color": ACCENT, "fontWeight": "600", "textAlign": "right",
                   "borderBottom": f"1px solid {GRID_COLOR}",
                   "borderLeft": f"1px solid {BORDER}"}
    td_tot_label = {**_base, "color": MUTED, "fontWeight": "700", "textAlign": "left",
                    "borderTop": f"2px solid {BORDER}", "backgroundColor": SURFACE2,
                    "fontSize": "10px", "textTransform": "uppercase", "letterSpacing": "0.06em"}
    td_tot_num   = {**_base, "color": TEXT, "fontWeight": "700", "textAlign": "right",
                    "borderTop": f"2px solid {BORDER}", "backgroundColor": SURFACE2}
    td_tot_total = {**_base, "color": ACCENT, "fontWeight": "700", "textAlign": "right",
                    "borderTop": f"2px solid {BORDER}", "backgroundColor": SURFACE2,
                    "borderLeft": f"1px solid {BORDER}"}

    # ── Header ───────────────────────────────────────────────────────────────────
    header = [html.Th("DS Bucket", style=th_label)]
    for src in sources:
        header.append(html.Th(src, style=th_src))
    header.append(html.Th("Total", style=th_total))

    # ── Data rows ────────────────────────────────────────────────────────────────
    rows = []
    grand = {src: 0 for src in sources}

    all_buckets = [(v, f"{int(v)}–{int(v)+9}", False) for v in bucket_vals]
    if has_no_ds:
        all_buckets.append((None, "No DS", True))

    for bucket_val, bucket_label, is_no_ds in all_buckets:
        sub = d[d["ds_score_bucket"].isna()] if is_no_ds \
              else d[d["ds_score_bucket"] == bucket_val]
        counts    = {src: int((sub["allocation_source"] == src).sum()) for src in sources}
        row_total = sum(counts.values())
        for src in sources:
            grand[src] += counts[src]

        cells = [html.Td(bucket_label, style=td_label)]
        for src in sources:
            n = counts[src]
            cells.append(html.Td(f"{n:,}" if n else "—", style=td_num if n else td_zero))
        cells.append(html.Td(f"{row_total:,}", style=td_row_tot))
        rows.append(html.Tr(cells))

    # ── Total row ────────────────────────────────────────────────────────────────
    grand_total = sum(grand.values())
    tot_cells   = [html.Td("Total", style=td_tot_label)]
    for src in sources:
        tot_cells.append(html.Td(f"{grand[src]:,}", style=td_tot_num))
    tot_cells.append(html.Td(f"{grand_total:,}", style=td_tot_total))
    rows.append(html.Tr(tot_cells))

    table = html.Table(
        [html.Thead(html.Tr(header)), html.Tbody(rows)],
        style={"width": "100%", "borderCollapse": "collapse"},
    )
    return html.Div(table, style={"overflowX": "auto", "padding": "0 4px 16px"})


def layout():
    d = allodf.copy()
    d = d[d["is_human_transfered"] != 1]

    total       = len(d)
    high_intent = int((d["ds_score_bucket"] >= 70).sum()) if total else 0
    hi_pct      = f"{high_intent / total * 100:.1f}% of total" if total else ""

    kpis = dbc.Row([
        kpi_card("Total Allocated", f"{total:,}",       _BAR_BLUE, width=3),
        kpi_card("Leads ≥ 70 DS",   f"{high_intent:,}", _BAR_TEAL, hi_pct, width=3),
    ], className="g-3", style={"marginBottom": "20px"})

    if total > 0:
        days_sorted = sorted(d["date"].dropna().unique())
        day_strs    = [pd.Timestamp(dt).strftime("%d %b") for dt in days_sorted]

        day_total = d.groupby("date").size().reindex(days_sorted, fill_value=0)
        day_hi    = (d[d["ds_score_bucket"] >= 70]
                     .groupby("date").size()
                     .reindex(days_sorted, fill_value=0))

        total_list = day_total.tolist()
        hi_list    = day_hi.tolist()
        pct_list   = [round(h / t * 100, 1) if t else 0 for h, t in zip(hi_list, total_list)]
        max_pct    = max(pct_list) if pct_list else 100

        fig = go.Figure([
            go.Bar(name="Total Allocated", x=day_strs, y=total_list,
                   marker_color=_BAR_BLUE, marker_line_width=0),
            go.Bar(name="Leads ≥ 70",      x=day_strs, y=hi_list,
                   marker_color=_BAR_TEAL, marker_line_width=0),
            go.Scatter(name="% Leads ≥ 70", x=day_strs, y=pct_list,
                       yaxis="y2", mode="lines+markers",
                       line=dict(color=_LINE_CLR, width=2),
                       marker=dict(size=6, color=_LINE_CLR),
                       hovertemplate="%{y:.1f}%<extra></extra>"),
        ])
        fig.update_layout(
            **CHART, height=340, barmode="group", showlegend=True,
            yaxis2=dict(
                overlaying="y", side="right",
                showgrid=False, zeroline=False, showline=False,
                tickfont=dict(color=MUTED, size=10),
                ticksuffix="%",
                range=[0, min(max_pct * 1.5, 100)],
            ),
        )
        fig.update_xaxes(**AXIS,      tickfont=dict(color=MUTED, size=11))
        fig.update_yaxes(**AXIS_GRID, tickfont=dict(color=MUTED, size=10))
    else:
        fig = go.Figure()
        fig.update_layout(**CHART, height=320)

    return html.Div([
        navbar("allocations"),
        dbc.Container(fluid=True,
            style={"backgroundColor": BG, "minHeight": "100vh", "padding": "32px 28px"},
            children=[
                dbc.Row(dbc.Col(html.P(
                    f"{_alloc_date_range}  ·  Lead Allocations",
                    style={"color": MUTED, "fontSize": "13px", "margin": "0 0 24px"}
                ))),
                kpis,
                dbc.Row(dbc.Col(html.Div([
                    slabel("Daywise Allocations — Total vs High Intent (DS ≥ 70)"),
                    dcc.Graph(figure=fig, config={"displayModeBar": False}),
                ], style=CARD))),
                dbc.Row(dbc.Col(html.Div([
                    slabel("DS Bucket Breakdown — Allocated / Attempted / Connected (Last 3 Days)"),
                    _build_ds_daywise_table(d),
                ], style=CARD), className="mt-3")),
                dbc.Row(dbc.Col(html.Div([
                    slabel("Allocation Source × DS Bucket — Users Allocated"),
                    _build_source_bucket_table(d),
                ], style=CARD), className="mt-3")),
            ])
    ])


def register_callbacks(app):
    pass
