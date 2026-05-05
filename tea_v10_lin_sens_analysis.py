#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 09:30:29 2026

@author: leahclayton
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

#%% 
"""
PARAMETERIZATION -------------------------------------------------------------
TEA unit = $ MTCO2e_i^-1 (cost per MTCO2e in initial biomass) ##
"""

# phi: forest process costs of cutting and aggregating material (2026$) MTCO2e_i^-1
phi_b = 25.93 # average across accessibility classifications
phi_l = 17.17 # 0-500 ft from roads, 0-20% slope
phi_h = 38.03 # 1000 ft - 0.5 mi from roads, 20-40% slope

# alpha: transport cost($) ONE-WAY distance(km)^-1 MTCO2e_i^-1
alpha_b = 0.1023 # Stolaroff et al. 2021, convers. to 2026$
alpha_l = 0.1023 # Stolaroff et al. 2021, convers. to 2026$
alpha_h = 0.2774 # theoretical, field-based understanding

# x: ONE-WAY transport distance; km
x_beccs_b = 196 # this paper network LCA
x_beccs_l = 14 # this paper network LCA
x_beccs_h = 798 # this paper network LCA

x_bur_b = 140 # this paper network LCA
x_bur_l = 8 # this paper network LCA
x_bur_h = 295 # this paper network LCA

x_char_b = 0 # assume in-situ application
x_pb_b = 0 # in-situ by default

# eta: carbon efficiency; MTCO2e_stored MTCO2e_i^-1
eta_bur_b = 0.783 # this paper network LCA
eta_bur_l = 0.511 # this paper =0.521 lowCH4ox - 0.01 transportation
eta_bur_h = 0.897 # this paper =0.907 lowDOCf - 0.01 transportation

eta_beccs_b = 0.809 # this paper network LCA
eta_beccs_l = 0.767 # this paper network LCA
eta_beccs_h = 0.878 # Sanchez et al. 2025

eta_char_b = 0.435 # this paper
eta_char_l = 0.16 # Chiquier et al. 2022
eta_char_h = 0.459 # Rodrigues et al. 2023

# rho: credit price; $ MTCO2e_stored^-1
rho_b = 100 # Roads to Removal
rho_l = 50 # Roads to Removal
rho_h = 300 # Roads to Removal

# xi: salable products price; price (2026$) MTCO2e_stored^-1
xi_beccs_b = 102.093 # Roads to Removal analysis, convers. to 2026$
xi_beccs_l = 0 # No market scenario
#xi_beccs_l = 37.877 # Roads to Removal analysis, convers. to 2026$
#xi_beccs_h = 154.984 # Roads to Removal analysis, convers. to 2026$
xi_beccs_h = 345.691 # Roads to Removal analysis gasification high bound + hydrogen incentive, convers. to 2026$

xi_char_b = 83.360 # Elias et al. 2024, convers. to 2026$
xi_char_l = 0 # In-situ application/no market scenario
xi_char_h = 560 # Trapero et al. 2025

# kappa: capex; cost (2026$) MTCO2e_stored^-1
kappa_bur_b = 8.576 # Yablonovitch and Deckman 2023, Zeng and Hausmann 2022, convers. to 2026$
kappa_bur_l = 5.585 # Yablonovitch and Deckman 2023, Zeng and Hausmann 2022, convers. to 2026$
kappa_bur_h = 36.180 # Theoretical, convers. to 2026$

kappa_beccs_b = 66.644 # Roads to Removal analysis, convers. to 2026$
kappa_beccs_l = 9.147 # Roads to Removal analysis, convers. to 2026$
kappa_beccs_h = 89.268 # Roads to Removal analysis, convers. to 2026$

kappa_char_b = 27.092 # Elias et al. 2024, convers. to 2026$

# omega: opex; cost (2026$) MTCO2e_stored^-1
omega_bur_b = 13.681 # Yablonovitch and Deckman 2023, Zeng and Hausmann 2022, convers. to 2026$
omega_bur_l = 5.585 # Zeng and Hausmann 2022, convers. to 2026$
omega_bur_h = 21.440 # Yablonovitch and Deckman 2023, convers. to 2026$

omega_beccs_b = 64.243 # Roads to Removal analysis, convers. to 2026$
omega_beccs_l = 37.338 # Roads to Removal analysis, convers. to 2026$
omega_beccs_h = 147.397 # Roads to Removal analysis, convers. to 2026$

omega_char_b = 93.78 # Elias et al. 2024, convers. to 2026$

# cost of pile burning; cost (2026$) MTCO2e_i^-1
omega_pb_b = 22.91 # Barker et al. 2025, convers. to 2026$
omega_pb_l = 10.38 # Campbell and Anderson 2019, convers. to 2026$
omega_pb_h = 41.69 # Barker et al. 2025, convers. to 2026$


""" v8 and prior
omega_pb_b = 58.051 # calculated from Barker et al. 2025, convers. to 2026$
omega_pb_l = 10.38 # Campbell and Anderson 2019, convers. to 2026$
omega_pb_h = 104.33 # Barker et al. 2025, convers. to 2026$
"""

# figure save path
save_path = '/set_save_path'

#%%
"""
MODEL EQUATIONS --------------------------------------------------------------
"""
def cost_bur(phi, alpha, x_bur, eta_bur, rho, kappa_bur, omega_bur):
    return -phi-(alpha*x_bur)+eta_bur*(rho-kappa_bur-omega_bur)

def cost_beccs(phi, alpha, x_beccs, eta_beccs, rho, kappa_beccs, omega_beccs, xi_beccs):
    return -phi-(alpha*x_beccs)+eta_beccs*(rho+xi_beccs-kappa_beccs-omega_beccs)

def cost_char(phi, eta_char, rho, xi_char, kappa_char, omega_char):
    return -phi+eta_char*(rho+xi_char-kappa_char-omega_char)

def cost_pb(phi, omega_pb):
    return -phi-omega_pb

def breakeven_dist(alpha, rho, eta_bur, eta_beccs, kappa_bur, kappa_beccs, omega_bur, omega_beccs, xi_beccs):
    return (1/alpha)*(eta_bur*(rho-kappa_bur-omega_bur)+eta_beccs*(-rho-xi_beccs+kappa_beccs+omega_beccs))

def pileburn_bur_dist(sigma, eta_bur, rho, kappa_bur, omega_bur, alpha):
    return (sigma + eta_bur*(rho + kappa_bur + omega_bur))/alpha

def pileburn_beccs_dist(sigma, eta_beccs, rho, kappa_beccs, omega_beccs, xi_beccs, alpha):
    return (sigma + eta_beccs*(rho + kappa_beccs + omega_beccs+ xi_beccs))/alpha

def breakeven_char_price(rho, kappa_char, omega_char, alpha, x_bur, eta_bur, kappa_bur, omega_bur, eta_char):
    return -rho+kappa_char+omega_char-(((alpha*x_bur)+eta_bur*(-rho+kappa_bur+omega_bur))/eta_char)

#%% Sensitivity analysis, one fig
fig, ax = plt.subplots(figsize=(8.5, 4), layout='constrained')

df = pd.DataFrame(columns=['variable', 'pathway', 'type', 'x0', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9'])

color_map ={
    'phi': 'olivedrab',
    'alpha': 'lightcoral',
    'x': 'indianred',
    'kappa': 'firebrick',
    'omega': 'darkred',
    'eta': 'lightsteelblue',
    'rho': 'cornflowerblue',
    'xi': 'darkblue'
    }

# phi: forest processes
phi_range = np.linspace(phi_l, phi_h, 10)
l = ['phi', 'na', 'range']+phi_range.tolist()
df.loc[len(df)] = l

phi_perch = [((i-phi_b)/phi_b)*100 for i in phi_range]
l = ['phi', 'na', 'perch']+phi_perch
df.loc[len(df)] = l

phi_beccs = [cost_beccs(i, alpha_b, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in phi_range]
l = ['phi', 'beccs', 'cost']+phi_beccs
df.loc[len(df)] = l

phi_bur = [cost_bur(i, alpha_b, x_bur_b, eta_bur_b, rho_b, kappa_bur_b, omega_bur_b) for i in phi_range]
l = ['phi', 'bur', 'cost']+phi_bur

phi_char = [cost_char(i, eta_char_b, rho_b, xi_char_b, kappa_char_b, omega_char_b) for i in phi_range]
l = ['phi', 'char', 'cost']+phi_char

phi_pb = [cost_pb(i, omega_pb_b) for i in phi_range]
l = ['phi', 'pb', 'cost']+phi_pb

ax.plot(phi_perch, phi_beccs, color=color_map['phi'], label='forestry cost')
ax.scatter(phi_perch, phi_beccs, color=color_map['phi'])
ax.plot(phi_perch, phi_bur, color=color_map['phi'])
ax.plot(phi_perch, phi_char, color=color_map['phi'])
ax.plot(phi_perch, phi_pb, color=color_map['phi'])

# alpha: transportation cost
alpha_range = np.linspace(alpha_l, alpha_h, 10)
l = ['alpha', 'na', 'range']+alpha_range.tolist()
df.loc[len(df)] = l

alpha_beccs = [cost_beccs(phi_b, i, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in alpha_range]
l = ['alpha', 'beccs', 'cost']+alpha_beccs
df.loc[len(df)] = l


alpha_bur = [cost_bur(phi_b, i, x_bur_b, eta_bur_b, rho_b, kappa_bur_b, omega_bur_b) for i in alpha_range]
l = ['alpha', 'bur', 'cost']+alpha_bur
df.loc[len(df)] = l

alpha_perch = [((i-alpha_b)/alpha_b)*100 for i in alpha_range]
l = ['alpha', 'na', 'perch']+alpha_perch
df.loc[len(df)] = l

ax.plot(alpha_perch, alpha_beccs, color='lightcoral', label='transport cost')
ax.plot(alpha_perch, alpha_bur, color='lightcoral', marker='o')
ax.scatter(alpha_perch, alpha_beccs, color='lightcoral', marker='s')

# x: transportation distance
## BECCS
x_beccs_range = np.linspace(x_beccs_l, x_beccs_h, 10)
l = ['x', 'beccs', 'range']+x_beccs_range.tolist()
df.loc[len(df)] = l

x_beccs = [cost_beccs(phi_b, alpha_b, i, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in x_beccs_range]
l = ['x', 'beccs', 'cost']+x_beccs
df.loc[len(df)] = l

x_beccs_perch = [((i-x_beccs_b)/x_beccs_b)*100 for i in x_beccs_range]
l = ['x', 'beccs', 'perch']+x_beccs_perch
df.loc[len(df)] = l

ax.plot(x_beccs_perch, x_beccs, color='indianred', label='transport distance')
ax.scatter(x_beccs_perch, x_beccs, color='indianred', marker='s')

## burial
x_bur_range = np.linspace(x_bur_l, x_bur_h, 10)
l = ['x', 'bur', 'range']+x_bur_range.tolist()
df.loc[len(df)] = l

x_bur = [cost_bur(phi_b, alpha_b, i, eta_bur_b, rho_b, kappa_bur_b, omega_bur_b) for i in x_bur_range]
l = ['x', 'bur', 'cost']+x_bur
df.loc[len(df)] = l

x_bur_perch = [((i-x_bur_b)/x_bur_b)*100 for i in x_bur_range]
l = ['x', 'bur', 'perch']+x_bur_perch
df.loc[len(df)] = l

ax.plot(x_bur_perch, x_bur, color='indianred', marker='o')

# kappa
## BECCS
kappa_beccs_range = np.linspace(kappa_beccs_l, kappa_beccs_h, 10)
l = ['kappa', 'beccs', 'range']+kappa_beccs_range.tolist()
df.loc[len(df)] = l

kappa_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, rho_b, i, omega_beccs_b, xi_beccs_b) for i in kappa_beccs_range]
l = ['kappa', 'beccs', 'cost']+kappa_beccs
df.loc[len(df)] = l

kappa_beccs_perch = [((i-kappa_beccs_b)/kappa_beccs_b)*100 for i in kappa_beccs_range]
l = ['kappa', 'beccs', 'perch']+kappa_beccs_perch
df.loc[len(df)] = l

ax.plot(kappa_beccs_perch, kappa_beccs, color='firebrick', label='capital cost')
ax.scatter(kappa_beccs_perch, kappa_beccs, color='firebrick', marker='s')

## burial
kappa_bur_range = np.linspace(kappa_bur_l, kappa_bur_h, 10)
l = ['kappa', 'bur', 'range']+kappa_bur_range.tolist()
df.loc[len(df)] = l

kappa_bur = [cost_bur(phi_b, alpha_b, x_bur_b, eta_bur_b, rho_b, i, omega_bur_b) for i in kappa_bur_range]
l = ['kappa', 'bur', 'cost']+kappa_bur
df.loc[len(df)] = l

kappa_bur_perch = [((i-kappa_bur_b)/kappa_bur_b)*100 for i in kappa_bur_range]
l = ['kappa', 'bur', 'perch']+kappa_bur_perch
df.loc[len(df)] = l

ax.plot(kappa_bur_perch, kappa_bur, color='firebrick', marker='o')

## biochar
kappa_char_range = np.linspace(kappa_char_b-10, kappa_char_b+10, 10)
l = ['kappa', 'char', 'range']+kappa_char_range.tolist()
df.loc[len(df)] = l

kappa_char = [cost_char(phi_b, eta_char_b, rho_b, xi_char_b, i, omega_char_b) for i in kappa_char_range]
l = ['kappa', 'char', 'cost']+kappa_char
df.loc[len(df)] = l

kappa_char_perch = [((i-kappa_char_b)/kappa_char_b)*100 for i in kappa_char_range]
l = ['kappa', 'char', 'perch']+kappa_char_perch
df.loc[len(df)] = l

ax.plot(kappa_char_perch, kappa_char, color='firebrick', marker='^')

# omega
## BECCS
omega_beccs_range = np.linspace(omega_beccs_l, omega_beccs_h, 10)
l = ['omega', 'beccs', 'range']+omega_beccs_range.tolist()
df.loc[len(df)] = l

omega_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, i, xi_beccs_b) for i in omega_beccs_range]
l = ['omega', 'beccs', 'cost']+omega_beccs
df.loc[len(df)] = l

omega_beccs_perch = [((i-omega_beccs_b)/omega_beccs_b)*100 for i in omega_beccs_range]
ax.plot(omega_beccs_perch, omega_beccs, color='darkred', label = 'operational costs')
ax.scatter(omega_beccs_perch, omega_beccs, color='darkred', marker='s')

## burial
omega_bur_range = np.linspace(omega_bur_l, omega_bur_h, 10)
l = ['omega', 'bur', 'range']+omega_bur_range.tolist()
df.loc[len(df)] = l

omega_bur = [cost_bur(phi_b, alpha_b, x_bur_b, eta_bur_b, rho_b, kappa_bur_b, i) for i in omega_bur_range]
l = ['omega', 'bur', 'cost']+omega_bur
df.loc[len(df)] = l

omega_bur_perch = [((i-omega_bur_b)/omega_bur_b)*100 for i in omega_bur_range]
l = ['omega', 'bur', 'perch']+alpha_beccs
df.loc[len(df)] = l

ax.plot(omega_bur_perch, omega_bur, color='darkred', marker='o')

## biochar
omega_char_range = np.linspace(omega_char_b-20, omega_char_b+20, 10)
l = ['omega', 'char', 'range']+omega_char_range.tolist()
df.loc[len(df)] = l

omega_char = [cost_char(phi_b, eta_char_b, rho_b, xi_char_b, kappa_char_b, i) for i in omega_char_range]
l = ['omega', 'char', 'cost']+omega_char
df.loc[len(df)] = l

omega_char_perch = [((i-omega_char_b)/omega_char_b)*100 for i in omega_char_range]
l = ['omega', 'char', 'perch']+omega_char_perch
df.loc[len(df)] = l

ax.plot(omega_char_perch, omega_char, color='darkred', marker='^')

## pileburn
omega_pb_range = np.linspace(omega_pb_l, omega_pb_h, 10)
l = ['omega', 'pb', 'range']+omega_pb_range.tolist()
df.loc[len(df)] = l

omega_pb = [cost_pb(phi_b, i) for i in omega_pb_range]
l = ['omega', 'pb', 'cost']+omega_pb

omega_pb_perch = [((i-omega_pb_b)/omega_pb_b)*100 for i in omega_pb_range]
l = ['omega', 'pb', 'perch']+omega_pb_perch
df.loc[len(df)] = l

ax.plot(omega_pb_perch, omega_pb, color='darkred', marker='x')

# carbon efficiency
## BECCS
eta_beccs_range = np.linspace(eta_beccs_l, eta_beccs_h, 10)
l = ['eta', 'beccs', 'range']+eta_beccs_range.tolist()
df.loc[len(df)] = l

eta_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, i, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in eta_beccs_range]
l = ['eta', 'beccs', 'cost']+eta_beccs
df.loc[len(df)] = l

eta_beccs_perch = [((i-eta_beccs_b)/eta_beccs_b)*100 for i in eta_beccs_range]
l = ['eta', 'beccs', 'perch']+eta_beccs_perch
df.loc[len(df)] = l

ax.plot(eta_beccs_perch, eta_beccs, color='lightsteelblue', label='carbon efficiency')
ax.scatter(eta_beccs_perch, eta_beccs, color='lightsteelblue', marker='s')

## burial
eta_bur_range = np.linspace(eta_bur_l, eta_bur_h, 10)
l = ['eta', 'bur', 'range']+eta_bur_range.tolist()
df.loc[len(df)] = l

eta_bur = [cost_bur(phi_b, alpha_b, x_bur_b, i, rho_b, kappa_bur_b, omega_bur_b) for i in eta_bur_range]
l = ['eta', 'bur', 'cost']+eta_bur
df.loc[len(df)] = l

eta_bur_perch = [((i-eta_bur_b)/eta_bur_b)*100 for i in eta_bur_range]
l = ['eta', 'bur', 'perch']+eta_bur_perch
df.loc[len(df)] = l

ax.plot(eta_bur_perch, eta_bur, color='lightsteelblue', marker='o')

## biochar
eta_char_range = np.linspace(eta_char_l, eta_char_h, 10)
l = ['eta', 'char', 'range']+eta_char_range.tolist()
df.loc[len(df)] = l

eta_char = [cost_char(phi_b, i, rho_b, xi_char_b, kappa_char_b, omega_char_b) for i in eta_char_range]
l = ['eta', 'char', 'cost']+eta_char
df.loc[len(df)] = l

eta_char_perch = [((i-eta_char_b)/eta_char_b)*100 for i in eta_char_range]
l = ['eta', 'char', 'perch']+eta_char_perch
df.loc[len(df)] = l

ax.plot(eta_char_perch, eta_char, color='lightsteelblue', marker='^')

# rho
rho_range = np.linspace(rho_l, rho_h, 10)
l = ['rho', 'na', 'range']+rho_range.tolist()
df.loc[len(df)] = l

rho_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, i, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in rho_range]
l = ['rho', 'beccs', 'cost']+rho_beccs
df.loc[len(df)] = l

rho_bur = [cost_bur(phi_b, alpha_b, x_bur_b, eta_bur_b, i, kappa_bur_b, omega_bur_b) for i in rho_range]
l = ['rho', 'bur', 'cost']+rho_bur
df.loc[len(df)] = l

rho_char = [cost_char(phi_b, eta_char_b, i, xi_char_b, kappa_char_b, omega_char_b) for i in rho_range]
l = ['rho', 'char', 'cost']+rho_char
df.loc[len(df)] = l

rho_perch = [((i-rho_b)/rho_b)*100 for i in rho_range]
l = ['rho', 'na', 'perch']+rho_perch
df.loc[len(df)] = l

ax.plot(rho_perch, rho_beccs, color='cornflowerblue', label='carbon credit price')
ax.scatter(rho_perch, rho_beccs, color='cornflowerblue', marker='s')
ax.plot(rho_perch, rho_bur, color='cornflowerblue', marker='o')
ax.plot(rho_perch, rho_char, color='cornflowerblue', marker='^')

# xi
## BECCS
xi_beccs_range = np.linspace(xi_beccs_l, xi_beccs_h, 10)
l = ['xi', 'beccs', 'range']+xi_beccs_range.tolist()
df.loc[len(df)] = l

xi_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, i) for i in xi_beccs_range]
l = ['xi', 'beccs', 'cost']+xi_beccs
df.loc[len(df)] = l

xi_beccs_perch = [((i-xi_beccs_b)/xi_beccs_b)*100 for i in xi_beccs_range]
l = ['xi', 'beccs', 'perch']+xi_beccs_perch
df.loc[len(df)] = l

ax.plot(xi_beccs_perch, xi_beccs, color='darkblue', label = 'salable product price')
ax.scatter(xi_beccs_perch, xi_beccs, color='darkblue', marker='s')

## biochar
xi_char_range = np.linspace(xi_char_l, xi_char_h, 10)
l = ['xi', 'char', 'range']+xi_char_range.tolist()
df.loc[len(df)] = l

xi_char = [cost_char(phi_b, eta_char_b, rho_b, i, kappa_char_b, omega_char_b) for i in xi_char_range]
l = ['xi', 'char', 'cost']+xi_char
df.loc[len(df)] = l

xi_char_perch = [((i-xi_char_b)/xi_char_b)*100 for i in xi_char_range]
l = ['xi', 'char', 'perch']+xi_char_perch
df.loc[len(df)] = l

ax.plot(xi_char_perch, xi_char, color='darkblue', marker='^')

plot_symbols = []
base_beccs = cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b)
s1, = ax.plot(0, base_beccs, color='black', marker='s')
base_bur = cost_bur(phi_b, alpha_b, x_bur_b, eta_bur_b, rho_b, kappa_bur_b, omega_bur_b)
s2, = ax.plot(0, base_bur, color='black', marker='o')
base_char = cost_char(phi_b, eta_char_b, rho_b, xi_char_b, kappa_char_b, omega_char_b)
s3, = ax.plot(0, base_char, color='black', marker='^')
base_pb = cost_pb(phi_b, omega_pb_b)
s4, = ax.plot(0, base_pb, color='black', marker='x')
plot_symbols.append([s1, s2, s3, s4])
legend2 = plt.legend(plot_symbols[0], ['BECCS', 'Burial', 'Biochar', 'Pile Burn'], loc=3, fontsize='small')
print(f'Base burial= {base_bur}')
print(f'Base BECCS= {base_beccs}')
print(f'Base char= {base_char}')
print(f'Base pile burn = {base_pb}')

ax.axvline(0, color='black', linewidth=0.5)
ax.axhline(0, color='black', linewidth=0.5)
ax.grid(True, color='silver', linewidth = 0.25)
ax.set_xlabel('Change in parameter (% from base)')
ax.set_ylabel('Cost ($ MTCO₂eᵢ⁻¹)')

plt.legend(loc=4)
plt.gca().add_artist(legend2)
plt.savefig(save_path+'/tea_v10_lin_sens_analysis_oneway.png', dpi=300)
plt.show()

df.to_excel(save_path+"/tea_v10_lin_sens_analysis_oneway.xlsx", index=False)


#%% Sensitivity analysis, 4 panels
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(7.5, 7), sharex=True, sharey=True, layout='constrained')

color_map ={
    'phi': 'XKCD:pinkish grey',
    'alpha': 'lightcoral',
    'x': 'indianred',
    'kappa': 'firebrick',
    'omega': 'XKCD:mahogany',
    'eta': 'lightsteelblue',
    'rho': 'cornflowerblue',
    'xi': 'darkblue'
    }

symbols ={
    'phi': '.',
    'alpha': '.',
    'x': '.',
    'kappa': '.',
    'omega': '.',
    'eta': '^',
    'rho': '^',
    'xi': '^'
    }

labels ={
    'phi': 'φ, forestry cost',
    'alpha': 'α, cost/transport. dist.',
    'x': 'x, transport. dist',
    'kappa': 'κ, capital expenditure',
    'omega': 'ω, operational expenditure',
    'eta': 'η, carbon efficiency',
    'rho': 'ρ, carbon credit price',
    'xi': 'ξ, salable product price'
    }

# phi: forest processes
var= 'phi'
phi_range = np.linspace(phi_l, phi_h, 10)
phi_perch = [((i-phi_b)/phi_b)*100 for i in phi_range]

phi_beccs = [cost_beccs(i, alpha_b, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in phi_range]
phi_bur = [cost_bur(i, alpha_b, x_bur_b, eta_bur_b, rho_b, kappa_bur_b, omega_bur_b) for i in phi_range]
phi_char = [cost_char(i, eta_char_b, rho_b, xi_char_b, kappa_char_b, omega_char_b) for i in phi_range]
phi_pb = [cost_pb(i, omega_pb_b) for i in phi_range]

ax2.plot(phi_perch, phi_beccs, color=color_map[var], label=labels[var], marker=symbols[var], zorder=3)
ax1.plot(phi_perch, phi_bur, color=color_map[var], marker=symbols[var], zorder=3)
ax3.plot(phi_perch, phi_char, color=color_map[var], marker=symbols[var], zorder=3)
ax4.plot(phi_perch, phi_pb, color=color_map[var], marker=symbols[var], zorder=3)

# alpha: transportation cost
var = 'alpha'
alpha_range = np.linspace(alpha_l, alpha_h, 10)
alpha_beccs = [cost_beccs(phi_b, i, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in alpha_range]
alpha_bur = [cost_bur(phi_b, i, x_bur_b, eta_bur_b, rho_b, kappa_bur_b, omega_bur_b) for i in alpha_range]
alpha_perch = [((i-alpha_b)/alpha_b)*100 for i in alpha_range]

ax2.plot(alpha_perch, alpha_beccs, color=color_map[var], label=labels[var], marker=symbols[var], zorder=3)
ax1.plot(alpha_perch, alpha_bur, color=color_map[var], marker=symbols[var])

# transportation distance
var = 'x'
## BECCS
x_beccs_range = np.linspace(x_beccs_l, x_beccs_h, 10)
x_beccs = [cost_beccs(phi_b, alpha_b, i, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in x_beccs_range]
x_beccs_perch = [((i-x_beccs_b)/x_beccs_b)*100 for i in x_beccs_range]
ax2.plot(x_beccs_perch, x_beccs, color=color_map[var], label=labels[var], marker=symbols[var])

## burial
x_bur_range = np.linspace(x_bur_l, x_bur_h, 10)
x_bur = [cost_bur(phi_b, alpha_b, i, eta_bur_b, rho_b, kappa_bur_b, omega_bur_b) for i in x_bur_range]
x_bur_perch = [((i-x_bur_b)/x_bur_b)*100 for i in x_bur_range]
ax1.plot(x_bur_perch, x_bur, color=color_map[var], marker=symbols[var])

# kappa
var = 'kappa'
## BECCS
kappa_beccs_range = np.linspace(kappa_beccs_l, kappa_beccs_h, 10)
kappa_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, rho_b, i, omega_beccs_b, xi_beccs_b) for i in kappa_beccs_range]
kappa_beccs_perch = [((i-kappa_beccs_b)/kappa_beccs_b)*100 for i in kappa_beccs_range]
ax2.plot(kappa_beccs_perch, kappa_beccs, color=color_map[var], label=labels[var], marker=symbols[var])

## burial
kappa_bur_range = np.linspace(kappa_bur_l, kappa_bur_h, 10)
kappa_bur = [cost_bur(phi_b, alpha_b, x_bur_b, eta_bur_b, rho_b, i, omega_bur_b) for i in kappa_bur_range]
kappa_bur_perch = [((i-kappa_bur_b)/kappa_bur_b)*100 for i in kappa_bur_range]
ax1.plot(kappa_bur_perch, kappa_bur, color=color_map[var], marker=symbols[var])

## biochar
kappa_char_range = np.linspace(kappa_char_b-10, kappa_char_b+10, 10)
kappa_char = [cost_char(phi_b, eta_char_b, rho_b, xi_char_b, i, omega_char_b) for i in kappa_char_range]
kappa_char_perch = [((i-kappa_char_b)/kappa_char_b)*100 for i in kappa_char_range]
ax3.plot(kappa_char_perch, kappa_char, color=color_map[var], marker=symbols[var])

# omega
var = 'omega'
## BECCS
omega_beccs_range = np.linspace(omega_beccs_l, omega_beccs_h, 10)
omega_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, i, xi_beccs_b) for i in omega_beccs_range]
omega_beccs_perch = [((i-omega_beccs_b)/omega_beccs_b)*100 for i in omega_beccs_range]
ax2.plot(omega_beccs_perch, omega_beccs, color=color_map[var], label=labels[var], marker=symbols[var])

## burial
omega_bur_range = np.linspace(omega_bur_l, omega_bur_h, 10)
omega_bur = [cost_bur(phi_b, alpha_b, x_bur_b, eta_bur_b, rho_b, kappa_bur_b, i) for i in omega_bur_range]
omega_bur_perch = [((i-omega_bur_b)/omega_bur_b)*100 for i in omega_bur_range]
ax1.plot(omega_bur_perch, omega_bur, color=color_map[var], marker=symbols[var])

## biochar
omega_char_range = np.linspace(omega_char_b-20, omega_char_b+20, 10)
omega_char = [cost_char(phi_b, eta_char_b, rho_b, xi_char_b, kappa_char_b, i) for i in omega_char_range]
omega_char_perch = [((i-omega_char_b)/omega_char_b)*100 for i in omega_char_range]
ax3.plot(omega_char_perch, omega_char, color=color_map[var], marker=symbols[var])

## pileburn
omega_pb_range = np.linspace(omega_pb_l, omega_pb_h, 10)
omega_pb = [cost_pb(phi_b, i) for i in omega_pb_range]
omega_pb_perch = [((i-omega_pb_b)/omega_pb_b)*100 for i in omega_pb_range]
ax4.plot(omega_pb_perch, omega_pb, color=color_map[var], marker=symbols[var])

# carbon efficiency
var = 'eta'
## BECCS
eta_beccs_range = np.linspace(eta_beccs_l, eta_beccs_h, 10)
eta_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, i, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in eta_beccs_range]
eta_beccs_perch = [((i-eta_beccs_b)/eta_beccs_b)*100 for i in eta_beccs_range]
ax2.plot(eta_beccs_perch, eta_beccs, color=color_map[var], label=labels[var], marker=symbols[var], ms=3, zorder=4)

## burial
eta_bur_range = np.linspace(eta_bur_l, eta_bur_h, 10)
eta_bur = [cost_bur(phi_b, alpha_b, x_bur_b, i, rho_b, kappa_bur_b, omega_bur_b) for i in eta_bur_range]
eta_bur_perch = [((i-eta_bur_b)/eta_bur_b)*100 for i in eta_bur_range]
ax1.plot(eta_bur_perch, eta_bur, color=color_map[var], marker=symbols[var], ms=3, zorder=4)

## biochar
eta_char_range = np.linspace(eta_char_l, eta_char_h, 10)
eta_char = [cost_char(phi_b, i, rho_b, xi_char_b, kappa_char_b, omega_char_b) for i in eta_char_range]
eta_char_perch = [((i-eta_char_b)/eta_char_b)*100 for i in eta_char_range]
ax3.plot(eta_char_perch, eta_char, color=color_map[var], marker=symbols[var], ms=3, zorder=4)

# rho
var = 'rho'
rho_range = np.linspace(rho_l, rho_h, 10)
rho_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, i, kappa_beccs_b, omega_beccs_b, xi_beccs_b) for i in rho_range]
rho_bur = [cost_bur(phi_b, alpha_b, x_bur_b, eta_bur_b, i, kappa_bur_b, omega_bur_b) for i in rho_range]
rho_char = [cost_char(phi_b, eta_char_b, i, xi_char_b, kappa_char_b, omega_char_b) for i in rho_range]
rho_perch = [((i-rho_b)/rho_b)*100 for i in rho_range]

ax2.plot(rho_perch, rho_beccs, color=color_map[var], label=labels[var], marker=symbols[var], ms=3, zorder=3)
ax1.plot(rho_perch, rho_bur, color=color_map[var], marker=symbols[var], ms=3)
ax3.plot(rho_perch, rho_char, color=color_map[var], marker=symbols[var], ms=3)

# xi
var = 'xi'
## BECCS
xi_beccs_range = np.linspace(xi_beccs_l, xi_beccs_h, 10)
xi_beccs = [cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, i) for i in xi_beccs_range]
xi_beccs_perch = [((i-xi_beccs_b)/xi_beccs_b)*100 for i in xi_beccs_range]
ax2.plot(xi_beccs_perch, xi_beccs, color=color_map[var], label=labels[var], marker=symbols[var], ms=3)

## biochar
xi_char_range = np.linspace(xi_char_l, xi_char_h, 10)
xi_char = [cost_char(phi_b, eta_char_b, rho_b, i, kappa_char_b, omega_char_b) for i in xi_char_range]
xi_char_perch = [((i-xi_char_b)/xi_char_b)*100 for i in xi_char_range]
ax3.plot(xi_char_perch, xi_char, color=color_map[var], marker=symbols[var], ms=3)

"""
plot_symbols = []
base_beccs = cost_beccs(phi_b, alpha_b, x_beccs_b, eta_beccs_b, rho_b, kappa_beccs_b, omega_beccs_b, xi_beccs_b)
s1, = ax4.plot(0, base_beccs, color='black', marker='s', ms=5)
base_bur = cost_bur(phi_b, alpha_b, x_bur_b, eta_bur_b, rho_b, kappa_bur_b, omega_bur_b)
s2, = ax4.plot(0, base_bur, color='black', marker='o', ms=5)
base_char = cost_char(phi_b, eta_char_b, rho_b, xi_char_b, kappa_char_b, omega_char_b)
s3, = ax4.plot(0, base_char, color='black', marker='^', ms=3)
base_pb = omega_pb_b
s4, = ax4.plot(0, base_pb, color='black', marker='x', ms=5)
plot_symbols.append([s1, s2, s3, s4])
legend2 = ax4.legend(plot_symbols[0], ['BECCS', 'Burial', 'Biochar', 'Pile Burn'], loc=4, fontsize='small')
"""

for ax in [ax1, ax2, ax3, ax4]:
    ax.axvline(0, color='black', linewidth=1)
    ax.axhline(0, color='black', linewidth=1)
    ax.grid(True, color='silver', linewidth = 0.5)
    #ax.scatter(0, base_beccs, color='black', marker='s', s=14, zorder=5)
    #ax.scatter(0, base_bur, color='black', marker='o', s=14, zorder=5)
    #ax.scatter(0, base_char, color='black', marker='^', s=5, zorder=5)
    #ax.scatter(0, base_pb, color='black', marker='x', s=9, zorder=5)
    ax.axhline(base_beccs, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
    ax.axhline(base_bur, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
    ax.axhline(base_char, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
    ax.axhline(base_pb, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
ax3.set_xlabel('Change in parameter (% from base)')
ax3.set_ylabel('Net Income ($ MTCO₂eᵢ⁻¹)')
ax2.axhline(base_beccs, color='dimgrey', linestyle='dashed', zorder=0, linewidth=1)
ax1.axhline(base_bur, color='dimgrey', linestyle='dashed', zorder=0, linewidth=1)
ax3.axhline(base_char, color='dimgrey',  linestyle='dashed', zorder=0, linewidth=1)
ax4.axhline(base_pb, color='dimgrey',  linestyle='dashed', zorder=0, linewidth=1)
ax2.scatter(0, base_beccs, color='black', marker='o', s=14, zorder=5)
ax1.scatter(0, base_bur, color='black', marker='o', s=14, zorder=5)
ax3.scatter(0, base_char, color='black', marker='o', s=14, zorder=5)
ax4.scatter(0, base_pb, color='black', marker='o', s=14, zorder=5)

ax1.set_title('A. Burial')
ax2.set_title('B. BECCS')
ax3.set_title('C. Biochar')
ax4.set_title('D. Pile Burn')

#ax1.yaxis.set_inverted(True)
#ax2.yaxis.set_inverted(True)
#ax3.yaxis.set_inverted(True)
#ax4.yaxis.set_inverted(True)

ax2.legend(loc=1, fontsize='small')
#plt.gca().add_artist(legend2)
plt.savefig(save_path+'/tea_v10_lin_sens_analysis_4_pan_oneway.png', dpi=300)
plt.savefig(save_path+'/tea_v10_lin_sens_analysis_4_pan_oneway.svg')
plt.show()

#%% biochar inset
fig, ax = plt.subplots(figsize=(2, 1.5), layout='constrained')

# phi
ax.plot(phi_perch, phi_char, color='XKCD:pinkish grey', marker='.', zorder=3)

# kappa
ax.plot(kappa_char_perch, kappa_char, color='firebrick', marker='.')

# omega
ax.plot(omega_char_perch, omega_char, color='XKCD:mahogany', marker='.')

# carbon efficiency
ax.plot(eta_char_perch, eta_char, color='lightsteelblue', marker='^', ms=3, zorder=4)

# rho
ax.plot(rho_perch, rho_char, color='cornflowerblue', marker='^', ms=3)

# xi
ax.plot(xi_char_perch, xi_char, color='darkblue', marker='^', ms=3)


ax.axvline(0, color='black', linewidth=1)
ax.axhline(0, color='black', linewidth=1)
ax.grid(True, color='silver', linewidth = 0.5)
ax.axhline(base_beccs, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
ax.axhline(base_bur, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
ax.axhline(base_char, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
ax.axhline(base_pb, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)

ax.set_xlim(-75, 60)
ax.set_ylim(-25, 25)
ax.axhline(base_char, color='dimgrey',  linestyle='dashed', zorder=0, linewidth=1)
ax.scatter(0, base_char, color='black', marker='o', s=14, zorder=5)

#ax.yaxis.set_inverted(True)

plt.savefig(save_path+'/tea_v10_lin_sens_analysis_4_pan_char_sub_oneway.png', dpi=300)
plt.savefig(save_path+'/tea_v10_lin_sens_analysis_4_pan_char_sub_oneway.svg')
plt.show()

#%% burial inset
fig, ax = plt.subplots(figsize=(2, 1.5), layout='constrained')

# phi
ax.plot(phi_perch, phi_bur, color='XKCD:pinkish grey', marker='.', zorder=3)

# alpha
ax.plot(alpha_perch, alpha_bur, color='lightcoral', marker='.')

# x
ax.plot(x_bur_perch, x_bur, color='indianred', marker='.')

# kappa
ax.plot(kappa_bur_perch, kappa_bur, color='firebrick', marker='.')

# omega
ax.plot(omega_bur_perch, omega_bur, color='XKCD:mahogany', marker='^', ms=3)

# carbon efficiency
ax.plot(eta_bur_perch, eta_bur, color='lightsteelblue', marker='^', ms=3, zorder=4)

# rho
ax.plot(rho_perch, rho_bur, color='cornflowerblue', marker='^', ms=3)


ax.axvline(0, color='black', linewidth=1)
ax.axhline(0, color='black', linewidth=1)
ax.grid(True, color='silver', linewidth = 0.5)
ax.axhline(base_beccs, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
ax.axhline(base_bur, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
ax.axhline(base_char, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)
ax.axhline(base_pb, color='dimgrey', alpha=0.4, linestyle='dashed', zorder=0, linewidth=1)

ax.set_xlim(-100, 200)
ax.set_ylim(-25, 50)
ax.axhline(base_bur, color='dimgrey',  linestyle='dashed', zorder=0, linewidth=1)
ax.scatter(0, base_bur, color='black', marker='o', s=14, zorder=5)

#ax.yaxis.set_inverted(True)

plt.savefig(save_path+'/tea_v10_lin_sens_analysis_4_pan_bur_sub_oneway.png', dpi=300)
plt.savefig(save_path+'/tea_v10_lin_sens_analysis_4_pan_bur_sub_oneway.svg')
plt.show()


#%% "best" and "worst" case scenarios
best_bur = cost_bur(phi_l, alpha_l, x_bur_l, eta_bur_h, rho_h, kappa_bur_l, omega_bur_l)
print(f'Burial best case: ${best_bur:.3f} MTCO2ei-1')
worst_bur = cost_bur(phi_h, alpha_h, x_bur_h, eta_bur_l, rho_l, kappa_bur_h, omega_bur_h)
print(f'Burial worst case: ${worst_bur:.3f} MTCO2ei-1')

best_beccs = cost_beccs(phi_l, alpha_l, x_beccs_l, eta_beccs_h, rho_h, kappa_beccs_l, omega_beccs_l, xi_beccs_h)
print(f'BECCS best case: ${best_beccs:.3f} MTCO2ei-1')
worst_beccs = cost_beccs(phi_h, alpha_h, x_beccs_h, eta_beccs_l, rho_l, kappa_beccs_h, omega_beccs_h, xi_beccs_l)
print(f'BECCS worst case: ${worst_beccs:.3f} MTCO2ei-1')

best_char = cost_char(phi_l, eta_char_h, rho_h, xi_char_h, kappa_char_b-10, omega_char_b-20)
print(f'Biochar best case: ${best_char:.3f} MTCO2ei-1')
worst_char = cost_char(phi_h, eta_char_l, rho_l, xi_char_l, kappa_char_b+10, omega_char_b+20)
print(f'Biochar worst case: ${worst_char:.3f} MTCO2ei-1')
best_char_insitu = cost_char(phi_l, eta_char_h, rho_h, 0, kappa_char_b-10, omega_char_b-20)
print(f'Biochar best case in situ: ${best_char_insitu:.3f} MTCO2ei-1')
insitu_char = cost_char(phi_b, eta_char_b, rho_b, 0, kappa_char_b-10, omega_char_b-20)
print(f'Biochar base case in situ: ${insitu_char:.3f} MTCO2ei-1')

best_pb = cost_pb(phi_l, omega_pb_l)
print(f'Pile burn best case: ${best_pb:.3f} MTCO2ei-1')
worst_pb = cost_pb(phi_h, omega_pb_h)
print(f'Pile burn worst case: ${worst_pb:.3f} MTCO2ei-1')








