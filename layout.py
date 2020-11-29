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
import plotly.graph_objs as go

# get geojson to plot US map with plotly
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    geojson = json.load(response)

#build discrete scolor map
colors = ["#d3d3d3", "#97c5c5", "#52b6b6", "#c098b9", "#898ead", "#4a839f", "#ad5b9c", "#7c5592", "#434e87"]
sample_pallette = ["Low Growth/Low Mobility",
                   "Low Growth/Medium Mobility",
                   "Low Growth/High Mobility",
                   "Medium Growth/Low Mobility",
                   "Medium Growth/Medium Mobility",
                   "Medium Growth/High Mobility",
                   "High Growth/Low Mobility",
                   "High Growth/Medium Mobility",
                   "High Growth/High Mobility"]


discrete_color_map = {}
for color,desc in zip(colors,sample_pallette):
    discrete_color_map[desc] = color


def colors_to_colorscale(biv_colors):
    # biv_colors: list of  color codes in hexa or RGB255
    # returns a discrete colorscale  defined by biv_colors
    n = len(biv_colors)
    biv_colorscale = []
    for k, col in enumerate(biv_colors):
        biv_colorscale.extend([[round(k / n, 2), col], [round((k + 1) / n, 2), col]])
    return biv_colorscale


def colorsquare(text_x, text_y, colorscale, n=3, xaxis='x2', yaxis='y2'):
    # text_x : list of n strings, representing intervals of values for the first variable or its n percentiles
    # text_y : list of n strings, representing intervals of values for the second variable or its n percentiles

    z = [[j + n * i for j in range(n)] for i in range(n)]
    n = len(text_x)
    if len(text_x) != n or len(text_y) != n or len(colorscale) != 2 * n ** 2:
        raise ValueError('Your lists of strings  must have the length {n} and the colorscale, {n**2}')

    text = [[text_x[j] + '<br>' + text_y[i] for j in range(len(text_x))] for i in range(len(text_y))]
    return go.Heatmap(x=list(range(n)),
                      y=list(range(n)),
                      z=z,
                      xaxis=xaxis,
                      yaxis=yaxis,
                      text=text,
                      hoverinfo='text',
                      colorscale=colorscale,
                      showscale=False)


text_x = ["Low Mobility","Medium Mobility","High Mobility",]
text_y = ["Low Growth","Medium Growth","High Growth",]

color_legend = colorsquare(text_x, text_y, colors_to_colorscale(colors), xaxis='x1', yaxis='y1')

# Load data 
counties = pd.read_pickle("final_county.gz",compression="gzip")
states = pd.read_pickle("final_state.gz",compression="gzip")

# Get date range and states list
dates = counties["Date"].unique()
drilldown_options = ["States","Counties"]
states_list = list(pd.unique(counties["State"]))
[drilldown_options.append(x) for x in states_list]


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
        html.Div([
            dcc.Graph(id='graph1')
        ],className="eight columns"),
        html.Div([
            dcc.Graph(id='legend', figure=go.FigureWidget(data=[color_legend], layout = dict(title='Growth Rate vs Mobility Percentile',title_x = 0.5,title_y = 0.8,
            width=400, height=350, autosize=False,
            xaxis=dict(visible=True,ticktext=["Mobility <= 33rd", "33rd < Mobility <= 66th", "Mobility > 66th"], tickvals=[0,1,2]),
            yaxis=dict(visible=True, ticktext=["Growth <= 33rd", "33rd < Growth <= 66th", "Growth > 66th"], tickvals=[0,1,2]),
            hovermode='closest')
))
        ],className="four columns")
    ],className="row"),
    
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
        
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},showlegend=False)
    print("Finished updating")
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)