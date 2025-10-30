import streamlit as st
import geopandas as gpd
import rasterio
import rasterio.mask
import requests
import tempfile
import os
import zipfile
import numpy as np
import pandas as pd
from io import BytesIO
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import time
from shapely.geometry import Point, MultiPolygon
import warnings
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Access to Care Analysis",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (same blue dark theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    :root {
        --primary-blue: #2563eb;
        --secondary-blue: #3b82f6;
        --dark-bg: #0a0e1a;
        --card-bg: rgba(15, 23, 42, 0.95);
    }
    
    .stApp {
        background: #0a0e1a;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background: #0f172a;
        border-right: 1px solid rgba(37, 99, 235, 0.2);
    }
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }
    
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    h1 {
        background: #0d1b2a;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 8px 32px rgba(96, 165, 250, 0.3);
        border: 1px solid rgba(96, 165, 250, 0.3);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(96, 165, 250, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        transform: translateY(-2px);
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(96, 165, 250, 0.3);
    }
    
    .stSelectbox > div > div, .stNumberInput > div > div, .stTextInput > div > div {
        background: #0f172a !important;
        border: 2px solid #60a5fa !important;
        border-radius: 12px !important;
        color: #93c5fd !important;
    }
    
    [data-testid="stFileUploader"] {
        background: #0f172a;
        border: 2px dashed #60a5fa;
        border-radius: 15px;
        padding: 2rem;
    }
    
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="metric-container"] {
        background: #0f172a;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(96, 165, 250, 0.3);
    }
    
    .stSuccess, .stInfo, .stWarning, .stError {
        background: #0f172a;
        color: #ffffff;
        border: 1px solid rgba(96, 165, 250, 0.5);
        border-radius: 12px;
        padding: 1rem;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        border-radius: 10px;
    }
    
    p, li, span, label {
        color: #ffffff !important;
    }
    
    strong {
        color: #93c5fd !important;
    }
    
    [role="listbox"] {
        background-color: #0a0e1a !important;
        border: 1px solid rgba(96, 165, 250, 0.4) !important;
    }
    
    [role="option"] {
        background-color: #0a0e1a !important;
        color: #93c5fd !important;
    }
    
    [role="option"]:hover {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    input, textarea {
        color: #93c5fd !important;
        background-color: #0f172a !important;
    }
    
    [data-testid="stDataFrame"] {
        background: #0f172a;
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 12px;
    }
    
    table {
        background: #0f172a !important;
        color: #ffffff !important;
    }
    
    thead tr th {
        background: #1e293b !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-bottom: 2px solid rgba(96, 165, 250, 0.4) !important;
    }
    
    tbody tr {
        border-bottom: 1px solid rgba(96, 165, 250, 0.2) !important;
    }
    
    tbody tr:hover {
        background: rgba(30, 41, 59, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# Country codes for WorldPop
COUNTRY_OPTIONS = {
    "Angola": "AGO", "Benin": "BEN", "Botswana": "BWA", "Burkina Faso": "BFA",
    "Burundi": "BDI", "Cameroon": "CMR", "Central African Republic": "CAF",
    "Chad": "TCD", "Democratic Republic of the Congo": "COD", "Equatorial Guinea": "GNQ",
    "Ethiopia": "ETH", "Gabon": "GAB", "Gambia": "GMB", "Ghana": "GHA",
    "Guinea": "GIN", "Guinea-Bissau": "GNB", "Ivory Coast": "CIV", "Kenya": "KEN",
    "Liberia": "LBR", "Madagascar": "MDG", "Malawi": "MWI", "Mali": "MLI",
    "Mauritania": "MRT", "Mozambique": "MOZ", "Namibia": "NAM", "Niger": "NER",
    "Nigeria": "NGA", "Republic of the Congo": "COG", "Rwanda": "RWA",
    "Senegal": "SEN", "Sierra Leone": "SLE", "South Africa": "ZAF",
    "South Sudan": "SSD", "Sudan": "SDN", "Tanzania": "TZA", "Togo": "TGO",
    "Uganda": "UGA", "Zambia": "ZMB", "Zimbabwe": "ZWE"
}

WORLDPOP_CODES = {code: code.lower() for code in COUNTRY_OPTIONS.values()}

# Initialize session state
if 'facilities_df' not in st.session_state:
    st.session_state.facilities_df = None
if 'country_code' not in st.session_state:
    st.session_state.country_code = "SLE"
if 'boundary_source' not in st.session_state:
    st.session_state.boundary_source = "GADM Database"
if 'custom_boundaries' not in st.session_state:
    st.session_state.custom_boundaries = None

@st.cache_data
def download_worldpop_data(country_code, year):
    """Download WorldPop data"""
    country_lower = WORLDPOP_CODES[country_code]
    
    # Try multiple URL patterns as WorldPop structure varies by year
    urls_to_try = [
        # Pattern 1: Constrained with BSGM folder (some years)
        f"https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/{year}/BSGM/{country_code.upper()}/{country_lower}_ppp_{year}_UNadj_constrained.tif",
        # Pattern 2: Constrained without BSGM folder
        f"https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/{year}/{country_code.upper()}/{country_lower}_ppp_{year}_UNadj_constrained.tif",
        # Pattern 3: Standard without constrained
        f"https://data.worldpop.org/GIS/Population/Global_2000_2020/{year}/{country_code.upper()}/{country_lower}_ppp_{year}_UNadj.tif",
        # Pattern 4: Without UNadj
        f"https://data.worldpop.org/GIS/Population/Global_2000_2020/{year}/{country_code.upper()}/{country_lower}_ppp_{year}.tif",
    ]
    
    last_error = None
    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=180, stream=True)
            response.raise_for_status()
            
            chunks = []
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    chunks.append(chunk)
            
            return b''.join(chunks), url
        except Exception as e:
            last_error = e
            continue
    
    # If all attempts failed, raise the last error
    raise ConnectionError(f"Failed to download WorldPop data for {country_code} {year}. Tried {len(urls_to_try)} different URL patterns. Last error: {str(last_error)}")

@st.cache_data
def download_gadm_boundaries(country_code, admin_level):
    """Download GADM boundaries"""
    gadm_url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_{country_code}_shp.zip"
    
    try:
        response = requests.get(gadm_url, timeout=120, stream=True)
        response.raise_for_status()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, f"gadm41_{country_code}.zip")
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            
            shapefile_name = f"gadm41_{country_code}_{admin_level}.shp"
            shapefile_path = os.path.join(tmpdir, shapefile_name)
            
            if not os.path.exists(shapefile_path):
                raise FileNotFoundError(f"Admin level {admin_level} not found")
            
            gdf = gpd.read_file(shapefile_path)
            
    except Exception as e:
        raise ValueError(f"Failed to download boundaries: {str(e)}")
    
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    
    return gdf

def detect_coordinate_columns(df):
    """Auto-detect longitude and latitude columns"""
    lon_candidates = ['longitude', 'long', 'lon', 'x', 'lng', 'Longitude', 'LONGITUDE', 'Long', 'LON']
    lat_candidates = ['latitude', 'lat', 'y', 'Latitude', 'LATITUDE', 'Lat', 'LAT']
    
    lon_col = None
    lat_col = None
    
    # Check for exact matches first
    for col in df.columns:
        if col in lon_candidates:
            lon_col = col
        if col in lat_candidates:
            lat_col = col
    
    # If not found, check for partial matches
    if lon_col is None:
        for col in df.columns:
            col_lower = col.lower()
            if any(cand.lower() in col_lower for cand in lon_candidates):
                lon_col = col
                break
    
    if lat_col is None:
        for col in df.columns:
            col_lower = col.lower()
            if any(cand.lower() in col_lower for cand in lat_candidates):
                lat_col = col
                break
    
    return lon_col, lat_col

def validate_coordinates(df, lon_col, lat_col):
    """Validate and clean coordinate data"""
    original_count = len(df)
    
    # Convert to numeric, coercing errors to NaN
    df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
    df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
    
    # Remove rows with NaN coordinates
    df = df.dropna(subset=[lon_col, lat_col])
    
    # Validate coordinate ranges
    # Longitude: -180 to 180, Latitude: -90 to 90
    df = df[
        (df[lon_col] >= -180) & (df[lon_col] <= 180) &
        (df[lat_col] >= -90) & (df[lat_col] <= 90)
    ]
    
    # Additional validation: Check if coordinates are not (0, 0) unless valid
    df = df[~((df[lon_col] == 0) & (df[lat_col] == 0))]
    
    invalid_count = original_count - len(df)
    
    return df, invalid_count

def load_facility_file(uploaded_file):
    """Load facility file (CSV or Excel) and detect coordinates"""
    try:
        # Read file based on extension
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("Unsupported file format. Please upload CSV or Excel file.")
        
        # Detect coordinate columns
        lon_col, lat_col = detect_coordinate_columns(df)
        
        if lon_col is None or lat_col is None:
            return None, None, None, "Could not detect longitude/latitude columns"
        
        # Validate coordinates
        df_clean, invalid_count = validate_coordinates(df, lon_col, lat_col)
        
        if len(df_clean) == 0:
            return None, None, None, "No valid coordinates found in the file"
        
        return df_clean, lon_col, lat_col, invalid_count
        
    except Exception as e:
        return None, None, None, f"Error loading file: {str(e)}"

def load_custom_shapefile(shp_file, shx_file, dbf_file, prj_file=None):
    """Load custom shapefile from uploaded components"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save uploaded files
        shp_path = os.path.join(tmpdir, "boundary.shp")
        shx_path = os.path.join(tmpdir, "boundary.shx")
        dbf_path = os.path.join(tmpdir, "boundary.dbf")
        
        with open(shp_path, "wb") as f:
            f.write(shp_file.getvalue())
        with open(shx_path, "wb") as f:
            f.write(shx_file.getvalue())
        with open(dbf_path, "wb") as f:
            f.write(dbf_file.getvalue())
        
        # Save projection file if provided
        if prj_file is not None:
            prj_path = os.path.join(tmpdir, "boundary.prj")
            with open(prj_path, "wb") as f:
                f.write(prj_file.getvalue())
        
        try:
            # Load the shapefile
            gdf = gpd.read_file(shp_path)
        except Exception as e:
            raise ValueError(f"Failed to read shapefile: {str(e)}")
    
    # Handle CRS
    if gdf.crs is None:
        st.warning("No coordinate system detected. Assuming WGS84 (EPSG:4326)")
        gdf = gdf.set_crs("EPSG:4326")
    
    return gdf

def create_distance_raster_optimized(pop_raster_array, facilities_gdf, transform, crs, chunk_size=500):
    """Create distance raster from facilities using chunked processing for memory efficiency"""
    height, width = pop_raster_array.shape
    
    # Initialize distance array with large values
    min_distances = np.full((height, width), np.inf, dtype=np.float32)
    
    # Process in chunks to save memory
    for i in range(0, height, chunk_size):
        for j in range(0, width, chunk_size):
            # Define chunk bounds
            i_end = min(i + chunk_size, height)
            j_end = min(j + chunk_size, width)
            
            # Get pixel coordinates for this chunk
            rows, cols = np.meshgrid(
                np.arange(i, i_end), 
                np.arange(j, j_end), 
                indexing='ij'
            )
            
            # Convert pixel coordinates to geographic coordinates
            xs, ys = rasterio.transform.xy(transform, rows.flatten(), cols.flatten())
            xs = np.array(xs).reshape(rows.shape)
            ys = np.array(ys).reshape(rows.shape)
            
            # Calculate distance to each facility for this chunk
            chunk_min_dist = np.full(rows.shape, np.inf, dtype=np.float32)
            
            for idx, facility in facilities_gdf.iterrows():
                facility_x = facility.geometry.x
                facility_y = facility.geometry.y
                
                # Calculate Euclidean distance in degrees
                dx = xs - facility_x
                dy = ys - facility_y
                distances_deg = np.sqrt(dx**2 + dy**2)
                
                # Convert to meters (approximate)
                # At equator: 1 degree ≈ 111,320 meters
                # Adjust for latitude: meters = degrees * 111320 * cos(latitude)
                lat_rad = np.radians(ys)
                distances_m = distances_deg * 111320 * np.cos(lat_rad)
                
                # Keep minimum distance
                chunk_min_dist = np.minimum(chunk_min_dist, distances_m)
            
            # Store chunk result
            min_distances[i:i_end, j:j_end] = chunk_min_dist
    
    return min_distances

def calculate_access_statistics(pop_raster_array, distance_raster, radius_km, nodata_value):
    """Calculate population access statistics"""
    radius_m = radius_km * 1000
    
    # Create mask for valid population data
    valid_mask = (pop_raster_array != nodata_value) & (~np.isnan(pop_raster_array)) & (pop_raster_array > 0)
    
    # Create access masks
    within_radius = (distance_raster <= radius_m) & valid_mask
    beyond_radius = (distance_raster > radius_m) & valid_mask
    
    # Calculate populations
    pop_within = np.sum(pop_raster_array[within_radius])
    pop_beyond = np.sum(pop_raster_array[beyond_radius])
    total_pop = np.sum(pop_raster_array[valid_mask])
    
    # Calculate percentages
    pct_within = (pop_within / total_pop * 100) if total_pop > 0 else 0
    pct_beyond = (pop_beyond / total_pop * 100) if total_pop > 0 else 0
    
    return {
        'pop_within': pop_within,
        'pop_beyond': pop_beyond,
        'total_pop': total_pop,
        'pct_within': pct_within,
        'pct_beyond': pct_beyond
    }

def calculate_distance_bands(pop_raster_array, distance_raster, nodata_value):
    """Calculate population in different distance bands"""
    bands = [
        (0, 1, "0-1 km"),
        (1, 2, "1-2 km"),
        (2, 3, "2-3 km"),
        (3, 5, "3-5 km"),
        (5, 10, "5-10 km"),
        (10, 999, ">10 km")
    ]
    
    results = []
    valid_mask = (pop_raster_array != nodata_value) & (~np.isnan(pop_raster_array)) & (pop_raster_array > 0)
    total_pop = np.sum(pop_raster_array[valid_mask])
    
    for min_km, max_km, label in bands:
        min_m = min_km * 1000
        max_m = max_km * 1000
        
        band_mask = (distance_raster >= min_m) & (distance_raster < max_m) & valid_mask
        band_pop = np.sum(pop_raster_array[band_mask])
        band_pct = (band_pop / total_pop * 100) if total_pop > 0 else 0
        
        results.append({
            'distance_band': label,
            'population': int(band_pop),
            'percentage': round(band_pct, 2)
        })
    
    return pd.DataFrame(results)

# Main app
st.markdown("""
<h1>
    🏥 Access to Care Analysis
</h1>
<p style='text-align: center; color: #9ca3af; font-size: 1.2rem; margin-top: -1rem; margin-bottom: 2rem;'>
    Analyze population access to health facilities using distance-based metrics
</p>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## Analysis Parameters")
    
    # Boundary source selection
    boundary_source = st.radio(
        "Boundary Data Source",
        ["GADM Database", "Upload Custom Shapefile"],
        help="Choose between GADM boundaries or upload your own"
    )
    st.session_state.boundary_source = boundary_source
    
    if boundary_source == "GADM Database":
        # Country selection
        country = st.selectbox(
            "Select Country",
            list(COUNTRY_OPTIONS.keys()),
            help="Select the country for analysis"
        )
        country_code = COUNTRY_OPTIONS[country]
        st.session_state.country_code = country_code
        
        # Administrative level
        admin_level = st.selectbox(
            "Administrative Level",
            [0, 1, 2, 3],
            index=2,  # Default to level 2 (districts)
            help="0=Country, 1=Regions, 2=Districts, 3=Communes"
        )
        
        level_descriptions = {
            0: "Country boundary",
            1: "First-level (regions/states)",
            2: "Second-level (districts/provinces)",
            3: "Third-level (communes/counties)"
        }
        st.caption(f"Level {admin_level}: {level_descriptions[admin_level]}")
        
    else:  # Upload Custom Shapefile
        st.markdown("**Upload Boundary Files**")
        st.caption("Upload all required shapefile components")
        
        shp_file = st.file_uploader("Shapefile (.shp)", type=['shp'], help="Main geometry file")
        shx_file = st.file_uploader("Shape Index (.shx)", type=['shx'], help="Spatial index file")
        dbf_file = st.file_uploader("Attribute Table (.dbf)", type=['dbf'], help="Attribute data")
        prj_file = st.file_uploader("Projection (.prj)", type=['prj'], help="Coordinate system (optional)")
        
        if shp_file and shx_file and dbf_file:
            try:
                custom_boundaries = load_custom_shapefile(shp_file, shx_file, dbf_file, prj_file)
                st.session_state.custom_boundaries = custom_boundaries
                st.success(f"✅ Loaded {len(custom_boundaries)} boundary features")
                
                if custom_boundaries.crs:
                    st.info(f"📍 CRS: {custom_boundaries.crs}")
            except Exception as e:
                st.error(f"❌ Error loading shapefile: {str(e)}")
                st.session_state.custom_boundaries = None
        else:
            st.info("Please upload .shp, .shx, and .dbf files")
            st.session_state.custom_boundaries = None
        
        # For custom boundaries, still need country for WorldPop
        st.markdown("**Select Country for Population Data**")
        country = st.selectbox(
            "Country",
            list(COUNTRY_OPTIONS.keys()),
            help="Select country to download WorldPop data"
        )
        country_code = COUNTRY_OPTIONS[country]
        st.session_state.country_code = country_code
        admin_level = "Custom"
    
    st.markdown("---")
    
    # Year selection (default 2020)
    year = st.selectbox(
        "Population Year",
        list(range(2000, 2021)),
        index=20,  # 2020 is at index 20
        help="Year for population data (2020 is most recent)"
    )
    
    st.info(f"📅 Using **{year}** population data from WorldPop")
    
    st.markdown("---")
    
    # Facility file upload
    st.markdown("### Health Facility Data")
    
    facility_file = st.file_uploader(
        "Upload Facility Coordinates",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel file with facility coordinates"
    )
    
    if facility_file:
        df_facilities, lon_col, lat_col, result = load_facility_file(facility_file)
        
        if df_facilities is not None:
            st.session_state.facilities_df = df_facilities
            st.success(f"✅ Loaded {len(df_facilities)} facilities")
            st.info(f"📍 Detected columns: **{lon_col}**, **{lat_col}**")
            
            if isinstance(result, int) and result > 0:
                st.warning(f"⚠️ Skipped {result} invalid coordinates")
            
            # IMPROVED FILTERING - Show all categorical columns
            available_columns = [col for col in df_facilities.columns if col not in [lon_col, lat_col]]
            
            # Identify categorical columns (non-numeric or with few unique values)
            categorical_columns = []
            for col in available_columns:
                unique_count = df_facilities[col].nunique()
                # Consider categorical if: non-numeric OR has fewer than 50 unique values
                if df_facilities[col].dtype == 'object' or unique_count < 50:
                    categorical_columns.append(col)
            
            if categorical_columns:
                st.markdown("**Optional: Filter Facilities**")
                
                enable_filter = st.checkbox("Enable facility filtering", value=False)
                
                if enable_filter:
                    st.markdown("**Select Columns and Values to Filter**")
                    
                    # Multi-column filtering
                    selected_filters = {}
                    
                    # Allow selection of multiple columns
                    filter_columns = st.multiselect(
                        "Select columns to filter by",
                        categorical_columns,
                        help="Choose one or more columns to filter facilities"
                    )
                    
                    if filter_columns:
                        for filter_col in filter_columns:
                            st.markdown(f"**Filter by: {filter_col}**")
                            
                            # Get unique values for this column
                            unique_values = df_facilities[filter_col].dropna().unique().tolist()
                            
                            if len(unique_values) > 0:
                                # Always use multiselect for consistency
                                if len(unique_values) <= 30:
                                    # Show all values
                                    selected_values = st.multiselect(
                                        f"Select {filter_col} values",
                                        sorted(unique_values, key=str),
                                        default=unique_values,
                                        key=f"filter_{filter_col}",
                                        help=f"Select which {filter_col} to include"
                                    )
                                else:
                                    # For many values, offer text search + multiselect
                                    search_text = st.text_input(
                                        f"Search {filter_col}",
                                        key=f"search_{filter_col}",
                                        help=f"Type to search {filter_col} values"
                                    )
                                    
                                    if search_text:
                                        filtered_values = [v for v in unique_values if search_text.lower() in str(v).lower()]
                                    else:
                                        filtered_values = unique_values
                                    
                                    selected_values = st.multiselect(
                                        f"Select {filter_col} values ({len(filtered_values)} shown)",
                                        sorted(filtered_values, key=str),
                                        default=filtered_values,
                                        key=f"filter_{filter_col}",
                                        help=f"Select which {filter_col} to include"
                                    )
                                
                                if selected_values:
                                    selected_filters[filter_col] = selected_values
                        
                        # Apply all filters
                        if selected_filters:
                            df_facilities_filtered = df_facilities.copy()
                            
                            for col, values in selected_filters.items():
                                df_facilities_filtered = df_facilities_filtered[df_facilities_filtered[col].isin(values)]
                            
                            st.session_state.facilities_df = df_facilities_filtered
                            
                            # Show filter summary
                            st.markdown("**Active Filters:**")
                            for col, values in selected_filters.items():
                                if len(values) < len(df_facilities[col].dropna().unique()):
                                    st.caption(f"• {col}: {len(values)} values selected")
                            
                            st.info(f"📊 Filtered to **{len(df_facilities_filtered)}** facilities")
                        else:
                            st.warning("Please select at least one value for each filter column")
                    else:
                        st.info("Select columns above to start filtering")
        else:
            st.error(f"❌ {result}")
    else:
        st.info("Please upload a CSV or Excel file with facility coordinates")
        
        with st.expander("File Format Requirements"):
            st.markdown("""
            **Required:**
            - Longitude and Latitude columns (auto-detected)
            - Valid coordinate values
            
            **Accepted column names:**
            - Longitude: `longitude`, `long`, `lon`, `lng`, `x`
            - Latitude: `latitude`, `lat`, `y`
            
            **Optional:**
            - Facility name/ID column
            - Facility type column (for filtering)
            - Any other attribute columns
            
            **Valid coordinate ranges:**
            - Longitude: -180 to 180
            - Latitude: -90 to 90
            
            **Example format:**
            ```
            facility_name, longitude, latitude, type
            Hospital A, -13.2345, 8.4567, Hospital
            Clinic B, -13.1234, 8.5678, Clinic
            ```
            """)
    
    st.markdown("---")
    
    # Distance parameters
    st.markdown("### Distance Parameters")
    
    radius_km = st.number_input(
        "Access Radius (km)",
        min_value=1.0,
        max_value=50.0,
        value=5.0,
        step=0.5,
        help="Distance threshold for 'access' (default: 5 km)"
    )
    
    st.info(f"🎯 Analyzing access within **{radius_km} km** radius")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🚀 Run Access Analysis", type="primary", use_container_width=True):
        if st.session_state.facilities_df is None or len(st.session_state.facilities_df) == 0:
            st.error("❌ Please upload facility coordinates first")
        else:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Load boundaries
                status_text.text("Loading administrative boundaries...")
                progress_bar.progress(10)
                
                if st.session_state.boundary_source == "GADM Database":
                    admin_boundaries = download_gadm_boundaries(country_code, admin_level)
                    st.success(f"✅ Loaded {len(admin_boundaries)} administrative units from GADM")
                else:
                    if st.session_state.custom_boundaries is None:
                        st.error("❌ Please upload boundary shapefile first")
                        st.stop()
                    admin_boundaries = st.session_state.custom_boundaries
                    st.success(f"✅ Using custom boundaries ({len(admin_boundaries)} features)")
                
                progress_bar.progress(20)
                
                # Step 2: Download population data
                status_text.text(f"Downloading {year} population data...")
                progress_bar.progress(30)
                
                pop_data, pop_url = download_worldpop_data(country_code, year)
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    pop_path = os.path.join(tmpdir, "population.tif")
                    with open(pop_path, "wb") as f:
                        f.write(pop_data)
                    
                    # Load population raster
                    with rasterio.open(pop_path) as src:
                        pop_array = src.read(1)
                        pop_transform = src.transform
                        pop_crs = src.crs
                        pop_nodata = src.nodata if src.nodata is not None else -99999
                        pop_bounds = src.bounds
                
                st.success(f"✅ Population data loaded ({year})")
                progress_bar.progress(40)
                
                # Step 3: Process facilities
                status_text.text("Processing facility locations...")
                progress_bar.progress(50)
                
                facilities_df = st.session_state.facilities_df.copy()
                
                # Detect coordinate columns again (in case of filtering)
                lon_col, lat_col = detect_coordinate_columns(facilities_df)
                
                # Create GeoDataFrame from facilities
                geometry = [Point(xy) for xy in zip(facilities_df[lon_col], facilities_df[lat_col])]
                facilities_gdf = gpd.GeoDataFrame(facilities_df, geometry=geometry, crs="EPSG:4326")
                
                # Transform to match population raster CRS
                facilities_gdf = facilities_gdf.to_crs(pop_crs)
                
                # Filter facilities within country bounds (with some buffer)
                minx, miny, maxx, maxy = pop_bounds
                buffer = 0.5  # Larger buffer to catch facilities near borders
                facilities_gdf = facilities_gdf.cx[minx-buffer:maxx+buffer, miny-buffer:maxy+buffer]
                
                if len(facilities_gdf) == 0:
                    st.error("❌ No facilities found within country boundaries. Check coordinate system or country selection.")
                    st.stop()
                
                st.success(f"✅ Processing {len(facilities_gdf)} facilities within country")
                progress_bar.progress(60)
                
                # Step 4: Calculate distances
                status_text.text("Calculating distances to nearest facility (this may take a moment)...")
                progress_bar.progress(70)
                
                distance_raster = create_distance_raster_optimized(
                    pop_array, facilities_gdf, pop_transform, pop_crs
                )
                
                st.success("✅ Distance calculations complete")
                progress_bar.progress(80)
                
                # Step 5: Calculate statistics
                status_text.text("Calculating access statistics...")
                progress_bar.progress(90)
                
                # Overall statistics
                overall_stats = calculate_access_statistics(
                    pop_array, distance_raster, radius_km, pop_nodata
                )
                
                # Distance bands
                distance_bands_df = calculate_distance_bands(
                    pop_array, distance_raster, pop_nodata
                )
                
                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                time.sleep(0.5)
                status_text.empty()
                progress_bar.empty()
                
                st.success("🎉 Access analysis completed successfully!")
                
                # Display results
                st.markdown("## 📊 Overall Access Statistics")
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric(
                        "Total Population",
                        f"{overall_stats['total_pop']:,.0f}"
                    )
                
                with col_stat2:
                    st.metric(
                        f"Within {radius_km} km",
                        f"{overall_stats['pop_within']:,.0f}",
                        f"{overall_stats['pct_within']:.1f}%"
                    )
                
                with col_stat3:
                    st.metric(
                        f"Beyond {radius_km} km",
                        f"{overall_stats['pop_beyond']:,.0f}",
                        f"{overall_stats['pct_beyond']:.1f}%"
                    )
                
                # Distance bands table
                st.markdown("### Distance Band Analysis")
                st.dataframe(distance_bands_df, use_container_width=True)
                
                # Create visualizations
                st.markdown("## 🗺️ Access Maps")
                
                # Prepare data for mapping
                access_within = (distance_raster <= radius_km * 1000) & (pop_array != pop_nodata) & (~np.isnan(pop_array)) & (pop_array > 0)
                access_beyond = (distance_raster > radius_km * 1000) & (pop_array != pop_nodata) & (~np.isnan(pop_array)) & (pop_array > 0)
                
                pop_within_array = np.where(access_within, pop_array, np.nan)
                pop_beyond_array = np.where(access_beyond, pop_array, np.nan)
                
                # Map 1: Population within radius
                st.markdown(f"### Population Within {radius_km} km of Health Facilities")
                
                fig1, ax1 = plt.subplots(1, 1, figsize=(12, 10), facecolor='white')
                ax1.set_facecolor('white')
                
                # Plot admin boundaries
                admin_boundaries_plot = admin_boundaries.to_crs("EPSG:4326")
                admin_boundaries_plot.boundary.plot(ax=ax1, edgecolor='black', linewidth=0.5, alpha=0.7)
                
                # Plot population within radius
                from matplotlib.colors import LinearSegmentedColormap
                colors_within = ['#e0f2fe', '#bae6fd', '#7dd3fc', '#38bdf8', '#0ea5e9', '#0284c7', '#0369a1']
                cmap_within = LinearSegmentedColormap.from_list('access_within', colors_within)
                
                # Only show areas with population > 0
                pop_within_display = np.where(pop_within_array > 0, pop_within_array, np.nan)
                
                if np.nansum(pop_within_display) > 0:
                    im1 = ax1.imshow(
                        pop_within_display,
                        extent=[pop_bounds.left, pop_bounds.right, pop_bounds.bottom, pop_bounds.top],
                        cmap=cmap_within,
                        alpha=0.7,
                        interpolation='bilinear',
                        vmin=0,
                        vmax=np.nanpercentile(pop_within_display, 98)  # Cap at 98th percentile for better visualization
                    )
                    plt.colorbar(im1, ax=ax1, label='Population Density', shrink=0.7)
                
                # Plot facilities
                facilities_gdf_plot = facilities_gdf.to_crs("EPSG:4326")
                facilities_gdf_plot.plot(ax=ax1, color='#dc2626', markersize=30, marker='^', 
                                        edgecolor='#7f1d1d', linewidth=0.8, label='Health Facilities', zorder=5)
                
                ax1.set_title(
                    f"{country} - Population with Access to Health Services\nWithin {radius_km} km Radius ({year})",
                    fontweight='bold', fontsize=13, color='black', pad=15
                )
                ax1.set_xlabel('Longitude', fontsize=10, color='black')
                ax1.set_ylabel('Latitude', fontsize=10, color='black')
                ax1.legend(loc='upper right', framealpha=0.9, edgecolor='black')
                ax1.tick_params(colors='black', labelsize=9)
                ax1.grid(True, alpha=0.2, linestyle='--', color='gray')
                
                plt.tight_layout()
                st.pyplot(fig1)
                
                # Map 2: Population beyond radius
                st.markdown(f"### Population Beyond {radius_km} km from Health Facilities")
                
                fig2, ax2 = plt.subplots(1, 1, figsize=(12, 10), facecolor='white')
                ax2.set_facecolor('white')
                
                # Plot admin boundaries
                admin_boundaries_plot.boundary.plot(ax=ax2, edgecolor='black', linewidth=0.5, alpha=0.7)
                
                # Plot population beyond radius
                colors_beyond = ['#fef2f2', '#fecaca', '#fca5a5', '#f87171', '#ef4444', '#dc2626', '#b91c1c']
                cmap_beyond = LinearSegmentedColormap.from_list('access_beyond', colors_beyond)
                
                # Only show areas with population > 0
                pop_beyond_display = np.where(pop_beyond_array > 0, pop_beyond_array, np.nan)
                
                if np.nansum(pop_beyond_display) > 0:
                    im2 = ax2.imshow(
                        pop_beyond_display,
                        extent=[pop_bounds.left, pop_bounds.right, pop_bounds.bottom, pop_bounds.top],
                        cmap=cmap_beyond,
                        alpha=0.7,
                        interpolation='bilinear',
                        vmin=0,
                        vmax=np.nanpercentile(pop_beyond_display, 98)  # Cap at 98th percentile
                    )
                    plt.colorbar(im2, ax=ax2, label='Population Density', shrink=0.7)
                
                # Plot facilities
                facilities_gdf_plot.plot(ax=ax2, color='#16a34a', markersize=30, marker='^',
                                        edgecolor='#14532d', linewidth=0.8, label='Health Facilities', zorder=5)
                
                ax2.set_title(
                    f"{country} - Population without Access to Health Services\nBeyond {radius_km} km Radius ({year})",
                    fontweight='bold', fontsize=13, color='black', pad=15
                )
                ax2.set_xlabel('Longitude', fontsize=10, color='black')
                ax2.set_ylabel('Latitude', fontsize=10, color='black')
                ax2.legend(loc='upper right', framealpha=0.9, edgecolor='black')
                ax2.tick_params(colors='black', labelsize=9)
                ax2.grid(True, alpha=0.2, linestyle='--', color='gray')
                
                plt.tight_layout()
                st.pyplot(fig2)
                
                # Download section
                st.markdown("## 📥 Download Results")
                
                col_dl1, col_dl2 = st.columns(2)
                
                with col_dl1:
                    # CSV download
                    summary_data = pd.DataFrame([
                        {
                            'Country': country,
                            'Country_Code': country_code,
                            'Year': year,
                            'Radius_km': radius_km,
                            'Total_Population': int(overall_stats['total_pop']),
                            'Population_Within_Radius': int(overall_stats['pop_within']),
                            'Population_Beyond_Radius': int(overall_stats['pop_beyond']),
                            'Percent_Within': round(overall_stats['pct_within'], 2),
                            'Percent_Beyond': round(overall_stats['pct_beyond'], 2),
                            'Number_of_Facilities': len(facilities_gdf),
                            'Admin_Level': admin_level,
                            'Analysis_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    ])
                    
                    csv_data = summary_data.to_csv(index=False)
                    st.download_button(
                        label="📊 Download Summary (CSV)",
                        data=csv_data,
                        file_name=f"access_summary_{country_code}_{year}_{radius_km}km.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_dl2:
                    # Excel download with multiple sheets
                    excel_buffer = BytesIO()
                    
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        # Summary sheet
                        summary_data.to_excel(writer, sheet_name='Summary', index=False)
                        
                        # Distance bands sheet
                        distance_bands_df.to_excel(writer, sheet_name='Distance_Bands', index=False)
                        
                        # Facilities sheet
                        facilities_df.to_excel(writer, sheet_name='Facilities', index=False)
                        
                        # Metadata sheet
                        metadata = pd.DataFrame({
                            'Parameter': ['Country', 'Country Code', 'Year', 'Access Radius (km)', 
                                        'Total Population', 'Population Within Access', 'Population Beyond Access',
                                        '% Within Access', '% Beyond Access', 'Number of Facilities',
                                        'Admin Level', 'Analysis Date', 'Tool Version'],
                            'Value': [country, country_code, year, radius_km,
                                    f"{overall_stats['total_pop']:,.0f}",
                                    f"{overall_stats['pop_within']:,.0f}",
                                    f"{overall_stats['pop_beyond']:,.0f}",
                                    f"{overall_stats['pct_within']:.2f}%",
                                    f"{overall_stats['pct_beyond']:.2f}%",
                                    len(facilities_gdf),
                                    admin_level,
                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'Access to Care Analysis v1.0']
                        })
                        metadata.to_excel(writer, sheet_name='Metadata', index=False)
                    
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="📊 Download Full Report (Excel)",
                        data=excel_buffer.getvalue(),
                        file_name=f"access_analysis_{country_code}_{year}_{radius_km}km.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                # PDF maps download
                st.markdown("### Download Maps")
                
                pdf_buffer = BytesIO()
                with PdfPages(pdf_buffer) as pdf:
                    pdf.savefig(fig1, dpi=300, bbox_inches='tight', facecolor='white')
                    pdf.savefig(fig2, dpi=300, bbox_inches='tight', facecolor='white')
                
                pdf_buffer.seek(0)
                
                st.download_button(
                    label="🗺️ Download Maps (PDF)",
                    data=pdf_buffer,
                    file_name=f"access_maps_{country_code}_{year}_{radius_km}km.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                import traceback
                
                with st.expander("Debug Information"):
                    st.write(f"Country: {country}")
                    st.write(f"Country Code: {country_code}")
                    st.write(f"Year: {year}")
                    st.write(f"Radius: {radius_km} km")
                    st.write(f"Facilities: {len(st.session_state.facilities_df) if st.session_state.facilities_df is not None else 0}")
                    st.code(traceback.format_exc())

with col2:
    st.markdown("## About This Tool")
    st.markdown("""
    **Access to Care Analysis Tool**
    
    Analyze population access to health facilities using distance-based metrics and high-resolution population data.
    
    **Features:**
    - 🗺️ Distance-based access analysis
    - 📍 Auto-detect coordinate columns
    - ✅ Automatic coordinate validation
    - 🔍 Filter facilities by type/attribute
    - 📊 Multiple distance bands
    - 🎯 Customizable access radius
    - 📥 Comprehensive reporting
    
    **Data Sources:**
    - WorldPop: Population distribution
    - GADM: Administrative boundaries
    - User upload: Health facility locations
    
    **Methodology:**
    - Euclidean distance calculation
    - Distance to nearest facility
    - Population aggregation by distance
    - Latitude-adjusted distance conversion
    
    **Default Settings:**
    - Population year: 2020 (most recent)
    - Access radius: 5 km (WHO standard)
    - Admin level: 2 (districts)
    - Country: Sierra Leone
    
    **Use Cases:**
    - Health service coverage analysis
    - Facility gap identification
    - Resource allocation planning
    - Equity assessment
    - Strategic facility placement
    """)
    
    with st.expander("Usage Guide"):
        st.markdown("""
        **Step 1: Select Country**
        - Choose your country from the list
        - Select analysis year (default: 2020)
        - Choose administrative level
        
        **Step 2: Upload Facilities**
        - Prepare CSV or Excel file
        - Include longitude and latitude
        - Optionally include facility type
        
        **Step 3: Configure Analysis**
        - Set access radius (default: 5 km)
        - Optionally filter by facility type
        - Review facility count
        
        **Step 4: Run Analysis**
        - Click "Run Access Analysis"
        - Review results and maps
        - Download reports and maps
        
        **Tips:**
        - Use level 2-3 for detailed analysis
        - 5 km is WHO standard for access
        - Filter by facility type for targeted analysis
        - Download Excel for complete data
        - Large countries may take 2-3 minutes
        """)
    
    with st.expander("File Format Guide"):
        st.markdown("""
        **CSV/Excel Requirements:**
        
        **Required columns** (auto-detected):
        - Longitude: `longitude`, `lon`, `long`, `lng`, `x`
        - Latitude: `latitude`, `lat`, `y`
        
        **Optional columns:**
        - Facility name/ID
        - Facility type (for filtering)
        - Ownership (public/private)
        - Services offered
        - Any custom attributes
        
        **Coordinate validation:**
        - Longitude: -180 to 180
        - Latitude: -90 to 90
        - No (0, 0) coordinates
        - Numeric values only
        
        **Example CSV:**
        ```
        name,longitude,latitude,type
        Hospital A,-13.2345,8.4567,Hospital
        Clinic B,-13.1234,8.5678,Health Post
        Center C,-13.3456,8.6789,Health Center
        ```
        """)
    
    with st.expander("Distance Metrics"):
        st.markdown("""
        **Access Radius:**
        - **5 km**: WHO standard for basic health access
        - **3 km**: Walking distance (~1 hour)
        - **10 km**: Extended coverage area
        - **Custom**: Set any radius for your needs
        
        **Distance Bands:**
        - 0-1 km: Immediate access
        - 1-2 km: Easy walking distance
        - 2-3 km: Moderate walking distance
        - 3-5 km: Extended walking distance
        - 5-10 km: Requires transport
        - >10 km: Limited access
        
        **Calculation Method:**
        - Euclidean (straight-line) distance
        - Distance to nearest facility
        - Latitude-adjusted for accuracy
        - Measured in kilometers
        - Pixel-based precision
        """)
    
    with st.expander("Output Files"):
        st.markdown("""
        **CSV Summary:**
        - Overall statistics
        - Single-sheet format
        - Easy to analyze
        
        **Excel Report:**
        - Summary statistics
        - Distance band breakdown
        - Facility list
        - Metadata
        
        **PDF Maps:**
        - Population with access (blue)
        - Population without access (red)
        - Facility locations (triangles)
        - High resolution (300 DPI)
        - Grid and boundaries
        """)
    
    with st.expander("Performance Notes"):
        st.markdown("""
        **Processing Time:**
        - Small countries: 1-2 minutes
        - Medium countries: 2-4 minutes
        - Large countries: 4-8 minutes
        
        **First Run:**
        - Downloads data (50-200 MB)
        - Processes distances
        
        **Subsequent Runs:**
        - Much faster (cached data)
        - Only recalculates distances
        
        **Optimization:**
        - Uses chunked processing
        - Memory efficient
        - Latitude-adjusted distances
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6b7280; padding: 2rem 0;'>
    <p style='margin-bottom: 0.5rem;'><strong>Built for health service planning and equity analysis</strong></p>
    <p style='margin-bottom: 0.5rem;'><strong>Contact</strong>: Mohamed Sillah Kanu | Informatics Consultancy Firm - Sierra Leone (ICF-SL)</p>
    <p style='margin-bottom: 0.5rem;'><strong>Email</strong>: mohamed.kanu@informaticsconsultancyfirm.com</p>
    <p><strong>Data Sources</strong>: WorldPop (www.worldpop.org) | GADM (gadm.org)</p>
</div>
""", unsafe_allow_html=True)
