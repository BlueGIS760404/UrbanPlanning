import geopandas as gpd
import pandas as pd

# Step 1: Load your land use shapefile
gdf = gpd.read_file('landuse.shp')

# Step 2: Extract and display unique land use classes from 'fclass' column
unique_classes = gdf['fclass'].dropna().unique()
print("Available land use classes in shapefile:")
for cls in sorted(unique_classes):
    print(f" - {cls}")

# Step 3: Define a more comprehensive land use classification
landuse_mapping = {
    # Residential and urban
    'residential': 'Residential',
    'suburb': 'Residential',
    'neighbourhood': 'Residential',

    # Commercial and retail
    'commercial': 'Commercial',
    'retail': 'Commercial',
    'marketplace': 'Commercial',

    # Industrial
    'industrial': 'Industrial',
    'warehouse': 'Industrial',

    # Public/institutional/military
    'military': 'Military',
    'school': 'Public Facility',
    'university': 'Public Facility',
    'hospital': 'Public Facility',
    'cemetery': 'Cemetery',

    # Agricultural
    'farmland': 'Agricultural',
    'farmyard': 'Agricultural',
    'orchard': 'Agricultural',
    'vineyard': 'Agricultural',
    'allotments': 'Agricultural',
    'greenhouse_horticulture': 'Agricultural',
    'plant_nursery': 'Agricultural',

    # Natural/vegetated
    'grass': 'Natural',
    'forest': 'Natural',
    'scrub': 'Natural',
    'meadow': 'Natural',
    'heath': 'Natural',
    'fell': 'Natural',
    'moor': 'Natural',
    'wood': 'Natural',
    'nature_reserve': 'Natural',

    # Water-related
    'reservoir': 'Water',
    'basin': 'Water',
    'wetland': 'Water',
    'lake': 'Water',
    'pond': 'Water',

    # Recreational / Green urban areas
    'park': 'Recreational',
    'recreation_ground': 'Recreational',
    'pitch': 'Recreational',
    'sports_centre': 'Recreational',
    'stadium': 'Recreational',
    'golf_course': 'Recreational',
    'playground': 'Recreational',

    # Extractive or industrial
    'quarry': 'Extractive',
    'landfill': 'Extractive',
    'brownfield': 'Extractive',
    'construction': 'Construction',

    # Transport-related
    'railway': 'Transport',
    'railway_yard': 'Transport',
    'port': 'Transport',
    'aerodrome': 'Transport',

    # Others
    'religious': 'Religious',
    'place_of_worship': 'Religious'
}

# Step 4: Apply mapping based on 'fclass' column
gdf['landuse_group'] = gdf['fclass'].map(landuse_mapping)

# Step 5: Identify and print any unmapped values
unmapped = gdf[gdf['landuse_group'].isna()]['fclass'].dropna().unique()
if len(unmapped) > 0:
    print("\nUnmapped land use classes (consider adding to mapping):")
    for cls in sorted(unmapped):
        print(f" - {cls}")
else:
    print("\nAll land use classes successfully mapped.")

# Step 6: Save the result to a new shapefile
gdf.to_file('landuse_categorized.shp')
print("\n✅ Categorized shapefile saved as 'landuse_categorized.shp'")
