#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 14:03:24 2024

@author: leahclayton
"""

import xarray as xr
import numpy as np
import os

# paths to the NetCDF files (don't include / at the end)
base_path = '/base-path/palmer_scratch'

# set to true if performing a sensitivity analysis run (boolean)
sens_analysis = True

# specify the type of sensitivity analysis (str) 
# Options currently coded for: high_rdd, low_rdd, no_snow
sens_type = 'no_snow'

# for AET correction (boolean)
aet_correct = True

# specify AET correction factor (float; units of mm d-1)
aet_factor = 0.5

# model version number (string; check file name)
vers = '35'
## vers 34 -> 35: compatability with Daymet data now in m instead of km

"""
--- Check file paths below ---------------------------------------------------
"""
aet_path = '/base-path/final_daily_wb_data/ssebop_daily_aet_2000_2020.nc'

if aet_correct == True:
    tmax_path = base_path + '/rddr_app_water_daily/tmax_daily/tmax_daily_2000_2020.nc'
    print('AET correction present, tmax path loaded')

output_loc = base_path + f'/daily_wb_results_2001_2020_v{vers}'

if aet_correct == True:
    aet_num = str(aet_factor)
    aet_str = aet_num.replace('.','')
    
if sens_analysis == False:
    app_water_path = '/base-path/final_daily_wb_data/rddr_daily_app_water_2000_2020.nc'
    snow_path = base_path + '/rddr_app_water_daily/snow_presence/snow_presence_daily_2000_2020.nc'
    if aet_correct == True:
        output_path = output_loc + f'/daily_required_storage_2001_2020_v{vers}_aet{aet_str}.nc'
    else:
        output_path = output_loc + f'/daily_required_storage_2001_2020_v{vers}.nc'
else:
    sens_dir = base_path + f'/rddr_app_water_daily/sens_analysis/{sens_type}'
    sens_output = output_loc + f'/sens_analysis/{sens_type}'
    snow_path = sens_dir + f'/snow_presence/snow_presence_daily_{sens_type}_2000_2020.nc'
    if aet_correct == True:
        output_path = sens_output + f'/daily_required_storage_2001_2020_v{vers}_{sens_type}_aet{aet_str}.nc'
    else:
        output_path = sens_output + f'/daily_required_storage_2001_2020_v{vers}_{sens_type}.nc'
    if sens_type == 'high_rdd' or 'low_rdd':
        app_water_path = sens_dir + f'/rddr_daily_app_water_{sens_type}_2000_2020.nc'
    if sens_type == 'no_snow':
        app_water_path = base_path + '/rddr_app_water_daily/prcp/prcp_daily_2000_2020.nc'

print(output_path)

"""
--- Do not edit code below this line -----------------------------------------
"""

#%%
def create_dir_if_not_exists(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        print(f"Folder '{output_path}' already exists.")
        
create_dir_if_not_exists(output_loc)

if sens_analysis == True:
    create_dir_if_not_exists(sens_output)

# ensure that sens_type is empty if sens_analysis is set to False
if sens_analysis == False:
    sens_type = ''

#%%
# open the NetCDF files as xarrays
ds_app_water = xr.open_dataset(app_water_path)
print('app water netcdf:\n', ds_app_water)
ds_aet = xr.open_dataset(aet_path)
print("aet netcdf:\n", ds_aet)

# (v35 update) SINCE DAYMET CHANGED FROM KM TO M SCALE:
"""
ds_app_water = ds_app_water.assign_coords({
    'x': ds_app_water['x']/1000,
    'y': ds_app_water['y']/1000
    })
"""

if aet_correct == True:
    ds_tmax = xr.open_dataset(tmax_path)
    ds_tmax = ds_tmax.assign_coords({
        'x': ds_tmax['x']/1000,
        'y': ds_tmax['y']/1000
        })
    print('tmax netcdf:\n', ds_tmax)
    if sens_type != 'no_snow':
        ds_snow = xr.open_dataset(snow_path)
        """
        ds_snow = ds_snow.assign_coords({
            'x': ds_snow['x']/1000,
            'y': ds_snow['y']/1000
            })
        """
        print('snow presence netcdf:\n', ds_snow)

"""
# check the shapes of the arrays before subtraction
print("aet shape:", ds_aet['aet'].shape)
if sens_type != 'no_snow':
    print("app water shape:", ds_app_water['app_water'].shape)
else:
    print('prcp shape:', ds_app_water['prcp'].shape)
"""

# set up a new netcdf to store water balance
ds_wb = xr.Dataset(coords={dim: [] for dim in ds_app_water.dims})
ds_wb['time'] = ds_app_water['time']
ds_wb['x'] = ds_app_water['x']
ds_wb['y'] = ds_app_water['y']

# display the combined xarray
print("\ncombined_xarray:")
print(ds_wb)

# initialize accumulated required storage
if sens_type != 'no_snow':
    ds_wb['sr'] = xr.DataArray(np.zeros_like(ds_app_water['app_water']), dims=('time', 'y', 'x'))
else:
   ds_wb['sr'] = xr.DataArray(np.zeros_like(ds_app_water['prcp']), dims=('time', 'y', 'x')) 
ds_wb['sr'].attrs['long_name'] = 'Accumulated Required Storage'
ds_wb['sr'].attrs['units'] = 'mm'

# iteratively calculate accumulated required storage
for day in range(1, len(ds_wb['time'])):
    if sens_type != 'no_snow':
        app_water_day = ds_app_water['app_water'].isel(time=day).values
    else:
        app_water_day = ds_app_water['prcp'].isel(time=day).values  
    print(app_water_day)
    
    if aet_correct == True:
        tmax_day = ds_tmax['tmax'].isel(time=day).values
        if sens_type != 'no_snow':
            snow_presence_daily = ds_snow['swe'].isel(time=day).values
        
    aet_init = ds_aet['aet'].isel(time=day).values
    
    # If AET for a given day is reported as zero, check if tmax is above freezing and snow is absent and institute factor
    if aet_correct == True and sens_type != 'no_snow':
        aet_zero = xr.where((aet_init == 0) & (tmax_day > 0) & (snow_presence_daily == 0), aet_factor, aet_init)
        aet_day = aet_init + aet_zero
        print('AET correction with snow presence calculated')
    else:
        if aet_correct == True and sens_type == 'no_snow':
            aet_zero = xr.where((aet_init == 0) & (tmax_day > 0), aet_factor, aet_init)
            aet_day = aet_init + aet_zero
            print('AET correction without snow presence calculated')
        else:
            aet_day = aet_init
            print('No AET correction performed')
    print(aet_day)
    
    if day == 1:
        sr_prelim_day = app_water_day - aet_day
        sr_day = xr.where(sr_prelim_day > 0, sr_prelim_day, 0)
        ds_wb['sr'].loc[dict(time=ds_wb['time'][day])] = sr_day
    else:    
        sr_prior_day = ds_wb['sr'].isel(time=day-1).values
        
        sr_prelim_day = sr_prior_day + app_water_day - aet_day
        sr_day = xr.where(sr_prelim_day > 0, sr_prelim_day, 0)
        ds_wb['sr'].loc[dict(time=ds_wb['time'][day])] = sr_day

# select only the study years of required storage, removing initialization year (index starts at 0)
sr = ds_wb['sr'].isel(time=slice(365, None))

sr.to_netcdf(output_path)

print('final netCDF:\n')
print(sr)

sr.close()
ds_aet.close()
ds_app_water.close()
ds_tmax.close()
