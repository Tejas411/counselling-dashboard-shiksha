import os
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

from data import adf, cdf, rdf
from theme import navbar
import pages.applications as applications
import pages.calls as calls
import pages.responses as responses
import pages.fresh_leads as fresh_leads
import pages.leaderboard as leaderboard
import pages.allocations as allocations

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)
app.title = "Dashboard"

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content"),
])

applications.register_callbacks(app)
calls.register_callbacks(app)
responses.register_callbacks(app)
fresh_leads.register_callbacks(app)
leaderboard.register_callbacks(app, adf, cdf, rdf)
allocations.register_callbacks(app)


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def route(pathname):
    if pathname == "/calls":       return calls.layout()
    if pathname == "/responses":   return responses.layout()
    if pathname == "/fresh-leads": return fresh_leads.layout()
    if pathname == "/leaderboard":  return html.Div([navbar("leaderboard"), leaderboard.leaderboard_content(adf, cdf, rdf)])
    if pathname == "/allocations":  return allocations.layout()
    return applications.layout()


server = app.server  # gunicorn entry point: gunicorn app:server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    debug = not os.environ.get("RENDER")
    app.run(host="0.0.0.0", port=port, debug=debug)
