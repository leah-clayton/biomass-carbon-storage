#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 21 09:10:03 2025

@author: leahclayton
"""

import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString

# post-processed csv
csv_path = '/base-path/post-processed.csv'

# output path
output_base = '/base-path/burial_lca/scenario_shapefiles'

# networks path
networks_base = '/base-path/burial_lca/shapefiles'

# specify trial (use '_{trial}' format)
trial = '_min1'

# One-way transportation c-weights?
one_way = True

# Two-way transportation c-weights?
two_way = True

# Create straight lines?
straight_lines = True

# Use road network geometry output?
network_geometry = True

output_path = output_base + f'/scenario_shapefiles{trial}'

def create_dir_if_not_exists(output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        print(f"Folder '{output_path}' already exists.")
        
create_dir_if_not_exists(output_path)


if one_way == True:
    df = pd.read_csv(csv_path)

    beccs_scenarios = ['25', '50', '75', '90', '99']

    beccs_25 = df[df['scenario'] == '25']
    beccs_50 = df[df['scenario'] == '50']
    beccs_75 = df[df['scenario'] == '75']
    beccs_90 = df[df['scenario'] == '90']
    beccs_99 = df[df['scenario'] == '99']
    burial = df[df['scenario'] == 'all'] 
    
    
    for beccs in beccs_scenarios:
        for i in range(0, 172):
            beccs_data = df[df['scenario'] == beccs]
            beccs_index = beccs_data[beccs_data['index'] == i]
            
            burial_index = burial[burial['index'] == i]
            print(burial_index)
            burial_c = burial_index['cumulative_c_weight'].values[0]
            
            if beccs_index.empty:
                print(f'No BECCS for BECCS scenario {beccs}, index {i}: use burial')
                if beccs == '25':
                    beccs_25 = pd.concat([beccs_25, burial_index], ignore_index = True)
                if beccs == '50':
                    beccs_50 = pd.concat([beccs_50, burial_index], ignore_index = True)
                if beccs == '75':
                    beccs_75 = pd.concat([beccs_75, burial_index], ignore_index = True)
                if beccs == '90':
                    beccs_90 = pd.concat([beccs_90, burial_index], ignore_index = True)
                if beccs == '99':
                    beccs_99 = pd.concat([beccs_99, burial_index], ignore_index = True)
                    
            else:
                beccs_c = beccs_index['cumulative_c_weight'].values[0]
                if burial_c < beccs_c:
                    print(f'For BECCS scenario {beccs} index {i}, burial c_weight ({burial_c}) < beccs c_weight ({beccs_c})')
                    if beccs == '25':
                        beccs_25 = beccs_25[beccs_25['index'] != i]
                        beccs_25 = pd.concat([beccs_25, burial_index], ignore_index = True)
                    if beccs == '50':
                        beccs_50 = beccs_50[beccs_50['index'] != i]
                        beccs_50 = pd.concat([beccs_50, burial_index], ignore_index = True)
                    if beccs == '75':
                        beccs_75 = beccs_75[beccs_75['index'] != i]
                        beccs_75 = pd.concat([beccs_75, burial_index], ignore_index = True)
                    if beccs == '90':
                        beccs_90 = beccs_90[beccs_90['index'] != i]
                        beccs_90 = pd.concat([beccs_90, burial_index], ignore_index = True)
                    if beccs == '99':
                        beccs_99 = beccs_99[beccs_99['index'] != i]
                        beccs_99 = pd.concat([beccs_99, burial_index], ignore_index = True)
    
    if straight_lines == True:
        def make_line(row):
            return LineString([(row['start_lon'], row['start_lat']), (row['end_lon'], row['end_lat'])])
        
        beccs_25['geometry'] = beccs_25.apply(make_line, axis = 1)
        gdf_25 = gpd.GeoDataFrame(beccs_25, geometry='geometry', crs='EPSG:4326')
        save_25 = output_path + f'/beccs_25_scenario{trial}_straight_w1.shp'
        gdf_25.to_file(save_25)
        print('BECCS 25 straight lines saved')
        
        beccs_50['geometry'] = beccs_50.apply(make_line, axis = 1)
        gdf_50 = gpd.GeoDataFrame(beccs_50, geometry='geometry', crs='EPSG:4326')
        save_50 = output_path + f'/beccs_50_scenario{trial}_straight_w1.shp'
        gdf_50.to_file(save_50)
        print('BECCS 50 straight lines saved')
        
        beccs_75['geometry'] = beccs_75.apply(make_line, axis = 1)
        gdf_75 = gpd.GeoDataFrame(beccs_75, geometry='geometry', crs='EPSG:4326')
        save_75 = output_path + f'/beccs_75_scenario{trial}_straight_w1.shp'
        gdf_75.to_file(save_75)
        print('BECCS 75 straight lines saved')
        
        beccs_90['geometry'] = beccs_90.apply(make_line, axis = 1)
        gdf_90 = gpd.GeoDataFrame(beccs_90, geometry='geometry', crs='EPSG:4326')
        save_90 = output_path + f'/beccs_90_scenario{trial}_straight_w1.shp'
        gdf_90.to_file(save_90)
        print('BECCS 90 straight lines saved')
        
        beccs_99['geometry'] = beccs_99.apply(make_line, axis = 1)
        gdf_99 = gpd.GeoDataFrame(beccs_99, geometry='geometry', crs='EPSG:4326')
        save_99 = output_path + f'/beccs_99_scenario{trial}_straight_w1.shp'
        gdf_99.to_file(save_99)
        print('BECCS 99 straight lines saved')
        
        burial['geometry'] = burial.apply(make_line, axis = 1)
        gdf_burial = gpd.GeoDataFrame(burial, geometry='geometry', crs='EPSG:4326')
        save_burial = output_path + f'/burial_scenario{trial}_straight_w1.shp'
        gdf_burial.to_file(save_burial)
        print('Burial only straight lines saved')
        
    if network_geometry == True:
        def add_geometry(row):
            # row_i = str(row['index'])
            # type_i = str(row['type'])
            file_i = str(row['file'])
            file_f = file_i.replace('.graphml', '_path.shp')
            file_path = networks_base + f'/{file_f}'
            """
            if type_i == 'beccs':
                scenario_i = str(row['scenario'])
                file_path = networks_base + f'/osmnx_beccs_{scenario_i}_pts_network_{row_i}_path.shp'
            else:
                file_path = networks_base + f'/osmnx_raster_pts_network_{row_i}_path.shp'
            """
            gdf = gpd.read_file(file_path).to_crs(epsg=4326)
            return gdf.geometry[0]
        
        dfs = [beccs_25, beccs_50, beccs_75, beccs_90, beccs_99, burial]
        df_names = ['beccs_25', 'beccs_50', 'beccs_75', 'beccs_90', 'beccs_99', 'burial']
        
        for i in range(len(dfs)):
            df = dfs[i].copy()
            df_name = df_names[i]
            df['geometry'] = df.apply(add_geometry, axis = 1)
            gdf_new = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
            save_path = output_path + f'/{df_name}{trial}_scenario_network_w1.shp'
            gdf_new.to_file(save_path)
            print(f'{df_name}{trial} network lines saved')

if two_way == True:
    df = pd.read_csv(csv_path)

    beccs_scenarios = ['25', '50', '75', '90', '99']

    beccs_25 = df[df['scenario'] == '25']
    beccs_50 = df[df['scenario'] == '50']
    beccs_75 = df[df['scenario'] == '75']
    beccs_90 = df[df['scenario'] == '90']
    beccs_99 = df[df['scenario'] == '99']
    burial = df[df['scenario'] == 'all'] 
    
    for beccs in beccs_scenarios:
        for i in range(0, 172):
            beccs_data = df[df['scenario'] == beccs]
            beccs_index = beccs_data[beccs_data['index'] == i]
            
            burial_index = burial[burial['index'] == i]
            print(burial_index)
            burial_c = burial_index['w2_c_weight'].values[0]
            
            if beccs_index.empty:
                print(f'No BECCS for BECCS scenario {beccs}, index {i}: use burial')
                if beccs == '25':
                    beccs_25 = pd.concat([beccs_25, burial_index], ignore_index = True)
                if beccs == '50':
                    beccs_50 = pd.concat([beccs_50, burial_index], ignore_index = True)
                if beccs == '75':
                    beccs_75 = pd.concat([beccs_75, burial_index], ignore_index = True)
                if beccs == '90':
                    beccs_90 = pd.concat([beccs_90, burial_index], ignore_index = True)
                if beccs == '99':
                    beccs_99 = pd.concat([beccs_99, burial_index], ignore_index = True)
                    
            else:
                beccs_c = beccs_index['w2_c_weight'].values[0]
                if burial_c < beccs_c:
                    print(f'For BECCS scenario {beccs} index {i}, burial c_weight ({burial_c}) < beccs c_weight ({beccs_c})')
                    if beccs == '25':
                        beccs_25 = beccs_25[beccs_25['index'] != i]
                        beccs_25 = pd.concat([beccs_25, burial_index], ignore_index = True)
                    if beccs == '50':
                        beccs_50 = beccs_50[beccs_50['index'] != i]
                        beccs_50 = pd.concat([beccs_50, burial_index], ignore_index = True)
                    if beccs == '75':
                        beccs_75 = beccs_75[beccs_75['index'] != i]
                        beccs_75 = pd.concat([beccs_75, burial_index], ignore_index = True)
                    if beccs == '90':
                        beccs_90 = beccs_90[beccs_90['index'] != i]
                        beccs_90 = pd.concat([beccs_90, burial_index], ignore_index = True)
                    if beccs == '99':
                        beccs_99 = beccs_99[beccs_99['index'] != i]
                        beccs_99 = pd.concat([beccs_99, burial_index], ignore_index = True)
    
    if straight_lines == True:
        def make_line(row):
            return LineString([(row['start_lon'], row['start_lat']), (row['end_lon'], row['end_lat'])])
        
        beccs_25['geometry'] = beccs_25.apply(make_line, axis = 1)
        gdf_25 = gpd.GeoDataFrame(beccs_25, geometry='geometry', crs='EPSG:4326')
        save_25 = output_path + f'/beccs_25_scenario{trial}_straight_w2.shp'
        gdf_25.to_file(save_25)
        print('BECCS 25 straight lines saved')
        
        beccs_50['geometry'] = beccs_50.apply(make_line, axis = 1)
        gdf_50 = gpd.GeoDataFrame(beccs_50, geometry='geometry', crs='EPSG:4326')
        save_50 = output_path + f'/beccs_50_scenario{trial}_straight_w2.shp'
        gdf_50.to_file(save_50)
        print('BECCS 50 straight lines saved')
        
        beccs_75['geometry'] = beccs_75.apply(make_line, axis = 1)
        gdf_75 = gpd.GeoDataFrame(beccs_75, geometry='geometry', crs='EPSG:4326')
        save_75 = output_path + f'/beccs_75_scenario{trial}_straight_w2.shp'
        gdf_75.to_file(save_75)
        print('BECCS 75 straight lines saved')
        
        beccs_90['geometry'] = beccs_90.apply(make_line, axis = 1)
        gdf_90 = gpd.GeoDataFrame(beccs_90, geometry='geometry', crs='EPSG:4326')
        save_90 = output_path + f'/beccs_90_scenario{trial}_straight_w2.shp'
        gdf_90.to_file(save_90)
        print('BECCS 90 straight lines saved')
        
        beccs_99['geometry'] = beccs_99.apply(make_line, axis = 1)
        gdf_99 = gpd.GeoDataFrame(beccs_99, geometry='geometry', crs='EPSG:4326')
        save_99 = output_path + f'/beccs_99_scenario{trial}_straight_w2.shp'
        gdf_99.to_file(save_99)
        print('BECCS 99 straight lines saved')
        
        burial['geometry'] = burial.apply(make_line, axis = 1)
        gdf_burial = gpd.GeoDataFrame(burial, geometry='geometry', crs='EPSG:4326')
        save_burial = output_path + f'/burial_scenario{trial}_straight_w2.shp'
        gdf_burial.to_file(save_burial)
        print('Burial only straight lines saved')
        
    if network_geometry == True:
        def add_geometry(row):
            # row_i = str(row['index'])
            # type_i = str(row['type'])
            file_i = str(row['file'])
            file_f = file_i.replace('.graphml', '_path.shp')
            file_path = networks_base + f'/{file_f}'
            """
            if type_i == 'beccs':
                scenario_i = str(row['scenario'])
                file_path = networks_base + f'/osmnx_beccs_{scenario_i}_pts_network_{row_i}_path.shp'
            else:
                file_path = networks_base + f'/osmnx_raster_pts_network_{row_i}_path.shp'
            """
            gdf = gpd.read_file(file_path).to_crs(epsg=4326)
            return gdf.geometry[0]
        
        dfs = [beccs_25, beccs_50, beccs_75, beccs_90, beccs_99, burial]
        df_names = ['beccs_25', 'beccs_50', 'beccs_75', 'beccs_90', 'beccs_99', 'burial']
        
        for i in range(len(dfs)):
            df = dfs[i].copy()
            df_name = df_names[i]
            df['geometry'] = df.apply(add_geometry, axis = 1)
            gdf_new = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
            save_path = output_path + f'/{df_name}{trial}_scenario_network_w2.shp'
            gdf_new.to_file(save_path)
            print(f'{df_name}{trial} network lines saved')

