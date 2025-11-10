#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 14:50:33 2024

@author: leahclayton
"""

import requests
import os
import zipfile

# Create a function to download and extract files
def download_and_extract(url):
    response = requests.get(url)
    if response.status_code == 200:
        # Get the file name from the URL
        file_name = url.split('/')[-1]
        with open(file_name, 'wb') as f:
            f.write(response.content)
        
        # Unzip the downloaded file
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            # Extract tif file
            for file in zip_ref.namelist():
                if file.endswith('.tif'):
                    zip_ref.extract(file)
                    # Rename the extracted tif file
                    os.rename(file, f'{file.split(".")[0][3:]}.tif')
                    
        # Remove the downloaded zip file after extraction
        os.remove(file_name)

# Function to generate URLs based on the given criteria
def generate_urls():
    urls = []
    for year in range(2000, 2022):
        days = 366 if year % 4 == 0 else 365
        for day in range(1, days + 1):
            day_str = str(day).zfill(3)
            urls.append(f'https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/uswem/web/conus/eta/modis_eta/daily/downloads/det{year}{day_str}.modisSSEBopETactual.zip')
    return urls

# Create a folder for extracted tif files
folder_name = '/home/lkc33/palmer_scratch/ssebop_daily'
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

os.chdir(folder_name)

# Download and extract files
urls = generate_urls()
for url in urls:
    download_and_extract(url)
    print(f'Downloaded and extracted: {url}')

# Move extracted tif files to the SSEBop Daily ET Data folder
for file in os.listdir():
    if file.endswith('.tif'):
        os.rename(file, os.path.join(folder_name, file))