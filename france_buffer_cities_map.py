import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

# -------------------------------
# 1️⃣ Load real-world country polygons (Natural Earth 110m)
# -------------------------------
url_countries = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(url_countries)

# Rename relevant columns
rename_map = {
    "NAME": "name",
    "ISO_A3": "iso_a3",
    "CONTINENT": "continent",
    "POP_EST": "pop_est",
    "GDP_MD": "gdp_md"
}
world = world.rename(columns={k: v for k, v in rename_map.items() if k in world.columns})

# Keep only relevant columns + geometry
keep_cols = [v for v in rename_map.values()] + ["geometry"]
world = world[[col for col in keep_cols if col in world.columns]]

# -------------------------------
# 2️⃣ Load city points (Natural Earth 10m populated places)
# -------------------------------
url_cities = "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip"
cities = gpd.read_file(url_cities)

# Keep only city name + geometry + country
cities = cities[["NAME", "geometry", "ADM0NAME"]].rename(
    columns={"NAME": "city_name", "ADM0NAME": "country_name"}
)

# -------------------------------
# 2️⃣1 Filter cities to Europe countries only
# -------------------------------
europe_countries = world[world['continent'] == 'Europe']['name'].tolist()
cities = cities[cities['country_name'].isin(europe_countries)]

# -------------------------------
# 3️⃣ Filter for one country (France)
# -------------------------------
target_country = "France"
country = world[world["name"] == target_country]
if country.empty:
    raise ValueError(f"No country found with name {target_country}")
print(f"Selected country: {country.iloc[0]['name']}")

# -------------------------------
# 4️⃣ Project to Europe-centered CRS (EPSG:3035) for accurate distances
# -------------------------------
crs_europe = 3035  # Lambert Europe Equal Area
world_m = world.to_crs(epsg=crs_europe)
country_m = country.to_crs(epsg=crs_europe)
cities_m = cities.to_crs(epsg=crs_europe)

# -------------------------------
# 5️⃣ Create a 50 km buffer around France
# -------------------------------
buffer_distance = 50_000  # meters
country_buffer = country_m.copy()
country_buffer["geometry"] = country_m.geometry.buffer(buffer_distance)

# -------------------------------
# 6️⃣ Spatial join: cities within 50 km buffer
# -------------------------------
cities_within_buffer = gpd.sjoin(cities_m, country_buffer, predicate="within", how="inner")
print(f"Cities within 50 km of {target_country}:")
print(cities_within_buffer[["city_name"]])

# -------------------------------
# 6️⃣1 List cities within buffer but NOT in France + compute distance
# -------------------------------
non_france_cities = cities_within_buffer[cities_within_buffer['country_name'] != target_country].copy()
non_france_cities["distance_km"] = non_france_cities.geometry.apply(lambda x: country_m.geometry.distance(x).min() / 1000)

# Create sorted table
table = non_france_cities[["city_name", "country_name", "distance_km"]].sort_values("distance_km")
print("\nCities within 50 km buffer but not in France:")
print(table.to_string(index=False))

# -------------------------------
# Export table as PNG
# -------------------------------
fig_table, ax_table = plt.subplots(figsize=(8, len(table)*0.3 + 1))
ax_table.axis('off')
mpl_table = ax_table.table(
    cellText=table.round(2).values,
    colLabels=table.columns,
    cellLoc='center',
    loc='center'
)
mpl_table.auto_set_font_size(False)
mpl_table.set_fontsize(10)
mpl_table.auto_set_column_width(col=list(range(len(table.columns))))

# Header formatting
for key, cell in mpl_table.get_celld().items():
    if key[0] == 0:
        cell.set_text_props(weight='bold', color='white')
        cell.set_facecolor('#4CAF50')
    else:
        cell.set_facecolor('#f1f1f1' if key[0]%2==1 else 'white')

table_png_filename = f"non_france_cities_within_50km_{target_country.lower().replace(' ', '_')}.png"
plt.savefig(table_png_filename, dpi=300, bbox_inches='tight')
plt.close(fig_table)
print(f"\n Table exported as PNG: {table_png_filename}")

# -------------------------------
# 7️⃣ Visualization (Europe-centered, France zoom)
# -------------------------------
fig, ax = plt.subplots(figsize=(12, 10))
world_m.plot(ax=ax, color="lightgray", linewidth=0.5, edgecolor="white")
country_buffer.plot(color="lightgreen", alpha=0.5, ax=ax)
country_m.plot(color="lightblue", edgecolor="black", ax=ax)
cities_m.plot(color="red", markersize=20, ax=ax)
cities_within_buffer.plot(color="orange", markersize=50, ax=ax)

legend_elements = [
    mpatches.Patch(facecolor='lightblue', edgecolor='black', label='France'),
    mpatches.Patch(facecolor='lightgreen', label='50 km Buffer'),
    mpatches.Patch(facecolor='red', label='All Cities'),
    mpatches.Patch(facecolor='orange', label='Cities within 50 km')
]
ax.legend(handles=legend_elements)
ax.set_aspect('equal')

minx, miny, maxx, maxy = country_buffer.total_bounds
width = maxx - minx
height = maxy - miny
europe = world_m[world_m['continent'] == 'Europe']
center_x = europe.geometry.centroid.x.mean()
center_y = europe.geometry.centroid.y.mean()
ax.set_xlim(center_x - width/2, center_x + width/2)
ax.set_ylim(center_y - height/2, center_y + height/2)

ax.set_title(f"Cities within 50 km of {target_country} (Europe-centered)")
ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")

# Export map as PNG
png_filename = f"cities_within_50km_of_{target_country.lower().replace(' ', '_')}.png"
plt.savefig(png_filename, dpi=300, bbox_inches='tight')
plt.show()
print(f"\n Map exported as PNG: {png_filename}")

# -------------------------------
# 8️ Export results to GeoJSON
# -------------------------------
cities_within_buffer.to_file(f"cities_within_50km_of_{target_country.lower().replace(' ', '_')}.geojson", driver="GeoJSON")
country_buffer.to_file(f"{target_country.lower().replace(' ', '_')}_50km_buffer.geojson", driver="GeoJSON")

print(" Exported GeoJSON files:")
print(f" - cities_within_50km_of_{target_country.lower().replace(' ', '_')}.geojson")
print(f" - {target_country.lower().replace(' ', '_')}_50km_buffer.geojson")
