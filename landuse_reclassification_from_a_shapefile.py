import geopandas as gpd
import pandas as pd

# Step 1: Load your land use shapefile
# Replace with your actual shapefile path
gdf = gpd.read_file('landuse.shp')

# Step 2: Define detailed land use classification
landuse_mapping = {
    'residential': 'Residential',
    'commercial': 'Commercial',
    'retail': 'Commercial',
    'industrial': 'Industrial',
    'military': 'Military',
    'cemetery': 'Cemetery',

    'farmland': 'Agricultural',
    'farmyard': 'Agricultural',
    'orchard': 'Agricultural',
    'vineyard': 'Agricultural',
    'allotments': 'Agricultural',

    'park': 'Recreational',
    'recreation_ground': 'Recreational',

    'grass': 'Natural',
    'forest': 'Natural',
    'scrub': 'Natural',
    'meadow': 'Natural',
    'heath': 'Natural',
    'nature_reserve': 'Natural',

    'quarry': 'Extractive'
}

# Step 3: Apply mapping based on 'fclass' column
gdf['landuse_group'] = gdf['fclass'].map(landuse_mapping)

# Step 4: (Optional) Check for any unmapped values
unmapped = gdf[gdf['landuse_group'].isna()]['fclass'].unique()
if len(unmapped) > 0:
    print("Unmapped fclass values:", unmapped)

# Step 5: (Optional) Save the result to a new shapefile
gdf.to_file('landuse_categorized.shp')
