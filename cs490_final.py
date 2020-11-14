import pandas as pd
from datetime import datetime
import numpy as np 


#import and formate trip data

trips = pd.read_csv('Trips_by_Distance.csv')
trips.head()

trips['Date'] = trips['Date'].astype('datetime64[ns]')
trips = trips.dropna(subset=['County FIPS','Population Staying at Home'])
trips['County FIPS'] = trips['County FIPS'].astype('int64')

# trips['Number of Trips 1-3']=trips['Number of Trips 1-3']*2
# trips['Number of Trips 3-5']=trips['Number of Trips 3-5']*4
# trips['Number of Trips 5-10']=trips['Number of Trips 5-10']*7.5
# trips['Number of Trips 10-25']=trips['Number of Trips 10-25']*17.5
# trips['Number of Trips 25-50']=trips['Number of Trips 25-50']*37.5
# trips['Number of Trips 50-100']=trips['Number of Trips 50-100']*75
# trips['Number of Trips 100-250']=trips['Number of Trips 100-250']*175
# trips['Number of Trips 250-500']=trips['Number of Trips 250-500']*375
# trips['Number of Trips >=500']=trips['Number of Trips >=500']*500
# filter_col = [col for col in trips if col.startswith('Number of Trips ')]
# trips['Average Trip Distance'] = trips[filter_col].sum(axis=1)/trips['Number of Trips']


column_names = [0,1,2,3,4,5,6]

base_trips = trips[trips['Date']<='2020-01-21']
base_trips = base_trips[base_trips['Date']>='2020-01-08']
base_trips['Day'] = base_trips['Date'].apply(lambda x: x.weekday())
base_trips = base_trips.groupby(['County FIPS','Day'],as_index=False)['Number of Trips'].mean()
base_trips = base_trips.pivot(index='County FIPS', columns='Day', values='Number of Trips')

trips = trips[trips['County FIPS'].isin(list(base_trips.index))]
trips['Mobility'] = trips['Number of Trips']/trips.apply(lambda row: base_trips.loc[row['County FIPS'],row['Date'].weekday()], axis = 1)


# import and format county population data

population = pd.read_csv('covid_county_population_usafacts.csv')
population = population[population.population > 1]

#import and format deaths data

deaths = pd.read_csv('covid_deaths_usafacts.csv')
deaths = deaths.melt(id_vars=["countyFIPS", "County Name", "State", 'stateFIPS'], 
        var_name="Date", 
        value_name="Total Deaths")
deaths['Date'] = deaths['Date'].astype('datetime64[ns]')
deaths = pd.merge(right=deaths, left=population, how='left', right_on=['countyFIPS', 'County Name', 'State'], left_on=['countyFIPS', 'County Name', 'State'])

deaths = deaths.sort_values(by=['countyFIPS', 'Date'],ignore_index=True)
# deaths['Total Pop Death Percent'] = deaths['Total Deaths']/deaths['population']*100
# deaths['Total Deaths per 1000'] = deaths['Total Deaths']/deaths['population']*1000
deaths['New Deaths'] = deaths['Total Deaths'] - deaths['Total Deaths'].shift(1)
deaths.loc[deaths.groupby('countyFIPS',as_index=False).head(1).index,'New Deaths'] = deaths.loc[deaths.groupby('countyFIPS',as_index=False).head(1).index,'Total Deaths']
# deaths['New Pop Death Percent'] = deaths['New Deaths']/deaths['population']*100
# deaths['New Deaths per 1000'] = deaths['New Deaths']/deaths['population']*1000
# deaths['Seven day death average'] = deaths.groupby('countyFIPS')['New Deaths'].rolling(7, min_periods = 1).mean().reset_index(drop = True)
deaths['Seven day death total'] = deaths.groupby('countyFIPS')['New Deaths'].rolling(7, min_periods = 1).mean().reset_index(drop = True)
deaths['Three day death total'] = deaths.groupby('countyFIPS')['New Deaths'].rolling(3, min_periods = 1).mean().reset_index(drop = True)
deaths['Death growth rate'] = np.log(deaths['Three day death total'])/np.log(deaths['Seven day death total'])
# deaths['Seven day death total per 1000'] = deaths['Seven day death total']/deaths['population']*1000

#import and format case data

cases = pd.read_csv('covid_confirmed_usafacts.csv')
cases = cases.melt(id_vars=["countyFIPS", "County Name", "State", 'stateFIPS'], 
        var_name="Date", 
        value_name="Total Cases")
cases['Date'] = cases['Date'].astype('datetime64[ns]')
cases = pd.merge(right=cases, left=population, how='left', right_on=['countyFIPS', 'County Name', 'State'], left_on=['countyFIPS', 'County Name', 'State'])
cases = cases.sort_values(by=['countyFIPS', 'Date'])
# cases['Total Pop Cases Percent'] = cases['Total Cases']/cases['population']*100
# cases['Total Cases per 1000'] = cases['Total Cases']/cases['population']*1000
cases['New Cases'] = cases['Total Cases'] - cases['Total Cases'].shift(1)
cases.loc[cases.groupby('countyFIPS',as_index=False).head(1).index,'New Cases'] = cases.loc[cases.groupby('countyFIPS',as_index=False).head(1).index,'Total Cases']
# cases['New Pop Case Percent'] = cases['New Cases']/cases['population']*100
# cases['New Case per 1000'] = cases['New Cases']/cases['population']*1000
# cases['Seven day case average'] = cases.groupby('countyFIPS')['New Cases'].rolling(7, min_periods = 1).mean().reset_index(drop = True)
cases['Seven day case total'] = cases.groupby('countyFIPS')['New Cases'].rolling(7, min_periods = 1).mean().reset_index(drop = True)
cases['Three day case total'] = cases.groupby('countyFIPS')['New Cases'].rolling(3, min_periods = 1).mean().reset_index(drop = True)
cases['Case growth rate'] = np.log(cases['Three day case total'])/np.log(cases['Seven day case total'])
# cases['Seven day case total per 1000'] = cases['Seven day case total']/cases['population']*1000

from numpy import inf
case_death = pd.merge(right=cases, left=deaths, how='left', right_on=['countyFIPS', 'Date', 'County Name', 'State', 'stateFIPS', 'population'], left_on=['countyFIPS', 'Date', 'County Name', 'State', 'stateFIPS', 'population'])

final = pd.merge(right=trips, left=case_death, how='left', right_on=['County FIPS', 'Date'], left_on=['countyFIPS', 'Date'])
final = final.sort_values(by=['countyFIPS', 'Date'])
final['Change in trips'] = final['Number of Trips'] - final['Number of Trips'].shift(1)
final['Trips per 1000'] = (final['Number of Trips']/final['population'])*1000
final['Case growth rate'] = final['Case growth rate'].replace(np.inf, np.nan).replace(-np.inf, np.nan).interpolate(axis=0, limit_direction='forward')
final['Death growth rate'] = final['Death growth rate'].replace(np.inf, np.nan).replace(-np.inf, np.nan).interpolate(axis=0, limit_direction='forward')
final['Mobility'] = final['Mobility'].shift(11).interpolate(axis=0, limit_direction='forward')