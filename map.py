"""
This script is for testing the plotly mapping.

The counties variable holds the mapping layout plotly needs for BOTH counties and states

If we create bins for the covid cases/deaths we can create a discrete color theme

"""

import pandas as pd
import plotly.express as px
import numpy as np 
from datetime import datetime
from urllib.request import urlopen
import json

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    geojson = json.load(response)



# Plotting counties
def plot_counties():
    counties = pd.read_pickle("final_county.gz",compression="gzip")
    # preprocessing that won't need be done in the final verison (should be already done in the data)
    counties["countyFIPS"] = counties["countyFIPS"].astype(str)
    counties['countyFIPS'] = counties['countyFIPS'].apply(lambda x: ('0'+x if(len(x) == 4) else x))

    # getting list of dates
    dates = counties["Date"].unique()
    # building discrete color map
    discrete_color = list(pd.unique(counties["Case Rate Color"]))
    discrete_color_map = {}
    for i in discrete_color:
        discrete_color_map[i] = i
        
    # slicing data for 1 day
    sample = counties[counties.Date == dates[100]]
        
    """
    px.choropleth break down
    
    sample = dateframe
    geojson = geojson (dictionary of points to draw the map)
    locations = matches the geojson and is a way to match the data to a part of the map (example counties, which is contained in the geojson)
    color = the data that we are visualizing
    color_discrete_map = discrete color map for the data in color
    scope = what to show
    
    """
    fig = px.choropleth(sample,geojson=geojson,locations='countyFIPS', color='Case Rate Color',color_discrete_map=discrete_color_map, scope="usa")
    
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()

# Plotting states
def plot_states():
    states = pd.read_pickle("final_state.gz",compression="gzip")
#     dates = states["Date"].unique()
#     sample = states[states.Date == dates[50]]

    fig = px.choropleth(states,locationmode="USA-states",locations='State', color='Case growth rate',scope="usa", animation_frame="Date")
    
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()
# 
plot_states()                        