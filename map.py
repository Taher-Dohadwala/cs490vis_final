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
    counties = json.load(response)


df = pd.read_csv("covid_confirmed_usafacts.csv")

sample = df[["countyFIPS","stateFIPS","County Name", "10/24/20"]]

sample["scaled_case"] = np.log10(sample["10/24/20"])
#print(sample.head())

fig = px.choropleth(sample, geojson=counties, locations='stateFIPS', color='scaled_case',
                           scope="usa",
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()