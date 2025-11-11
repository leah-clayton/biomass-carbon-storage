#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 09:27:37 2025

@author: leahclayton
"""

import pandas as pd
import numpy as np
from scipy.stats import mode
from scipy.stats import kurtosis
import matplotlib.pyplot as plt

# sensitivity analysis?
sens_analy = True
# ensure sens_type is EMPTY ('') if sens_analy == False
sens_type = 'lowCH4ox'

# input dataset
if sens_analy == True:
    input_data = f'/base-path/optimized_paths_results_{sens_type}_post_process.csv'
else:
    input_data = '/base-path/optimized_paths_results_coded.xlsx'

no_data = -999

# output dataset
save_excel = False
output_data = '/base-path/burial_geo_lca_stats_python.xlsx'

carbon_efficiency = True

burial_color = 'indianred'
beccs_color = 'darkslateblue'

if sens_analy == True:
    hist_base = f'/base-path/scenario_shapefiles_{sens_type}'
else:
    hist_base = '/base-path/burial_geo_lca_hist'

if sens_analy == True:
    df = pd.read_csv(input_data, dtype={'scenario':str})
else:
    df = pd.read_excel(input_data, sheet_name = 'optimized_paths_results', dtype={'scenario':str})

beccs_scenarios = ['25', '50', '75', '90', '99']

#%% scenarios with all included (whether or not optimal)
beccs_25 = df[df['scenario'] == '25']
beccs_50 = df[df['scenario'] == '50']
beccs_75 = df[df['scenario'] == '75']
beccs_90 = df[df['scenario'] == '90']
beccs_99 = df[df['scenario'] == '99']
burial = df[df['scenario'] == 'all'] 

for beccs in beccs_scenarios:
    for i in range(0, 173):
        beccs_data = df[df['scenario'] == beccs]
        beccs_index = beccs_data[beccs_data['index'] == i]
        
        burial_index = burial[burial['index'] == i]
        #print(burial_index)
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

datasets = [burial, beccs_25, beccs_50, beccs_75, beccs_90, beccs_99]
names = ['burial', 'beccs_25', 'beccs_50', 'beccs_75', 'beccs_90', 'beccs_99']
columns = ['w2_c_weight']

for i in range(0, len(datasets)):
    base_name = names[i]
    dataset = datasets[i]
    
    beccs = dataset[dataset['type'] == 'beccs']
    burial = dataset[dataset['type'] == 'burial']
    
    if carbon_efficiency == True:
        if sens_analy == False:
            bin_edges = np.arange(0.70, 0.84, 0.007)
        else:
            if sens_type == 'lowCH4ox':
                bin_edges = np.arange(0.47, 0.82, 0.015)
            if sens_type == 'lowDOCf':
                bin_edges = np.arange(0.84, 0.94, 0.005)
            if sens_type == 'min1':
                bin_edges = np.arange(0.70, 0.82, 0.005)
    else:
       if sens_analy == False:
           bin_edges = np.arange(0.17, 0.25, 0.005)
       else:
           if sens_type == 'lowCH4ox':
               bin_edges = np.arange(0.17, 0.53, 0.015)
           if sens_type == 'lowDOCf':
               bin_edges = np.arange(0.84, 0.94, 0.005) # NOT UPDATED CORRECTLY (NEED 1 - everything)
           if sens_type == 'min1':
               bin_edges = np.arange(0.17, 0.30, 0.005)
    
    if burial.empty:
        print(f'Burial empty for {base_name}')
        for column in columns:
            beccs_data = []
            
            if carbon_efficiency == True:
                beccs_data = [1.0 - x for x in beccs[column]]
            else:
                beccs_data = beccs[column]
            beccs_mean = np.mean(beccs_data)
            print(f'{base_name} BECCS mean:', beccs_mean)
            
            plt.figure(figsize=(3, 1))
            plt.hist(beccs_data, alpha = 0.4, color=beccs_color, bins = bin_edges, density = False, label = 'beccs')
            plt.hist(beccs_data, bins=bin_edges, color=beccs_color, density=False, histtype='step', linewidth=1)
            #plt.xlabel(f'{base_name} {column}')
            #plt.ylabel('Count')
            if carbon_efficiency == True:
                if sens_analy == False:
                    plt.xlim(0.70, 0.84)
                    plt.xticks([0.70, 0.74, 0.78, 0.82], fontsize=7)
                else:
                    if sens_type == 'lowCH4ox':
                        plt.xlim(0.47, 0.82)
                        plt.xticks([0.45, 0.55, 0.65, 0.75, 0.85], fontsize=7)
                    if sens_type == 'lowDOCf':
                        plt.xlim(0.84, 0.94)
                        plt.xticks([0.84, 0.86, 0.88, 0.90, 0.92, 0.94], fontsize=7)
                    if sens_type == 'min1':
                        plt.xlim(0.70, 0.82)
                        plt.xticks([0.70, 0.74, 0.78, 0.82], fontsize=7)
            else:
                if sens_analy == False:
                    plt.xlim(0.17, 0.25)
                    plt.xticks(fontsize=7)
                else:
                    if sens_type == 'lowCH4ox':
                        plt.xlim(0.17, 0.53)
                        plt.xticks([0.20, 0.30, 0.40, 0.50], fontsize=7)
                    if sens_type == 'lowDOCf': # NOT UPDATED CORRECTLY (NEED 1 - everything)
                        plt.xlim(0.84, 0.94)
                        plt.xticks([0.84, 0.86, 0.88, 0.90, 0.92, 0.94], fontsize=7)
                    if sens_type == 'min1':
                        plt.xlim(0.17, 0.30)
                        plt.xticks([0.15, 0.20, 0.25, 0.30], fontsize=7)
                
            #plt.legend()
            #plt.grid(True)
            ymin, ymax = plt.ylim()
            yticks = np.arange(start=0, stop=ymax + 10, step=20)
            plt.yticks(yticks)
            ax = plt.gca()
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.yticks(fontsize=7)
            if carbon_efficiency == True:
                plt.savefig(f'{hist_base}/{sens_type}burial_beccs_hist_{base_name}_{column}_c_eff.svg', transparent=True)
            else:
                plt.savefig(f'{hist_base}/{sens_type}burial_beccs_hist_{base_name}_{column}.svg', transparent=True)
            plt.show()
    if beccs.empty:
        print(f'BECCS empty for {base_name}')
        for column in columns: 
            burial_data = []
            
            if carbon_efficiency == True:
                burial_data = [1.0 - x for x in burial[column]]
            else:
                burial_data = burial[column]
                
            burial_mean = np.mean(burial_data)
            print(f'{base_name} Burial mean:', burial_mean)
            
            plt.figure(figsize=(3, 1))
            plt.hist(burial_data, alpha = 0.4, color=burial_color, bins = bin_edges, density = False, label = f'burial\nmean = {burial_mean:.3f}\n n = {len(burial[column])}')
            plt.hist(burial_data, bins=bin_edges, color=burial_color, density=False, histtype='step', linewidth=1)
            plt.axvline(burial_mean, color=burial_color, linestyle='dotted', linewidth=2)
            #plt.xlabel(f'{base_name} {column}')
            #plt.ylabel('Count')
            if carbon_efficiency == True:
                if sens_analy == False:
                    plt.xlim(0.70, 0.84)
                    plt.xticks([0.70, 0.74, 0.78, 0.82], fontsize=7)
                else:
                    if sens_type == 'lowCH4ox':
                        plt.xlim(0.47, 0.82)
                        plt.xticks([0.45, 0.55, 0.65, 0.75, 0.85], fontsize=7)
                    if sens_type == 'lowDOCf':
                        plt.xlim(0.84, 0.94)
                        plt.xticks([0.84, 0.86, 0.88, 0.90, 0.92, 0.94], fontsize=7)
                    if sens_type == 'min1':
                        plt.xlim(0.70, 0.82)
                        plt.xticks([0.70, 0.74, 0.78, 0.82], fontsize=7)
            else:
                if sens_analy == False:
                    plt.xlim(0.17, 0.25)
                    plt.xticks(fontsize=7)
                else:
                    if sens_type == 'lowCH4ox':
                        plt.xlim(0.17, 0.53)
                        plt.xticks([0.20, 0.30, 0.40, 0.50], fontsize=7)
                    if sens_type == 'lowDOCf':
                        plt.xlim(0.84, 0.94) # NOT UPDATED CORRECTLY (NEED 1 - everything)
                        plt.xticks([0.84, 0.86, 0.88, 0.90, 0.92, 0.94], fontsize=7)
                    if sens_type == 'min1':
                        plt.xlim(0.17, 0.30)
                        plt.xticks([0.15, 0.20, 0.25, 0.30], fontsize=7)
            #plt.legend()
            #plt.grid(True)
            ymin, ymax = plt.ylim()
            yticks = np.arange(start=0, stop=ymax + 10, step=20)
            plt.yticks(yticks)
            ax = plt.gca()
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.xticks(fontsize=7)
            plt.yticks(fontsize=7)
            if carbon_efficiency == True:
                plt.savefig(f'{hist_base}/{sens_type}burial_beccs_hist_{base_name}_{column}_c_eff.svg', transparent=True)
            else:
                plt.savefig(f'{hist_base}/{sens_type}burial_beccs_hist_{base_name}_{column}.svg', transparent=True)
            plt.show()
    else:
        for column in columns:
            beccs_data = []
            burial_data = []

            if carbon_efficiency == True:
                burial_data = [1.0 - x for x in burial[column]]
                beccs_data = [1.0 - x for x in beccs[column]]
            else:
                burial_data = burial[column]
                beccs_data = beccs[column]
                
            burial_mean = np.mean(burial_data)
            print(f'{base_name} Burial mean:', burial_mean)
            beccs_mean = np.mean(beccs_data)
            print(f'{base_name} BECCS mean:', beccs_mean)
            
            plt.figure(figsize=(3, 1))
            plt.hist(beccs_data, alpha = 0.4, color=beccs_color, bins = bin_edges, density = False, label = f'beccs\nmean = {beccs_mean:.3f}\n n = {len(beccs[column])}')
            plt.hist(burial_data, alpha = 0.4, color=burial_color, bins = bin_edges, density = False, label = f'burial\nmean = {burial_mean:.3f}\nn = {len(burial[column])}')
            plt.hist(beccs_data, bins = bin_edges, color=beccs_color, density=False, histtype='step', linewidth=1)
            plt.hist(burial_data, bins = bin_edges, color=burial_color, density=False, histtype='step', linewidth=1)
            plt.axvline(burial_mean, color = burial_color, linestyle = 'dotted', linewidth = 2)
            plt.axvline(beccs_mean, color = beccs_color, linestyle = 'dotted', linewidth = 2)
            #plt.xlabel(f'{base_name} {column}')
            #plt.ylabel('Count')
            if carbon_efficiency == True:
                if sens_analy == False:
                    plt.xlim(0.70, 0.84)
                    plt.xticks([0.70, 0.74, 0.78, 0.82], fontsize=7)
                else:
                    if sens_type == 'lowCH4ox':
                        plt.xlim(0.47, 0.82)
                        plt.xticks([0.45, 0.55, 0.65, 0.75, 0.85], fontsize=7)
                    if sens_type == 'lowDOCf':
                        plt.xlim(0.84, 0.94)
                        plt.xticks([0.84, 0.86, 0.88, 0.90, 0.92, 0.94], fontsize=7)
                    if sens_type == 'min1':
                        plt.xlim(0.70, 0.82)
                        plt.xticks([0.70, 0.74, 0.78, 0.82], fontsize=7)
            else:
                if sens_analy == False:
                    plt.xlim(0.17, 0.25)
                    plt.xticks(fontsize=7)
                else:
                    if sens_type == 'lowCH4ox':
                        plt.xlim(0.17, 0.53)
                        plt.xticks([0.20, 0.30, 0.40, 0.50], fontsize=7)
                    if sens_type == 'lowDOCf': # NOT UPDATED CORRECTLY (NEED 1 - everything)
                        plt.xlim(0.84, 0.94)
                        plt.xticks([0.84, 0.86, 0.88, 0.90, 0.92, 0.94], fontsize=7)
                    if sens_type == 'min1':
                        plt.xlim(0.17, 0.30)
                        plt.xticks([0.15, 0.20, 0.25, 0.30], fontsize=7)
            ymin, ymax = plt.ylim()
            yticks = np.arange(start=0, stop=ymax + 10, step=20)
            plt.yticks(yticks)
            #plt.legend()
            #plt.grid(True)
            ax = plt.gca()
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.xticks(fontsize=7)
            plt.yticks(fontsize=7)
            if carbon_efficiency == True:
                plt.savefig(f'{hist_base}/{sens_type}burial_beccs_hist_{base_name}_{column}_c_eff.svg', transparent=True)
            else:
                plt.savefig(f'{hist_base}/{sens_type}burial_beccs_hist_{base_name}_{column}.svg', transparent=True)
            plt.show()
            plt.show()
