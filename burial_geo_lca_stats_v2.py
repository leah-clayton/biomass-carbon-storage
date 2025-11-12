#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 10 11:14:51 2025

@author: leahclayton
"""

import pandas as pd
import numpy as np
from scipy.stats import mode
from scipy.stats import kurtosis
import matplotlib.pyplot as plt

# input dataset; can be sensitivity analysis or not, just make sure BECCS are
# also included in the file if running a sensitivity analysis
input_data = '/base-path/optimized_paths_results_lowDOCf_coded.xlsx'

no_data = -999

# output dataset
save_excel = True
output_data = '/base-path/burial_geo_lca_stats_python_lowDOCf.xlsx'

states = ['Arizona', 'California', 'Colorado', 'Idaho', 'Montana', 'Nevada',
          'New Mexico', 'Oregon', 'Utah', 'Washington', 'Wyoming']

colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown',
          'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan', 'navy']

# States histograms?
states_hist = False
hist_base = '/base-path/stats/burial_geo_lca_hist'

df = pd.read_excel(input_data, sheet_name = 'optimized_paths_results', dtype={'scenario':str})

beccs_scenarios = ['25', '50', '75', '90', '99']

#%% scenarios with all included (whether or not optimal)
beccs_25 = df[df['scenario'] == '25']
beccs_50 = df[df['scenario'] == '50']
beccs_75 = df[df['scenario'] == '75']
beccs_90 = df[df['scenario'] == '90']
beccs_99 = df[df['scenario'] == '99']
burial = df[df['scenario'] == 'all'] 

new_df = pd.DataFrame(columns=['name', 'scenario', 'metric', 'region', 'count', 
                               'min', 'p5', 'q1', 'median', 'q3', 
                               'p95', 'max', 'mode', 'mean', 'stdev', 'kurtosis'])

datasets = [beccs_25, beccs_50, beccs_75, beccs_90, beccs_99, burial]
names = ['beccs_25', 'beccs_50', 'beccs_75', 'beccs_90', 'beccs_99', 'burial']

for i in range(0, len(datasets)):
    base_name = names[i]
    dataset = datasets[i]
    print(dataset)
    
    """
    columns = ['path_length_km', 'cumulative_c_weight', 'end_pt_c_weight', 
               'w1_transport_c', 'w1_beccs_vs_burial', 'w2_path_length_km', 'w2_c_weight',
               'w2_transport_c', 'w2_beccs_vs_burial']
    """
    
    columns = ['path_length_km', 'cumulative_c_weight', 'end_pt_c_weight', 
               'w1_transport_c', 'w2_path_length_km', 'w2_c_weight',
               'w2_transport_c']
    
    for column in columns:
        name = f'all_{base_name}_{column}'
        data = dataset[column].copy()
        #print(name)
        #print(data)
        
        data = data.replace(no_data, np.nan)
        
        #data.loc[data == no_data] = np.nan
        #data = data[~np.isnan(data)]
        
        if data.empty:
            print(f'All data nan, skipping column {column} for {base_name}')
        
        else:
            len_val = len(data)
            min_val = np.min(data)
            p5 = np.percentile(data, 5)
            q1 = np.percentile(data, 25)
            median = np.median(data)
            q3 = np.percentile(data, 75)
            p95 = np.percentile(data, 95)
            max_val = np.max(data)
            state_mode = mode(data)
            mode_val = state_mode.mode
            mean = np.mean(data)
            stdev = np.std(data)
            kurt = kurtosis(data)
            region = 'US West'
            
            new_df.loc[name] = [name, base_name, column, region, len_val, min_val, p5, q1, median, q3, p95,
                                max_val, mode_val, mean, stdev, kurt]
            
            print(f'{base_name} {column}')
            try:
                plt.figure(figsize=(7.5, 4))
                plt.hist(data, alpha = 0.6, bins = 20, density = True)
                plt.axvline(mean, label = f'mean = {mean:.2f}')
                plt.axvline(median, linestyle = 'dotted', label = f'median = {median:.2f}')
                plt.legend()
                plt.xlabel(f'{base_name} {column}')
                plt.ylabel('Frequency')
                plt.savefig(f'{hist_base}/all_{base_name}_{column}_us_west.png', dpi=300)
                plt.show()
            except ValueError:
                print(f'ValueError for {base_name} {column}, skipping')
            
    for state in states:
        state_data = dataset[dataset['start_state'] == state]
        for column in columns:
            name = f'all_{base_name}_{column}_{state}'
            data = state_data[column].copy()
            
            data = data.replace(no_data, np.nan)
            
            #data.loc[data == no_data] = np.nan
            #data = data[~np.isnan(data)]
            
            if data.empty:
                print(f'All data nan, skipping column {column} for {base_name}, {state}')
            
            else:
                len_val = len(data)
                min_val = np.min(data)
                p5 = np.percentile(data, 5)
                q1 = np.percentile(data, 25)
                median = np.median(data)
                q3 = np.percentile(data, 75)
                p95 = np.percentile(data, 95)
                max_val = np.max(data)
                state_mode = mode(data)
                mode_val = state_mode.mode
                mean = np.mean(data)
                stdev = np.std(data)
                kurt = kurtosis(data)
                
                new_df.loc[name] = [name, base_name, column, state, len_val, min_val, p5, q1, median, q3, p95,
                                    max_val, mode_val, mean, stdev, kurt]
print('Scenarios with every outcome completed')    
      

#%% one way scenarios WITH OPTIMAL CHOICE
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
                    
datasets = [beccs_25, beccs_50, beccs_75, beccs_90, beccs_99]
names = ['beccs_25', 'beccs_50', 'beccs_75', 'beccs_90', 'beccs_99']

for i in range(0, len(datasets)):
    base_name = names[i]
    dataset = datasets[i]
    
    """
    columns = ['path_length_km', 'cumulative_c_weight', 'end_pt_c_weight', 
               'w1_transport_c', 'w1_beccs_vs_burial']
    """
    columns = ['path_length_km', 'cumulative_c_weight', 'end_pt_c_weight', 
               'w1_transport_c']
    
    for column in columns:
        name = f'opt_{base_name}_{column}'
        data = dataset[column].copy()
        
        data = data.replace(no_data, np.nan)
        
        #data.loc[data == no_data] = np.nan
        #data = data[~np.isnan(data)]
        
        if data.empty:
            print(f'All data nan, skipping column {column} for {base_name}')
        
        else:
            len_val = len(data)
            min_val = np.min(data)
            p5 = np.percentile(data, 5)
            q1 = np.percentile(data, 25)
            median = np.median(data)
            q3 = np.percentile(data, 75)
            p95 = np.percentile(data, 95)
            max_val = np.max(data)
            state_mode = mode(data)
            mode_val = state_mode.mode
            mean = np.mean(data)
            stdev = np.std(data)
            kurt = kurtosis(data)
            region = 'US West'
            
            new_df.loc[name] = [name, base_name, column, region, len_val, min_val, p5, q1, median, q3, p95,
                                max_val, mode_val, mean, stdev, kurt]
            plt.figure(figsize=(7.5, 4))
            plt.hist(data, alpha = 0.6, bins = 20, density = True)
            plt.axvline(mean, label = f'mean = {mean:.2f}')
            plt.axvline(median, linestyle = 'dotted', label = f'median = {median:.2f}')
            plt.legend()
            plt.xlabel(f'{base_name} {column}')
            plt.ylabel('Frequency')
            plt.savefig(f'{hist_base}/opt_{base_name}_{column}_us_west.png', dpi=300)
            plt.show() 
            
    for state in states:
        state_data = dataset[dataset['start_state'] == state]
        for column in columns:
            name = f'opt_{base_name}_{column}_{state}'
            data = state_data[column].copy()
            
            data = data.replace(no_data, np.nan)
            
            #data.loc[data == no_data] = np.nan
            #data = data[~np.isnan(data)]
            
            if data.empty:
                print(f'All data nan, skipping column {column} for {base_name}, {state}')
            
            else:
                len_val = len(data)
                min_val = np.min(data)
                p5 = np.percentile(data, 5)
                q1 = np.percentile(data, 25)
                median = np.median(data)
                q3 = np.percentile(data, 75)
                p95 = np.percentile(data, 95)
                max_val = np.max(data)
                state_mode = mode(data)
                mode_val = state_mode.mode
                mean = np.mean(data)
                stdev = np.std(data)
                kurt = kurtosis(data)
                
                new_df.loc[name] = [name, base_name, column, state, len_val, min_val, p5, q1, median, q3, p95,
                                    max_val, mode_val, mean, stdev, kurt]

#%% two way scenarios WITH OPTIMAL CHOICE
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

datasets = [beccs_25, beccs_50, beccs_75, beccs_90, beccs_99]
names = ['beccs_25', 'beccs_50', 'beccs_75', 'beccs_90', 'beccs_99']

for i in range(0, len(datasets)):
    base_name = names[i]
    dataset = datasets[i]
    
    """
    columns = ['end_pt_c_weight', 'w2_path_length_km', 'w2_c_weight', 
               'w2_transport_c', 'w2_beccs_vs_burial']
    """
    columns = ['end_pt_c_weight', 'w2_path_length_km', 'w2_c_weight', 
               'w2_transport_c']
    
    for column in columns:
        name = f'opt_{base_name}_{column}'
        data = dataset[column].copy()
        
        data = data.replace(no_data, np.nan)
        
        #data.loc[data == no_data] = np.nan
        #data = data[~np.isnan(data)]
        
        if data.empty:
            print(f'All data nan, skipping column {column} for {base_name}')
        
        else:
            len_val = len(data)
            min_val = np.min(data)
            p5 = np.percentile(data, 5)
            q1 = np.percentile(data, 25)
            median = np.median(data)
            q3 = np.percentile(data, 75)
            p95 = np.percentile(data, 95)
            max_val = np.max(data)
            state_mode = mode(data)
            mode_val = state_mode.mode
            mean = np.mean(data)
            stdev = np.std(data)
            kurt = kurtosis(data)
            region = 'US West'
            
            new_df.loc[name] = [name, base_name, column, region, len_val, min_val, p5, q1, median, q3, p95,
                                max_val, mode_val, mean, stdev, kurt]
            
            plt.figure(figsize=(7.5, 4))
            plt.hist(data, alpha = 0.6, bins = 20, density = True)
            plt.axvline(mean, label = f'mean = {mean:.2f}')
            plt.axvline(median, linestyle = 'dotted', label = f'median = {median:.2f}')
            plt.legend()
            plt.xlabel(f'{base_name} {column}')
            plt.ylabel('Frequency')
            plt.savefig(f'{hist_base}/opt_{base_name}_{column}_us_west.png', dpi=300)
            plt.show() 
    
    for state in states:
        state_data = dataset[dataset['start_state'] == state]
        
        for column in columns:
            
            name = f'opt_{base_name}_{column}_{state}'
            data = state_data[column]
            
            data = data.replace(no_data, np.nan)
            
            
            if data.empty:
                print(f'All data nan, skipping column {column} for {base_name}, {state}')
            
            else:
                len_val = len(data)
                min_val = np.min(data)
                p5 = np.percentile(data, 5)
                q1 = np.percentile(data, 25)
                median = np.median(data)
                q3 = np.percentile(data, 75)
                p95 = np.percentile(data, 95)
                max_val = np.max(data)
                state_mode = mode(data)
                mode_val = state_mode.mode
                mean = np.mean(data)
                stdev = np.std(data)
                kurt = kurtosis(data)
                
                new_df.loc[name] = [name, base_name, column, state, len_val, min_val, p5, q1, median, q3, p95,
                                    max_val, mode_val, mean, stdev, kurt]
                
            

    if states_hist == True:
        for column in columns:
            states_data = {}
            states_means = []
            states_medians = []
            
            for state in states:
                state_data = dataset[dataset['start_state'] == state]
                
                data = state_data[column]
                
                data = data.replace(no_data, np.nan)
                
                if data.empty:
                    print('Empty')
                
                else:
                    states_data[state] = data
                    print(f'{state} {column} added to states_data')
                    
                    mean = np.mean(data)
                    median = np.median(data)
                    
                    states_means.append(mean)
                    states_medians.append(median)
                    
            file_base = f'states_{base_name}_{column}'
            plt.figure(figsize=(7.5, 4))
            for n, (name, data) in enumerate(states_data.items()):
                plt.hist(data, color=colors[n], alpha=0.6, bins=5, density=True)
                state_mean = states_means[n]
                plt.axvline(state_mean, color=colors[n], label=f'{states[n]}, mean = {state_mean:.2f}')
                plt.hist(data, color = colors[n], histtype='step', bins=5, density=True)
            plt.legend()
            plt.xlabel(f'{base_name} {column}')
            plt.ylabel('Frequency')
            plt.savefig(f'{hist_base}/{file_base}_mean_dens.png', dpi=300)
            plt.show()
        
            plt.figure(figsize=(7.5, 4))
            for n, (name, data) in enumerate(states_data.items()):
                plt.hist(data, color=colors[n], alpha=0.6, bins=5, density=False)
                state_mean = states_means[n]
                plt.axvline(state_mean, color=colors[n], label=f'{states[n]}, mean = {state_mean:.2f}')
                plt.hist(data, color = colors[n], histtype='step', bins=5, density=False)
            plt.legend()
            plt.xlabel(f'{base_name} {column}')
            plt.ylabel('Count')
            plt.savefig(f'{hist_base}/{file_base}_mean_nodens.png', dpi=300)
            plt.show()
            
            plt.figure(figsize=(7.5, 4))
            for n, (name, data) in enumerate(states_data.items()):
                plt.hist(data, color=colors[n], alpha=0.6, bins=5, density=True)
                state_median = states_medians[n]
                plt.axvline(state_median, color=colors[n], label=f'{states[n]}, median = {state_median:.2f}')
                plt.hist(data, color = colors[n], histtype='step', bins=5, density=True)
            plt.legend()
            plt.xlabel(f'{base_name} {column}')
            plt.ylabel('Frequency')
            plt.savefig(f'{hist_base}/{file_base}_median_dens.png', dpi=300)
            plt.show()
        
            plt.figure(figsize=(7.5, 4))
            for n, (name, data) in enumerate(states_data.items()):
                plt.hist(data, color=colors[n], alpha=0.6, bins=5, density=False)
                state_median = states_medians[n]
                plt.axvline(state_median, color=colors[n], label=f'{states[n]}, median = {state_median:.2f}')
                plt.hist(data, color = colors[n], histtype='step', bins=5, density=False)
            plt.legend()
            plt.xlabel(f'{base_name} {column}')
            plt.ylabel('Count')
            plt.savefig(f'{hist_base}/{file_base}_median_nodens.png', dpi=300)
            plt.show()
    
if save_excel == True:           
    new_df.to_excel(output_data)
