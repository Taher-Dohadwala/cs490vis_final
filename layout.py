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

# get geojson to plot US map with plotly
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    geojson = json.load(response)

# Load data 
counties = pd.read_pickle("final_county.gz",compression="gzip")
states = pd.read_pickle("final_state.gz",compression="gzip")

counties["countyFIPS"] = counties["countyFIPS"].astype(str)
counties['countyFIPS'] = counties['countyFIPS'].apply(lambda x: ('0'+x if(len(x) == 4) else x))
# Get date range and states list
dates = counties["Date"].unique()
drilldown_options = ["States","Counties"]
states = list(pd.unique(counties["State"]))
[drilldown_options.append(x) for x in states]

discrete_color = list(pd.unique(counties["Case Rate Color"]))
discrete_color_map = {}
for i in discrete_color:
    discrete_color_map[i] = i

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
            id="map-data",
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
            value="Counties"
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
     Input("cases-deaths","value"),
     Input("map-data","value")
     ])
def update_figure(date_value,drilldown,cases_deaths,map_data):
    print("Updating....")
    current = dates[date_value]
    data = ""
    color_map = "continuous"
    
    if map_data == "covid":
        if cases_deaths == "cases":
            data = "Case growth rate"
        else:
            data = "Death growth rate"
        
    elif map_data == "mobility":
        data = "Mobility"
    else:
        color_map = "discrete"
        if cases_deaths == "cases":
            data = "Case Rate Color"
        else:
            data = "Death Rate Color"
        
        
    if drilldown == "States":
        df = states[states["Date"] == current]
        print(df.head())
        if color_map == "discrete":
            fig = px.choropleth(df,locationmode="USA-states",locations='State', color=data,color_discrete_map=discrete_color_map,scope="usa")
        else:
            fig = px.choropleth(df,locationmode="USA-states",locations='State', color=data,scope="usa")
    elif drilldown == "Counties":
        df = counties[counties["Date"] == current]
        if color_map == "discrete":
            fig = px.choropleth(df, geojson=geojson, locations="countyFIPS", color=data,color_discrete_map=discrete_color_map, scope="usa")
        else:
            fig = px.choropleth(df, geojson=geojson, locations="countyFIPS", color=data, scope="usa")

    else:
        df = counties[counties["Date"] == current]
        df = df[df["State"] == drilldown]
        if color_map == "discrete":
            fig = px.choropleth(df, geojson=geojson, locations="countyFIPS", color=data,color_discrete_map=discrete_color_map)
        else:
            fig = px.choropleth(df, geojson=geojson, locations="countyFIPS", color=data)
        fig.update_geos(fitbounds="locations", visible=False)
        

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    print("Finished updating")
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)