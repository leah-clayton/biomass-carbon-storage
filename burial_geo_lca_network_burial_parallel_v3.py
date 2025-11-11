#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 13:02:30 2025

@author: leahclayton
"""

from concurrent.futures import ProcessPoolExecutor
import geopandas as gpd
import pandas as pd
import osmnx as ox
from shapely.geometry import LineString, Point
from itertools import count
import time
from pyproj import CRS
import os


"""
User inputs ******************************************************************
"""
''' ------------------------- Set File Paths ------------------------------'''

# identify trial for saved network output -- include '_' before trial names!
# ex. '_lowDOCf'
trials = ['']

# base path
base_path = '/base-path/burial_lca'

# Shapefile path for network generation (str)
shp_path = '/base-path/region.shp'

# network path
network_path = base_path + '/osmnx_network_weighted.graphml'
# is the provided network already weighted? True --> yes; False --> no
network_weighted = True

# biomass starting nodes csv
biomass_csv_path = base_path + '/input_files/biomass_centroids.csv'

# raster points from burial tool with c_weights attribute
# number of shp_paths in the list should match number of trials
shp_paths = [''
            ]


''' --------------------- Set Network Parameters --------------------------'''

# buffer distances from biomass centroids (units: km)
""" 5/9/25 This appears fine to stay in km """
beccs_buffer_width = 402.336 # = 250 mi
raster_buffer_width = 160.934 # = 100 mi

if '_250mi' in trials:
    print('Check raster radius, "_250mi" found in trials list')

# Select biomass county centroids
# NOTE: this model does not account for quantity of biomass, just presence/absence

# Select the biomass accessibility classification (str; 'A1'-'A6' or 'all')
# Case sensitive!
# A1: <500ft from roads, Up to 20% slope
# A2: 500-1,000 ft from roads, Up to 20% slope
# A3: 1,000-1/2 mile from roads, Up to 20% slope
# A4: <500ft from roads, 20-40% slope
# A5: 500-1,000 ft from roads, 20-40% slope
# A6: 1,000-1/2 mile from roads, 20-40% slope
# all: all biomass from all accessibility classification; presence of any biomass in that county
biomass_access = 'all'

# Select forest management (str; 'USFS','Other', or 'Total')
# Selecting 'all' above will select 'Total' here
# Case sensitive!
forest_management = 'Total'

# set project CRS (given: Daymet LCC)
project_crs = '+proj=lcc +lat_1=25 +lat_2=60 +lat_0=42.5 +lon_0=-100 +datum=NAD83 +units=km +x_0=0 +y_0=0'
pyproj_crs =CRS.from_proj4(project_crs)


'''--------------------- Select Components to Run -------------------------'''

""" 5/9/25 Issue with certain packages ignoring km directive in the CRS """
# Select true to correct the c_weight to m instead of km once networks already
# weighted and clipped (occurs in BECCS and burial raster steps)
correct_c_weight_m = True

# Add burial c_weight raster points to the network? True --> yes; False --> no
build_raster_pts_network = True

# Save the network with raster points? True --> yes; False --> no
save_raster_pts_network = True

"""
Start script ******************************************************************
"""

#%% set up
networks_output = base_path + '/networks'

def create_dir_if_not_exists(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        print(f"Folder '{output_path}' already exists")
        
create_dir_if_not_exists(networks_output)

# import biomass start points csv
all_biomass = pd.read_csv(biomass_csv_path)

if biomass_access == 'all':
    biomass_column = 'Total_BDT'
else:
    biomass_column = f'{forest_management}_BDT_{biomass_access}'

# filter to selection    
biomass_filtered =  all_biomass[all_biomass[biomass_column] != -999]
print(f'Biomass class {biomass_column} selected and filtered')

# convert to gdf
biomass_pts = gpd.GeoDataFrame(biomass_filtered,
                             geometry = gpd.points_from_xy(biomass_filtered['longitude'], biomass_filtered['latitude']),
                             crs = 'EPSG:4326')

# project to LCC
biomass_proj = biomass_pts.to_crs(pyproj_crs)

# create buffer based on radius for burial potential
raster_buffer = biomass_proj.copy()
raster_buffer['geometry'] = raster_buffer.geometry.buffer(raster_buffer_width)
# reproject back to WGS84 for osmnx compatibility
raster_for_ox = raster_buffer.to_crs('EPSG:4326')

#%% c_weights classification initialization
# Forest road edge factor (conversion from LCA to per km)
# OLD, switching to m
# forest_factor = 1.72019E-4 / 1.609344

# Forest road edge factor (conversion from LCA mi to per m)
# 8/18/25 LCA parameter updated
forest_factor = 0.0000568 / 1.609344 / 1000

# Highway road edge factor (conversion from LCA to per km)
# OLD, switching to m
# highway_factor = 8.15303E-5 / 1.609344

# Highway road edge factor (conversion from LCA mi to per m)
# 8/18/25 LCA parameter updated
highway_factor = 0.0001199 / 1.609344 / 1000

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

# load shapefile of the Western US and reproject to WGS84 for use with osmnx
gdf = gpd.read_file(shp_path).to_crs(epsg=4326)
west_us = gdf.geometry[0]

if build_raster_pts_network == True:
    for i in range(0, len(shp_paths)):
        shp = base_path + f'/{shp_paths[i]}'
        trial = trials[i]
        raster_pts_lcc = gpd.read_file(shp) # CRS LCC
        raster_pts = raster_pts_lcc.to_crs('EPSG:4326') # reproject to WGS84
        
        def process_burial_network(args):
            idx, row = args
            polygon = row['geometry']
            
            raster_add_start = time.time()
            
            G = ox.load_graphml(f'{networks_output}/osmnx_network_weighted_{idx}.graphml')
            
            if correct_c_weight_m == True:
                for u, v, data in G.edges(data=True):
                    if 'c_weight' in data:
                        data['c_weight'] = float(data['c_weight']) / 1000
                        
                        # 8/18/25 correction for v2 from v1:
                        old_forest = 1.72019E-4
                        new_forest = 0.0001199
                        old_highway = 8.15303E-5
                        new_highway = 0.0000568
                        
                        if is_forest_road(data):
                            data['c_weight'] = (float(data['c_weight']) / old_forest) * new_forest
                        else:
                            data['c_weight'] = (float(data['c_weight']) / old_highway) * new_highway
            
            gdf_nodes, gdf_edges = ox.graph_to_gdfs(G) # LCC
            
            clip_pts_wgs = raster_pts[raster_pts.geometry.intersects(polygon)] # all inputs in EPGS:4326
            
            clip_pts = clip_pts_wgs.to_crs(crs = pyproj_crs) # to LCC
            
            print(f'Number of points in clip_pts for polygon {idx} = {len(clip_pts)}')
            
            if clip_pts.empty:
                print(f'Warning: no burial points from raster in polygon {idx}')
            
            # search for nearest edges with osmnx function
            nearest_nodes = ox.distance.nearest_nodes(G, X=clip_pts.geometry.x, Y=clip_pts.geometry.y)
            
            new_nodes = {}
            new_edges = []
            
            # generate all node IDs
            node_id_generator = count(start=max(G.nodes) + 1)
            
            # loop through each point to connect it to the network
            for point, nearest_node in zip(clip_pts.itertuples(), nearest_nodes):
                pt_geom = point.geometry
                c_weight = point.c_weight
            
                # add unique node ID
                new_node_id = next(node_id_generator)
            
                # store new node
                new_nodes[new_node_id] = {
                    'x': pt_geom.x, 
                    'y': pt_geom.y, 
                    'geometry': pt_geom,
                    'c_weight': c_weight,
                    'node_type': 'raster_pt',
                    'loc': 'end'
                }
                
                # create new edge connecting new node to nearest existing node
                edge_geom = LineString([pt_geom, Point(G.nodes[nearest_node]['x'], G.nodes[nearest_node]['y'])])
                
                # compute new edge weight; length (units: meters) * LCA forestry road factor
                length = edge_geom.length
                new_edge_c_weight = (length * forest_factor) + c_weight
            
                new_edge_attrs = {
                    'geometry': edge_geom,
                    'length': length,
                    'c_weight': new_edge_c_weight
                }
            
                # add bidirectional edges to list
                new_edges.append((new_node_id, nearest_node, new_edge_attrs))
                new_edges.append((nearest_node, new_node_id, new_edge_attrs))
            
            
            # add new nodes and edges to the graph
            G.add_nodes_from(new_nodes.items())
            G.add_edges_from((u, v, attrs) for u, v, attrs in new_edges)
            
            raster_add_end = time.time()
            raster_add_runtime = raster_add_end - raster_add_start
            print(f'Network {idx} LCA Raster Points --> Network Run time: {raster_add_runtime:.2f} s')
            
            if save_raster_pts_network == True:
                save_raster_pts_network_path = networks_output + f'/osmnx_raster_pts_network{trial}_{idx}.graphml'
                ox.save_graphml(G, save_raster_pts_network_path)
                print(f'Network with raster points saved for {idx}')
    
        args_list = list(raster_for_ox.iterrows())
    
        with ProcessPoolExecutor(max_workers=10) as executor:
            executor.map(process_burial_network, args_list)
    
    
    






