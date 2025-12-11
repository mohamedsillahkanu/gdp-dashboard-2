import streamlit as st
import geopandas as gpd
import rasterio
import rasterio.mask
import requests
import tempfile
import os
import zipfile
import math
import numpy as np
import pandas as pd
from io import BytesIO
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import time

# Set page config
st.set_page_config(
    page_title="WorldPop Population Analysis - ICF-SL",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ICF-SL Theme CSS (matching IQR tool)
st.markdown("""
<style>
    /* Import Oswald font */
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&display=swap');
    
    /* ICF-SL Theme Variables */
    :root {
        --primary-blue: #004080;
        --secondary-blue: #0066cc;
        --light-blue: #e7f3ff;
        --gold: #c4a000;
        --success: #28a745;
        --warning: #ffc107;
        --danger: #dc3545;
        --text-dark: #333333;
        --text-light: #666666;
        --white: #ffffff;
        --gray-light: #f8f9fa;
    }
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        font-family: 'Oswald', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #004080 0%, #002855 100%);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #ffffff;
    }
    
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-family: 'Oswald', sans-serif !important;
        font-weight: 700;
    }
    
    /* Main Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Oswald', sans-serif !important;
        color: #004080 !important;
        font-weight: 700;
    }
    
    /* Card Containers */
    [data-testid="stExpander"] {
        background: #ffffff;
        border: 2px solid #004080;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 64, 128, 0.15);
        margin-bottom: 1rem;
    }
    
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
        color: #333333 !important;
    }
    
    .streamlit-expanderHeader {
        background: #004080 !important;
        color: #ffffff !important;
        font-family: 'Oswald', sans-serif !important;
        font-weight: 600;
        border-radius: 8px 8px 0 0;
    }
    
    /* Buttons - Primary Blue */
    .stButton > button {
        background: linear-gradient(135deg, #004080 0%, #0066cc 100%);
        color: white !important;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-family: 'Oswald', sans-serif !important;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 15px rgba(0, 64, 128, 0.3);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #003366 0%, #004080 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 64, 128, 0.4);
    }
    
    /* Download Buttons - Gold */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #c4a000 0%, #9a7d00 100%);
        color: white !important;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-family: 'Oswald', sans-serif !important;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(196, 160, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #9a7d00 0%, #7a6300 100%);
        transform: translateY(-2px);
    }
    
    /* Select boxes */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: #ffffff !important;
        border: 2px solid #004080 !important;
        border-radius: 8px !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    .stSelectbox label,
    .stMultiSelect label {
        color: #004080 !important;
        font-family: 'Oswald', sans-serif !important;
        font-weight: 600;
    }
    
    /* Dropdown options */
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
    }
    
    [role="listbox"] {
        background-color: #ffffff !important;
        border: 2px solid #004080 !important;
        border-radius: 8px !important;
    }
    
    [role="option"] {
        background-color: #ffffff !important;
        color: #333333 !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    [role="option"]:hover {
        background-color: #e7f3ff !important;
        color: #004080 !important;
    }
    
    [role="option"][aria-selected="true"] {
        background-color: #004080 !important;
        color: #ffffff !important;
    }
    
    /* Input fields */
    input[type="number"], input[type="text"] {
        background: #ffffff !important;
        border: 2px solid #004080 !important;
        border-radius: 8px !important;
        color: #333333 !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #004080;
    }
    
    .stRadio label {
        color: #333333 !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    /* Checkboxes */
    .stCheckbox label {
        color: #333333 !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: #ffffff;
        border: 2px dashed #004080;
        border-radius: 10px;
        padding: 2rem;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #0066cc;
        background: #e7f3ff;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #004080 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #333333 !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    div[data-testid="metric-container"] {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 64, 128, 0.15);
        border: 2px solid #004080;
        transition: all 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 64, 128, 0.25);
    }
    
    /* Success/Info/Warning/Error messages */
    .stSuccess {
        background: #d4edda !important;
        color: #155724 !important;
        border: 1px solid #28a745 !important;
        border-radius: 8px;
        font-family: 'Oswald', sans-serif !important;
    }
    
    .stInfo {
        background: #e7f3ff !important;
        color: #004080 !important;
        border: 1px solid #004080 !important;
        border-radius: 8px;
        font-family: 'Oswald', sans-serif !important;
    }
    
    .stWarning {
        background: #fff3cd !important;
        color: #856404 !important;
        border: 1px solid #ffc107 !important;
        border-radius: 8px;
        font-family: 'Oswald', sans-serif !important;
    }
    
    .stError {
        background: #f8d7da !important;
        color: #721c24 !important;
        border: 1px solid #dc3545 !important;
        border-radius: 8px;
        font-family: 'Oswald', sans-serif !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #004080 0%, #0066cc 100%);
        border-radius: 10px;
    }
    
    /* Dataframe */
    [data-testid="stDataFrame"] {
        background: #ffffff;
        border: 2px solid #004080;
        border-radius: 10px;
    }
    
    /* Tables */
    table {
        background: #ffffff !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    thead tr th {
        background: #004080 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-family: 'Oswald', sans-serif !important;
    }
    
    tbody tr:hover {
        background: #e7f3ff !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff;
        border-radius: 10px;
        padding: 0.5rem;
        border: 2px solid #004080;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #004080;
        font-family: 'Oswald', sans-serif !important;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: #004080;
        color: white;
        border-radius: 8px;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #e7f3ff;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #004080;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #003366;
    }
    
    /* Main content text */
    p, li, span {
        font-family: 'Oswald', sans-serif !important;
        color: #333333 !important;
    }
    
    strong {
        color: #004080 !important;
    }
    
    /* Links */
    a {
        color: #004080 !important;
        text-decoration: none;
    }
    
    a:hover {
        color: #0066cc !important;
        text-decoration: underline;
    }
    
    /* Section Headers with Icon */
    .section-header {
        background: linear-gradient(135deg, #004080 0%, #0066cc 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 4px 15px rgba(0, 64, 128, 0.3);
    }
    
    .section-header .icon {
        background: white;
        color: #004080;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        font-weight: 700;
    }
    
    .section-header .title {
        font-size: 1.25rem;
        font-weight: 700;
        font-family: 'Oswald', sans-serif;
    }
    
    /* Stats Cards Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .stat-card {
        background: #ffffff;
        border: 2px solid #004080;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 64, 128, 0.25);
    }
    
    .stat-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: #004080;
        font-family: 'Oswald', sans-serif;
    }
    
    .stat-card .label {
        color: #666666;
        font-size: 0.9rem;
        font-family: 'Oswald', sans-serif;
    }
    
    /* Info Box */
    .info-box {
        background: #e7f3ff;
        border-left: 4px solid #004080;
        padding: 1rem 1.25rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    
    .info-box p {
        margin: 0;
        color: #004080 !important;
    }
    
    /* Feature Cards */
    .feature-card {
        background: #ffffff;
        border: 2px solid #004080;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .feature-card h4 {
        color: #004080;
        margin-bottom: 1rem;
        font-family: 'Oswald', sans-serif;
    }
    
    .feature-card ul {
        padding-left: 1.5rem;
    }
    
    .feature-card li {
        color: #333333;
        margin-bottom: 0.5rem;
    }
    
    /* Footer */
    .app-footer {
        background: linear-gradient(135deg, #004080 0%, #002855 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-top: 2rem;
    }
    
    .app-footer p {
        color: #ffffff !important;
        margin-bottom: 0.5rem;
    }
    
    .app-footer strong {
        color: #c4a000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Define country codes globally
COUNTRY_OPTIONS = {
    "Angola": "AGO",
    "Benin": "BEN",
    "Botswana": "BWA",
    "Burkina Faso": "BFA",
    "Burundi": "BDI",
    "Cameroon": "CMR",
    "Central African Republic": "CAF",
    "Chad": "TCD",
    "Democratic Republic of the Congo": "COD",
    "Equatorial Guinea": "GNQ",
    "Ethiopia": "ETH",
    "Gabon": "GAB",
    "Gambia": "GMB",
    "Ghana": "GHA",
    "Guinea": "GIN",
    "Guinea-Bissau": "GNB",
    "Ivory Coast": "CIV",
    "Kenya": "KEN",
    "Liberia": "LBR",
    "Madagascar": "MDG",
    "Malawi": "MWI",
    "Mali": "MLI",
    "Mauritania": "MRT",
    "Mozambique": "MOZ",
    "Namibia": "NAM",
    "Niger": "NER",
    "Nigeria": "NGA",
    "Republic of the Congo": "COG",
    "Rwanda": "RWA",
    "Senegal": "SEN",
    "Sierra Leone": "SLE",
    "South Africa": "ZAF",
    "South Sudan": "SSD",
    "Sudan": "SDN",
    "Tanzania": "TZA",
    "Togo": "TGO",
    "Uganda": "UGA",
    "Zambia": "ZMB",
    "Zimbabwe": "ZWE"
}

# WorldPop country codes (lowercase for URL construction)
WORLDPOP_CODES = {code: code.lower() for code in COUNTRY_OPTIONS.values()}

# Available years for WorldPop data (typically 2000-2020)
AVAILABLE_YEARS = list(range(2000, 2021))

# BACKEND CONFIGURATION FOR AGE/SEX DISAGGREGATION
AGE_GROUPS = {
    "Total Population": "ppp",
    "0-1 years": "0",
    "1-4 years": "1",
    "5-9 years": "5",
    "10-14 years": "10",
    "15-19 years": "15",
    "20-24 years": "20",
    "25-29 years": "25",
    "30-34 years": "30",
    "35-39 years": "35",
    "40-44 years": "40",
    "45-49 years": "45",
    "50-54 years": "50",
    "55-59 years": "55",
    "60-64 years": "60",
    "65-69 years": "65",
    "70-74 years": "70",
    "75-79 years": "75",
    "80+ years": "80"
}

SEX_OPTIONS = {
    "Male": "m",
    "Female": "f"
}

# Initialize session state variables
if 'data_source' not in st.session_state:
    st.session_state.data_source = "GADM Database"
if 'country' not in st.session_state:
    st.session_state.country = "Sierra Leone"
if 'country_code' not in st.session_state:
    st.session_state.country_code = "SLE"
if 'admin_level' not in st.session_state:
    st.session_state.admin_level = 1
if 'use_custom_shapefile' not in st.session_state:
    st.session_state.use_custom_shapefile = False

# Add caching for better performance
@st.cache_data
def check_file_exists(url):
    """Check if a file exists on server with timeout"""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

@st.cache_data
def download_shapefile_from_gadm(country_code, admin_level):
    """Download and load shapefiles directly from GADM website"""
    gadm_url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_{country_code}_shp.zip"
    
    try:
        # Download the zip file
        response = requests.get(gadm_url, timeout=120, stream=True)
        response.raise_for_status()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save zip file
            zip_path = os.path.join(tmpdir, f"gadm41_{country_code}.zip")
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            
            # Find the correct shapefile for the admin level
            shapefile_name = f"gadm41_{country_code}_{admin_level}.shp"
            shapefile_path = os.path.join(tmpdir, shapefile_name)
            
            if not os.path.exists(shapefile_path):
                available_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                available_levels = []
                for file in available_files:
                    if f"gadm41_{country_code}_" in file:
                        level = file.split('_')[-1].replace('.shp', '')
                        if level.isdigit():
                            available_levels.append(level)
                raise FileNotFoundError(f"Admin level {admin_level} not found for {country_code}. Available levels: {sorted(available_levels)}")
            
            # Load the shapefile
            gdf = gpd.read_file(shapefile_path)
            
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to download from GADM: {str(e)}")
    except zipfile.BadZipFile:
        raise ValueError("Downloaded file is not a valid zip file")
    except Exception as e:
        raise ValueError(f"Failed to process shapefile: {str(e)}")
    
    # Ensure CRS is set
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    
    return gdf

def load_uploaded_shapefile(shp_file, shx_file, dbf_file, prj_file=None):
    """Load shapefile from uploaded files with optional projection file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save uploaded files
        shp_path = os.path.join(tmpdir, "uploaded.shp")
        shx_path = os.path.join(tmpdir, "uploaded.shx") 
        dbf_path = os.path.join(tmpdir, "uploaded.dbf")
        prj_path = os.path.join(tmpdir, "uploaded.prj")
        
        with open(shp_path, "wb") as f:
            f.write(shp_file.getvalue())
        with open(shx_path, "wb") as f:
            f.write(shx_file.getvalue())
        with open(dbf_path, "wb") as f:
            f.write(dbf_file.getvalue())
        
        # Save projection file if provided
        projection_info = None
        if prj_file is not None:
            with open(prj_path, "wb") as f:
                f.write(prj_file.getvalue())
            
            # Read projection info for display
            try:
                with open(prj_path, "r") as f:
                    projection_info = f.read().strip()
            except Exception:
                projection_info = "Could not read projection file"
        
        try:
            # Load the shapefile (GeoPandas will automatically read .prj if it exists)
            gdf = gpd.read_file(shp_path)
        except Exception as e:
            raise ValueError(f"Failed to read uploaded shapefile: {str(e)}")
    
    # Handle coordinate reference system
    crs_source = None
    if gdf.crs is not None:
        crs_source = "from .prj file" if prj_file is not None else "detected automatically"
    else:
        # No CRS detected - assume WGS84
        st.warning("No coordinate reference system detected. Assuming WGS84 (EPSG:4326)")
        gdf = gdf.set_crs("EPSG:4326")
        crs_source = "assumed (WGS84)"
    
    return gdf, crs_source, projection_info

def construct_worldpop_url(country_code, year, age_group, sex):
    """Construct WorldPop download URL based on parameters"""
    country_lower = WORLDPOP_CODES[country_code]
    
    # For total population (both sexes, all ages)
    if age_group == "ppp" and sex == "both":
        # Unconstrained individual countries 2000-2020 UN adjusted
        url = f"https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/{country_code.upper()}/{country_lower}_ppp_{year}_UNadj_constrained.tif"
        return url
    
    # For age/sex disaggregated data
    else:
        # Age-sex structure data
        url = f"https://data.worldpop.org/GIS/AgeSex_structures/Global_2000_2020/{year}/{country_code.upper()}/{country_lower}_{sex}_{age_group}_{year}.tif"
        return url

@st.cache_data
def download_worldpop_data(country_code, year, age_group, sex):
    """Download WorldPop data and return the file content (cached version)"""
    
    url = construct_worldpop_url(country_code, year, age_group, sex)
    
    try:
        response = requests.get(url, timeout=180, stream=True)
        response.raise_for_status()
        
        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Download all data
        chunks = []
        for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
            if chunk:
                chunks.append(chunk)
        
        return b''.join(chunks), url, total_size
        
    except requests.exceptions.RequestException as e:
        # Try alternative URL formats if first attempt fails
        alt_urls = []
        
        # Alternative 1: Try constrained version
        if age_group == "ppp":
            country_lower = WORLDPOP_CODES[country_code]
            alt_url = f"https://data.worldpop.org/GIS/Population/Global_2000_2020/{year}/{country_code.upper()}/{country_lower}_ppp_{year}.tif"
            alt_urls.append(alt_url)
        
        for alt_url in alt_urls:
            try:
                response = requests.get(alt_url, timeout=180, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                chunks = []
                
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        chunks.append(chunk)
                
                return b''.join(chunks), alt_url, total_size
            except:
                continue
        
        raise ConnectionError(f"Failed to download WorldPop data for {country_code} {year}: {str(e)}\nTried URL: {url}")

def download_worldpop_data_with_progress(country_code, year, age_group, sex, progress_callback=None):
    """Download WorldPop data with progress tracking (non-cached wrapper)"""
    
    url = construct_worldpop_url(country_code, year, age_group, sex)
    
    try:
        response = requests.get(url, timeout=180, stream=True)
        response.raise_for_status()
        
        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Download with progress tracking
        chunks = []
        downloaded = 0
        
        for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
            if chunk:
                chunks.append(chunk)
                downloaded += len(chunk)
                
                # Update progress if callback provided
                if progress_callback and total_size > 0:
                    progress = (downloaded / total_size) * 100
                    progress_callback(progress, downloaded, total_size)
        
        return b''.join(chunks), url, total_size
        
    except requests.exceptions.RequestException as e:
        # Try alternative URL formats if first attempt fails
        alt_urls = []
        
        # Alternative 1: Try constrained version
        if age_group == "ppp":
            country_lower = WORLDPOP_CODES[country_code]
            alt_url = f"https://data.worldpop.org/GIS/Population/Global_2000_2020/{year}/{country_code.upper()}/{country_lower}_ppp_{year}.tif"
            alt_urls.append(alt_url)
        
        for alt_url in alt_urls:
            try:
                response = requests.get(alt_url, timeout=180, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                chunks = []
                downloaded = 0
                
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        chunks.append(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress, downloaded, total_size)
                
                return b''.join(chunks), alt_url, total_size
            except:
                continue
        
        raise ConnectionError(f"Failed to download WorldPop data for {country_code} {year}: {str(e)}\nTried URL: {url}")

def process_worldpop_data(_gdf, country_code, year, age_group, sex, progress_callback=None):
    """Process WorldPop population data with improved error handling and smart caching"""
    
    # Create a copy to avoid modifying the original
    gdf = _gdf.copy()
    
    # Try cached version first (no progress tracking, but instant if cached)
    try:
        worldpop_data, used_url, file_size = download_worldpop_data(country_code, year, age_group, sex)
        # If we get here, data was cached (fast)
    except:
        # If cached version fails, try with progress tracking
        worldpop_data, used_url, file_size = download_worldpop_data_with_progress(
            country_code, year, age_group, sex, progress_callback
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        tif_file_path = os.path.join(tmpdir, "worldpop.tif")
        
        # Save the downloaded data
        with open(tif_file_path, "wb") as f:
            f.write(worldpop_data)

        try:
            with rasterio.open(tif_file_path) as src:
                # Reproject geodataframe to match raster CRS
                gdf_reproj = gdf.to_crs(src.crs)
                
                total_pop = []
                mean_density = []
                valid_pixels_count = []
                
                for idx, geom in enumerate(gdf_reproj.geometry):
                    try:
                        masked_data, _ = rasterio.mask.mask(src, [geom], crop=True, nodata=src.nodata)
                        masked_data = masked_data.flatten()
                        
                        # Filter out nodata values
                        if src.nodata is not None:
                            valid_data = masked_data[masked_data != src.nodata]
                        else:
                            valid_data = masked_data
                        valid_data = valid_data[~np.isnan(valid_data)]
                        valid_data = valid_data[valid_data >= 0]  # Remove negative values
                        
                        if len(valid_data) > 0:
                            total_pop.append(np.sum(valid_data))
                            mean_density.append(np.mean(valid_data))
                            valid_pixels_count.append(len(valid_data))
                        else:
                            total_pop.append(0)
                            mean_density.append(0)
                            valid_pixels_count.append(0)
                    except Exception as e:
                        st.warning(f"Error processing geometry {idx}: {str(e)}")
                        total_pop.append(0)
                        mean_density.append(0)
                        valid_pixels_count.append(0)

                gdf["total_population"] = total_pop
                gdf["mean_density"] = mean_density
                gdf["valid_pixels"] = valid_pixels_count
                
        except rasterio.errors.RasterioIOError as e:
            raise ValueError(f"Failed to process raster file: {str(e)}")
    
    return gdf, used_url, file_size

def project_population(base_gdf, base_year, growth_rate, num_years):
    """Project population for multiple years using compound growth formula."""
    projected_data = {}
    growth_factor = 1 + (growth_rate / 100)
    years = list(range(base_year + 1, base_year + 1 + num_years))
    
    for year_idx, proj_year in enumerate(years):
        projected_gdf = base_gdf.copy()
        years_from_base = year_idx + 1
        projected_gdf['total_population'] = base_gdf['total_population'] * (growth_factor ** years_from_base)
        projected_gdf['mean_density'] = base_gdf['mean_density'] * (growth_factor ** years_from_base)
        projected_data[proj_year] = projected_gdf
    
    return projected_data

# ICF-SL Header with Logo
st.markdown("""
<div style="background: linear-gradient(135deg, #004080 0%, #0066cc 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 8px 25px rgba(0, 64, 128, 0.3);">
    <div style="display: flex; align-items: center; justify-content: center; gap: 1.5rem;">
        <div style="background: white; padding: 0.75rem 1.5rem; border-radius: 10px;">
            <span style="font-family: 'Oswald', sans-serif; font-weight: 700; font-size: 1.5rem; color: #004080;">ICF-SL</span>
        </div>
        <div style="text-align: center;">
            <h1 style="color: white !important; font-family: 'Oswald', sans-serif; font-size: 2rem; margin: 0;">WorldPop Population Analysis</h1>
            <p style="color: #e7f3ff; font-family: 'Oswald', sans-serif; margin: 0.5rem 0 0 0;">Analyze population distribution for public health planning</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="background: white; padding: 0.5rem 1rem; border-radius: 8px; display: inline-block;">
            <span style="font-family: 'Oswald', sans-serif; font-weight: 700; color: #004080;">ICF-SL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## ⚙️ Analysis Parameters")
    
    # Data source selection
    data_source = st.radio(
        "📁 Data Source", 
        ["GADM Database", "Upload Custom Shapefile"],
        help="Choose between official GADM boundaries or upload your own shapefile"
    )
    st.session_state.data_source = data_source
    
    if data_source == "GADM Database":
        # Country and admin level selection
        country = st.selectbox("🌍 Select Country", list(COUNTRY_OPTIONS.keys()), 
                              index=list(COUNTRY_OPTIONS.keys()).index("Sierra Leone"),
                              help="Select any African country")
        admin_level = st.selectbox("📊 Administrative Level", [0, 1, 2, 3, 4], 
                                  index=2,
                                  help="0=Country, 1=Regions, 2=Districts, 3=Communes, 4=Localities")
        
        level_descriptions = {
            0: "Country boundary",
            1: "First-level admin (regions/states)",
            2: "Second-level admin (districts/provinces)", 
            3: "Third-level admin (communes/counties)",
            4: "Fourth-level admin (localities/wards)"
        }
        st.caption(f"Level {admin_level}: {level_descriptions.get(admin_level, 'Administrative division')}")
        
        country_code = COUNTRY_OPTIONS[country]
        use_custom_shapefile = False
        
        st.session_state.country = country
        st.session_state.country_code = country_code
        st.session_state.admin_level = admin_level
        st.session_state.use_custom_shapefile = False
        
    else:
        st.markdown("**📤 Upload Shapefile Components**")
        
        shp_file = st.file_uploader("Shapefile (.shp)", type=['shp'])
        shx_file = st.file_uploader("Shape Index (.shx)", type=['shx'])
        dbf_file = st.file_uploader("Attribute Table (.dbf)", type=['dbf'])
        prj_file = st.file_uploader("Projection File (.prj)", type=['prj'])
        
        if shp_file and shx_file and dbf_file:
            st.success("✅ Required files uploaded!")
            use_custom_shapefile = True
        else:
            use_custom_shapefile = False
            st.info("Please upload .shp, .shx, and .dbf files")
        
        country = "Custom Area"
        country_code = "CUSTOM"
        admin_level = "Custom"
        
        st.session_state.country = country
        st.session_state.country_code = country_code
        st.session_state.admin_level = admin_level
        st.session_state.use_custom_shapefile = use_custom_shapefile

    st.markdown("---")
    
    st.markdown("### 📅 Year Selection & Projection")
    
    enable_projection = st.checkbox("Enable Multi-Year Projection", value=False)
    
    if enable_projection:
        year = 2020
        st.info("📊 **2020 selected as baseline** for projections")
        
        col_proj1, col_proj2 = st.columns(2)
        
        with col_proj1:
            projection_years = st.number_input("Years to Project", min_value=1, max_value=20, value=5, step=1)
        
        with col_proj2:
            growth_rate = st.number_input("Growth Rate (%)", min_value=-10.0, max_value=10.0, value=2.5, step=0.1, format="%.2f")
        
        projected_years_list = list(range(2021, 2021 + projection_years))
        
        if growth_rate >= 0:
            st.success(f"📈 Projecting growth: {projected_years_list[0]}-{projected_years_list[-1]} at {growth_rate}%")
        else:
            st.warning(f"📉 Projecting decline: {projected_years_list[0]}-{projected_years_list[-1]} at {growth_rate}%")
    
    else:
        year = st.selectbox("Select Year", AVAILABLE_YEARS, index=len(AVAILABLE_YEARS)-1)
        projection_years = 0
        growth_rate = 0.0
        projected_years_list = []
        st.info(f"📅 Single year analysis: **{year}**")
    
    st.markdown("---")
    
    st.markdown("### 👥 Population Parameters")
    
    analysis_type = st.radio("Analysis Type", ["Total Population", "Age/Sex Disaggregated"])
    
    if analysis_type == "Total Population":
        age_group = "ppp"
        sex = "both"
        st.info("Analyzing total population (all ages, both sexes)")
    else:
        age_group_name = st.selectbox("Age Group", list(AGE_GROUPS.keys())[1:])
        age_group = AGE_GROUPS[age_group_name]
        
        sex_name = st.selectbox("Sex", list(SEX_OPTIONS.keys()))
        sex = SEX_OPTIONS[sex_name]
        
        st.info(f"Analyzing: {age_group_name}, {sex_name}")

    st.markdown("---")
    
    st.markdown("### 🎨 Display Options")
    show_statistics = st.checkbox("Show Statistics", value=True)
    color_scheme = st.selectbox("Color Scheme", ["YlOrRd", "viridis", "plasma", "Reds", "Blues", "Purples"])

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🚀 Generate Analysis", type="primary", use_container_width=True):
        if st.session_state.data_source == "Upload Custom Shapefile" and not st.session_state.use_custom_shapefile:
            st.error("Please upload all required shapefile components (.shp, .shx, .dbf)")
        else:
            progress_container = st.container()
            status_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
            with status_container:
                status_text = st.empty()
            
            try:
                if st.session_state.data_source == "GADM Database":
                    status_text.text(f"Downloading {st.session_state.country} shapefile from GADM...")
                    progress_bar.progress(20)
                    
                    gdf = download_shapefile_from_gadm(st.session_state.country_code, st.session_state.admin_level)
                    st.success(f"✅ {st.session_state.country} Admin Level {st.session_state.admin_level} loaded ({len(gdf)} features)")
                    
                else:
                    status_text.text("Processing uploaded shapefile...")
                    progress_bar.progress(20)
                    
                    gdf, crs_source, projection_info = load_uploaded_shapefile(shp_file, shx_file, dbf_file, prj_file)
                    st.success(f"✅ Custom shapefile loaded ({len(gdf)} features)")
                
                status_text.text(f"Downloading WorldPop population data ({year})...")
                progress_bar.progress(40)
                
                download_status = st.empty()
                
                def update_download_progress(percent, downloaded, total):
                    mb_downloaded = downloaded / (1024*1024)
                    mb_total = total / (1024*1024)
                    download_status.info(f"Downloading: {mb_downloaded:.1f} MB / {mb_total:.1f} MB ({percent:.1f}%)")
                
                try:
                    if st.session_state.data_source == "GADM Database":
                        processed_gdf_base, used_url, file_size = process_worldpop_data(
                            gdf, st.session_state.country_code, year, age_group, sex, 
                            progress_callback=update_download_progress
                        )
                    else:
                        st.warning("Custom shapefile: Using Sierra Leone (SLE) WorldPop data as default.")
                        processed_gdf_base, used_url, file_size = process_worldpop_data(
                            gdf, "SLE", year, age_group, sex,
                            progress_callback=update_download_progress
                        )
                    
                    download_status.empty()
                    
                    file_size_mb = file_size / (1024*1024) if file_size > 0 else 0
                    st.success(f"✅ Population data ({year}) processed successfully ({file_size_mb:.1f} MB)")
                    
                except Exception as e:
                    download_status.empty()
                    st.error(f"Error processing population data: {str(e)}")
                    st.stop()

                all_years_data = {year: processed_gdf_base}
                
                if enable_projection:
                    status_text.text(f"Generating population projections from {year}...")
                    progress_bar.progress(60)
                    
                    projected_data = project_population(processed_gdf_base, year, growth_rate, projection_years)
                    all_years_data.update(projected_data)
                    
                    st.success(f"✅ Population projected for {len(projected_data)} years using {growth_rate}% annual growth")
                
                status_text.text("Generating maps...")
                progress_bar.progress(80)
                
                all_figures = {}
                
                for proj_year in sorted(all_years_data.keys()):
                    year_gdf = all_years_data[proj_year]
                    
                    if year_gdf['total_population'].sum() == 0:
                        st.error(f"No valid population data for year {proj_year}")
                        continue
                    
                    fig, ax = plt.subplots(1, 1, figsize=(12, 10), facecolor='white')
                    ax.set_facecolor('white')
                    
                    year_gdf.plot(
                        column="total_population",
                        ax=ax,
                        legend=True,
                        cmap=color_scheme,
                        edgecolor="black",
                        linewidth=0.5,
                        legend_kwds={"shrink": 0.8, "label": "Population"},
                        missing_kwds={"color": "#e5e5e5", "label": "No data"}
                    )
                    
                    if proj_year == year:
                        title = f"{st.session_state.country} - Population ({proj_year}) [Baseline]"
                    else:
                        title = f"{st.session_state.country} - Population ({proj_year}) [Projected]"
                    
                    ax.set_title(title, fontweight='bold', fontsize=14, color='#004080', pad=20)
                    ax.set_axis_off()
                    
                    plt.tight_layout()
                    all_figures[proj_year] = fig
                
                progress_bar.progress(100)
                status_text.text("Analysis complete!")
                time.sleep(0.5)
                status_text.empty()
                
                st.success(f"✅ Analysis completed! Generated maps for {len(all_figures)} year(s)")
                
                # Display maps with ICF-SL styling
                st.markdown("""
                <div class="section-header">
                    <div class="icon">🗺️</div>
                    <div class="title">POPULATION MAPS</div>
                </div>
                """, unsafe_allow_html=True)
                
                for proj_year in sorted(all_figures.keys()):
                    label = "[Baseline]" if proj_year == year else "[Projected]"
                    st.markdown(f"### Year {proj_year} {label}")
                    st.pyplot(all_figures[proj_year])
                
                # Download section
                st.markdown("""
                <div class="section-header">
                    <div class="icon">📥</div>
                    <div class="title">DOWNLOAD RESULTS</div>
                </div>
                """, unsafe_allow_html=True)
                
                col_pdf, col_csv = st.columns(2)
                
                with col_pdf:
                    pdf_buffer = BytesIO()
                    with PdfPages(pdf_buffer) as pdf:
                        for proj_year in sorted(all_figures.keys()):
                            pdf.savefig(all_figures[proj_year], dpi=300, bbox_inches='tight', facecolor='white')
                    
                    pdf_buffer.seek(0)
                    
                    st.download_button(
                        label=f"📄 Download Maps (PDF - {len(all_figures)} pages)",
                        data=pdf_buffer,
                        file_name=f"worldpop_maps_{st.session_state.country_code}_{year}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                with col_csv:
                    all_years_combined = []
                    for proj_year in sorted(all_years_data.keys()):
                        year_gdf = all_years_data[proj_year].copy()
                        year_gdf = year_gdf.drop(columns='geometry')
                        year_gdf['year'] = proj_year
                        year_gdf['is_baseline'] = (proj_year == year)
                        all_years_combined.append(year_gdf)
                    
                    download_df = pd.concat(all_years_combined, ignore_index=True)
                    csv_data = download_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📊 Download Data (CSV)",
                        data=csv_data,
                        file_name=f"worldpop_population_{st.session_state.country_code}_{year}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                # Statistics section
                if show_statistics:
                    st.markdown("""
                    <div class="section-header">
                        <div class="icon">📈</div>
                        <div class="title">POPULATION STATISTICS</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for proj_year in sorted(all_years_data.keys()):
                        year_gdf = all_years_data[proj_year]
                        label = "(Baseline)" if proj_year == year else "(Projected)"
                        
                        st.markdown(f"### Year {proj_year} {label}")
                        
                        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                        
                        with col_stat1:
                            total = year_gdf['total_population'].sum()
                            st.metric("Total Population", f"{total:,.0f}")
                        
                        with col_stat2:
                            mean_pop = year_gdf['total_population'].mean()
                            st.metric("Mean per Unit", f"{mean_pop:,.0f}")
                        
                        with col_stat3:
                            max_pop = year_gdf['total_population'].max()
                            st.metric("Maximum", f"{max_pop:,.0f}")
                        
                        with col_stat4:
                            min_pop = year_gdf['total_population'].min()
                            st.metric("Minimum", f"{min_pop:,.0f}")

            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    st.markdown("""
    <div class="section-header">
        <div class="icon">ℹ️</div>
        <div class="title">ABOUT THIS TOOL</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    **WorldPop Population Analysis Tool**
    
    Analyze high-resolution population distribution data for public health planning.
    
    ---
    
    **📊 Data Sources:**
    - WorldPop: High-resolution global population
    - GADM: Global Administrative Areas database
    
    ---
    
    **🌍 Coverage:**
    - All African countries
    - Admin levels 0-4
    - Years: 2000-2020
    - ~100m resolution
    
    ---
    
    **💡 Usage Tips:**
    - Use level 2-3 for district analysis
    - 2020 has the most recent data
    - Enable projection for future estimates
    - Growth rates can be negative
    - First download may be slow (50-200 MB)
    
    ---
    
    **🏥 Public Health Uses:**
    - SMC target population
    - ITN distribution planning
    - Immunization coverage
    - Health facility planning
    - Survey sample calculation
    """)

# ICF-SL Footer
st.markdown("""
<div class="app-footer">
    <p><strong>Informatics Consultancy Firm - Sierra Leone (ICF-SL)</strong></p>
    <p>Built for public health professionals and researchers</p>
    <p><strong>Contact:</strong> Mohamed Sillah Kanu</p>
    <p><strong>Email:</strong> mohamed.kanu@informaticsconsultancyfirm.com</p>
    <p style="margin-top: 1rem;"><strong>Data Sources:</strong> WorldPop (www.worldpop.org) | GADM (gadm.org)</p>
    <p style="margin-top: 1rem; font-size: 0.9rem;">Supported by the National Malaria Control Programme (NMCP)</p>
</div>
""", unsafe_allow_html=True)
