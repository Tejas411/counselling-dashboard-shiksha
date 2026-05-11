import dash_bootstrap_components as dbc
from dash import html

BG         = "#F5F4EF"
SURFACE    = "#FFFFFF"
SURFACE2   = "#FAFAF8"
BORDER     = "#E8E4DC"
TEXT       = "#1A1915"
MUTED      = "#8B8680"
SUBTLE     = "#D4D0C8"
ACCENT     = "#CF6A4C"
GRID_COLOR = "#F0EDE8"

CHART = dict(
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(family="Inter, sans-serif", color=MUTED, size=11),
    margin=dict(l=8, r=8, t=44, b=8),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT, size=11),
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER,
                    font_color=TEXT, font_family="Inter, sans-serif", font_size=12),
)
AXIS      = dict(showgrid=False, zeroline=False, showline=False, tickcolor=SUBTLE)
AXIS_GRID = dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False, showline=False, tickcolor=SUBTLE)

CARD = {"backgroundColor": SURFACE, "border": f"1px solid {BORDER}",
        "borderRadius": "12px", "overflow": "hidden",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.05)"}
DROP_STYLE = {"backgroundColor": SURFACE, "border": f"1px solid {BORDER}", "borderRadius": "8px"}

SC          = {"ACCEPTED": "#16A34A", "PENDING": "#D97706", "REJECTED": "#DC2626"}
CALL_BLUE   = "#2563EB"
CALL_INDIGO = "#4F46E5"
CALL_TEAL   = "#0D9488"
CALL_PURPLE = "#7C3AED"
CALL_SKY    = "#0284C7"
RESP_GREEN  = "#059669"
RESP_TEAL   = "#0D9488"
RESP_VIOLET = "#7C3AED"
RESP_SKY    = "#0284C7"
CLIENT_SC   = {"Client": RESP_GREEN, "Non-Client": "#94A3B8"}


def flabel(text):
    return html.Span(text, style={
        "color": MUTED, "fontSize": "11px", "fontWeight": "500",
        "letterSpacing": "0.06em", "textTransform": "uppercase",
        "display": "block", "marginBottom": "6px",
    })


def kpi_card(title, value, color, sub="", width=2):
    return dbc.Col(html.Div([
        html.Div(style={"height": "3px", "backgroundColor": color,
                        "borderRadius": "12px 12px 0 0", "marginBottom": "16px"}),
        html.P(title, style={"color": MUTED, "fontSize": "11px", "fontWeight": "500",
                              "textTransform": "uppercase", "letterSpacing": "0.06em",
                              "margin": "0 0 6px"}),
        html.Div(str(value), style={"color": TEXT, "fontSize": "30px", "fontWeight": "700",
                                    "lineHeight": "1", "fontVariantNumeric": "tabular-nums"}),
        html.P(sub, style={"color": color, "fontSize": "11px", "fontWeight": "500",
                           "margin": "6px 0 0"}),
    ], style={**CARD, "padding": "0 20px 18px", "borderTop": "none"}), width=width)


def slabel(text):
    return html.Div(text, style={
        "color": MUTED, "fontSize": "10px", "fontWeight": "600",
        "letterSpacing": "0.10em", "textTransform": "uppercase",
        "padding": "16px 20px 4px",
    })


def fmt_duration(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m}m" if h else f"{m}m"


def navbar(active):
    def nav_link(label, href, is_active):
        return html.A(label, href=href, style={
            "color": ACCENT if is_active else MUTED,
            "fontWeight": "600" if is_active else "500",
            "fontSize": "13px",
            "textDecoration": "none",
            "padding": "0 4px 12px",
            "borderBottom": f"2px solid {ACCENT}" if is_active else "2px solid transparent",
            "marginRight": "28px",
            "transition": "color 0.15s",
        })
    return html.Div([
        html.Div([
            html.Div([
                html.Div(style={"width": "8px", "height": "8px", "borderRadius": "50%",
                                "backgroundColor": ACCENT, "display": "inline-block",
                                "marginRight": "10px", "verticalAlign": "middle"}),
                html.Span("Counselling Dashboard", style={
                    "color": TEXT, "fontSize": "15px", "fontWeight": "700",
                    "verticalAlign": "middle", "letterSpacing": "-0.01em",
                }),
            ], style={"marginRight": "40px", "display": "flex", "alignItems": "center"}),
            html.Div([
                nav_link("Applications", "/",            active == "applications"),
                nav_link("Calls",        "/calls",        active == "calls"),
                nav_link("Responses",    "/responses",    active == "responses"),
                nav_link("Fresh Leads",  "/fresh-leads",  active == "fresh_leads"),
                nav_link("Leaderboard",  "/leaderboard",  active == "leaderboard"),
            ], style={"display": "flex", "alignItems": "flex-end", "paddingTop": "4px"}),
        ], style={
            "maxWidth": "100%", "margin": "0 auto",
            "display": "flex", "alignItems": "center",
            "padding": "16px 28px 0",
        }),
        html.Div(style={"height": "1px", "backgroundColor": BORDER, "marginTop": "0"}),
    ], style={"backgroundColor": SURFACE, "boxShadow": "0 1px 0 rgba(0,0,0,0.06)",
              "position": "sticky", "top": "0", "zIndex": "100"})
