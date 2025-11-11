#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  6 11:43:04 2025

@author: leahclayton
"""

import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import pyproj
from scipy.stats import kurtosis
import pandas as pd
import geopandas as gpd

fig, axes = plt.subplots(4, 5, figsize = (10,9), 
                         layout='constrained', sharex=True, sharey=True)

# paths to the NetCDF files (don't include / at the end)
base_path = '/home/lkc33/palmer_scratch'

# shapefile path
shp_path = '/home/lkc33/project/western_states_tight_lcc/western_states_tight_lcc.shp'
# shp_path = '/home/lkc33/project/western_us_shp_lcc/Western_States_Merge_4_LCC.shp'

# specify the type of sensitivity analysis (str) 
# Options currently coded for: 'high_rdd', 'low_rdd', 'no_snow'
sens_types = ['avg_rdd', 'low_rdd', 'high_rdd', 'no_snow']
row_labels = ['Required Water Storage (mm)', '% Difference low_rdd',
              '% Difference high_rdd', '% Difference no_snow']

#row-wise limits for the color bars
vmins = [50, -1, -1, -100]
vmaxs = [77000, 1, 1, 100]

#%%


# for AET correction (boolean)
aet_correct = True

# specify AET correction factor (float; units of mm d-1)
aet_factor = 0.5

# model version number (string; check file name)
vers = '35'

# list order of statistic rasters to graph
# options: '95th', 'mean', 'stdev', 'coevar', 'max', 'med' (median)
stats = ['mean', 'stdev', 'med', '95th', 'max']

# Graph labeling
plot_labels = ['(a)', '(b)', '(c)', '(d)', '(e)']
# x_labels order corresponds to stats order
x_labels = ['Mean', 'Standard Deviation', 
            'Median', '95th Percentile', 'Maximum']

# open shapefile
gdf_i = gpd.read_file(shp_path)

target_crs = pyproj.CRS.from_string(
    '+proj=lcc +lat_1=25 +lat_2=60 +lat_0=42.5 +lon_0=-100 +x_0=0 +y_0=0 '
    '+a=6378137.0 +b=6356752.314140 +units=km +no_defs'
)

#gdf = gdf_i.to_crs(target_crs.to_wkt())

input_loc = base_path + f'/daily_wb_results_2001_2020_v{vers}'

all_paths = {}

for sens_type in sens_types:
    input_files =[]
    for stat in stats:
        if aet_correct == True:
            aet_num = str(aet_factor)
            aet_str = aet_num.replace('.','')
            
        if sens_type == 'avg_rdd':
            if aet_correct == True:
                input_path = input_loc + f'/req_storage_{stat}_2001_2020_v{vers}_aet{aet_str}.tif'
            else:
                input_path = input_loc + f'/req_storage_{stat}_2001_2020_v{vers}.tif'
        else:
            sens_dir = input_loc + f'/sens_analysis/{sens_type}'
            if aet_correct == True:
                input_path = sens_dir + f'/req_storage_{stat}_2001_2020_v{vers}_{sens_type}_aet{aet_str}.tif'
            else:
                input_path = sens_dir + f'/req_storage_{stat}_2001_2020_v{vers}_{sens_type}.tif'
        input_files.append(input_path)
    all_paths[sens_type] = input_files

#%% Base condition (average rdd)
file_paths = all_paths[sens_types[0]]
paths_0 = dict(zip(stats, file_paths))

data_0 = {}

for stat, file_path in paths_0.items():
    with rasterio.open(file_path) as src:
        data_i = src.read(1)
        data_i[data_i == 0] = np.nan
        data_0[stat] = data_i
        raster_crs = src.crs
        raster_bounds = src.bounds

gdf = gdf_i.to_crs(raster_crs)

print("Shapefile bounds:", gdf.total_bounds)
print("Raster bounds:", raster_bounds)

print("Shapefile CRS:", gdf.crs)
print("Raster CRS:", raster_crs)
        
#%% Low RDD
file_paths = all_paths[sens_types[1]]
paths_1 = dict(zip(stats, file_paths))

data_1 = {}

for stat, file_path in paths_1.items():
    with rasterio.open(file_path) as src:
        data_i = src.read(1)
        data_i[data_i == 0] = np.nan
        data_1[stat] = data_i
        
change_1 = []
        
for n in range(5):
    initial = data_0[stats[n]]
    final = data_1[stats[n]]
    per_change = (final - initial) / initial * 100
    change_1.append(per_change)
    
#%% High RDD
file_paths = all_paths[sens_types[2]]
paths_2 = dict(zip(stats, file_paths))

data_2 = {}

for stat, file_path in paths_2.items():
    with rasterio.open(file_path) as src:
        data_i = src.read(1)
        data_i[data_i == 0] = np.nan
        data_2[stat] = data_i
        
change_2 = []
        
for n in range(5):
    initial = data_0[stats[n]]
    final = data_2[stats[n]]
    per_change = (final - initial) / initial * 100
    change_2.append(per_change)
    
#%% No snow
file_paths = all_paths[sens_types[3]]
paths_3 = dict(zip(stats, file_paths))

data_3 = {}

for stat, file_path in paths_3.items():
    with rasterio.open(file_path) as src:
        data_i = src.read(1)
        data_i[data_i == 0] = np.nan
        data_3[stat] = data_i
        
change_3 = []
        
for n in range(5):
    initial = data_0[stats[n]]
    final = data_3[stats[n]]
    per_change = (final - initial) / initial * 100
    change_3.append(per_change)
        
#%%
cbar_axes = []

#fig.subplots_adjust(right=0.85)

for row in range(4):
    for col in range(5):
        ax = axes[row, col]
        if row == 0:
            pcm = ax.pcolormesh(np.flipud(data_0[stats[col]]), cmap='turbo_r', 
                                norm=LogNorm(vmin=vmins[row],vmax=vmaxs[row]), 
                                shading='auto')
            array_0 = data_0[stats[col]]
            flat_0 = array_0.flatten()
            flat_0 = flat_0[~np.isnan(flat_0)]
            max_0 = max(flat_0)
            min_0 = min(flat_0)
            mean_0 = sum(flat_0)/len(flat_0)
            p95_0 = np.percentile(flat_0, 95)
            p05_0 = np.percentile(flat_0, 5)
            print(f'\n{row_labels[row]} {x_labels[col]} max:', max_0)
            print(f'\n{row_labels[row]} {x_labels[col]} min:', min_0)
            print(f'\n{row_labels[row]} {x_labels[col]} mean:', mean_0)
            print(f'\n{row_labels[row]} {x_labels[col]} 95th perc:', p95_0)
            print(f'\n{row_labels[row]} {x_labels[col]} 5th perc:', p05_0)
        if row == 1:
            pcm = ax.pcolormesh(np.flipud(change_1[col]), vmin=vmins[row], vmax=vmaxs[row], 
                                cmap='seismic_r', shading='auto')
            array_1 = change_1[col]
            flat_1 = array_1.flatten()
            flat_1 = flat_1[~np.isnan(flat_1)]
            max_1 = max(flat_1)
            min_1 = min(flat_1)
            mean_1 = sum(flat_1)/len(flat_1)
            p95_1 = np.percentile(flat_1, 95)
            p05_1 = np.percentile(flat_1, 5)
            print(f'\n{row_labels[row]} {x_labels[col]} max:', max_1)
            print(f'\n{row_labels[row]} {x_labels[col]} min:', min_1)
            print(f'\n{row_labels[row]} {x_labels[col]} mean:', mean_1)
            print(f'\n{row_labels[row]} {x_labels[col]} 95th perc:', p95_1)
            print(f'\n{row_labels[row]} {x_labels[col]} 5th perc:', p05_1)
        if row == 2:
            pcm = ax.pcolormesh(np.flipud(change_2[col]), vmin=vmins[row], vmax=vmaxs[row], 
                                cmap='seismic_r', shading='auto')
            array_2 = change_2[col]
            flat_2 = array_2.flatten()
            flat_2 = flat_2[~np.isnan(flat_2)]
            max_2 = max(flat_2)
            min_2 = min(flat_2)
            mean_2 = sum(flat_2)/len(flat_2)
            p95_2 = np.percentile(flat_2, 95)
            p05_2 = np.percentile(flat_2, 5)
            print(f'\n{row_labels[row]} {x_labels[col]} max:', max_2)
            print(f'\n{row_labels[row]} {x_labels[col]} min:', min_2)
            print(f'\n{row_labels[row]} {x_labels[col]} mean:', mean_2)
            print(f'\n{row_labels[row]} {x_labels[col]} 95th perc:', p95_2)
            print(f'\n{row_labels[row]} {x_labels[col]} 5th perc:', p05_2)
        if row == 3:
            pcm = ax.pcolormesh(np.flipud(change_3[col]), vmin=vmins[row], vmax=vmaxs[row],
                                cmap='PiYG', shading='auto')
            array_3 = change_3[col]
            flat_3 = array_3.flatten()
            flat_3 = flat_3[~np.isnan(flat_3)]
            max_3 = max(flat_3)
            min_3 = min(flat_3)
            mean_3 = sum(flat_3)/len(flat_3)
            p95_3 = np.percentile(flat_3, 95)
            p05_3 = np.percentile(flat_3, 5)
            print(f'\n{row_labels[row]} {x_labels[col]} max:', max_3)
            print(f'\n{row_labels[row]} {x_labels[col]} min:', min_3)
            print(f'\n{row_labels[row]} {x_labels[col]} mean:', mean_3)
            print(f'\n{row_labels[row]} {x_labels[col]} 95th perc:', p95_3)
            print(f'\n{row_labels[row]} {x_labels[col]} 5th perc:', p05_3)
        ax.set_aspect('equal')  # Ensure square cells
        ax.set_xticks([])
        ax.set_yticks([])
        """
        if ax == axes[3, 0]:
            ax.set_xticklabels()
            ax.set_yticklabels()
            """
        
        #gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=0.5)

    # Add a color bar for each row
    """
    cbar = fig.colorbar(pcm, ax=axes[row, :], orientation='vertical', fraction=0.05, pad=0.1)
    cbar.set_label(f'{row_labels[row]}')
    """
    
    #cbar_ax = fig.add_axes([0.87, 0.76 - row * 0.21, 0.02, 0.18])
    #cbar = fig.colorbar(pcm, cax=cbar_ax, orientation='vertical')
    cbar = fig.colorbar(pcm, orientation='vertical')
    cbar.set_label(f'{row_labels[row]}')
   # cbar_axes.append(cbar_ax)

# Show the plot
save_path = base_path + f'/high_res_v{vers}_map_analysis_high_res.png'
plt.savefig(save_path, dpi=300)

plt.show()