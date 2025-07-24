import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.patches as mpatches
import numpy as np

# Step 1: Load the shapefiles
boundaries = gpd.read_file('study_area.shp')  # Administrative boundaries
buildings = gpd.read_file('buildings.shp')    # Building polygons

# Ensure both shapefiles have the same coordinate reference system (CRS)
if boundaries.crs != buildings.crs:
    buildings = buildings.to_crs(boundaries.crs)

# Step 2: Count buildings in each boundary
# Perform a spatial join to associate buildings with boundaries
joined = gpd.sjoin(buildings, boundaries, how='left', predicate='within')

# Count buildings per boundary
building_counts = joined.groupby('index_right').size()
boundaries['building_count'] = boundaries.index.map(building_counts).fillna(0)

# Step 3: Create a choropleth map
fig, ax = plt.subplots(figsize=(12, 8))

# Define a colormap (e.g., viridis) and normalize it based on building counts
cmap = plt.cm.viridis
norm = Normalize(vmin=boundaries['building_count'].min(), 
                 vmax=boundaries['building_count'].max())

# Plot boundaries with colors based on building count
boundaries.plot(column='building_count', cmap=cmap, norm=norm, ax=ax, 
                edgecolor='black', linewidth=0.5)

# Remove axis ticks for a cleaner look
ax.set_axis_off()

# Step 4: Create a fancy legend (colorbar with custom styling)
sm = ScalarMappable(cmap=cmap, norm=norm)
cbar = plt.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label('Number of Buildings', fontsize=12, weight='bold')
cbar.outline.set_linewidth(1.5)
cbar.ax.tick_params(labelsize=10)

# Add a title
plt.title('Building Density by Administrative Boundary', fontsize=16, weight='bold', pad=20)

# Optional: Add a background for the legend (fancy touch)
cbar.ax.set_frame_on(True)
cbar.ax.set_facecolor('#f5f5f5')  # Light gray background for legend

# Save the map
plt.savefig('building_density_map.png', dpi=300, bbox_inches='tight')
plt.show()
