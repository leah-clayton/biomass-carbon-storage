#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  2 15:53:30 2025

@author: leahclayton
"""

import osmnx as ox
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.crs import CRS
from shapely.geometry import box, Point
import time

"""
User inputs ******************************************************************

This script is to generate the network for analysis. Acquiring one large network
and then clipping it (different script) is preferable to prevent API load-shedding
on osmnx given the large spatial areas being analyzed.

Please read through the user inputs section carefully and respond to each variable.

Note: This script is designed sequentially
1) Network acquisition from OpenStreetMap
2) Adding carbon weights to the acquired network
3) Clipping the burial tool raster to within 0.5 mi (or set threshold) from 
road network
4) Creating points from the burial tool raster and saving as a shapefile

Complete processing requires significant time and compuational power. The below
section can be used to split the process into several pieces.

* indicates a high-level if statement used for entire section

The boolean variables and if/else statements are designed for the sequential
framework. If certain steps are skipped,
the remainder of the script may not run properly. This is likely because the 
network isn't loaded in at the correct place.

"""

# base path
base_path = '/base-path/burial_lca'

#%% 
""" Network generation ----------------------------------------------------"""
# (1) * Generate base network from osmnx? (bool) True-> yes,  False-> load file from path
generate_network = False

# If generate network == True,
## (1a) Shapefile path for outer bounds of network generation (str)
shp_path = '/base-path/region.shp'

## (1b) Save network WITHOUT c_weights? (bool) True-> yes, False-> no
save_network = False

## (1c) Configure the network
# Docs: https://osmnx.readthedocs.io/en/stable/user-reference.html#osmnx.graph.graph_from_polygon
# specify if a custom network is being built or a network type is being set (bool)
# True-> custom_filter, False-> network_type
custom_network = True

# (1d) set network type (str) OR custom_filter
# options: "all", "all_public", "drive", "drive_service", "walk"
# 'drive' selects all roads excluding service roads
# 'drive_service' includes service roads
# NEITHER option includes PRIVATE roads; use the custom_filter option instead
network_type = ''

# Custom filter instead of the network type presets (str, list[str], or none)
# If string is used, the intersection of the items will be used
# If list is used, the union of the list items will be used
# e.g., ["highway"~"motorway|trunk"] or ['[maxspeed=50]', '[lanes=2]']
# given: all roads, both public and private
custom_filter = (
    '["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|'
    'service|track|road"]'
)

## If generate_network == False,
# (1e) * Should a network be loaded at this step?
load_base_network = False

# (1f) * If True, filter a saved network to add c_weights? True-> yes, load base network from 
#      file path; False-> no, network filtering and c_weights added and saved
add_network_c_weights = False

## (1e.i) If True, specify the file path for the network to import
base_network_path = base_path + '/osmnx_network.graphml'

## (1e.ii) If True, should the network with weights added be saved?
save_network_weights = False

## (1e.iii) If False, should a base network with c_weights be loaded?
load_network_weighted = True
network_weighted_path = base_path + '/osmnx_network_weighted.graphml'

#%%
""" Biomass burial LCA raster addition ------------------------------------"""
# (2) * Generate points from LCA raster? (bool) True-> yes, False-> load file from path
generate_raster_pts = True

## (2a) If generate_raster_pts == True, select whether to True-> build raster path 
##      from parameters or False-> provide the raster path
build_raster_path = True
## (2a.i) If build_raster_path = False, specify the raster path (str)
set_raster_path = ''

## (2a.ii) if build_raster_path == True, specify the following parameters:
### min depth threshold (units: m)
min_dep_threshold = True
min_depth = 1
### depth threshold (units: m)
max_depth = 6.67
### excavator and dozer emissions factor (units: carbon efficiency per m)
excavator = 0.00543
dozer = 0.009188
### soil carbon oxidation rate (units: proportion)
ox_rate = 0.1
### DOCf (units: proportion)
docf = 0.03
### proportion of methane oxidized in the cover
ch4_ox = 0.75

## (2b) buffer distance for burial distance off existing road (units: km)
buffer_distance = 0.80467

"""
Start script, do not edit below this line ************************************
"""
#%%
# Universal project CRS (Daymet LCC)
project_crs = '+proj=lcc +lat_1=25 +lat_2=60 +lat_0=42.5 +lon_0=-100 +datum=NAD83 +units=km +x_0=0 +y_0=0'

# Forest road edge factor (conversion from LCA to per km, updated 8/18/25)
forest_factor = 0.0001199 / 1.609344

# Highway road edge factor (conversion from LCA to per km, updated 8/18/25)
highway_factor = 0.0000568 / 1.609344

# define function to determine if a road is a forestry road
# unpaved list from https://wiki.openstreetmap.org/wiki/Key:surface
unpaved_list = ['unpaved', 'compacted', 'fine_gravel', 'gravel', 'rock', 
                'pebblestone', 'ground', 'dirt', 'earth']

def is_forest_road(data):
    highway = data.get('highway', '')
    surface = data.get('surface', '')

    if (
        highway == 'track' or 
        (highway == 'service' and surface in unpaved_list) or
        (highway == 'unclassified' and surface in unpaved_list)
    ):
        return True
    return False

#%% road network generation / network load
if generate_network == True:
    start_time = time.time()
    
    # ensure shapefile is in EPSG:4326 (WGS84) to be compatable with osmnx
    gdf = gpd.read_file(shp_path).to_crs(epsg=4326)
    
    # Create graph from network
    if custom_network == True:
        G_i = ox.graph_from_polygon(gdf.geometry[0],
                                  simplify=True,
                                  retain_all=False,
                                  truncate_by_edge=True,
                                  custom_filter = custom_filter)
    else:
        G_i = ox.graph_from_polygon(gdf.geometry[0],  
                                  network_type = network_type,
                                  simplify=True,
                                  retain_all=False,
                                  truncate_by_edge=True)
    
    print('Network original CRS:', G_i.graph['crs'])
    
    
    # reproject to LCC
    G = ox.project_graph(G_i, to_crs=project_crs)
    print('Network reprojected CRS:', G.graph['crs'])
    
    # Save network
    if save_network == True:
        save_network_path = base_path + '/osmnx_network.graphml'
        ox.save_graphml(G, filepath = save_network_path)
        
    network_time = time.time()
    network_runtime = network_time - start_time
    print(f'Network building run time: {network_runtime:.2f} s')

else:    
    if load_base_network == True:
        G = ox.load_graphml(base_network_path)
        print('Base network loaded')
        print('Loaded network CRS:', G.graph['crs'])
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)

#%% road network weighting
if add_network_c_weights == True:
    weights_start = time.time()
        
    # set the c_weights for forest roads vs. other road types
    # updated 8/18/25 to c_weight for m instead of km
    for u, v, key, data in G.edges(keys=True, data=True):
        if is_forest_road(data):
            c_weight = (data.get('length', 0)/1000) * forest_factor
        else:
            c_weight = (data.get('length', 0)/1000) * highway_factor
        
        if data.get('c_weight', None) != c_weight:
            data['c_weight'] = c_weight
            
    print('c_weights added to the network')
    
    # Convert to geodataframes
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
    
    # Save network
    if save_network_weights == True:
        save_network_path = base_path + '/osmnx_network_weighted.graphml'
        ox.save_graphml(G, filepath = save_network_path)
        
    weights_end = time.time()
    weights_runtime = weights_end - weights_start
    print(f'Network weights filtering run time: {weights_runtime:.2f} s')
else:
    if load_network_weighted == True:
        G = ox.load_graphml(network_weighted_path)
        print('Weighted network loaded')
        print('Loaded network CRS:', G.graph['crs'])
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
    
#%% generate points from LCA raster for biomass burial
if generate_raster_pts == True:
    raster_start = time.time()
    gdf_buffer = gdf_edges.copy() 
    
    # raster file path
    if build_raster_path == True:
        md_str = str(max_depth).replace('.', '')
        exc_str = str(excavator).replace('.', '')
        doz_str = str(dozer).replace('.', '')
        ox_str = str(ox_rate).replace('.', '')
        docf_str = str(docf).replace('.', '')
        ch4_str = str(ch4_ox).replace('.', '')
        
        if min_dep_threshold == True:
            min_dep_str = str(min_depth)
            raster_path = base_path + f'/burial_lca_min{min_dep_str}_md{md_str}_exc{exc_str}_doz{doz_str}_ox{ox_str}_docf{docf_str}_ch4ox{ch4_str}.tif'
        else:
            raster_path = base_path + f'/burial_lca_md{md_str}_exc{exc_str}_doz{doz_str}_ox{ox_str}_docf{docf_str}_ch4ox{ch4_str}.tif'
    else:
        raster_path = set_raster_path
    
    # extract raster crs
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        print('Raster CRS:', raster_crs)
        proj_crs = CRS.from_proj4(project_crs)
        if raster_crs != proj_crs:
            print('Warning: Raster CRS does not match project CRS')
        
    # reproject gdf_buffer to projected coordinate system to better measure distance
    # gdf_buffer.to_crs(raster_crs) # v7 should already be in LCC here
    gdf_buffer['geometry'] = gdf_edges.geometry.buffer(buffer_distance)
    buffer_union = gdf_buffer.union_all()
    buffer_gdf = gpd.GeoDataFrame(geometry=[buffer_union], crs=raster_crs)
    
    # load raster
    with rasterio.open(raster_path) as src:
        raster = src.read(1)
        transform = src.transform
        nodata_value = src.nodata
        raster_crs = src.crs
        raster_bounds = box(*src.bounds) # v2 troubleshooting
        print('Raster bounds:', raster_bounds)
            
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
    
    mskd_save_path = raster_path.replace('.tif', '_buffered.tif')
    
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
        
        # v2 troubleshooting
        print('empty geometries:', buffer_gdf.is_empty.any())  # Check for empty geometries
        print('NaN geometries:', buffer_gdf.geometry.isna().any())  # Check for NaN geometries
    
        points = [Point(rasterio.transform.xy(out_transform, r, c)) for r, c in zip(rows, cols)]
        c_weights = [mskd_raster[r, c] for r, c in zip(rows, cols)]
    
    # create gdf with point geometries and pixel values
    raster_pts = gpd.GeoDataFrame({"c_weight": c_weights, "geometry": points}, crs=raster_crs)
    
    # save to shp file
    if build_raster_path == True:
        if min_dep_threshold == True:
            output_raster_pts = base_path + f'/raster_pts_min{min_dep_str}_md{md_str}_exc{exc_str}_doz{doz_str}_ox{ox_str}_docf{docf_str}_ch4ox{ch4_str}.shp'
        else:
            output_raster_pts = base_path + f'/raster_pts_md{md_str}_exc{exc_str}_doz{doz_str}_ox{ox_str}_docf{docf_str}_ch4ox{ch4_str}.shp'
    else:
        cleaned_raster_path = str(raster_path).replace('.tif', '')
        output_raster_pts = base_path + f'/raster_pts_{cleaned_raster_path}.shp'
        
    raster_pts.to_file(output_raster_pts)
    
    raster_end = time.time()
    raster_runtime = raster_end - raster_start
    print(f'LCA Raster --> Points Run time: {raster_runtime:.2f} s')
    
else: # open existing points file
    print('generate_raster_pts == False, no point layer generated')
