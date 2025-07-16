import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
import geopandas as gpd

# Reload and clip the raster to ensure correct shape
raster_path = "...path/raster.tif"
study_area_path = "...path/boundary.shp"

# Load study area
study_area = gpd.read_file(study_area_path)

# Load raster and ensure CRS match
with rasterio.open(raster_path) as src:
    raster_crs = src.crs
    if study_area.crs != raster_crs:
        study_area = study_area.to_crs(raster_crs)
    
    # Clip raster to study area
    geoms = [mapping(geom) for geom in study_area.geometry]
    clipped_raster, clipped_transform = mask(src, geoms, crop=True, nodata=-9999)
    clipped_meta = src.meta.copy()
    clipped_meta.update({
        "height": clipped_raster.shape[1],
        "width": clipped_raster.shape[2],
        "transform": clipped_transform
    })

# Check shape of clipped raster
print("Clipped raster shape:", clipped_raster.shape)  # Should be (1, height, width)
clipped_data = clipped_raster[0]  # First band
print("Clipped data shape:", clipped_data.shape)  # Should be (height, width)

# Mask invalid values
clipped_data = np.ma.masked_where(clipped_data <= -9999, clipped_data)
clipped_data = np.ma.masked_invalid(clipped_data)

# If clipped_data is 1D, raise an error or reshape (if possible)
if clipped_data.ndim == 1:
    raise ValueError("Clipped raster is 1D. Check your study area shapefile or clipping process.")

# Define bins for classification (adjusted for Tehran-Alborz population density)
bins = [0, 50, 100, 500, 1000, np.max(clipped_data) + 1]  # Adjusted bins
labels = ['0-50', '50-100', '100-500', '500-1000', '>1000']
classified = np.digitize(clipped_data, bins, right=True)

# Create colormap
cmap = ListedColormap(['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#08306b'])

# Plot classified map
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(classified, cmap=cmap)
cbar = plt.colorbar(im, shrink=0.5, label='Population Density (people per km²)')
cbar.set_ticks(np.arange(len(labels)) + 0.5)
cbar.set_label(labels)
plt.title('Classified Population Density Map (2000)')
plt.axis('off')
plt.savefig('classified_population_density_map_2000.png', dpi=300, bbox_inches='tight')
plt.show()
