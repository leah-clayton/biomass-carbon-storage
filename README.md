# biomass-burial
Code for the model and visualizations in {paper citation}, in preparation

## Implementation diagram
(Zoom in to read)
<img width="6545" height="6040" alt="code_infrastructure_nov2025" src="https://github.com/user-attachments/assets/7925d567-7488-4cbb-833e-94ea42d62236" />

## Requirements
### Python version
The model was designed and run in 2023-2025 using Python 3.11 and 3.12

### Dependencies
- bottleneck
- bs4
- cftime
- dask
- geopandas
- gdal
- matplotlib
- netCDF4
- networkx
- numpy
- osmnx
- pandas
- pydayment
- pyproj
- rasterio
- rioxarray
- scipy
- shapely
- xarray

### Computing
Most of the scripts are designed for high-performance computing due to their large memory requirements (up to 1TB) or time requirements (up to 5 days). Scripts designed for parallel processing are marked in the diagram with suggested configurations, but they can be adapted for a single processor.
