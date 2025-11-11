#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  9 10:16:22 2025

@author: leahclayton
"""

import os
import osmnx as ox
import networkx as nx
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from pyproj import CRS, Transformer
import glob

"""
User inputs ******************************************************************
"""
''' ------------------------- Set File Paths ------------------------------'''

## THIS VERSION RASTER (BURIAL) ONLY, use v6 for BECCS inclusion ##
trials = ['_lowDOCf', '_lowCH4ox']

# path to networks
network_path = '/base-path/burial_lca/networks'

# set working directory
wd = '/base-path/burial_lca'
os.chdir(wd)

"""
Start script ******************************************************************
"""


def process_graph(file_path, out_shapefile_dir):    
    G = ox.load_graphml(file_path)

    # set projection (Daymet LCC) and transformer (to WGS84)
    project_crs = '+proj=lcc +lat_1=25 +lat_2=60 +lat_0=42.5 +lon_0=-100 +datum=NAD83 +units=km +x_0=0 +y_0=0'
    pyproj_crs =CRS.from_proj4(project_crs)
    transformer = Transformer.from_crs(pyproj_crs, 'EPSG:4326', always_xy=True)

    # find start and end nodes
    start_node = next((n for n, d in G.nodes(data=True) if d.get('loc') == 'start'), None)
    if not start_node:
        print('No start node identified')
    
    end_nodes = [n for n, d in G.nodes(data=True) if d.get('loc') == 'end']
    if not end_nodes:
        print('No end nodes identified')
        
    if not start_node or not end_nodes:
        return None
    
    for u, v, data in G.edges(data=True):
        try:
            data['c_weight'] = float(data['c_weight'])
        except (ValueError, TypeError):
            print(f"Invalid c_weight on edge ({u}, {v}): {data.get('c_weight')}")
            data['c_weight'] = 1e9
    
    # run single source Dijkstra
    try:
        lengths, paths = nx.single_source_dijkstra(G, start_node, weight='c_weight')
    except Exception as e:
        print(f'Error in Dijkstra on {file_path}: {e}')
        return None

    # select best end node
    reachable = [n for n in end_nodes if n in lengths]
    if not reachable:
        return None
    best_end = min(reachable, key=lambda n: (lengths[n], len(paths[n])))
    best_path = paths[best_end]
    best_cost = lengths[best_end]

    # get start and end point coords, convert to WGS84
    def get_coords(nid):
        return G.nodes[nid]['x'], G.nodes[nid]['y']
    x_start, y_start = get_coords(start_node)
    x_end, y_end = get_coords(best_end)
    lon_start, lat_start = transformer.transform(x_start, y_start)
    lon_end, lat_end = transformer.transform(x_end, y_end)
    print('Start coordinates: (', lon_start, ',', lat_start, ')')

    # build path geometry and total length
    line_geoms = []
    total_length = 0
    for u, v in zip(best_path[:-1], best_path[1:]):
        edge_data = G.get_edge_data(u, v) or G.get_edge_data(v, u)
        if isinstance(edge_data, dict) and 0 in edge_data:
            edge_data = edge_data[0]
        if not edge_data:
            continue

        geom = edge_data.get('geometry')
        if isinstance(geom, str):
            try:
                geom = eval(geom)
            except:
                geom = None
        if geom and not isinstance(geom, LineString):
            geom = LineString(geom)
        if not geom:
            geom = LineString([(G.nodes[u]['x'], G.nodes[u]['y']), (G.nodes[v]['x'], G.nodes[v]['y'])])

        line_geoms.append(geom)
        total_length += edge_data.get('length', geom.length)

    # save shapefile
    if line_geoms:
        merged = LineString([pt for line in line_geoms for pt in line.coords])
        gdf = gpd.GeoDataFrame([{
            'file': Path(file_path).name,
            'start': start_node,
            'end': best_end,
            'geometry': merged
        }], crs=pyproj_crs)

        out_path = Path(out_shapefile_dir) / f'{Path(file_path).stem}_path.shp'
        gdf.to_file(out_path)
        
    # return summary row
    return {
        'file': Path(file_path).name,
        'start_lat': float(lat_start),
        'start_lon': float(lon_start),
        'end_lat': float(lat_end),
        'end_lon': float(lon_end),
        'path_length_km': float(total_length)/1000,
        'cumulative_c_weight': float(best_cost)
    }

# multiprocessing wrapper
def safe_process(file_path):
    shapefile_out = Path('shapefiles')
    shapefile_out.mkdir(parents=True, exist_ok=True)
    try:
        return process_graph(file_path, shapefile_out)
    except Exception as e:
        print(f'Error processing {file_path}: {e}')
        return None

def main():
    for trial in trials:
    
        graph_dir = network_path
            
        files = sorted(glob.glob(f'{graph_dir}/osmnx_raster_pts_network{trial}*.graphml'))
    
        print(f'Found {len(files)} network files.')
            
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(safe_process, files))
    
        # write CSV summary
        csv_output = wd + f'/optimized_paths_results{trial}.csv'
        results = [r for r in results if r is not None]
        pd.DataFrame(results).to_csv(csv_output, index=False)
        print('CSV and shapefiles written.')

if __name__ == '__main__':
    main()

