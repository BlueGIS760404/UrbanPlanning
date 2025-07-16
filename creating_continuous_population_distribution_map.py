import rasterio
import geopandas as gpd
import numpy as np
from rasterio.mask import mask
import matplotlib.pyplot as plt
from shapely.geometry import mapping

# Load the study area shapefile
study_area_path = "...path/boundary.shp"
study_area = gpd.read_file(study_area_path)

# Load the WorldPop raster
raster_path = "...path/raster.tif"
with rasterio.open(raster_path) as src:
    # Reproject study area if needed
    if study_area.crs != src.crs:
        study_area = study_area.to_crs(src.crs)

    # Clip the raster using the geometry
    geoms = [mapping(geom) for geom in study_area.geometry]
    clipped_raster, clipped_transform = mask(src, geoms, crop=True)
    clipped_meta = src.meta.copy()
    clipped_meta.update({
        "height": clipped_raster.shape[1],
        "width": clipped_raster.shape[2],
        "transform": clipped_transform
    })

# Remove invalid values
clipped_raster = clipped_raster[0]  # Remove band dimension if only one band
clipped_raster = np.ma.masked_where((clipped_raster <= 0) | (np.isnan(clipped_raster)), clipped_raster)

# Display raster with colorbar resized to match plot height
plt.figure(figsize=(10, 8))
img = plt.imshow(clipped_raster, cmap='viridis')
cbar = plt.colorbar(img, shrink=0.5)  # shrink controls colorbar height
cbar.set_label('Population Count')
plt.title("Clipped Population Raster (Tehran/Alborz)")
plt.xlabel("X")
plt.ylabel("Y")
plt.tight_layout()
plt.savefig('population_plot_2000.png', dpi=300, bbox_inches='tight')
plt.show()

# Optional: Print basic stats
print("Clipped Raster Statistics:")
print(f"  Min: {clipped_raster.min()}")
print(f"  Max: {clipped_raster.max()}")
print(f"  Mean: {clipped_raster.mean()}")
print(f"  Total population (approx): {clipped_raster.sum()}")
