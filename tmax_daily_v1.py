#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 14:27:55 2024

@author: leahclayton
"""

import xarray as xr
import numpy as np
import os


"""
------ User Inputs -----------------------------------------------------------
"""

# Edit the start and end years. The start year should be the initialization year
start_year = 2000
end_year = 2020

# Set path for input Daymet data (do not include a / at the end)
input_path = '/base-path/daymet_data'

# Set folder for output file (do not include a / at the end)
output_loc = '/base-path/rddr_app_water_daily/tmax_daily'


"""
------ Do not edit any code below this line ----------------------------------
"""
#%%
# create output directory if it doesn't exist
def create_dir_if_not_exists(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        print(f"Folder '{output_path}' already exists")
        
create_dir_if_not_exists(output_loc)

# initialize range of years to extract data
years = range(start_year, end_year + 1)

for year_int in years:
    year = str(year_int)

    year_input = f'{input_path}/daily_{year}.nc'
    daily = xr.open_dataset(year_input)
    print(f'{year} Daymet Info:')
    daily.info()
    
    #%%
    # Reduce to tmax
    ds = daily['tmax']
    
     # remove the first and last time steps (one day of prior and subsequent year data)
    ds_trim = ds.isel(time=slice(1,366))
    
    # select file path to save output to
    file_path = f'{output_loc}/tmax_daily_{year}.nc'
    
    # save to netCDF
    ds_trim.to_netcdf(file_path)
    
    # close open files
    daily.close()
    ds.close()
    ds_trim.close()
    
#%% combine all files
input_loc = output_loc

file_paths = []

for year in range(start_year, end_year + 1):
    file_path = input_loc + f'/tmax_daily_{year}.nc'
    file_paths.append(file_path)

# output NetCDF file
output_netcdf = output_loc + '/tmax_daily_2000_2020.nc'

datasets = [xr.open_dataset(file) for file in file_paths]

# combine datasets along the time dimension
combined_dataset = xr.concat(datasets, dim='time', join='override')

print(combined_dataset)

# save the combined dataset to a netCDF file
combined_dataset.to_netcdf(output_netcdf)
