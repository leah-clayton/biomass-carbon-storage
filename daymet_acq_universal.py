#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 13:10:59 2024

@author: leahclayton
"""

import pydaymet as daymet
import geopandas as gpd
import warnings
import calendar
import os

"""
------ User Inputs -----------------------------------------------------------
"""
# Edit the start and end years. The start year should be the initialization year
start_year = 2000
end_year = 2020

# update the last year in the Daymet record
daymet_end_year = 2023

# Set pathway where shapefile is located (do not include / at the end)
shapefile_loc = '/shapefile_loc_string.shp'

# Set folder for output file (do not include / at the end)
output_loc = '/output_folder_string'

"""
------ Do not edit any code below this line ----------------------------------
"""
# create the output directory if it does not yet exist
def create_dir_if_not_exists(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        print(f"Folder '{output_path}' already exists.")
    
create_dir_if_not_exists(output_loc)

# recommended by pydaymet creators
warnings.filterwarnings("ignore", message=".*Index.*")

# read in shapefile from location location and print shapefile headers
gdf = gpd.read_file(shapefile_loc)

# select the geometry from the shapefile as 'polygon' and feed to geometry variable
# this may change depending on the exact shapefile, so check for individual file
row_index = 0
column_name = 'geometry'
polygon = gdf.loc[row_index, column_name]
geometry = polygon

# select variables of interest -- need tmin, tmax, prcp, srad, and dayl
var = ['tmin', 'tmax', 'prcp', 'srad', 'dayl']

for year_int in range(start_year, end_year + 1):
    year = str(year_int)
            
    # find prior year 
    prior_year = str(eval(year)-1)
    
    # check if the year is a leap year and set start date accordingly
    # necessary since 12-31 is cut for leap years to keep 365 days/year
    if calendar.isleap(eval(prior_year)):
        start_date = '12-30-' + prior_year
    else:
        start_date = '12-31-' + prior_year
    
    # set the end date (unless at the last year in the Daymet record)
    next_year = str(eval(year)+1)
    if year == str(daymet_end_year):
        end_date = '12-31-22'
    else:
        end_date = '01-01-' + next_year
    
    dates = (start_date, end_date)
    
    # use pydaymet to pull data into xarray (multidimensional array) and save netCDF
    daily = daymet.get_bygeom(geometry, dates, variables=var, time_scale='daily')
    daily.to_netcdf(f'{output_loc}/daily_{year}.nc')
    daily.close()
    print(f'{year} acquired and saved')
