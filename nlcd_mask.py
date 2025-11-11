#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  7 16:18:51 2024

@author: leahclayton
"""

## output files are 4 GB each where input are 1 GB -- check for this error

import rasterio
from rasterio.mask import mask
import numpy as np
import geopandas as gpd

base_path = '/home/lkc33/palmer_scratch'
shp_path = '/home/lkc33/project/western_us_shp_wgs84/Western_States_Merge_4_WGS84.shp'

# reclassification rules
reclass_map = {11: 1, # open water
               12: 1, # perennial snow/ice
               21: 0, # developed, open space
               22: 0, # developed, low intensity
               23: 1, # developed, medium intensity
               24: 1, # developed, high intensity
               31: 0, # barren land (rock/sand/clay)
               41: 0, # deciduous forest
               42: 0, # evergreen forest
               43: 0, # mixed forest
               52: 0, # shrub/scrub
               71: 0, # grassland/herbaceous
               81: 1, # pasture/hay
               82: 1, # cultivated crops
               90: 1, # woody wetlands
               95: 1, # emergent herbaceous wetlands
               } 

clip_shp = gpd.read_file(shp_path)

# create file path structure
for year in range(2001, 2021):
    input_raster = base_path + f'/annual_nlcd/Annual_NLCD_LndCov_{year}_CU_C1V0.tif'
    output_raster = base_path + f'/annual_nlcd/nlcd_west_mask_{year}.tif'

    # Open the raster
    with rasterio.open(input_raster) as src:
        # clip to the shapefile
        raster_crs = src.crs
        reproj_shp = clip_shp.to_crs(raster_crs)
        clipped_data, clipped_transform = mask(src, shapes=reproj_shp.geometry, crop=True)
        
        # reclassify using the defined rules
        for old_value, new_value in reclass_map.items():
            clipped_data[clipped_data == old_value] = new_value
        
        nodata_value = src.nodata
        clipped_data[src == nodata_value] = nodata_value
        
        # copy metadata
        meta = src.meta.copy()
        meta.update({
            'transform': clipped_transform,
            'height': clipped_data.shape[1],
            'width': clipped_data.shape[2],
            'dtype': clipped_data.dtype
        })
    
    # write to a new file
    with rasterio.open(output_raster, "w", **meta) as dst:
        dst.write(clipped_data)
    
    print(f'{year} reclassified clipped raster saved')
    
rasters = []

for year in range(2001, 2021):
    raster_file = base_path + f'/annual_nlcd/nlcd_west_mask_{year}.tif'

    with rasterio.open(raster_file) as src:
        rasters.append(src.read(1))  # Assumes single-band rasters

# Stack rasters into a 3D NumPy array (shape: height x width x number of rasters)
stacked_rasters = np.stack(rasters, axis=2)

# Apply majority rule
final_raster = np.all(stacked_rasters == 1, axis=2).astype(int)  # Convert boolean to integer

# Copy metadata from the first raster
with rasterio.open(raster_file) as src:
    meta = src.meta.copy()

# Update metadata for the output raster
meta.update({
    'dtype': 'int8',
    'count': 1  # Only one band in the final raster
})

final_output = base_path + '/annual_nlcd/nlcd_west_mask_2001_2020.tif'

# write to a new file
with rasterio.open(final_output, "w", **meta) as dst:
    dst.write(final_raster, 1)

print('Final combined raster saved')
