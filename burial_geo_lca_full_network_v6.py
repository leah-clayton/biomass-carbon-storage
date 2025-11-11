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
given the large spatial areas being analyzed.

Note 8/18/25: Split into several scripts to reduce processing time and future
parallelization; acquiring the full network still takes several days

Please read through the user inputs section carefully and respond to each variable.

Note: This script is designed sequentially
1) Network acquisition from OpenStreetMap
2) Adding carbon weights to the acquired network

Complete processing requires significant time and compuational power. The below
section can be used to split the process into several pieces.

* indicates a high-level if statement used for entire section

The boolean variables and if/else statements are designed for the sequential
framework. If certain steps are skipped,
the remainder of the script may not run properly. This is likely because the 
network isn't loaded in at the correct place.

"""

# base path
base_path = '/home/lkc33/palmer_scratch/burial_lca'

#%% 
""" Network generation ----------------------------------------------------"""
# (1) * Generate base network from osmnx? (bool) True-> yes,  False-> load file from path
generate_network = False

# If generate network == True,
## (1a) Shapefile path for outer bounds of network generation (str)
shp_path = '/home/lkc33/project/western_us_shp_wgs84/Western_States_Merge_4_WGS84.shp'

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
    

