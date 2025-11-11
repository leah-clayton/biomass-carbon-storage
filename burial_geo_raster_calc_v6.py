#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 25 15:43:35 2025

@author: leahclayton
"""

import rasterio
from rasterio.mask import mask
import numpy as np
import geopandas as gpd

"""
User inputs -------------------------------------------------------------------
"""
#%% set file paths

base_path = '/home/lkc33/palmer_scratch/burial_lca'

# minimum required burial depth (raster, units: m)
bur_dep_path = base_path + '/input_files/req_soil_depth_95th_v35_aet05_1km_finalclip.tif'

# protected lands mask (vector)
protected_lands_path = base_path + '/input_files/west_us_combined_gap_1_2/west_us_combined_gap_1_2.shp'

# soil organic matter (raster, units: %)
soil_om_path = base_path + '/input_files/gnatsgo_om_r_lcc_1km_finalclip.tif'

# soil bulk density (raster, units: g/cm3 = MT/m3)
soil_bd_path = base_path + '/input_files/boiko_bulk_density_lcc_1km_finalclip.tif'

#%%
# minimum required burial depth masked for protected lands output location
mskd_save_path = base_path + '/input_files/req_soil_depth_95th_v35_aet05_1km_finalclip_mskd.tif'

#%% set parameters
# set the minimum depth threshold?
min_dep_threshold = True

# (units: m; use 0 if not specifying)
# pixels with burial depth less than this threshold will be set to this threshold
min_depth = 0

# set the maximum depth threshold (units: m)
max_depth = 6.67

# set the forestry process emissions factor
fp_em = 0.0065939

# set the excavator and dozer emissions factor (units: 1 - carbon efficiency per m)
excavator = 0.0045734
dozer = 0.0099195

# set soil carbon oxidation rate (units: proportion)
ox_rate = 0.1
#ox_rates = [0.0365, 0.1, 0.3]

# set DOCf
docf = 0.088
#docfs = [0.03, 0.088, 0.183]

# set proportion of methane oxidized in the cover
ch4_ox = 0.75
#ch4_oxs = [0.1, 0.55, 0.75, 0.9]

# no data value for output file (default: -999)(input agnostic)
nodata_out = -999

"""
Start script, do not edit below this line -------------------------------------
"""

#%% process total emissions

# open protected lands shapefile
gdf = gpd.read_file(protected_lands_path)

# import minimum required burial depth
with rasterio.open(bur_dep_path) as src:
    bur_dep_i = src.read(1)
    nodata_val = src.nodata
    meta = src.meta.copy()
    crs = src.crs
    
    # use an inverse mask to remove protected lands
    gdf = gdf.to_crs(crs)
    mask_geos = [geom for geom in gdf.geometry]
    bur_dep_ii, bur_dep_ii_transform = mask(src, mask_geos, invert=True)
    
    bur_dep_ii_meta = meta
    bur_dep_ii_meta.update({'driver': 'GTiff',
                            'height': bur_dep_ii.shape[1],
                            'width': bur_dep_ii.shape[2],
                            'transform': bur_dep_ii_transform})

# save masked version
with rasterio.open(mskd_save_path, 'w', **bur_dep_ii_meta) as dest:
    dest.write(bur_dep_ii)

# open masked version for processing        
with rasterio.open(mskd_save_path) as src:
    bur_dep_iii = src.read(1)
    nodata_val = src.nodata
    meta = src.meta.copy()
    crs = src.crs

bur_dep_iii[bur_dep_iii == 0] = np.nan
bur_dep_iii[bur_dep_iii == nodata_val] = np.nan

if min_dep_threshold == True:    
    # use minimum burial depth threshold
    bur_dep_iv = np.where(bur_dep_iii < min_depth, min_depth, bur_dep_iii)
else:
    bur_dep_iv = bur_dep_iii

# mask burial depth below max depth threshold    
bur_dep = np.where(bur_dep_iv < max_depth, bur_dep_iv, np.nan)

# convert -999 to nan for calculations
bur_dep[bur_dep == nodata_val] = np.nan
bur_dep[bur_dep == 0] = np.nan

# calculate equipment emissions
equip_em = (bur_dep * excavator) + (bur_dep * dozer)

# import soil organic matter
with rasterio.open(soil_om_path) as src:
    soil_om_i = src.read(1)
    nodata_val = src.nodata
    
# convert -999 to nan for calculations
soil_om_i[soil_om_i == nodata_val] = np.nan
soil_om = soil_om_i

# convert soil organic matter to soil percent carbon
perC = soil_om * 1.724

# import soil bulk density
with rasterio.open(soil_bd_path) as src:
    soil_bd_i = src.read(1)
    nodata_val = src.nodata
    
# convert -999 to nan for calculations
soil_bd_i[soil_bd_i == nodata_val] = np.nan
soil_bd = soil_bd_i

# calculate soil emissions
soil_em = bur_dep * perC/100 * soil_bd * ox_rate * 4.4944

# calculate methane emissions
# ch4_em = 0.044 + (0.044 * ch4_ox) + (0.448 * (1 - ch4_ox))
ch4_em = (0.5 * docf) + (0.5 * docf * ch4_ox) + ((0.5 * docf * (16/12) * 28) / 3.67) * (1-ch4_ox)

# calculate final total emissions
tot_em = fp_em + equip_em + soil_em + ch4_em

print(tot_em)

#%% export result
# replace np.nan with nodata_out value and update the metadata
tot_em[np.isnan(tot_em)] = nodata_out
meta.update(nodata=nodata_out, dtype=rasterio.float32, crs=crs)

# set new file path
md_str = str(max_depth).replace('.', '')
exc_str = str(excavator).replace('.', '')
doz_str = str(dozer).replace('.', '')
ox_str = str(ox_rate).replace('.', '')
docf_str = str(docf).replace('.', '')
ch4_str = str(ch4_ox).replace('.', '')

if min_dep_threshold == True:
    min_dep_str = str(min_depth)
    output_path = base_path + f'/burial_lca_min{min_dep_str}_md{md_str}_exc{exc_str}_doz{doz_str}_ox{ox_str}_docf{docf_str}_ch4ox{ch4_str}.tif'
else:
    output_path = base_path + f'/burial_lca_md{md_str}_exc{exc_str}_doz{doz_str}_ox{ox_str}_docf{docf_str}_ch4ox{ch4_str}.tif'

# write new file
with rasterio.open(output_path, "w", **meta) as dst:
    dst.write(tot_em.astype(rasterio.float32), 1)