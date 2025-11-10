#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 14:36:24 2024

@author: leahclayton
"""

import xarray as xr
import numpy as np
import os
import sys

"""
------ User Inputs -----------------------------------------------------------
"""

# Edit the start and end years. The start year should be the initialization year
start_year = 2000
end_year = 2020

# Set path for input Daymet data (do not include a / at the end)
input_path = '/home/lkc33/palmer_scratch/daymet_data'

# Set folder for output file (do not include a / at the end)
output_loc = '/home/lkc33/palmer_scratch/rddr_app_water_daily'


"""
------ For sensitivity analysis ----------------------------------------------
"""

# set to true if performing a sensitivity analysis run
sens_analysis = False

# specify the type of sensitivity analysis (str) 
# Options currently coded for: high_rdd, low_rdd
sens_type = ' '

# Select True if you also want to run rainfall and prcp
rain_prcp = True

"""
------ Do not edit any code below this line ----------------------------------
"""

# Specify the constants for the accumulated degree day snowmelt methodology
# From Kustas et al. 1994: A simple energy budget algorithm for the snowmelt runoff model
# Cited in Khire et al. 1997: Water Balance Modeling of Earthen Final Covers
# Equation: M = (a_r)(tave) + (m_q)(1-a)(sradall)

# a_r: Restricted degree day factor (2-2.5 mm/ºC, depending on wind)
# Standard vers: 2.25 mm/ºC

if sens_analysis == False:
    a_r = 2.25
    
else:
    if sens_type == 'high_rdd':
        a_r = 2.5
    else:
        if sens_type == 'low_rdd':
            a_r = 2.0
        else:
            sys.exit('Error in sensitivity analysis settings: specify sens_type')

# m_q: conversion factor for energy flux density to snowmelt depth (0.26 (mm d-1)/(W m-2))
m_q = 0.26
# a: snow surface albedo (dimensionless)
a = 0.74

"""
------ Start script ----------------------------------------------------------
"""
#%%
def create_dir_if_not_exists(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        print(f"Folder '{output_path}' already exists")
        
create_dir_if_not_exists(output_loc)

years = range(start_year, end_year + 1)

for year_int in years:
    year = str(year_int)

    year_input = f'{input_path}/daily_{year}.nc'
    daily = xr.open_dataset(year_input)
    print(f'{year} Daymet Info:')
    daily.info()
    
    #%% Calculate rainfall and snowfall using a simple accumulation model
    # Calculate daily average temperature ('tave')
    tmax = daily['tmax']
    tmin = daily['tmin']
    tave = (tmax + tmin)/2
    daily['tave'] = tave
    prcp = daily['prcp']
    if rain_prcp == True:
        prcp_trim = daily['prcp'].isel(time=slice(1,366))
        base_path = f'{output_loc}/prcp'
        create_dir_if_not_exists(base_path)
        file_path = base_path + f'/prcp_daily_{year}.nc'
        prcp_trim.to_netcdf(file_path)
    
    # Define rainfall (record prcp as rain when tave > 0)
    rainfall = xr.where(daily['tave'] > 0, daily['prcp'], 0, keep_attrs=True)
    daily['rainfall'] = rainfall
    daily['rainfall'].attrs['long_name'] = 'Rainfall'
    daily['rainfall'].attrs['units'] = 'mm d-1'
    
    if rain_prcp == True:
        rainfall_trim = daily['rainfall'].isel(time=slice(1,366))
        base_path = f'{output_loc}/rainfall'
        create_dir_if_not_exists(base_path)
        file_path = f'{output_loc}/rainfall/rainfall_daily_{year}.nc'
        rainfall_trim.to_netcdf(file_path)
    
    # Define snowfall (record prcp as snow when tave ≤ 0, as water depth equivalent)
    snowfall = xr.where(daily['tave'] <= 0, daily['prcp'], 0)
    daily['snowfall'] = snowfall
    daily['snowfall'].attrs['long_name'] = 'Snowfall'
    daily['snowfall'].attrs['units'] = 'mm d-1'
    
    
    #%% Iteratively calculate snowpack and snowmelt
    # Initialize empty 'swe' variable
    daily['swe'] = xr.DataArray(np.zeros_like(daily['prcp']), dims=('time', 'y', 'x'))
    daily['swe'].attrs['long_name'] = 'Snow Water Equivalent'
    daily['swe'].attrs['units'] = 'kg m-2'
    
    # Initialize SWE (12/30 or 12/31 dependent on leap years)
    # If this is the first year of the time series, set the first day to snowfall
    starting_year = str(start_year)
    
    if year == starting_year:
        daily['swe'].isel(time=0).values = daily['snowfall'].isel(time=0).values
    # If this is not the first year of the time series, initialize SWE with the prior year final date
    else:
        swe_init_path = f'{output_loc}/swe_initialize_{year}.nc'
        swe_init = xr.open_dataset(swe_init_path)
        print(f'{year} SWE Initialization Array:')
        swe_init.info()
        print(swe_init)
        if not swe_init['y'].equals(daily['swe']['y']):
            swe_init = swe_init.assign_coords(y=daily['swe']['y'])
            print(f'{year} y coordinates updated')
        if not swe_init['y'].equals(daily['swe']['y']):
            swe_init = swe_init.assign_coords(x=daily['swe']['x'])
            print(f'{year} x coordinates updated')
        daily['swe'].loc[dict(time=daily['time'][0])] = swe_init['swe']
        swe_init.close()
    
    # Calculate the daily daylight fraction (divide daylength by seconds per day)
    # [dayl] = s; [daylfrac] = dimensionless
    dayl = daily['dayl']
    daylfrac = dayl/86400
    
    # Calculate the radiation flux density averaged over the entire day (not just daylight hours)
    # Since radiation flux density is 0 when it is not daylight, the weighted average is
    # simply the daylight fraction times the average incident shortwave radiation flux
    # [srad] = W m-2; [sradall] = W m-2
    srad = daily['srad']
    sradall = daylfrac * srad
    daily['sradall'] = sradall
    
    srad.close()
    sradall.close()
    dayl.close()
    daylfrac.close()
    
    # 1/8/24 updated iteration script
    # Create a new variable 'snowmelt'
    daily['snowmelt'] = xr.DataArray(np.zeros_like(daily['prcp']), dims=('time', 'y', 'x'))
    daily['snowmelt'].attrs['long_name'] = 'Snowmelt'
    daily['snowmelt'].attrs['units'] = 'mm d-1'
    
    # From Kustas et al. 1994: A simple energy budget algorithm for the snowmelt runoff model
    # Cited in Khire et al. 1997: Water Balance Modeling of Earthen Final Covers
    # Equation: M = (a_r)(tave) + (m_q)(1-a)(sradall)
    # Calculate possible snowmelt for all pixels and time
    all_snowmelt =(a_r * tave) + (m_q * (1-a) * sradall)
    
    # Snowmelt possible for days above the base temperature, assumed to be 0ºC
    possible_snowmelt = xr.where(tave > 0, all_snowmelt, 0)
    daily['possible_snowmelt'] = possible_snowmelt
    
    all_snowmelt.close()
    possible_snowmelt.close()
    
    # Iterate through each day for SWE and snowmelt
    for day in range(1, len(daily['time'])):
        snowfall_day = daily['snowfall'].isel(time=day).values
        swe_prev_day = daily['swe'].isel(time=day-1).values
        
        possible_snowmelt_day = daily['possible_snowmelt'].isel(time=day).values
        possible_snowpack_day = snowfall_day + swe_prev_day
        possible_snow_dif = possible_snowpack_day - possible_snowmelt_day
        
        # Update 'snowmelt' with current values
        snowmelt_day = xr.where(possible_snow_dif >= 0, possible_snowmelt_day, possible_snowpack_day)
        daily['snowmelt'].loc[dict(time=daily['time'][day])]= snowmelt_day
        
        # Update 'swe' with current values
        swe_day = xr.where(possible_snow_dif >= 0, possible_snow_dif, 0)
        daily['swe'].loc[dict(time=daily['time'][day])] = swe_day
        
        # snowfall_day.close()
        # swe_prev_day.close()
        # possible_snowmelt_day.close()
        # possible_snowpack_day.close()
        # possible_snow_dif.close()
        # snowmelt_day.close()
        # swe_day.close()
    
    # Save SWE from 12/30 or 12/31 (leap year dependent) to initialize the next year
    next_year = str(eval(year)+1)
    swe_export_path = f'{output_loc}/swe_initialize_{next_year}.nc'
    swe_init_export = daily['swe'].isel(time=365)
    swe_init_export.to_netcdf(swe_export_path)
    swe_init_export.close()
    
    swe = daily['swe']
    #%% Calculate and export snow presence/absence
    snow_presence = xr.where(swe > 0, 1, 0)
    snow_presence_trim = snow_presence.isel(time=slice(1,366))
    
    if sens_analysis == True:
        base_path = output_loc + f'/sens_analysis/{sens_type}/snow_presence'
        create_dir_if_not_exists(base_path)
        file_path = base_path + f'/snow_presence_daily_{sens_type}_{year}.nc'
        snow_presence_trim.to_netcdf(file_path)
    else:
        base_path = output_loc + '/snow_presence'
        create_dir_if_not_exists(base_path)
        file_path = base_path + f'/snow_presence_daily_{year}.nc'
        snow_presence_trim.to_netcdf(file_path)
    
    # close open files
    daily.close()
    snow_presence.close()
    snow_presence_trim.close()

    
#%% Combine all files

if rain_prcp == True:
    variables = ['rainfall', 'prcp', 'snow_presence']
else:
    variables = ['snow_presence']

for var in variables:

    if sens_analysis == True and var == 'snow_presence':
        path = output_loc + f'/sens_analysis/{sens_type}/{var}'
    else:
        path = output_loc + f'/{var}'
    
    file_paths = []
    
    if sens_analysis == True and var == 'snow_presence':
        for year in range(start_year, end_year+1):
            file_path = path + f'/{var}_daily_{sens_type}_{year}.nc'
            file_paths.append(file_path)
        output_netcdf = path + f'/{var}_daily_{sens_type}_2000_2020.nc'
    else:
        for year in range(start_year, end_year+1):
            file_path = path + f'/{var}_daily_{year}.nc'
            file_paths.append(file_path)
        output_netcdf = path + f'/{var}_daily_2000_2020.nc'
    
    datasets = [xr.open_dataset(file) for file in file_paths]
    
    # Step 3: Combine datasets along the time dimension
    combined_dataset = xr.concat(datasets, dim='time', join='override')
    
    print(combined_dataset)
    
    # Step 5: Save the combined dataset to a netCDF file
    combined_dataset.to_netcdf(output_netcdf)
    
    combined_dataset.close()
    for dataset in datasets:
        dataset.close()
