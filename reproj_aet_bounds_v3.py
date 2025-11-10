#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 10:28:19 2024

@author: leahclayton
"""

import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
import pyproj
import datetime
import calendar
import os

# generate file paths for the raster patterns
raster_patterns = []
input_loc = '/home/lkc33/palmer_scratch/ssebop_daily'
output_loc = '/home/lkc33/palmer_scratch/ssebop_analysis_ready'

def create_dir_if_not_exists(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        print(f"Folder '{output_path}' already exists.")
        
create_dir_if_not_exists(output_loc)

start_date = datetime.date(2000, 1, 1)
end_date = datetime.date(2020, 12, 30)

current_date = start_date
while current_date <= end_date:
    year_str = str(current_date.year)
    day_str = current_date.strftime('%j')
    # exclude 12/31 on leap years to match Daymet extent
    if calendar.isleap(current_date.year) and current_date.month == 12 and current_date.day == 31:
        current_date += datetime.timedelta(days=1)
    else:
        raster_pattern = f'/{year_str}{day_str}.tif'
        raster_patterns.append(raster_pattern)
        current_date += datetime.timedelta(days=1)

# Define the desired bounds for the reprojected raster
xmin = -1950.75
xmax = xmin + 1786
ymax = 906.5
ymin = ymax - 2060
target_bounds = (xmin, ymin, xmax, ymax)

# Define the desired pixel size (1 km in both x and y directions)
pixel_size = 1

# Define width and height
width = int(1786)
height = int(2060)

# Define the target coordinate system using pyproj.CRS
daymet_lcc = pyproj.CRS.from_string(
    '+proj=lcc +lat_1=25 +lat_2=60 +lat_0=42.5 +lon_0=-100 +x_0=0 +y_0=0 '
    '+a=6378137.0 +b=6356752.314140 +units=km +no_defs'
)

# Create an affine transformation matrix for the target coordinate system
transform = from_origin(target_bounds[0], target_bounds[3], pixel_size, pixel_size)

for file in raster_patterns:
    source_raster_path = input_loc + file
    target_raster_path = output_loc + file
    # Open the source raster in its original coordinate system (WGS84)
    with rasterio.open(source_raster_path) as src:
        # Reproject the source raster to the target coordinate system
        with rasterio.open(target_raster_path, 'w', driver='GTiff',
                           transform=transform, width=width, height=height,
                           count=src.count, dtype=src.dtypes[0], crs=daymet_lcc) as dst:
    
            # Set the origin and bounds of the new reprojected raster
            # dst.transform = transform
            # dst.bounds = target_bounds
    
            # Perform the reprojection
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=daymet_lcc,
                resampling=Resampling.cubic
            )
