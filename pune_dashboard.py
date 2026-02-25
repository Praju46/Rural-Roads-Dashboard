import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("Pune District Rural Road Connectivity Dashboard")

import os


# =====================================================
# LOAD DATA (WEB OPTIMIZED GEOJSON)
# =====================================================

@st.cache_data
def load_data():

    roads = gpd.read_file("Data/Pune_Roads_Web.geojson")
    hab = gpd.read_file("Data/Pune_Hab_Web.geojson")
    block = gpd.read_file("Data/Pune_Taluka_Web.geojson")

    return roads, hab, block


roads, hab, block = load_data()# =====================================================
# SIDEBAR FILTERS
# =====================================================

st.sidebar.header("Filters")

selected_scheme = st.sidebar.multiselect(
    "Select Scheme",
    roads["Scheme_Type"].unique(),
    default=roads["Scheme_Type"].unique()
)

selected_taluka = st.sidebar.multiselect(
    "Select Taluka",
    roads["THENAME"].unique(),
    default=roads["THENAME"].unique()
)

filtered_roads = roads[
    (roads["Scheme_Type"].isin(selected_scheme)) &
    (roads["THENAME"].isin(selected_taluka))
]

# =====================================================
# CREATE MAP
# =====================================================

m = folium.Map(
    location=[18.52, 73.85],
    zoom_start=9,
    tiles=None
)

# Basemaps
folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
folium.TileLayer("CartoDB positron", name="Light Map").add_to(m)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="ESRI Satellite",
    name="Satellite",
).add_to(m)

# =====================================================
# ADD ROADS
# =====================================================

def road_style(feature):
    scheme = feature["properties"]["Scheme_Type"]
    if scheme == "PMGSY":
        return {"color": "blue", "weight": 3}
    elif scheme == "MMGSY":
        return {"color": "green", "weight": 3}
    elif scheme == "Proposed":
        return {"color": "orange", "weight": 3}
    else:
        return {"color": "gray", "weight": 2}

folium.GeoJson(
    filtered_roads,
    name="Roads",
    style_function=road_style,
    tooltip=folium.GeoJsonTooltip(
        fields=["Connected_Habs", "Connected_Pop", "Scheme_Type"],
        aliases=["Habitation", "Population", "Scheme"]
    )
).add_to(m)

# =====================================================
# ADD HABITATIONS
# =====================================================

for _, row in hab.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=4,
        popup=f"{row['HAB_NAME']}<br>Population: {row['TOT_POPULA']}",
        color="red",
        fill=True,
    ).add_to(m)

# =====================================================
# ADD TALUKA BOUNDARY
# =====================================================

folium.GeoJson(
    block,
    name="Taluka Boundary",
    style_function=lambda x: {"color": "black", "weight": 1, "fillOpacity": 0}
).add_to(m)

# Layer control
folium.LayerControl().add_to(m)

# Display map
st_folium(m, width=1400, height=700)

# =====================================================
# SUMMARY STATS
# =====================================================

st.subheader("Summary Statistics")

col1, col2 = st.columns(2)

col1.metric("Total Roads", len(filtered_roads))
col2.metric("Total Population Connected", int(filtered_roads["Connected_Pop"].sum()))