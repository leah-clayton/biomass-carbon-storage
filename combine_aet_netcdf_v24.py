#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 15:11:37 2024

@author: leahclayton
"""

import subprocess
import os
import datetime
import calendar
import xarray as xr

input_loc = '/home/lkc33/palmer_scratch/ssebop_analysis_ready'

output_loc = '/home/lkc33/palmer_scratch/final_daily_wb_data'
output_file = output_loc + '/ssebop_daily_aet_2000_2020.nc'

daymet_path = '/home/lkc33/palmer_scratch/rddr_app_water_daily/rddr_daily_app_water_2000_2020.nc'

start_date = datetime.date(2000, 1, 1)
end_date = datetime.date(2020, 12, 30)

file_names = []

current_date = start_date
while current_date <= end_date:
    year_str = str(current_date.year)
    day_str = current_date.strftime('%j')
    # exclude 12/31 on leap years to match Daymet extent
    if calendar.isleap(current_date.year) and current_date.month == 12 and current_date.day == 31:
        current_date += datetime.timedelta(days=1)
    else:
        file_name = input_loc + f'/{year_str}{day_str}.tif'
        file_names.append(file_name)
        current_date += datetime.timedelta(days=1)

# print(len(file_names))
daily_geotiffs = file_names

#%%
def create_dir_if_not_exists(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        print(f"Folder '{output_path}' already exists.")
        
create_dir_if_not_exists(output_loc)

# create a temporary directory to store intermediate NetCDF files
temp_dir = '/home/lkc33/palmer_scratch/temp_dir'
os.makedirs(temp_dir, exist_ok=True)

# Daymet CRS as string
daymet_string = '+proj=lcc +lat_1=25 +lat_2=60 +lat_0=42.5 +lon_0=-100 +x_0=0 +y_0=0 +a=6378137.0 +b=6356752.314140 +units=km +no_defs'

# specify upper left and lower right bounds of the raster in Daymet LCC
# upper_left_x = -1950.75
# upper_left_y = 906.50
# lower_right_x = -164.75
# lower_right_y = -1153.50

# convert each GeoTIFF to NetCDF
netcdf_files = []
for i, geotiff in enumerate(daily_geotiffs):
    output_netcdf = os.path.join(temp_dir, f'time_step_{i}.nc')
      
    # use gdal_translate to convert GeoTIFF to NetCDF
    translate_command = [
        'gdal_translate',
        '-of', 'netCDF',
        '-co', 'FORMAT=NC4',
        '-co', 'WRITE_BOTTOMUP=NO',
        #'-r', 'cubic',
        #'-a_ullr', str(upper_left_x), str(upper_left_y), str(lower_right_x), str(lower_right_y),
        '-a_srs', daymet_string,
        geotiff,
        output_netcdf,
    ]
    subprocess.run(translate_command)
    
    netcdf_files.append(output_netcdf)

# concatenate all of the daily files
datasets = [xr.open_dataset(file) for file in netcdf_files]
concatenated_dataset = xr.concat(datasets, dim='time')

print('\ndataset before Daymet axis application')
print(concatenated_dataset)

# ensure axes between Daymet and AET data are identical

daymet = xr.open_dataset(daymet_path)

time_axis = daymet['time']
x_axis = daymet['x']
y_axis = daymet['y']

if not concatenated_dataset['time'].equals(time_axis):
    print('time axis not equal\n AET time axis:\n')
    print(concatenated_dataset['time'])
    print('Daymet time axis:\n')
    print(time_axis)
    concatenated_dataset['time'] = time_axis
    print('\ntime axis set with Daymet')
    
if not concatenated_dataset['x'].equals(x_axis):
    print('x axis not equal\n AET x-axis:\n')
    print(concatenated_dataset['x'])
    print('Daymet x-axis:\n')
    print(x_axis)
    concatenated_dataset['x'] = x_axis
    print('\nx-axis set with Daymet')
    
if not concatenated_dataset['y'].equals(y_axis):
    print('y axis not equal\n AET y-axis:\n')
    print(concatenated_dataset['y'])
    print('Daymet y-axis:\n')
    print(y_axis)
    print('\ny-axis not equal')
    concatenated_dataset['y'] = y_axis

print('\ndataset after Daymet axis application')
print(concatenated_dataset)

# rename variable data to 'aet' for actual evapotranspriation
concatenated_dataset = concatenated_dataset.rename({'Band1':'aet'})

# correct band name and magnitude for aet (documentation says all rasters x1000)
aet = concatenated_dataset['aet']
rescale_aet = aet/1000.0
concatenated_dataset['aet'] = rescale_aet

# add aet attributes
concatenated_dataset['aet'].attrs['long_name'] = 'SSEBop Actual Evapotranspiration'
concatenated_dataset['aet'].attrs['units'] = 'mm'

# save the concatenated dataset to a new NetCDF file
concatenated_dataset.to_netcdf(output_file)

# clean up temporary NetCDF files
for netcdf_file in netcdf_files:
    os.remove(netcdf_file)

# remove temporary directory
os.rmdir(temp_dir)

# close the daily datasets
for ds in datasets:
    ds.close()

# close the concatenated dataset
concatenated_dataset.close()