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
    pwd = gpd.read_file("Pune_PWD_Web.geojson")

    # Fix truncated shapefile column
    if "Scheme_Typ" in roads.columns:
        roads = roads.rename(columns={"Scheme_Typ": "Scheme_Type"})

    return roads, hab, block, pwd


roads, hab, block, pwd = load_data()

# =====================================================
# SIDEBAR FILTERS (CASCADE)
# =====================================================

st.sidebar.header("Filters")

# 1️⃣ TALUKA
selected_taluka = st.sidebar.selectbox(
    "Select Taluka",
    sorted(roads["THENAME"].dropna().unique())
)

roads_taluka = roads[roads["THENAME"] == selected_taluka]

# 2️⃣ SCHEME
selected_scheme = st.sidebar.multiselect(
    "Select Scheme",
    sorted(roads_taluka["Scheme_Type"].dropna().unique()),
    default=roads_taluka["Scheme_Type"].dropna().unique()
)

roads_scheme = roads_taluka[
    roads_taluka["Scheme_Type"].isin(selected_scheme)
]

# 3️⃣ CONNECTIVITY (NH/SH/MDR/ODR)
selected_connectivity = st.sidebar.multiselect(
    "Starts From",
    sorted(roads_scheme["Start_From"].dropna().unique()),
    default=roads_scheme["Start_From"].dropna().unique()
)

filtered_roads = roads_scheme[
    roads_scheme["Start_From"].isin(selected_connectivity)
]

# =====================================================
# CREATE MAP
# =====================================================

m = folium.Map(
    location=[18.5204, 73.8567],
    zoom_start=10,
    control_scale=True
)

# Google Satellite
folium.TileLayer(
    tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    attr="Google",
    name="Google Satellite",
    subdomains=["mt0", "mt1", "mt2", "mt3"],
).add_to(m)

# Google Maps
folium.TileLayer(
    tiles="https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google",
    name="Google Maps",
    subdomains=["mt0", "mt1", "mt2", "mt3"],
).add_to(m)

# =====================================================
# ADD TALUKA BOUNDARY
# =====================================================

selected_block = block[block["THENAME"] == selected_taluka]

folium.GeoJson(
    selected_block,
    name="Selected Taluka",
    style_function=lambda x: {
        "color": "black",
        "weight": 2,
        "fillOpacity": 0
    }
).add_to(m)

# =====================================================
# ADD NH / SH / MDR BASE NETWORK
# =====================================================

def pwd_style(feature):
    road_no = str(feature["properties"].get("DP_NEW", ""))

    if road_no.startswith("NH"):
        return {"color": "black", "weight": 4}
    elif road_no.startswith("SH"):
        return {"color": "orange", "weight": 3}
    elif road_no.startswith("MDR"):
        return {"color": "purple", "weight": 2}
    else:
        return {"color": "gray", "weight": 1}

folium.GeoJson(
    pwd,
    name="NH / SH / MDR Network",
    style_function=pwd_style,
    tooltip=folium.GeoJsonTooltip(
        fields=["DP_NEW"],
        aliases=["Road Number"]
    )
).add_to(m)

# =====================================================
# STYLE FUNCTION FOR RURAL ROADS
# =====================================================

def rural_style(feature):
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
# ADD FILTERED RURAL ROADS
# =====================================================

folium.GeoJson(
    filtered_roads,
    name="Filtered Rural Roads",
    style_function=rural_style,
    tooltip=folium.GeoJsonTooltip(
        fields=["Name", "Scheme_Type", "Start_From", "Connected_", "Connecte_1"],
        aliases=["Road Name", "Scheme", "Starts From", "Habitation", "Population"]
    )
).add_to(m)

# =====================================================
# ADD HABITATION LAYER (ONLY SELECTED TALUKA)
# =====================================================

if "THENAME" in hab.columns:
    hab_display = hab[hab["THENAME"] == selected_taluka]
else:
    hab_display = hab

folium.GeoJson(
    hab_display,
    name="Habitations",
    marker=folium.CircleMarker(radius=3, color="red", fill=True),
    tooltip=folium.GeoJsonTooltip(
        fields=["HAB_NAME", "TOT_POPULA"],
        aliases=["Habitation", "Population"]
    )
).add_to(m)

# =====================================================
# LAYER CONTROL
# =====================================================

folium.LayerControl().add_to(m)

# =====================================================
# DISPLAY MAP
# =====================================================

st_folium(m, width=1400, height=700)

# =====================================================
# SUMMARY PANEL
# =====================================================

st.subheader("Summary")

col1, col2 = st.columns(2)

col1.metric("Total Roads", len(filtered_roads))

if "Connecte_1" in filtered_roads.columns:
    col2.metric(
        "Total Population Connected",
        int(filtered_roads["Connecte_1"].sum())
    )
else:
    col2.metric("Total Population Connected", 0)