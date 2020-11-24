import pandas as pd
from datetime import datetime
import numpy as np 
from numpy import inf

#import and format trip data
col_list = ['Level', 'Date', 'State FIPS', 'County FIPS',
       'County Name', 'Population Staying at Home', 'Number of Trips']
trips = pd.read_pickle('Trips_by_Distance.gz')
trips = trips.filter(col_list)

trips['Date'] = trips['Date'].astype('datetime64[ns]')

trips_state = trips[trips['Level'] == 'State'].copy()
trips_state = trips_state.drop(columns=['County FIPS', 'Level'])
trips_state['State FIPS'] = trips_state['State FIPS'].astype('int64')
# trips_state = trips_state.dropna(subset=['Population Staying at Home'])


trips_county = trips[trips['Level'] == 'County'].copy()
trips_county = trips_county.drop(columns=['State FIPS', 'Level'])
trips_county['County FIPS'] = trips_county['County FIPS'].astype('int64')
# trips_county = trips_county.dropna(subset=['Population Staying at Home'])

column_names = [0,1,2,3,4,5,6]


base_trips_state = trips_state[(trips_state['Date']<='2020-01-21') & (trips_state['Date']>='2020-01-08')].copy()
base_trips_state['Day'] = base_trips_state['Date'].apply(lambda x: x.weekday())
base_trips_state = base_trips_state.groupby(['State FIPS','Day'],as_index=False)['Number of Trips'].mean()
base_trips_state = base_trips_state.pivot(index='State FIPS', columns='Day', values='Number of Trips')

base_trips_county = trips_county[(trips_county['Date']<='2020-01-21') & (trips_county['Date']>='2020-01-08')].copy()
base_trips_county['Day'] = base_trips_county['Date'].apply(lambda x: x.weekday())
base_trips_county = base_trips_county.groupby(['County FIPS','Day'],as_index=False)['Number of Trips'].mean()
base_trips_county = base_trips_county.pivot(index='County FIPS', columns='Day', values='Number of Trips')

trips_state = trips_state[trips_state['State FIPS'].isin(list(base_trips_state.index))]
trips_state['Mobility'] = trips_state['Number of Trips']/trips_state.apply(lambda row: base_trips_state.loc[row['State FIPS'],row['Date'].weekday()], axis = 1)

trips_county = trips_county[trips_county['County FIPS'].isin(list(base_trips_county.index))]
trips_county['Mobility'] = trips_county['Number of Trips']/trips_county.apply(lambda row: base_trips_county.loc[row['County FIPS'],row['Date'].weekday()], axis = 1)


# import and format county population data

population = pd.read_csv('covid_county_population_usafacts.csv')
population = population[population.population > 1]

population_state = population.groupby(['State'])['population'].sum().reset_index()
population_county = population


#import and format deaths data

deaths = pd.read_csv('covid_deaths_usafacts.csv')
deaths = deaths.melt(id_vars=["countyFIPS", "County Name", "State", 'stateFIPS'], 
        var_name="Date", 
        value_name="Total Deaths")
deaths['Date'] = deaths['Date'].astype('datetime64[ns]')

deaths_state = deaths.groupby(['State', 'stateFIPS', 'Date'])['Total Deaths'].sum().reset_index()
deaths_state = pd.merge(right=deaths_state, left=population_state, how='left', right_on=['State'], left_on=['State'])
deaths_state = deaths_state.sort_values(by=['stateFIPS', 'Date'],ignore_index=True)


deaths_county = deaths[deaths.countyFIPS != 0]
deaths_county = pd.merge(right=deaths_county, left=population_county, how='left', right_on=['countyFIPS', 'County Name', 'State'], left_on=['countyFIPS', 'County Name', 'State'])
deaths_county = deaths_county.sort_values(by=['countyFIPS', 'Date'],ignore_index=True)


deaths_state['New Deaths'] = deaths_state['Total Deaths'] - deaths_state['Total Deaths'].shift(1)
deaths_state.loc[deaths_state.groupby('stateFIPS',as_index=False).head(1).index,'New Deaths'] = deaths_state.loc[deaths_state.groupby('stateFIPS',as_index=False).head(1).index,'Total Deaths']


deaths_county['New Deaths'] = deaths_county['Total Deaths'] - deaths_county['Total Deaths'].shift(1)
deaths_county.loc[deaths_county.groupby('countyFIPS',as_index=False).head(1).index,'New Deaths'] = deaths_county.loc[deaths_county.groupby('countyFIPS',as_index=False).head(1).index,'Total Deaths']


deaths_state['Seven day death total'] = deaths_state.groupby('stateFIPS')['New Deaths'].rolling(7, min_periods = 1).mean().reset_index(drop = True)
deaths_state['Three day death total'] = deaths_state.groupby('stateFIPS')['New Deaths'].rolling(3, min_periods = 1).mean().reset_index(drop = True)
deaths_state['Death growth rate'] = np.log(deaths_state['Three day death total'])/np.log(deaths_state['Seven day death total'])
deaths_state = deaths_state.drop(columns = ['Seven day death total','Three day death total'])


deaths_county['Seven day death total'] = deaths_county.groupby('countyFIPS')['New Deaths'].rolling(7, min_periods = 1).mean().reset_index(drop = True)
deaths_county['Three day death total'] = deaths_county.groupby('countyFIPS')['New Deaths'].rolling(3, min_periods = 1).mean().reset_index(drop = True)
deaths_county['Death growth rate'] = np.log(deaths_county['Three day death total'])/np.log(deaths_county['Seven day death total'])
deaths_county = deaths_county.drop(columns = ['Seven day death total','Three day death total'])

#import and format case data

cases = pd.read_csv('covid_confirmed_usafacts.csv')
cases = cases.melt(id_vars=["countyFIPS", "County Name", "State", 'stateFIPS'], 
        var_name="Date", 
        value_name="Total Cases")
cases['Date'] = cases['Date'].astype('datetime64[ns]')

cases_state = cases.groupby(['State', 'stateFIPS', 'Date'])['Total Cases'].sum().reset_index()
cases_state = pd.merge(right=cases_state, left=population_state, how='left', right_on=['State'], left_on=['State'])
cases_state = cases_state.sort_values(by=['stateFIPS', 'Date'],ignore_index=True)


cases_county = cases[cases.countyFIPS != 0]
cases_county = pd.merge(right=cases_county, left=population_county, how='left', right_on=['countyFIPS', 'County Name', 'State'], left_on=['countyFIPS', 'County Name', 'State'])
cases_county = cases_county.sort_values(by=['countyFIPS', 'Date'],ignore_index=True)


cases_state['New Cases'] = cases_state['Total Cases'] - cases_state['Total Cases'].shift(1)
cases_state.loc[cases_state.groupby('stateFIPS',as_index=False).head(1).index,'New Cases'] = cases_state.loc[cases_state.groupby('stateFIPS',as_index=False).head(1).index,'Total Cases']


cases_county['New Cases'] = cases_county['Total Cases'] - cases_county['Total Cases'].shift(1)
cases_county.loc[cases_county.groupby('countyFIPS',as_index=False).head(1).index,'New Cases'] = cases_county.loc[cases_county.groupby('countyFIPS',as_index=False).head(1).index,'Total Cases']


cases_state['Seven day case total'] = cases_state.groupby('stateFIPS')['New Cases'].rolling(7, min_periods = 1).mean().reset_index(drop = True)
cases_state['Three day case total'] = cases_state.groupby('stateFIPS')['New Cases'].rolling(3, min_periods = 1).mean().reset_index(drop = True)
cases_state['Case growth rate'] = np.log(cases_state['Three day case total'])/np.log(cases_state['Seven day case total'])
cases_state = cases_state.drop(columns = ['Seven day case total','Three day case total'])

cases_county['Seven day case total'] = cases_county.groupby('countyFIPS')['New Cases'].rolling(7, min_periods = 1).mean().reset_index(drop = True)
cases_county['Three day case total'] = cases_county.groupby('countyFIPS')['New Cases'].rolling(3, min_periods = 1).mean().reset_index(drop = True)
cases_county['Case growth rate'] = np.log(cases_county['Three day case total'])/np.log(cases_county['Seven day case total'])
cases_county = cases_county.drop(columns = ['Seven day case total','Three day case total'])


#combine all files 
case_death_state = pd.merge(right=cases_state, left=deaths_state, how='left', right_on=['stateFIPS', 'Date', 'State', 'population'], left_on=['stateFIPS', 'Date', 'State', 'population'])

case_death_county = pd.merge(right=cases_county, left=deaths_county, how='left', right_on=['countyFIPS', 'Date', 'County Name', 'State', 'stateFIPS', 'population'], left_on=['countyFIPS', 'Date', 'County Name', 'State', 'stateFIPS', 'population'])


final_state = pd.merge(right=trips_state, left=case_death_state, how='left', right_on=['State FIPS', 'Date'], left_on=['stateFIPS', 'Date'])
final_state = final_state.sort_values(by=['stateFIPS', 'Date'])
final_state['Population Staying Home %'] = (final_state['Population Staying at Home']/final_state['population'])*100
# final_state['Change in trips'] = final_state['Number of Trips'] - final_state['Number of Trips'].shift(1)
# final_state.loc[final_state.groupby('stateFIPS',as_index=False).head(1).index,'Change in trips'] = 0
final_state['Case growth rate'] = np.abs(final_state['Case growth rate'].replace(np.inf, 1).replace(-np.inf, 0).interpolate(axis=0, limit_direction='forward').fillna(0))
final_state['Death growth rate'] = np.abs(final_state['Death growth rate'].replace(np.inf, 1).replace(-np.inf, 0).interpolate(axis=0, limit_direction='forward').fillna(0))
final_state['Mobility'] = final_state['Mobility'].shift(11).interpolate(axis=0, limit_direction='forward').fillna(1)
final_state = final_state.drop(columns = ['State FIPS', 'County Name', 'Population Staying at Home'])
final_state = final_state.dropna(subset=['Population Staying Home %'])
final_state['Date']= final_state['Date'].apply(lambda x: x.strftime("%m/%d/%Y"))



final_county = pd.merge(right=trips_county, left=case_death_county, how='left', right_on=['County FIPS', 'Date','County Name'], left_on=['countyFIPS', 'Date', 'County Name'])
final_county = final_county.sort_values(by=['countyFIPS', 'Date'])
final_county['Population Staying Home %'] = (final_county['Population Staying at Home']/final_county['population'])*100
# final_county['Change in trips'] = final_county['Number of Trips'] - final_county['Number of Trips'].shift(1)
final_county['Case growth rate'] = np.abs(final_county['Case growth rate'].replace(np.inf, 0).replace(-np.inf, 0).interpolate(axis=0, limit_direction='forward').fillna(0))
final_county['Death growth rate'] = np.abs(final_county['Death growth rate'].replace(np.inf, 0).replace(-np.inf, 0).interpolate(axis=0, limit_direction='forward').fillna(0))
final_county['Mobility'] = final_county['Mobility'].shift(11).interpolate(axis=0, limit_direction='forward').fillna(1)
final_county = final_county.drop(columns = ['stateFIPS','County FIPS', 'Population Staying at Home'])
final_county = final_county.dropna(subset=['Population Staying Home %'])
final_county['Date']= final_county['Date'].apply(lambda x: x.strftime("%m/%d/%Y"))


# apply colors based on value

def set_interval_value(x, a, b):
    if x <= a: 
        return 0
    elif a < x <= b: 
        return 1
    else: 
        return 2

# maps growth rate, mobility to correct color
def data2color(x, y, a, b, c, d, biv_colors):
    n_colors = 9
    n = 3    
    growth_col = set_interval_value(x, a, b)
    mob_col = set_interval_value(y, c, d)
    col_idx = int(growth_col + n*mob_col)
    colors = np.array(biv_colors)[col_idx]
    return colors

state_case_perc = np.percentile(final_state['Case growth rate'], [33, 66])
state_death_perc = np.percentile(final_state['Death growth rate'], [33, 66])
state_mob_perc = np.percentile(final_state['Mobility'], [33, 66])

county_case_perc = np.percentile(final_county['Case growth rate'], [33, 66])
county_death_perc = np.percentile(final_county['Death growth rate'], [33, 66])
county_mob_perc = np.percentile(final_county['Mobility'], [33, 66])

# sample_pallette = ["#d3d3d3", "#97c5c5", "#52b6b6", "#c098b9", "#898ead", "#4a839f", "#ad5b9c", "#7c5592", "#434e87"]
sample_pallette = ["Low Growth/Low Mobility",
                   "Low Growth/Medium Mobility",
                   "Low Growth/High Mobility",
                   "Medium Growth/Low Mobility",
                   "Medium Growth/Medium Mobility",
                   "Medium Growth/High Mobility",
                   "High Growth/Low Mobility",
                   "High Growth/Medium Mobility",
                   "High Growth/High Mobility"]
color_scale = np.array(sample_pallette)
final_state['Death Rate Color'] = final_state.apply(lambda x: data2color(x['Death growth rate'], x['Mobility'],state_death_perc[0],state_death_perc[1],state_mob_perc[0],state_mob_perc[1], color_scale), axis=1)
final_state['Case Rate Color'] = final_state.apply(lambda x: data2color(x['Case growth rate'], x['Mobility'],state_case_perc[0],state_case_perc[1],state_mob_perc[0],state_mob_perc[1], color_scale), axis=1)
final_county['Death Rate Color'] = final_county.apply(lambda x: data2color(x['Death growth rate'], x['Mobility'],county_death_perc[0],county_death_perc[1],county_mob_perc[0],county_mob_perc[1], color_scale), axis=1)
final_county['Case Rate Color'] = final_county.apply(lambda x: data2color(x['Case growth rate'], x['Mobility'],county_case_perc[0],county_case_perc[1],county_mob_perc[0],county_mob_perc[1], color_scale), axis=1)

final_county['countyFIPS'] = final_county.apply(lambda x: str(x.countyFIPS) if len(str(x.countyFIPS)) == 5 else '0' + str(x.countyFIPS), axis=1)

# Save to pickle files
final_county.to_pickle("final_county.gz")
final_state.to_pickle("final_state.gz")