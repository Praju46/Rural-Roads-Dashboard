import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("Pune District Rural Road Connectivity Dashboard")

# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data
def load_data():

    roads = gpd.read_file("Pune_Roads_Web.geojson")
    hab = gpd.read_file("Pune_Hab_Web.geojson")
    block = gpd.read_file("Pune_Taluka_Web.geojson")

    # Fix truncated shapefile column name
    if "Scheme_Typ" in roads.columns:
        roads = roads.rename(columns={"Scheme_Typ": "Scheme_Type"})

    return roads, hab, block


roads, hab, block = load_data()

# =====================================================
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
    location=[18.5204, 73.8567],
    zoom_start=9,
    control_scale=True
)

# Google Satellite Layer
folium.TileLayer(
    tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    attr="Google",
    name="Google Satellite",
    subdomains=["mt0", "mt1", "mt2", "mt3"],
    overlay=False,
    control=True
).add_to(m)

# Google Maps Layer
folium.TileLayer(
    tiles="https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google",
    name="Google Maps",
    subdomains=["mt0", "mt1", "mt2", "mt3"],
    overlay=False,
    control=True
).add_to(m)

# =====================================================
# STYLE FUNCTION FOR ROADS
# =====================================================

def style_function(feature):
    scheme = feature["properties"].get("Scheme_Type", "")

    if scheme == "PMGSY":
        return {"color": "blue", "weight": 3}
    elif scheme == "MMGSY":
        return {"color": "green", "weight": 3}
    elif scheme == "Proposed":
        return {"color": "red", "weight": 3}
    else:
        return {"color": "gray", "weight": 2}

# =====================================================
# ADD LAYERS
# =====================================================

# Taluka Boundary
folium.GeoJson(
    block,
    name="Taluka Boundary",
    style_function=lambda x: {
        "color": "black",
        "weight": 1,
        "fillOpacity": 0
    }
).add_to(m)

# Roads
folium.GeoJson(
    filtered_roads,
    name="Roads",
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["Name", "Scheme_Type", "Start_From", "Connected_", "Connecte_1"],
        aliases=["Road Name", "Scheme", "Connected To", "Habitation", "Population"]
    )
).add_to(m)

# Habitations
folium.GeoJson(
    hab,
    name="Habitations",
    marker=folium.CircleMarker(radius=4, color="orange", fill=True),
    tooltip=folium.GeoJsonTooltip(
        fields=["HAB_NAME", "TOT_POPULA"],
        aliases=["Habitation", "Population"]
    )
).add_to(m)

folium.LayerControl().add_to(m)

# =====================================================
# DISPLAY MAP
# =====================================================

st_folium(m, width=1400, height=700)