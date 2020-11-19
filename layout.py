"""
This script contains the page layout, UI, mapping, and callback code for the vis

app.layout is the page layout with dcc components embedded inside


"""

import pandas as pd
import numpy as np
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import date
from urllib.request import urlopen
import json


with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

cases = pd.read_csv("covid_confirmed_usafacts.csv")
deaths = pd.read_csv("covid_deaths_usafacts.csv")
dates = list(cases.columns[4:])
drilldown_options = ["States","Counties"]
states = list(pd.unique(cases["State"]))
[drilldown_options.append(x) for x in states]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([
        html.Div([
            html.H4(children="Covid-19 Data:"),
            dcc.Tabs(id='cases-deaths', value='cases', children=[
                dcc.Tab(label='Cases', value='cases'),
                dcc.Tab(label='Deaths', value='deaths'),])
        ],className="three columns"),
        
        html.Div([
            html.H4(id="display-date",children=dates[50]),
            dcc.Slider(
                id="date-slider",
                min=0,
                max=len(dates),
                value=50,
                marks={
                    0:{"label":dates[0]},
                    len(dates):{"label":dates[len(dates)-1]}
                })
        ],className="three columns"),
        
        html.Div([
        html.H4(children="Map Data:"),
        dcc.RadioItems(
            options=[
            {'label': 'Covid-19 vs Mobility', 'value': 'covid_mobility'},
            {'label': 'Covid-19', 'value': 'covid'},
            {'label': 'Mobility', 'value': 'mobility'}],
            value='covid_mobility')
        ],className="three columns"),
        
        html.Div([
        html.H4(children="Drilldown"),
        dcc.Dropdown(
            id="drilldown",
            options=[{"label":x,"value":x} for x in drilldown_options],
            multi=False,
            value="States"
        )
        ],className="three columns"),
    ],className="row",style={"padding":25}),
    
    html.Div([
        dcc.Graph(id='graph1')
    ],className="row")
    
],className="row")

@app.callback(
    Output('display-date', 'children'),
    [Input('date-slider', 'value')])
def update_display_date(date):
    return dates[date]

@app.callback(
    Output('graph1', 'figure'),
    [Input('date-slider', 'value'),
     Input("drilldown","value"),
     Input("cases-deaths","value")
     ])

def update_figure(date_value,drilldown,cases_deaths):
    current = dates[date_value]
    if cases_deaths == "cases":
        df = cases
    else:
        df = deaths
    print("Updating....")
    if drilldown == "States":
        sample = pd.DataFrame()
        sample["stateFIPS"] = df["stateFIPS"].unique()
        sample[current] =df[["stateFIPS",current]].groupby("stateFIPS").sum()[current]
        sample.fillna(0)
        loc = "stateFIPS"
    else:        
        sample = df[["countyFIPS", current]]
        sample[current] = np.log10(sample[current])
        loc = "countyFIPS"
    fig = px.choropleth(sample, geojson=counties, locations=loc, color=current, scope="usa")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    print("Finished updating")
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)