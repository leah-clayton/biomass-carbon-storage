#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 25 19:00:56 2025

@author: leahclayton
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import Point
import rasterio
from rasterio.plot import reshape_as_image
import numpy as np


### INSTRUCTIONS FOR SENSITIVITY ANALYSIS ###
# Where {sens_code} is equivalent to the sensitivity analysis code
# For base_shp, add _{sens_code} to the end of the file path
# For sens_type, specify '_{sens_code}'

# region shapefile
west_path = '/base-path/region.shp'
# scenario shapefile directory path
base_shp = '/base-path/burial_geo_lca/scenario_shapefiles'
# masked required soil depth raster
raster_path = '/base-path/req_soil_depth_95th_v35_aet05_1km_finalclip_mskd.tif'
# optional: sensitivity analysis
sens_type = '_lowCH4ox'

# specify output file type; 'svg' and 'png' coded
output_file = 'svg'

# colors for beccs and burial scenarios
beccs_color = 'darkslateblue'
burial_color = 'indianred'

# NOT CURRENTLY IN USE; edge color for the start/end nodes
beccs_edge = 'maroon'
burial_edge = 'midnightblue'

# select straight lines or network lines
line_type = 'network'

# select one way ('w1') or two way ('w2')
ways = 'w2'

# western US shapefile
outline = gpd.read_file(west_path)
target_crs = outline.crs

#open raster
with rasterio.open(raster_path) as src:
    raster_data = src.read(1)  # Read first band
    raster_bounds = src.bounds
    raster_transform = src.transform
    raster_crs = src.crs
    raster_extent = [raster_bounds.left, raster_bounds.right,
                     raster_bounds.bottom, raster_bounds.top]
# remove no data
raster_data = np.where(raster_data == src.nodata, np.nan, raster_data)
raster_data = np.where(raster_data <= 0, np.nan, raster_data)

if raster_crs != target_crs:
    from rasterio.warp import transform_bounds
    raster_extent = transform_bounds(raster_crs, target_crs, *raster_extent)

# Scenario filenames
scenarios = ['burial', 'beccs_25', 'beccs_50', 'beccs_75', 'beccs_90', 'beccs_99']

if ways == 'w2':
    scenario_files = [f'{base_shp}/{i}{sens_type}_scenario_{line_type}_{ways}.shp' for i in scenarios]

else:
    scenarios = ['burial', 'beccs_25', 'beccs_50', 'beccs_75', 'beccs_90', 'beccs_99']
    scenario_files = [f'{base_shp}/{i}_scenario{sens_type}_{line_type}_{ways}.shp' for i in scenarios]
    

# Set up the 2x3 subplot layout
fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(8, 7))
axes = axes.flatten()  # Flatten to make indexing easier

for i, scenario_file in enumerate(scenario_files):
    ax = axes[i]
    
    log_norm = mcolors.LogNorm(vmin=1, vmax=6.67)

    raster_img = ax.imshow(
        raster_data,
        cmap='gray',
        norm=log_norm,
        extent=raster_extent,
        origin='upper',
        alpha=0.5,
        zorder=0
    )
    
    # Load the scenario shapefile
    scenario = gpd.read_file(scenario_file)
    
    if scenario.crs != target_crs:
        scenario = scenario.to_crs(target_crs)

    # Plot the outline in black
    outline.plot(ax=ax, color='none', edgecolor='black', linewidth=0.5)

    beccs_type = scenario[scenario['type'] == 'beccs']
    burial_type = scenario[scenario['type'] == 'burial']
    
    if not beccs_type.empty:
        beccs_type.plot(ax=ax, color=beccs_color, linewidth=1)

    if not burial_type.empty:
        burial_type.plot(ax=ax, color=burial_color, linewidth=1)
    
    for t in ['beccs', 'burial']:
        subset = scenario[scenario['type'] == t]
        if not subset.empty:
            start_points = gpd.GeoDataFrame(
                        subset,
                        geometry=gpd.points_from_xy(subset['start_lon'], subset['start_lat']),
                        crs="EPSG:4326"
                    ).to_crs(target_crs)
        
            end_points = gpd.GeoDataFrame(
                        subset,
                        geometry=gpd.points_from_xy(subset['end_lon'], subset['end_lat']),
                        crs="EPSG:4326"
                    ).to_crs(target_crs)
        
            
            if t == 'beccs':
                color=beccs_color
                color_edge = beccs_edge
                marker_type = 'D'
                size_type = 9
                
            else:
                color=burial_color
                color_edge = burial_edge
                marker_type = 's'
                size_type = 9
                
            ax.scatter(start_points.geometry.x, start_points.geometry.y,
                       facecolors=color, edgecolors=color, marker='o', 
                       s=5, linewidth=1, zorder=2)
            ax.scatter(end_points.geometry.x, end_points.geometry.y,
                       facecolors='white', edgecolors=color, marker=marker_type,
                       s=size_type, linewidth=1, zorder=2)
                
            #start_points.plot(ax=ax, color=color, markersize=5, marker='o', label='Start')
            #end_points.plot(ax=ax, color=color, markersize=5, marker='^', label='End')
            


    # Set a title for each subplot
    #ax.set_title("Scenario x")

    ax.set_axis_off()

#fig.colorbar(raster_img, cax=cbar_ax, label='Raster value (log scale)')

plt.tight_layout()
if output_file == 'png':
    plt.savefig(f'{base_shp}/scenarios{sens_type}_{line_type}_{ways}.png', dpi=300)
if output_file == 'svg':
    plt.savefig(f'{base_shp}/scenarios{sens_type}_{line_type}_{ways}.svg', transparent=True)
plt.show()
