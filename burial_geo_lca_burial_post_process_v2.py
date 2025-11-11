#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 09:14:43 2025

@author: leahclayton
"""

import pandas as pd
import numpy as np
import rasterio
from rasterio.transform import rowcol
from rasterio.warp import transform

# csv file output from burial_geo_lca_analysis_v#.py scripts, list for sensitivity analyses
csv_files = ['/base-path/optimized_paths_results_lowDOCf.csv',
             '/base-path/optimized_paths_results_lowCH4ox.csv'
         ]

# corresponding burial C rasters for each csv file
c_rasters = ['/base-path/burial_lca_min0_md667_exc00045734_doz00099195_ox01_docf003_ch4ox075.tif',
             '/base-path/burial_geo_lca/burial_lca_min0_md667_exc00045734_doz00099195_ox01_docf0088_ch4ox01.tif'
             ]

# burial depth raster, final masked output from burial_geo_raster_calc_v#.py
depth_raster = '/base-path/req_soil_depth_95th_v35_aet05_1km_finalclip_mskd.tif'

# minimum burial depth thresholds for each file in the list
depth_thresholds = [0, 0]

# set beccs_end_pt c_weight
beccs_end_pt = 0.1765939

""" Column names in original output optimized_paths_results.csv files:
    'file'
    'start_lat'
    'start_lon'
    'end_lat'
    'end_lon'
    'path_length_km'
    'cumulative_c_weight'
"""

for i in range(len(csv_files)):
    csv_file = csv_files[i]
    print(csv_file)
    df = pd.read_csv(csv_file)
    
    # extract index number and add as new column
    df['index'] = df.iloc[:, 0].str.extract(r'_(\d+)\.graphml')
    df['index'] = df['index'].astype(int)
    
    # extract type of file  
    df['type'] = np.where(df['file'].str.contains('raster', case=False, na=False),
                          'burial',
                          'beccs')
    
    # set BECCS scenario
    df['scenario'] = np.where(df['file'].str.contains('beccs', case=False, na=False),
                              df.iloc[:, 0].str.extract(r'beccs_(\d+)\_pts')[0],
                              'all')
    
    # extract end pt lat/lon for burial_depth and end_pt_c_weight
    lon, lat = df['end_lon'].values, df['end_lat'].values
    
    with rasterio.open(depth_raster) as src:
        x, y = transform('EPSG:4326', src.crs, lon.tolist(), lat.tolist())
        coords = list(zip(x,y))
        depth_vals = [val[0] if val else np.nan for val in src.sample(coords)]
        df['burial_depth'] = depth_vals
        depth_threshold = float(depth_thresholds[i])
        df.loc[df['burial_depth'] < depth_threshold, 'burial_depth'] = depth_threshold
        df['burial_depth'] = np.where(df['type'].str.contains('burial', case=False, na=False),
                                      df['burial_depth'].values,
                                      -999)
    
    # w1_c_eff
    df['w1_c_eff'] = 1 - df['cumulative_c_weight']
    
    # extract end_pt_c_weight
    c_raster = c_rasters[i]
    with rasterio.open(c_raster) as src:
        c_vals = [val[0] if val else np.nan for val in src.sample(coords)]
        print(c_vals)
        df['end_pt_c_weight'] = c_vals
        df['end_pt_c_weight'] = np.where(df['type'].str.contains('burial', case=False, na=False),
                                         df.iloc[:, 12],
                                         beccs_end_pt)
    
    # w1_transport_c
    df['w1_transport_c'] = df['cumulative_c_weight'].values - df['end_pt_c_weight'].values
    
    # w2_path_length_km
    df['w2_path_length_km'] = 2 * df['path_length_km']
    
    # w2_transport_c
    df['w2_transport_c'] = 2 * df['w1_transport_c']
    
    # w2_c_weight
    df['w2_c_weight'] = df['w2_transport_c'] + df['end_pt_c_weight']
    
    # w2_c_eff
    df['w2_c_eff'] = 1 - df['w2_c_weight']
    
    output_file = csv_file.replace('.csv', '_post_process.csv')
    
    df.to_csv(output_file, index=False)
    
    
    
    
    
