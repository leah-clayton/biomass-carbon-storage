# biomass-carbon-storage
Code for the model and visualizations "Near-term, geospatial opportunity for biomass carbon storage to address the wildfire and climate crises" by Leah K. Clayton, Alexander S. Wyckoff, and Sinéad M. Crotty.

Code was written and compiled by Leah K. Clayton (leah.clayton@cclab.org)

## Implementation diagram
*(zoom in to read)*
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

### Additional publicly available data
Boiko, O., Kagone, S., & Senay, G. (2021). Soil properties dataset in the United States [Dataset]. U.S. Geological Survey. https://doi.org/10.5066/P9TI3IS8

Hengl, T., Jesus, J. M. de, Heuvelink, G. B. M., Gonzalez, M. R., Kilibarda, M., Blagotić, A., Shangguan, W., Wright, M. N., Geng, X., Bauer-Marschallinger, B., Guevara, M. A., Vargas, R., MacMillan, R. A., Batjes, N. H., Leenaars, J. G. B., Ribeiro, E., Wheeler, I., Mantel, S., & Kempen, B. (2017). SoilGrids250m: Global gridded soil information based on machine learning. PLOS ONE, 12(2), e0169748. https://doi.org/10.1371/journal.pone.0169748

Pett-Ridge, J., Kuebbing, S., Mayer, A., Hovorka, S., Pilorgé, H., Baker, S., Pang, S., Scown, C., Mayfield, K., Wong, A., Aines, R., Ammar, H., Aui, A., Ashton, M., Basso, B., Bradford, M., Bump, A., Busch, I., Calzado, E., … Zhang, Y. (2023). Roads to Removal: Options for Carbon Dioxide Removal in the United States (No. LLNL--TR-852901, 2301853, 1080440; p. LLNL--TR-852901, 2301853, 1080440). https://doi.org/10.2172/2301853

Senay, G. B., & Kagone, S. (2019). Daily SSEBop Evapotranspiration: U. S. Geological Survey Data Release [Dataset]. U.S. Geological Survey. https://doi.org/10.5066/P9L2YMV

Soil Survey Staff. Gridded National Soil Survey Geographic (gNATSGO) Database for the Conterminous United States. United States Department of Agriculture, Natural Resources Conservation Service. Available online at https://nrcs.app.box.com/v/soils. December 19, 2023 (FY2024 official release).

Thornton, M. M., Shrestha, R., Wei, Y., Thornton, P. E., &amp; Kao, S.-C. (2022). <i>Daymet: Daily Surface Weather Data on a 1-km Grid for North America, Version 4 R1</i> (Version 4.1). ORNL Distributed Active Archive Center. https://doi.org/10.3334/ORNLDAAC/2129

United States Geological Survey. (2024). Annual NLCD Collection 1 Science Products [U.S. Geological Survey data release]. https://doi.org/10.5066/P94UXNTS

United States Geological Survey. (2025). Protected Areas Database of the United States (PAD-US) 4 [Dataset]. U.S. Geological Survey. https://doi.org/10.5066/P96WBCHS

Zell, W. O., & Sanford, W. E. (2020). MODFLOW 6 models used to simulate the long-term average surficial groundwater system for the contiguous United States. U.S. Geological Survey. https://doi.org/10.5066/P91LFFN1
