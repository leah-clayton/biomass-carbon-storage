#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 22 14:21:56 2025

@author: leahclayton
"""

import rasterio
from rasterio.mask import mask
import numpy as np
import geopandas as gpd
import pandas as pd
from scipy.stats import mode
from scipy.stats import kurtosis
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

"""
User inputs -------------------------------------------------------------------
"""
#%% colors
ox_color = 'royalblue'
docf_color = 'midnightblue'
ch4ox_color = 'darkmagenta'

#%% output file type ('png' or 'svg')
out_type = 'svg'

#%% set file paths

base_path = '/home/lkc33/palmer_scratch/burial_lca'

# output csv file for dataframe
output_file = base_path + '/burial_geo_lca_raster_sens_analysis.csv'

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
#ox_rate = 0.1
base_ox_rate = 0.1
#ox_rates = [0.0365, 0.1, 0.3]
# ten values generated with np.linspace(min, max, 10)
ox_rates = np.linspace(0.0365, 0.3, 10).tolist()

# set DOCf
#docf = 0.088
base_docf = 0.088
#docfs = [0.03, 0.088, 0.183]
docfs = np.linspace(0.03, 0.183, 10).tolist()

# set proportion of methane oxidized in the cover
#ch4_ox = 0.75
base_ch4ox = 0.75
#ch4_oxs = [0.1, 0.55, 0.75, 0.9]
ch4oxs = np.linspace(0.1, 0.9, 10).tolist()

# no data value for output file (default: -999)(input agnostic)
nodata_out = -999

"""
Start script, do not edit below this line -------------------------------------
"""

#%% process total emissions

sens_types = ['ox_rate', 'docf', 'ch4ox']

# generate list of file paths
ox_paths = []
docf_paths = []
ch4ox_paths = []

for sens_type in sens_types:
    if sens_type == 'ox_rate':
        print('ox_rate sensitivity analysis starting')
        docf = base_docf
        ch4_ox = base_ch4ox
        for ox_rate in ox_rates:
            md_str = str(max_depth).replace('.', '')
            exc_str = str(excavator).replace('.', '')
            doz_str = str(dozer).replace('.', '')
            ox_str = str(ox_rate).replace('.', '')
            docf_str = str(docf).replace('.', '')
            ch4_str = str(ch4_ox).replace('.', '')
            min_dep_str = str(min_depth)
            path = base_path + f'/raster_sens_analysis/burial_lca_min{min_dep_str}_md{md_str}_exc{exc_str}_doz{doz_str}_ox{ox_str}_docf{docf_str}_ch4ox{ch4_str}.tif'
            
            ox_paths.append(path)
    if sens_type == 'docf':
         print('docf sensitivity analysis starting')
         ox_rate = base_ox_rate
         ch4_ox = base_ch4ox
         for docf in docfs:       
            md_str = str(max_depth).replace('.', '')
            exc_str = str(excavator).replace('.', '')
            doz_str = str(dozer).replace('.', '')
            ox_str = str(ox_rate).replace('.', '')
            docf_str = str(docf).replace('.', '')
            ch4_str = str(ch4_ox).replace('.', '')
            min_dep_str = str(min_depth)
            path = base_path + f'/raster_sens_analysis/burial_lca_min{min_dep_str}_md{md_str}_exc{exc_str}_doz{doz_str}_ox{ox_str}_docf{docf_str}_ch4ox{ch4_str}.tif'
            
            docf_paths.append(path)
            
    if sens_type == 'ch4ox':
        print('ch4ox sensitivity analysis starting')
        ox_rate = base_ox_rate
        docf = base_docf
        for ch4_ox in ch4oxs:
            md_str = str(max_depth).replace('.', '')
            exc_str = str(excavator).replace('.', '')
            doz_str = str(dozer).replace('.', '')
            ox_str = str(ox_rate).replace('.', '')
            docf_str = str(docf).replace('.', '')
            ch4_str = str(ch4_ox).replace('.', '')
            min_dep_str = str(min_depth)
            path = base_path + f'/raster_sens_analysis/burial_lca_min{min_dep_str}_md{md_str}_exc{exc_str}_doz{doz_str}_ox{ox_str}_docf{docf_str}_ch4ox{ch4_str}.tif'
            
            ch4ox_paths.append(path)

df = pd.DataFrame(columns=['sens_type', 'val', 'perdif', 'count', 'min', 'p5', 'q1', 'median', 'q3', 'p95', 'max', 'mode', 'mean', 'stdev', 'sterr', 'kurtosis'])

ox_means = []
ox_stdevs = []
ox_sterrs = []
ox_perdifs = []
ox_absdifs = []

for i in range(0, len(ox_paths)):
    ox_path = ox_paths[i]
    val = ox_rates[i]
    base_val = base_ox_rate
    abs_dif = val - base_val
    per_dif = ((val - base_val)/base_val) * 100
    
    with rasterio.open(ox_path) as src:
        data = src.read(1)
        nodata_val = src.nodata
        
        data[data == nodata_val] = np.nan
        data[data == 0] = np.nan
        data = data[~np.isnan(data)]
        data = 1 - data
    
        l_all = len(data)
        min_val = np.min(data)
        p5 = np.percentile(data, 5)
        q1 = np.percentile(data, 25)
        median = np.median(data)
        q3 = np.percentile(data, 75)
        p95 = np.percentile(data, 95)
        max_val = np.max(data)
        run_mode = mode(data)
        mode_val = run_mode.mode
        mean = np.mean(data)
        stdev = np.std(data)
        sterr = stdev / np.sqrt(l_all)
        kurt = kurtosis(data)
        
        df.loc[f'ox_rate_{i}'] = ['ox_rate', val, per_dif, l_all, min_val, p5, q1, median, q3, p95, max_val, mode_val, mean, stdev, sterr, kurt]
        
        ox_means.append(mean)
        ox_stdevs.append(stdev)
        ox_sterrs.append(sterr)
        ox_perdifs.append(per_dif)

docf_means = []
docf_stdevs = []
docf_sterrs = []
docf_perdifs = []

for i in range(0, len(docf_paths)):
    docf_path = docf_paths[i]
    val = docfs[i]
    base_val = base_docf
    per_dif = ((val - base_val)/base_val) * 100
    
    with rasterio.open(docf_path) as src:
        data = src.read(1)
        nodata_val = src.nodata
        
        data[data == nodata_val] = np.nan
        data[data == 0] = np.nan
        data = data[~np.isnan(data)]
        data = 1 - data
    
        l_all = len(data)
        min_val = np.min(data)
        p5 = np.percentile(data, 5)
        q1 = np.percentile(data, 25)
        median = np.median(data)
        q3 = np.percentile(data, 75)
        p95 = np.percentile(data, 95)
        max_val = np.max(data)
        run_mode = mode(data)
        mode_val = run_mode.mode
        mean = np.mean(data)
        stdev = np.std(data)
        sterr = stdev / np.sqrt(l_all)
        kurt = kurtosis(data)
        
        df.loc[f'docf_{i}'] = ['docf', val, per_dif, l_all, min_val, p5, q1, median, q3, p95, max_val, mode_val, mean, stdev, sterr, kurt]
        
        docf_means.append(mean)
        docf_stdevs.append(stdev)
        docf_sterrs.append(sterr)
        docf_perdifs.append(per_dif)
        
ch4ox_means = []
ch4ox_stdevs = []
ch4ox_sterrs = []
ch4ox_perdifs = []

for i in range(0, len(ch4ox_paths)):
    ch4ox_path = ch4ox_paths[i]
    val = ch4oxs[i]
    base_val = base_ch4ox
    per_dif = ((val - base_val)/base_val) * 100
    
    with rasterio.open(ch4ox_path) as src:
        data = src.read(1)
        nodata_val = src.nodata
        
        data[data == nodata_val] = np.nan
        data[data == 0] = np.nan
        data = data[~np.isnan(data)]
        data = 1 - data
    
        l_all = len(data)
        min_val = np.min(data)
        p5 = np.percentile(data, 5)
        q1 = np.percentile(data, 25)
        median = np.median(data)
        q3 = np.percentile(data, 75)
        p95 = np.percentile(data, 95)
        max_val = np.max(data)
        run_mode = mode(data)
        mode_val = run_mode.mode
        mean = np.mean(data)
        stdev = np.std(data)
        sterr = stdev / np.sqrt(l_all)
        kurt = kurtosis(data)
        
        df.loc[f'ch4ox_{i}'] = ['ch4ox', val, per_dif, l_all, min_val, p5, q1, median, q3, p95, max_val, mode_val, mean, stdev, sterr, kurt]
        
        ch4ox_means.append(mean)
        ch4ox_stdevs.append(stdev)
        ch4ox_sterrs.append(sterr)
        ch4ox_perdifs.append(per_dif)

print(df)
df.to_csv(output_file, index=False)

def linreg(x, a, b):
    x = np.asarray(x)
    return (a*x) + b

#%%
fig, (ax1) = plt.subplots(1, 1, figsize = (6,2.5), layout='constrained')
axes = [ax1]

# soil c ox
x = np.asarray(ox_perdifs)
y = np.asarray(ox_means)
error_bars = ox_sterrs
shading_data = np.asarray(ox_stdevs)

params, covariance = curve_fit(linreg, x, y)
a, b = params

x_fit = np.linspace(min(x), max(x), 100)
y_fit = linreg(x_fit, a, b)

residuals = y - linreg(x, a, b)

ss_res = np.sum(residuals**2)
ss_tot = np.sum((y - np.mean(y))**2)
r_squared = 1 - (ss_res / ss_tot)

equation = f'y = {a:.5f} x + {b:.5f}'
print('Linear Regression:', equation)
print('R-squared:', r_squared)

std_errs = np.sqrt(np.diag(covariance))

# Calculate confidence intervals
conf_ints = 1.96 * std_errs  # Assuming 95% confidence level
# Plot confidence intervals
lower_ci = linreg(x, *(params - conf_ints))
upper_ci = linreg(x, *(params + conf_ints))
# ax1.fill_between(x, lower_ci, upper_ci, color=ox_color, alpha=0.2) # ci's so small, not worth plotting
ax1.fill_between(x, y-shading_data, y+shading_data, color=ox_color, alpha=0.2, zorder=0, edgecolor='none') # plot stdev as fill between
ax1.scatter(x, y, color=ox_color, marker='^', s=7, zorder=2)
#ax1.errorbar(x, y, ox_stdevs, color=ox_color, fmt='o', capsize=2) # don't need error bars with shading
ax1.plot(x_fit, y_fit, color=ox_color, label='soilCox')

# docf
x = np.asarray(docf_perdifs)
y = np.asarray(docf_means)
error_bars = docf_sterrs
shading_data = np.asarray(docf_stdevs)

params, covariance = curve_fit(linreg, x, y)
a, b = params

x_fit = np.linspace(min(x), max(x), 100)
y_fit = linreg(x_fit, a, b)

residuals = y - linreg(x, a, b)

ss_res = np.sum(residuals**2)
ss_tot = np.sum((y - np.mean(y))**2)
r_squared = 1 - (ss_res / ss_tot)

equation = f'y = {a:.5f} x + {b:.5f}'
print('Linear Regression:', equation)
print('R-squared:', r_squared)

std_errs = np.sqrt(np.diag(covariance))

# Calculate confidence intervals
conf_ints = 1.96 * std_errs  # Assuming 95% confidence level
        
# Plot confidence intervals
lower_ci = linreg(x, *(params - conf_ints))
upper_ci = linreg(x, *(params + conf_ints))
# ax1.fill_between(x, lower_ci, upper_ci, color=docf_color, alpha=0.2) # ci's so small, not worth plotting
ax1.fill_between(x, y-shading_data, y+shading_data, color=docf_color, alpha=0.2, zorder=0, edgecolor='none') # plot stdev as fill between
ax1.scatter(x, y, color=docf_color, marker='s', s=7, zorder=2)
#ax1.errorbar(x, y, docf_stdevs, color=docf_color, fmt='o', capsize=2) # don't need error bars with shading
ax1.plot(x_fit, y_fit, color=docf_color, label='docf')

# soil c ch4ox
x = np.asarray(ch4ox_perdifs)
y = np.asarray(ch4ox_means)
error_bars = ch4ox_sterrs
shading_data = np.asarray(ch4ox_stdevs)

params, covariance = curve_fit(linreg, x, y)
a, b = params

x_fit = np.linspace(min(x), max(x), 100)
y_fit = linreg(x_fit, a, b)

residuals = y - linreg(x, a, b)

ss_res = np.sum(residuals**2)
ss_tot = np.sum((y - np.mean(y))**2)
r_squared = 1 - (ss_res / ss_tot)

equation = f'y = {a:.5f} x + {b:.5f}'
print('Linear Regression:', equation)
print('R-squared:', r_squared)

std_errs = np.sqrt(np.diag(covariance))

# Calculate confidence intervals
conf_ints = 1.96 * std_errs  # Assuming 95% confidence level
        
# Plot confidence intervals
lower_ci = linreg(x, *(params - conf_ints))
upper_ci = linreg(x, *(params + conf_ints))
# ax1.fill_between(x, lower_ci, upper_ci, color=ch4ox_color, alpha=0.2) # ci's so small, not worth plotting
ax1.fill_between(x, y-shading_data, y+shading_data, color=ch4ox_color, alpha=0.2, zorder=0, edgecolor='none') # plot stdev as fill between
ax1.scatter(x, y, color=ch4ox_color, marker='o', s=7, zorder=2)
#ax1.errorbar(x, y, ch4ox_stdevs, color=ch4ox_color, fmt='o', capsize=2) # don't need error bars with shading
ax1.plot(x_fit, y_fit, color=ch4ox_color, label='ch4ox')

ax1.axvline(0, color='black', linewidth = 1)
ax1.set_ylim(0, 1)
ax1.set_xlim(-100, 210)

plt.legend()
#plt.grid(True)
if out_type == 'png':
    plt.savefig(f'{base_path}/raster_sens_analysis/raster_sens_analysis_linreg_perdif.png', dpi=300)
if out_type == 'svg':
    plt.savefig(f'{base_path}/raster_sens_analysis/raster_sens_analysis_linreg_perdif.svg', transparent=True)
plt.show()

#%%
fig, (ax1) = plt.subplots(1, 1, figsize = (6,2.5), layout='constrained')
axes = [ax1]

# soil c ox
x = np.asarray(ox_rates)
y = np.asarray(ox_means)
error_bars = ox_sterrs
shading_data = np.asarray(ox_stdevs)

params, covariance = curve_fit(linreg, x, y)
a, b = params

x_fit = np.linspace(min(x), max(x), 100)
y_fit = linreg(x_fit, a, b)

residuals = y - linreg(x, a, b)

ss_res = np.sum(residuals**2)
ss_tot = np.sum((y - np.mean(y))**2)
r_squared = 1 - (ss_res / ss_tot)

equation = f'y = {a:.5f} x + {b:.5f}'
print('Linear Regression:', equation)
print('R-squared:', r_squared)

std_errs = np.sqrt(np.diag(covariance))

# Calculate confidence intervals
conf_ints = 1.96 * std_errs  # Assuming 95% confidence level
        
# Plot confidence intervals
lower_ci = linreg(x, *(params - conf_ints))
upper_ci = linreg(x, *(params + conf_ints))
# ax1.fill_between(x, lower_ci, upper_ci, color=ox_color, alpha=0.2) # ci's so small, not worth plotting
ax1.fill_between(x, y-shading_data, y+shading_data, color=ox_color, alpha=0.2, zorder=0, edgecolor='none') # plot stdev as fill between
ax1.scatter(x, y, color=ox_color, marker='^', s=7, zorder=2)
#ax1.errorbar(x, y, ox_stdevs, color=ox_color, fmt='o', capsize=2) # don't need error bars with shading
ax1.plot(x_fit, y_fit, color=ox_color, label='soilCox')

# docf
x = np.asarray(docfs)
y = np.asarray(docf_means)
error_bars = docf_sterrs
shading_data = np.asarray(docf_stdevs)

params, covariance = curve_fit(linreg, x, y)
a, b = params

x_fit = np.linspace(min(x), max(x), 100)
y_fit = linreg(x_fit, a, b)

residuals = y - linreg(x, a, b)

ss_res = np.sum(residuals**2)
ss_tot = np.sum((y - np.mean(y))**2)
r_squared = 1 - (ss_res / ss_tot)

equation = f'y = {a:.5f} x + {b:.5f}'
print('Linear Regression:', equation)
print('R-squared:', r_squared)

std_errs = np.sqrt(np.diag(covariance))

# Calculate confidence intervals
conf_ints = 1.96 * std_errs  # Assuming 95% confidence level
        
# Plot confidence intervals
lower_ci = linreg(x, *(params - conf_ints))
upper_ci = linreg(x, *(params + conf_ints))
# ax1.fill_between(x, lower_ci, upper_ci, color=docf_color, alpha=0.2) # ci's so small, not worth plotting
ax1.fill_between(x, y-shading_data, y+shading_data, color=docf_color, alpha=0.2, zorder=0, edgecolor='none') # plot stdev as fill between
ax1.scatter(x, y, color=docf_color, marker='s', s=7, zorder=2)
#ax1.errorbar(x, y, docf_stdevs, color=docf_color, fmt='o', capsize=2)
ax1.plot(x_fit, y_fit, color=docf_color, label='docf')

# soil c ch4ox
x = np.asarray(ch4oxs)
y = np.asarray(ch4ox_means)
error_bars = ch4ox_sterrs
shading_data = np.asarray(ch4ox_stdevs)

params, covariance = curve_fit(linreg, x, y)
a, b = params

x_fit = np.linspace(min(x), max(x), 100)
y_fit = linreg(x_fit, a, b)

residuals = y - linreg(x, a, b)

ss_res = np.sum(residuals**2)
ss_tot = np.sum((y - np.mean(y))**2)
r_squared = 1 - (ss_res / ss_tot)

equation = f'y = {a:.5f} x + {b:.5f}'
print('Linear Regression:', equation)
print('R-squared:', r_squared)

std_errs = np.sqrt(np.diag(covariance))

# Calculate confidence intervals
conf_ints = 1.96 * std_errs  # Assuming 95% confidence level
        
# Plot confidence intervals
lower_ci = linreg(x, *(params - conf_ints))
upper_ci = linreg(x, *(params + conf_ints))
#ax1.fill_between(x, lower_ci, upper_ci, color=ch4ox_color, alpha=0.2)
ax1.fill_between(x, y-shading_data, y+shading_data, color=ch4ox_color, alpha=0.2, zorder=0, edgecolor='none') # plot stdev as fill between
ax1.scatter(x, y, color=ch4ox_color, marker='o', s=7, zorder=2)
#ax1.errorbar(x, y, ch4ox_stdevs, color=ch4ox_color, fmt='o', capsize=2)
ax1.plot(x_fit, y_fit, color=ch4ox_color, label='ch4ox')

ax1.axvline(0, color='black', linewidth = 1)
ax1.set_ylim(0, 1)
ax1.set_xlim(-100, 210)

plt.legend()
#plt.grid(True)
if out_type == 'png':
    plt.savefig(f'{base_path}/raster_sens_analysis/raster_sens_analysis_linreg_actual.png', dpi=300)
if out_type == 'svg':
    plt.savefig(f'{base_path}/raster_sens_analysis/raster_sens_analysis_linreg_actual.svg', transparent=True)
plt.show()


