#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 12:37:21 2025

@author: leahclayton
"""

import osmnx as ox
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.crs import CRS
from shapely.geometry import Point
import time
import os

"""
User inputs ******************************************************************
"""

# base path
base_path = '/base-path/burial_lca'

#%% 
""" Load or Generate network -----------------------------------------------"""
generate_buffer = False
network_weighted_path = base_path + '/osmnx_network_weighted.graphml'

# if false, file path to load buffer
buffer_path = base_path + '/road_buffer/road_buffer_wgs84.shp'

#%%
""" Biomass burial LCA raster addition ------------------------------------"""

# * Generate points from LCA raster? (bool) True-> yes, False-> load file from path
generate_raster_pts = True

raster_base = base_path + '/raster_sens_analysis'

raster_paths = ['replace_with_raster_files.tif'
                ]

## buffer distance for burial distance off existing road (units: km)
buffer_distance = 0.80467 # = 0.5 mi

"""
Start script, do not edit below this line ************************************
"""
#%%
# Universal project CRS (Daymet LCC)
project_crs = '+proj=lcc +lat_1=25 +lat_2=60 +lat_0=42.5 +lon_0=-100 +datum=NAD83 +units=km +x_0=0 +y_0=0'

def create_dir_if_not_exists(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        print(f"Folder '{output_path}' already exists")

if generate_buffer == True: 
    buffer_start = time.time()
    G = ox.load_graphml(network_weighted_path)
    #G['crs'] = project_crs
    print('Weighted network loaded')
    print('Loaded network CRS:', G.graph['crs'])
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
    
    gdf_buffer = gdf_edges.copy()
    gdf_buffer['geometry'] = gdf_edges.geometry.buffer(buffer_distance)
    buffer_union = gdf_buffer.union_all()
    gdf_union = gpd.GeoDataFrame(geometry=[buffer_union], crs=G.graph['crs'])
    buffer_dir = base_path + '/road_buffer'
    create_dir_if_not_exists(buffer_dir)
    buffer_output = buffer_dir + '/road_buffer_wgs84.shp'
    gdf_union.to_file(buffer_output)
    buffer_end = time.time()
    
    buffer_run_time = buffer_end - buffer_start
    print(f'Buffer shapefile saved; time = {buffer_run_time:.2f}')
else:
    gdf_union = gpd.read_file(buffer_path)
    print('Buffer loaded from file')
    
#%% generate points from LCA raster for biomass burial
if generate_raster_pts == True:
    for raster_path in raster_paths: 
        raster_start = time.time()
        
        path = raster_base + f'/{raster_path}'
        
        # extract raster crs
        with rasterio.open(path) as src:
            raster_crs = src.crs
            print('Raster CRS:', raster_crs)
            proj_crs = CRS.from_proj4(project_crs)
            if raster_crs != proj_crs:
                print('Warning: Raster CRS does not match project CRS')
            
        # reproject gdf_buffer to projected coordinate system to better measure distance
        buffer_gdf = gdf_union.to_crs(raster_crs)
        
        # load raster
        with rasterio.open(path) as src:
            raster = src.read(1)
            transform = src.transform
            nodata_value = src.nodata
            raster_crs = src.crs
                
            if buffer_gdf.crs != raster_crs:
                print('Original buffer CRS:', buffer_gdf.crs)
                buffer_gdf = buffer_gdf.to_crs(raster_crs)
                print('Buffer reprojected to raster CRS')
            
            print('Buffer CRS:', buffer_gdf.crs)
            
            src_mskd, out_transform = mask(src, buffer_gdf.geometry, crop=True)
            mskd_meta = src.meta.copy()
            mskd_meta.update({
                'driver': 'GTiff',
                'height': src_mskd.shape[1],
                'width': src_mskd.shape[2],
                'transform': out_transform
            })
        
        mskd_save_path = path.replace('.tif', '_buffered.tif')
        
        # save masked raster
        with rasterio.open(mskd_save_path, 'w', **mskd_meta) as dest:
            dest.write(src_mskd)
        print('Buffered raster saved')
        
        with rasterio.open(mskd_save_path) as src:
            mskd_raster = src.read(1)
            nodata_val = src.nodata
            meta = src.meta.copy()
            crs = src.crs
            
            rows, cols = np.where(mskd_raster != nodata_value)
        
            points = [Point(rasterio.transform.xy(out_transform, r, c)) for r, c in zip(rows, cols)]
            c_weights = [mskd_raster[r, c] for r, c in zip(rows, cols)]
        
        # create gdf with point geometries and pixel values
        raster_pts = gpd.GeoDataFrame({"c_weight": c_weights, "geometry": points}, crs=raster_crs)
        
        # save to shp file
        cleaned_raster_path = str(raster_path).replace('.tif', '')
        output_folder = base_path + f'/{cleaned_raster_path}'
        create_dir_if_not_exists(output_folder)
        output_raster_pts = output_folder + f'/raster_pts_{cleaned_raster_path}.shp'
            
        raster_pts.to_file(output_raster_pts)
        
        raster_end = time.time()
        raster_runtime = raster_end - raster_start
        print(f'LCA Raster --> Points Run time: {raster_runtime:.2f} s')
        
    else: # open existing points file
        print('generate_raster_pts == False, no point layer generated')
