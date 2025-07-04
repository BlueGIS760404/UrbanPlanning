import geopandas as gpd
import pandas as pd
import folium
from shapely.geometry import Point, Polygon
import numpy as np
from jinja2 import Template

# Sample data creation for San Francisco with land boundary check
def create_sample_data():
    # Approximate San Francisco land boundary as a polygon (simplified, in EPSG:4326)
    sf_boundary = gpd.GeoDataFrame({
        'name': ['San Francisco'],
        'geometry': [Polygon([
            (-122.5176, 37.8088),  # Northwest (near Golden Gate Park)
            (-122.5176, 37.7047),  # Southwest
            (-122.3567, 37.7047),  # Southeast
            (-122.3567, 37.8088),  # Northeast
            (-122.5176, 37.8088)   # Close polygon
        ])]
    }, geometry='geometry', crs="EPSG:4326")

    # San Francisco BART stations (approximate coordinates in EPSG:4326)
    transit = gpd.GeoDataFrame({
        'name': ['Embarcadero', 'Montgomery', 'Powell', 'Civic Center'],
        'geometry': [
            Point(-122.3964, 37.7929),  # Embarcadero
            Point(-122.4018, 37.7894),  # Montgomery
            Point(-122.4076, 37.7858),  # Powell
            Point(-122.4138, 37.7793)   # Civic Center
        ]
    }, geometry='geometry', crs="EPSG:4326")

    # Hypothetical parcels in San Francisco (ensured to be on land)
    parcels_data = [
        {'id': 1, 'point': Point(-122.4000, 37.7900), 'pop_density': 5000, 'slope': 5},  # Near Embarcadero
        {'id': 2, 'point': Point(-122.4100, 37.7800), 'pop_density': 3000, 'slope': 15}, # Near Civic Center
        {'id': 3, 'point': Point(-122.4200, 37.7750), 'pop_density': 2000, 'slope': 25}, # South of Civic Center
        {'id': 4, 'point': Point(-122.3900, 37.7950), 'pop_density': 1000, 'slope': 10}  # North of Embarcadero
    ]

    # Filter parcels to ensure they are within the land boundary
    parcels = gpd.GeoDataFrame(
        [
            {'id': d['id'], 'geometry': d['point'].buffer(0.005), 'pop_density': d['pop_density'], 'slope': d['slope']}
            for d in parcels_data if sf_boundary.geometry.contains(d['point']).any()
        ],
        geometry='geometry',
        crs="EPSG:4326"
    )

    if parcels.empty:
        print("Warning: No parcels are within the land boundary. Using default land-based parcels.")
        parcels = gpd.GeoDataFrame({
            'id': [1, 2, 3, 4],
            'geometry': [
                Point(-122.4150, 37.7800).buffer(0.005),  # Adjusted to central SF
                Point(-122.4050, 37.7850).buffer(0.005),
                Point(-122.4100, 37.7750).buffer(0.005),
                Point(-122.4000, 37.7900).buffer(0.005)
            ],
            'pop_density': [5000, 3000, 2000, 1000],
            'slope': [5, 15, 25, 10]
        }, geometry='geometry', crs="EPSG:4326")

    return transit, parcels, sf_boundary

# Calculate proximity to transit (e.g., BART stations)
def calculate_proximity_to_transit(parcels, transit, buffer_distance=0.005):  # ~500m in degrees
    transit_buffers = transit.buffer(buffer_distance)
    parcels['proximity_score'] = parcels.geometry.apply(
        lambda x: 1 if any(transit_buffers.contains(x)) else 0.5
    )
    return parcels

# Normalize data for suitability scoring with NaN handling
def normalize_series(series):
    if series.max() == series.min():
        print(f"Warning: Series {series.name} has no variation (all values are {series.max()}). Returning constant score.")
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - series.min()) / (series.max() - series.min())

# Calculate land use suitability for urban development
def calculate_suitability(parcels):
    parcels['pop_density_norm'] = normalize_series(parcels['pop_density'])
    parcels['slope_norm'] = 1 - normalize_series(parcels['slope'])  # Lower slope is better
    parcels['proximity_score_norm'] = normalize_series(parcels['proximity_score'])
    
    for col in ['pop_density_norm', 'slope_norm', 'proximity_score_norm']:
        if parcels[col].isna().any():
            print(f"Warning: NaN values detected in {col}. Replacing with 0.5.")
            parcels[col] = parcels[col].fillna(0.5)
    
    weights = {'pop_density_norm': 0.4, 'slope_norm': 0.3, 'proximity_score_norm': 0.3}
    parcels['suitability_score'] = (
        parcels['pop_density_norm'] * weights['pop_density_norm'] +
        parcels['slope_norm'] * weights['slope_norm'] +
        parcels['proximity_score_norm'] * weights['proximity_score_norm']
    )
    
    if parcels['suitability_score'].isna().any():
        print("Warning: NaN values in suitability_score. Replacing with 0.5.")
        parcels['suitability_score'] = parcels['suitability_score'].fillna(0.5)
    
    return parcels

# Create interactive Folium map with reliable basemap
def create_suitability_map(parcels, sf_boundary):
    m = folium.Map(
        location=[37.7749, -122.4194],  # San Francisco center
        zoom_start=13,
        tiles="OpenStreetMap",
        attr="© <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
    )
    
    # Add San Francisco boundary for reference
    folium.GeoJson(
        sf_boundary.geometry,
        style_function=lambda x: {
            'fillColor': 'none',
            'color': 'blue',
            'weight': 2,
            'fillOpacity': 0
        },
        tooltip="San Francisco Boundary"
    ).add_to(m)
    
    # Add parcels with suitability scores
    for idx, row in parcels.iterrows():
        folium.GeoJson(
            row.geometry,
            style_function=lambda x, score=row['suitability_score']: {
                'fillColor': '#ff0000' if score < 0.3 else '#ffa500' if score < 0.7 else '#008000',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.6
            },
            tooltip=f"Suitability: {row['suitability_score']:.2f}, Pop Density: {row['pop_density']}, Slope: {row['slope']}°"
        ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add JavaScript to log tile errors
    tile_error_script = """
    <script>
        L.TileLayer.include({
            _tileOnError: function(done, tile, e) {
                console.error('Tile loading error:', e);
                done(e, tile);
            }
        });
    </script>
    """
    m.get_root().html.add_child(folium.Element(tile_error_script))
    
    return m

# Generate styled HTML table
def generate_styled_table(parcels):
    df = parcels[['id', 'pop_density', 'slope', 'proximity_score', 'suitability_score']].copy()
    df = df.round(2)
    
    def color_suitability(val):
        if val < 0.3:
            return 'background-color: #ffcccc'
        elif val < 0.7:
            return 'background-color: #ffe4b5'
        else:
            return 'background-color: #ccffcc'
    
    styled_df = df.style.set_properties(**{
        'text-align': 'center',
        'border': '1px solid #ddd'
    }).applymap(color_suitability, subset=['suitability_score']).to_html()
    
    return styled_df

# Main execution
if __name__ == "__main__":
    # Create or load sample data
    transit, parcels, sf_boundary = create_sample_data()
    
    # Calculate proximity and suitability
    parcels = calculate_proximity_to_transit(parcels, transit)
    parcels = calculate_suitability(parcels)
    
    # Generate map and table
    folium_map = create_suitability_map(parcels, sf_boundary)
    table_html = generate_styled_table(parcels)
    
    # Load HTML template
    with open('land_use_suitability_report.html', 'r') as f:
        template = Template(f.read())
    
    # Render HTML with table and map
    map_html = folium_map._repr_html_()
    final_html = template.render(table_html=table_html, map_html=map_html)
    
    # Save output
    with open('suitability_report_san_francisco.html', 'w') as f:
        f.write(final_html)
    
    print("Report saved as suitability_report_san_francisco.html")
