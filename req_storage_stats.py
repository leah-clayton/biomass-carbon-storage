#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 14:08:23 2025

@author: leahclayton
"""

import xarray as xr
import numpy as np
import pyproj
import rasterio
from rasterio.mask import mask
import geopandas as gpd

# paths to the NetCDF files (don't include / at the end)
base_path = '/home/lkc33/palmer_scratch'

# set to true if running stats for sensitivity analysis runs (boolean)
sens_analysis = False

# specify the type of sensitivity analysis (str) 
# Options currently coded for: 'high_rdd', 'low_rdd', 'no_snow'
sens_types = ['high_rdd', 'low_rdd', 'no_snow']

# for AET correction (boolean)
aet_correct = True

# specify AET correction factor (float; units of mm d-1)
aet_factor = 0.5

# model version number (string; check file name)
vers = '33'

# statistic rasters to output
# options: '95th', 'mean', 'stdev', 'coevar', 'max', 'med' (median)
# to calculate 'coevar', 'mean' and 'stdev' must also be calculated and listed BEFORE 'coevar'
stats = ['max', '95th', 'mean', 'stdev', 'coevar', 'med']

"""
--- Check file paths below ---------------------------------------------------
"""

input_loc = base_path + f'/daily_wb_results_2001_2020_v{vers}'

# shapefile path and import
shp_path = '/home/lkc33/project/western_us_shp_lcc/Western_States_Merge_4_LCC.shp'
gdf = gpd.read_file(shp_path)

src_crs = pyproj.CRS.from_string(
    '+proj=lcc +lat_1=25 +lat_2=60 +lat_0=42.5 +lon_0=-100 +x_0=0 +y_0=0 '
    '+a=6378137.0 +b=6356752.314140 +units=km +no_defs'
)


if sens_analysis == True:
    for sens_type in sens_types:
        
        if aet_correct == True:
            aet_num = str(aet_factor)
            aet_str = aet_num.replace('.','')
            
        if sens_analysis == False:
            if aet_correct == True:
                input_path = input_loc + f'/daily_required_storage_2001_2020_v{vers}_aet{aet_str}.nc'
            else:
                input_path = input_loc + f'/daily_required_storage_2001_2020_v{vers}.nc'
        else:
            sens_dir = input_loc + f'/sens_analysis/{sens_type}'
            if aet_correct == True:
                input_path = sens_dir + f'/daily_required_storage_2001_2020_v{vers}_{sens_type}_aet{aet_str}.nc'
            else:
                input_path = sens_dir + f'/daily_required_storage_2001_2020_v{vers}_{sens_type}.nc'
                
        ds = xr.open_dataset(input_path)
        
        for stat in stats:
                
            if sens_analysis == False:
                if aet_correct == True:
                    unmasked_save_loc = input_loc + f'/unmasked_req_storage_{stat}_2001_2020_v{vers}_aet{aet_str}.tif'
                    save_loc = input_loc + f'/req_storage_{stat}_2001_2020_v{vers}_aet{aet_str}.tif'
                else:
                    unmasked_save_loc = input_loc + f'/unmasked_req_storage_{stat}_2001_2020_v{vers}.tif'
                    save_loc = input_loc + f'/req_storage_{stat}_2001_2020_v{vers}.tif'
            else:
                sens_dir = input_loc + f'/sens_analysis/{sens_type}'
                if aet_correct == True:
                    unmasked_save_loc = sens_dir + f'/unmasked_req_storage_{stat}_2001_2020_v{vers}_{sens_type}_aet{aet_str}.tif'
                    save_loc = sens_dir + f'/req_storage_{stat}_2001_2020_v{vers}_{sens_type}_aet{aet_str}.tif'
                else:
                    unmasked_save_loc = sens_dir + f'/unmasked_req_storage_{stat}_2001_2020_v{vers}_{sens_type}.tif'
                    save_loc = sens_dir + f'/req_storage_{stat}_2001_2020_v{vers}_{sens_type}.tif'
            
            if stat == 'max':
                req_stat = ds.max(dim = 'time')
            if stat == 'mean':
                req_stat = ds.mean(dim = 'time')
                ds_mean = req_stat
            if stat == 'stdev':
                req_stat = ds.std(dim = 'time')
                ds_stdev = req_stat
            if stat == 'coevar':
                req_stat = ds_stdev/ds_mean
            if stat == '95th':
                req_stat = ds.quantile(0.95, dim = 'time')
            if stat == 'med':
                req_stat = ds.quantile(0.5, dim = 'time')
                
            # variable to extract from netcdfs
            variable_name = 'sr'
            
            variable_data = req_stat['sr']
        
            # Get the spatial information from the xarray dataset
            x_coords = req_stat['x'].values
            y_coords = req_stat['y'].values
            transform = rasterio.transform.from_origin(x_coords.min(), y_coords.max(), x_coords[1] - x_coords[0], y_coords[0] - y_coords[1])
        
            # Create a GeoTIFF file and save the variable as a raster
            with rasterio.open(unmasked_save_loc, 'w', driver='GTiff', height=variable_data.shape[0], width=variable_data.shape[1], count=1, dtype=variable_data.dtype, crs=src_crs, transform=transform) as dst:
                dst.write(variable_data, 1)
                
            with rasterio.open(unmasked_save_loc) as src:
                # Mask the raster using the shapefile
                clipped_data, clip_transform = mask(src, gdf.geometry, crop=True, invert=False)
                clip_meta = src.meta.copy()
        
            # Update metadata for the clipped raster
            clip_meta.update({
                'width': clipped_data.shape[2],
                'height': clipped_data.shape[1],
                'transform': clip_transform,
                'crs': src.crs
            })
        
            # Save the clipped raster to a new file
            with rasterio.open(save_loc, 'w', **clip_meta) as clipped_dst:
                clipped_dst.write(clipped_data)
                
            req_stat.close()
          
        ds.close()
        
        if 'mean' in stats:
            ds_mean.close()
        if 'stdev' in stats:
            ds_stdev.close()
else:

    if aet_correct == True:
        aet_num = str(aet_factor)
        aet_str = aet_num.replace('.','')
        
    if aet_correct == True:
        input_path = input_loc + f'/daily_required_storage_2001_2020_v{vers}_aet{aet_str}.nc'
    else:
        input_path = input_loc + f'/daily_required_storage_2001_2020_v{vers}.nc'
            
    ds = xr.open_dataset(input_path)
    
    for stat in stats:
            
        if aet_correct == True:
            unmasked_save_loc = input_loc + f'/unmasked_req_storage_{stat}_2001_2020_v{vers}_aet{aet_str}.tif'
            save_loc = input_loc + f'/req_storage_{stat}_2001_2020_v{vers}_aet{aet_str}.tif'
        else:
            unmasked_save_loc = input_loc + f'/unmasked_req_storage_{stat}_2001_2020_v{vers}.tif'
            save_loc = input_loc + f'/req_storage_{stat}_2001_2020_v{vers}.tif'

        
        if stat == 'max':
            req_stat = ds.max(dim = 'time')
        if stat == 'mean':
            req_stat = ds.mean(dim = 'time')
            ds_mean = req_stat
        if stat == 'stdev':
            req_stat = ds.std(dim = 'time')
            ds_stdev = req_stat
        if stat == 'coevar':
            req_stat = ds_stdev/ds_mean
        if stat == '95th':
            req_stat = ds.quantile(0.95, dim = 'time')
        if stat == 'med':
            req_stat = ds.quantile(0.5, dim = 'time')
            
        # variable to extract from netcdfs
        variable_name = 'sr'
        
        variable_data = req_stat['sr']
    
        # Get the spatial information from the xarray dataset
        x_coords = req_stat['x'].values
        y_coords = req_stat['y'].values
        transform = rasterio.transform.from_origin(x_coords.min(), y_coords.max(), x_coords[1] - x_coords[0], y_coords[0] - y_coords[1])
    
        # Create a GeoTIFF file and save the variable as a raster
        with rasterio.open(unmasked_save_loc, 'w', driver='GTiff', height=variable_data.shape[0], width=variable_data.shape[1], count=1, dtype=variable_data.dtype, crs=src_crs, transform=transform) as dst:
            dst.write(variable_data, 1)
            
        with rasterio.open(unmasked_save_loc) as src:
            # Mask the raster using the shapefile
            clipped_data, clip_transform = mask(src, gdf.geometry, crop=True, invert=False)
            clip_meta = src.meta.copy()
    
        # Update metadata for the clipped raster
        clip_meta.update({
            'width': clipped_data.shape[2],
            'height': clipped_data.shape[1],
            'transform': clip_transform,
            'crs': src.crs
        })
    
        # Save the clipped raster to a new file
        with rasterio.open(save_loc, 'w', **clip_meta) as clipped_dst:
            clipped_dst.write(clipped_data)
            
        req_stat.close()
      
    ds.close()
    
    if 'mean' in stats:
        ds_mean.close()
    if 'stdev' in stats:
        ds_stdev.close()

