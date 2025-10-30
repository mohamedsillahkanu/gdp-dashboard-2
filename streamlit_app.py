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

# Set page config with custom theme
st.set_page_config(
    page_title="WorldPop Population Analysis",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS matching the blue dark theme from HTML
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* Global theme variables */
    :root {
        --primary-blue: #2563eb;
        --secondary-blue: #3b82f6;
        --dark-bg: #0a0e1a;
        --card-bg: rgba(15, 23, 42, 0.95);
        --card-border: rgba(37, 99, 235, 0.2);
        --text-primary: #e1effe;
        --text-secondary: #93c5fd;
        --accent-cyan: #06b6d4;
    }
    
    /* Main app background - Pure dark */
    .stApp {
        background: #0a0e1a;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Sidebar styling - Pure dark */
    [data-testid="stSidebar"] {
        background: #0f172a;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(37, 99, 235, 0.2);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #ffffff;
    }
    
    [data-testid="stSidebar"] p {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }
    
    /* Sidebar headers */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    [data-testid="stSidebar"] h1 strong,
    [data-testid="stSidebar"] h2 strong,
    [data-testid="stSidebar"] h3 strong {
        color: #93c5fd !important;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Headers with pure dark background */
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
    
    /* Card-like containers - Pure dark */
    [data-testid="stExpander"] {
        background: #0f172a;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        margin-bottom: 1rem;
    }
    
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
        color: #ffffff;
    }
    
    [data-testid="stExpander"] p {
        color: #ffffff !important;
    }
    
    [data-testid="stExpander"] li {
        color: #ffffff !important;
    }
    
    [data-testid="stExpander"] strong {
        color: #93c5fd !important;
    }
    
    /* Expander header styling - Pure dark */
    .streamlit-expanderHeader {
        background: #1e293b;
        color: #ffffff !important;
        font-weight: 600;
        border-radius: 12px;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }
    
    .streamlit-expanderHeader:hover {
        background: #334155;
        border-color: rgba(96, 165, 250, 0.5);
    }
    
    /* Buttons - Light blue accent */
    .stButton > button {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 15px rgba(96, 165, 250, 0.3);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(96, 165, 250, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Download buttons - Light blue accent */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(96, 165, 250, 0.3);
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(96, 165, 250, 0.4);
    }
    
    /* Select boxes and inputs - Dark background with light blue text */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextInput > div > div,
    .stNumberInput > div > div {
        background: #0f172a !important;
        border: 2px solid #60a5fa !important;
        border-radius: 12px !important;
        color: #93c5fd !important;
    }
    
    .stSelectbox > div > div:focus-within,
    .stMultiSelect > div > div:focus-within,
    .stTextInput > div > div:focus-within {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.3) !important;
    }
    
    /* Selectbox text and options */
    .stSelectbox label,
    .stMultiSelect label {
        color: #93c5fd !important;
    }
    
    /* Dropdown menu styling - Dark with light blue text */
    [data-baseweb="select"] > div {
        background-color: #0a0e1a !important;
        color: #93c5fd !important;
    }
    
    /* Dropdown input field */
    [data-baseweb="select"] input {
        color: #93c5fd !important;
        background-color: #0a0e1a !important;
    }
    
    /* Dropdown selected value */
    [data-baseweb="select"] [data-baseweb="tag"] {
        background-color: rgba(96, 165, 250, 0.2) !important;
        color: #93c5fd !important;
    }
    
    /* Dropdown menu container - Pure black/dark */
    [role="listbox"] {
        background-color: #0a0e1a !important;
        border: 1px solid rgba(96, 165, 250, 0.4) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(15px) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8) !important;
    }
    
    /* Dropdown menu options - Light blue text on dark - FIXED */
    [role="option"] {
        background-color: #0a0e1a !important;
        color: #93c5fd !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    [role="option"]:hover {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    [role="option"][aria-selected="true"] {
        background-color: rgba(96, 165, 250, 0.3) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Additional dropdown option styling - FIXED */
    [data-baseweb="menu"] [role="option"] div {
        color: #93c5fd !important;
    }
    
    [data-baseweb="menu"] [role="option"]:hover div {
        color: #ffffff !important;
    }
    
    /* Force all text inside dropdowns to be visible - FIXED */
    [data-baseweb="popover"] * {
        color: #93c5fd !important;
    }
    
    [data-baseweb="popover"] [role="option"]:hover * {
        color: #ffffff !important;
    }
    
    /* Dropdown arrow icon - Light blue */
    [data-baseweb="select"] svg {
        color: #93c5fd !important;
    }
    
    /* Force dropdown popover to be dark */
    [data-baseweb="popover"] {
        background-color: #0a0e1a !important;
    }
    
    /* Additional dropdown styling for menu */
    [data-baseweb="menu"] {
        background-color: #0a0e1a !important;
    }
    
    ul[role="listbox"] {
        background-color: #0a0e1a !important;
    }
    
    /* Input text color - Light blue */
    input, textarea {
        color: #93c5fd !important;
        background-color: #0f172a !important;
    }
    
    input::placeholder, textarea::placeholder {
        color: #6b7280 !important;
    }
    
    /* Radio buttons - Pure dark */
    .stRadio > div {
        background: #0f172a;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }
    
    .stRadio > div > label {
        color: #ffffff !important;
    }
    
    .stRadio label {
        color: #ffffff !important;
    }
    
    /* Radio button options */
    .stRadio [role="radiogroup"] label {
        color: #ffffff !important;
    }
    
    /* Checkboxes */
    .stCheckbox > label {
        color: #ffffff !important;
    }
    
    .stCheckbox label span {
        color: #ffffff !important;
    }
    
    /* File uploader - Pure dark */
    [data-testid="stFileUploader"] {
        background: #0f172a;
        border: 2px dashed #60a5fa;
        border-radius: 15px;
        padding: 2rem;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #93c5fd;
        box-shadow: 0 12px 40px rgba(96, 165, 250, 0.2);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #ffffff !important;
    }
    
    div[data-testid="metric-container"] {
        background: #0f172a;
        backdrop-filter: blur(15px);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(96, 165, 250, 0.3);
        transition: all 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(96, 165, 250, 0.3);
        border-color: rgba(96, 165, 250, 0.5);
    }
    
    /* Success/Info/Warning/Error messages - Pure dark */
    .stSuccess {
        background: #0f172a;
        backdrop-filter: blur(15px);
        color: #ffffff;
        border: 1px solid rgba(96, 165, 250, 0.5);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(96, 165, 250, 0.2);
    }
    
    .stInfo {
        background: #0f172a;
        backdrop-filter: blur(15px);
        color: #ffffff;
        border: 1px solid rgba(96, 165, 250, 0.5);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(96, 165, 250, 0.2);
    }
    
    .stWarning {
        background: #0f172a;
        backdrop-filter: blur(15px);
        color: #ffffff;
        border: 1px solid rgba(96, 165, 250, 0.5);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(96, 165, 250, 0.2);
    }
    
    .stError {
        background: #0f172a;
        backdrop-filter: blur(15px);
        color: #ffffff;
        border: 1px solid rgba(220, 38, 38, 0.4);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.2);
    }
    
    /* Progress bar - Light blue */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        border-radius: 10px;
    }
    
    /* Dataframe - Pure dark */
    [data-testid="stDataFrame"] {
        background: #0f172a;
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    /* Tables - Pure dark */
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
    
    /* Tabs - Pure dark */
    .stTabs [data-baseweb="tab-list"] {
        background: #0f172a;
        border-radius: 12px;
        padding: 0.5rem;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #ffffff;
        font-weight: 600;
        border-radius: 8px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        color: white;
    }
    
    /* Spinner - Light blue */
    .stSpinner > div {
        border-top-color: #60a5fa !important;
    }
    
    /* Code blocks */
    code {
        background: rgba(10, 14, 26, 0.95);
        color: #93c5fd;
        padding: 0.2rem 0.4rem;
        border-radius: 6px;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }
    
    pre {
        background: rgba(10, 14, 26, 0.95);
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
    
    .badge-csv {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white;
    }
    
    .badge-excel {
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        color: white;
    }
    
    .badge-gadm {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
    }
    
    .badge-custom {
        background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
        color: white;
    }
    
    /* Links */
    a {
        color: #60a5fa !important;
        text-decoration: none;
        transition: color 0.3s ease;
    }
    
    a:hover {
        color: #93c5fd !important;
        text-decoration: underline;
    }
    
    /* Divider */
    hr {
        border-color: rgba(37, 99, 235, 0.2);
        margin: 2rem 0;
    }
    
    /* Caption text */
    .stCaptionContainer {
        color: #6b7280 !important;
    }
    
    /* Text color - Light blue and white theme */
    p, li, span, label {
        color: #ffffff !important;
    }
    
    /* Markdown text */
    [data-testid="stMarkdownContainer"] {
        color: #ffffff;
    }
    
    /* Strong/bold text - Light blue */
    strong {
        color: #93c5fd !important;
        font-weight: 600;
    }
    
    /* All headings - Light blue */
    h1, h2, h3, h4, h5, h6 {
        color: #93c5fd !important;
    }
    
    /* Paragraph text */
    p {
        color: #ffffff !important;
    }
    
    /* List items */
    ul li, ol li {
        color: #ffffff !important;
    }
    
    /* Make plotly charts have dark background */
    .js-plotly-plot {
        background: rgba(15, 23, 42, 0.5) !important;
        border-radius: 12px;
    }
    
    /* Footer styling - Pure dark */
    footer {
        background: #0f172a;
        border-top: 1px solid rgba(96, 165, 250, 0.3);
        color: #6b7280;
    }
    
    /* Animation for hover effects */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: .8;
        }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        h1 {
            font-size: 1.75rem;
            padding: 1.5rem 1rem;
        }
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

def project_population(base_gdf, growth_rate, num_years):
    """
    Project population for multiple years using compound growth formula.
    Always uses 2020 as the baseline year and projects forward.
    
    Parameters:
    - base_gdf: GeoDataFrame with 2020 population data
    - growth_rate: Annual growth rate as percentage (e.g., 2.5 for 2.5%, -1.5 for -1.5%)
    - num_years: Number of years to project from 2020 (e.g., 5 means 2021-2025)
    
    Returns:
    - Dictionary with years as keys and projected GeoDataFrames as values
    
    Example:
    - base_gdf has 2020 population = 100,000
    - growth_rate = 2.5% (positive growth)
    - num_years = 5
    - Returns: {2021: 102,500, 2022: 105,063, ..., 2025: 113,141}
    
    - If growth_rate = -1.5% (negative/decline)
    - Returns: {2021: 98,500, 2022: 97,023, ..., 2025: 92,774}
    """
    projected_data = {}
    
    # Calculate growth factor (works for both positive and negative rates)
    growth_factor = 1 + (growth_rate / 100)
    
    # Always project forward from 2020
    # Year 2021 = 2020 + 1 year, Year 2022 = 2020 + 2 years, etc.
    years = list(range(2021, 2021 + num_years))
    
    for year_idx, proj_year in enumerate(years):
        # Create a copy of the base geodataframe (2020 data)
        projected_gdf = base_gdf.copy()
        
        # Years from 2020 baseline: 1, 2, 3, 4, 5, ...
        years_from_2020 = year_idx + 1
        
        # Apply compound growth formula: P(year) = P(2020) * (1 + r)^t
        # Where t = years from 2020
        # For positive growth: population increases
        # For negative growth: population decreases
        projected_gdf['total_population'] = base_gdf['total_population'] * (growth_factor ** years_from_2020)
        projected_gdf['mean_density'] = base_gdf['mean_density'] * (growth_factor ** years_from_2020)
        
        projected_data[proj_year] = projected_gdf
    
    return projected_data

# Main app layout with custom header
st.markdown("""
<h1>
    WorldPop Population Data Analysis
</h1>
<p style='text-align: center; color: #9ca3af; font-size: 1.2rem; margin-top: -1rem; margin-bottom: 2rem;'>
    Analyze population distribution for public health planning and intervention targeting
</p>
""", unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.markdown("## Analysis Parameters")
    
    # Data source selection
    data_source = st.radio(
        "Select Data Source", 
        ["GADM Database", "Upload Custom Shapefile"],
        help="Choose between official GADM boundaries or upload your own shapefile"
    )
    st.session_state.data_source = data_source
    
    if data_source == "GADM Database":
        # Country and admin level selection
        country = st.selectbox("Select Country", list(COUNTRY_OPTIONS.keys()), 
                              help="Select any African country")
        admin_level = st.selectbox("Administrative Level", [0, 1, 2, 3, 4], 
                                  help="0=Country, 1=Regions, 2=Districts, 3=Communes, 4=Localities")
        
        # Show admin level description
        level_descriptions = {
            0: "Country boundary",
            1: "First-level admin (regions/states)",
            2: "Second-level admin (districts/provinces)", 
            3: "Third-level admin (communes/counties)",
            4: "Fourth-level admin (localities/wards)"
        }
        st.caption(f"Level {admin_level}: {level_descriptions.get(admin_level, 'Administrative division')}")
        
        # Set variables for GADM mode
        country_code = COUNTRY_OPTIONS[country]
        use_custom_shapefile = False
        
        # Update session state
        st.session_state.country = country
        st.session_state.country_code = country_code
        st.session_state.admin_level = admin_level
        st.session_state.use_custom_shapefile = False
        
    else:  # Upload Custom Shapefile
        st.markdown("**Upload Shapefile Components**")
        st.caption("Upload all required files for your shapefile")
        
        # File uploaders - Required files
        shp_file = st.file_uploader("Shapefile (.shp)", type=['shp'], help="Main geometry file (required)")
        shx_file = st.file_uploader("Shape Index (.shx)", type=['shx'], help="Spatial index file (required)")
        dbf_file = st.file_uploader("Attribute Table (.dbf)", type=['dbf'], help="Attribute data file (required)")
        
        # Optional projection file
        prj_file = st.file_uploader("Projection File (.prj)", type=['prj'], 
                                   help="Coordinate system definition (optional but recommended)")
        
        # Check if required files are uploaded
        if shp_file and shx_file and dbf_file:
            st.success("Required files uploaded successfully!")
            use_custom_shapefile = True
            
            # Show file details
            with st.expander("File Details"):
                st.write(f"**SHP file**: {shp_file.name} ({shp_file.size:,} bytes)")
                st.write(f"**SHX file**: {shx_file.name} ({shx_file.size:,} bytes)")
                st.write(f"**DBF file**: {dbf_file.name} ({dbf_file.size:,} bytes)")
                if prj_file:
                    st.write(f"**PRJ file**: {prj_file.name} ({prj_file.size:,} bytes)")
                    st.success("Projection file included - coordinate system will be automatically detected!")
                else:
                    st.warning("No projection file - will assume WGS84 coordinate system")
        else:
            use_custom_shapefile = False
            st.info("Please upload .shp, .shx, and .dbf files to proceed")
            
            # Show upload requirements
            with st.expander("Shapefile Upload Requirements"):
                st.markdown("""
                **Required Files:**
                - **.shp**: Contains the geometry data
                - **.shx**: Spatial index for quick access
                - **.dbf**: Attribute table with feature data
                
                **Optional Files:**
                - **.prj**: Coordinate system definition (highly recommended)
                
                **Important Notes:**
                - All files must have the same base name
                - Maximum file size: 200MB per file
                - If no .prj file is provided, WGS84 coordinate system will be assumed
                - Including a .prj file prevents coordinate system errors
                - Ensure your shapefile contains administrative boundaries or areas of interest
                """)
        
        # Set variables for custom mode
        country = "Custom Area"
        country_code = "CUSTOM"
        admin_level = "Custom"
        
        # Update session state
        st.session_state.country = country
        st.session_state.country_code = country_code
        st.session_state.admin_level = admin_level
        st.session_state.use_custom_shapefile = use_custom_shapefile

    st.markdown("---")
    
    # Year selection and projection
    st.markdown("### Year Selection & Projection")
    
    # Base year (always 2020 for consistency)
    year = st.selectbox("Base Year (WorldPop Data)", [2020], 
                       help="2020 is used as baseline for all analyses and projections (most recent complete WorldPop data)")
    
    # Multi-year projection toggle
    enable_projection = st.checkbox("Enable Multi-Year Projection", value=False,
                                   help="Project population forward from 2020 using growth rate")
    
    if enable_projection:
        col_proj1, col_proj2 = st.columns(2)
        
        with col_proj1:
            projection_years = st.number_input(
                "Number of Years to Project",
                min_value=1,
                max_value=20,
                value=5,
                step=1,
                help="Number of years forward from 2020 (e.g., 5 = years 2021-2025)"
            )
        
        with col_proj2:
            growth_rate = st.number_input(
                "Annual Growth Rate (%)",
                min_value=-10.0,
                max_value=10.0,
                value=2.5,
                step=0.1,
                format="%.2f",
                help="Annual population growth rate from 2020 baseline (positive = growth, negative = decline)"
            )
        
        # Calculate projected years (always forward from 2020)
        projected_years_list = list(range(2021, 2021 + projection_years))
        
        if growth_rate >= 0:
            st.info(f"📈 Projecting **growth** for years: {', '.join(map(str, projected_years_list))} at {growth_rate}% annual rate")
        else:
            st.info(f"📉 Projecting **decline** for years: {', '.join(map(str, projected_years_list))} at {growth_rate}% annual rate")
    else:
        projection_years = 0
        growth_rate = 0.0
        projected_years_list = []
    
    st.markdown("---")
    
    # Population disaggregation options
    st.markdown("### Population Parameters")
    
    analysis_type = st.radio(
        "Analysis Type",
        ["Total Population", "Age/Sex Disaggregated"],
        help="Choose between total population or age/sex specific analysis"
    )
    
    if analysis_type == "Total Population":
        age_group = "ppp"
        sex = "both"
        st.info("Analyzing total population (all ages, both sexes)")
    else:
        age_group_name = st.selectbox("Age Group", list(AGE_GROUPS.keys())[1:], 
                                     help="Select specific age group")
        age_group = AGE_GROUPS[age_group_name]
        
        sex_name = st.selectbox("Sex", list(SEX_OPTIONS.keys()), 
                               help="Select sex for analysis")
        sex = SEX_OPTIONS[sex_name]
        
        st.info(f"Analyzing: {age_group_name}, {sex_name}")

    st.markdown("---")
    
    # Display options
    st.markdown("### Display Options")
    show_statistics = st.checkbox("Show Statistics", value=True)
    color_scheme = st.selectbox("Color Scheme", 
                               ["YlOrRd", "viridis", "plasma", "Reds", "Blues", "Purples"])

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    if st.button("Generate Analysis", type="primary", use_container_width=True):
        if st.session_state.data_source == "Upload Custom Shapefile" and not st.session_state.use_custom_shapefile:
            st.error("Please upload all required shapefile components (.shp, .shx, .dbf)")
        else:
            # Progress tracking
            progress_container = st.container()
            status_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
            with status_container:
                status_text = st.empty()
            
            try:
                # Step 1: Load shapefile (GADM or uploaded)
                if st.session_state.data_source == "GADM Database":
                    status_text.text("Checking GADM database...")
                    progress_bar.progress(10)
                    
                    status_text.text(f"Downloading {st.session_state.country} shapefile from GADM...")
                    progress_bar.progress(20)
                    
                    gdf = download_shapefile_from_gadm(st.session_state.country_code, st.session_state.admin_level)
                    st.success(f"{st.session_state.country} Admin Level {st.session_state.admin_level} shapefile loaded ({len(gdf)} features)")
                    
                else:  # Custom shapefile
                    status_text.text("Processing uploaded shapefile...")
                    progress_bar.progress(10)
                    
                    gdf, crs_source, projection_info = load_uploaded_shapefile(shp_file, shx_file, dbf_file, prj_file)
                    progress_bar.progress(20)
                    st.success(f"Custom shapefile loaded ({len(gdf)} features)")
                    
                    # Show coordinate system info
                    if gdf.crs:
                        st.info(f"Coordinate System: {gdf.crs} ({crs_source})")
                        if projection_info and prj_file:
                            with st.expander("Projection Details"):
                                st.code(projection_info, language="text")
                    
                    # Show attribute columns
                    attribute_cols = [col for col in gdf.columns if col != 'geometry']
                    if attribute_cols:
                        st.info(f"Available attributes: {', '.join(attribute_cols[:5])}{'...' if len(attribute_cols) > 5 else ''}")
                
                # Show some basic info about the shapefile
                if hasattr(gdf, 'NAME_1') and (st.session_state.data_source == "GADM Database" and st.session_state.admin_level >= 1):
                    region_names = gdf['NAME_1'].unique()[:5]
                    st.info(f"Contains regions: {', '.join(region_names)}{'...' if len(gdf['NAME_1'].unique()) > 5 else ''}")
                elif hasattr(gdf, 'NAME_0'):
                    st.info(f"Country: {gdf['NAME_0'].iloc[0]}")
                elif st.session_state.data_source == "Upload Custom Shapefile":
                    geom_types = gdf.geometry.type.unique()
                    st.info(f"Geometry types: {', '.join(geom_types)}")
                
                # Test WorldPop data availability
                status_text.text("Testing WorldPop data availability...")
                progress_bar.progress(30)
                
                test_url = construct_worldpop_url(st.session_state.country_code if st.session_state.data_source == "GADM Database" else "SLE", 
                                                 year, age_group, sex)
                
                # Step 2: Process WorldPop data for base year
                status_text.text(f"Downloading WorldPop population data ({year} baseline)...")
                progress_bar.progress(40)
                
                # Create download progress display
                download_status = st.empty()
                
                def update_download_progress(percent, downloaded, total):
                    mb_downloaded = downloaded / (1024*1024)
                    mb_total = total / (1024*1024)
                    download_status.info(f"Downloading: {mb_downloaded:.1f} MB / {mb_total:.1f} MB ({percent:.1f}%)")
                
                try:
                    if st.session_state.data_source == "GADM Database":
                        processed_gdf_2020, used_url, file_size = process_worldpop_data(
                            gdf, st.session_state.country_code, year, age_group, sex, 
                            progress_callback=update_download_progress
                        )
                    else:
                        # For custom shapefiles, need to specify a country code for WorldPop data
                        st.warning("Custom shapefile detected. Using Sierra Leone (SLE) WorldPop data as default.")
                        st.info("Tip: For accurate results with custom shapefiles, ensure they align with a specific country's boundaries")
                        processed_gdf_2020, used_url, file_size = process_worldpop_data(
                            gdf, "SLE", year, age_group, sex,
                            progress_callback=update_download_progress
                        )
                    
                    download_status.empty()  # Clear download progress
                    
                    file_size_mb = file_size / (1024*1024) if file_size > 0 else 0
                    st.success(f"Population data (2020 baseline) processed successfully (File size: {file_size_mb:.1f} MB)")
                    
                    with st.expander("Data Source URL"):
                        st.code(used_url, language="text")
                        if file_size_mb > 100:
                            st.info("Large file: This data is now cached. Subsequent analyses will be much faster!")
                    
                except Exception as e:
                    download_status.empty()
                    st.error(f"Error processing population data: {str(e)}")
                    st.stop()

                # Step 3: Generate projections if enabled
                all_years_data = {2020: processed_gdf_2020}  # Start with 2020 baseline
                
                if enable_projection:
                    status_text.text("Generating population projections from 2020 baseline...")
                    progress_bar.progress(60)
                    
                    projected_data = project_population(processed_gdf_2020, growth_rate, projection_years)
                    all_years_data.update(projected_data)
                    
                    st.success(f"Population projected for {len(projected_data)} years from 2020 baseline using {growth_rate}% annual growth rate")
                
                # Step 4: Generate visualizations for all years
                status_text.text("Generating maps for all years...")
                progress_bar.progress(80)
                
                # Create maps for each year
                all_figures = {}
                
                for proj_year in sorted(all_years_data.keys()):
                    year_gdf = all_years_data[proj_year]
                    
                    # Handle missing data
                    if year_gdf['total_population'].sum() == 0:
                        st.error(f"No valid population data found for year {proj_year}")
                        continue
                    
                    # Create visualization with white background for display
                    fig, ax = plt.subplots(1, 1, figsize=(12, 10), facecolor='white')
                    ax.set_facecolor('white')
                    
                    # Create the plot
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
                    
                    if analysis_type == "Total Population":
                        if proj_year == year:
                            title = f"{st.session_state.country} - Total Population ({proj_year}) [Baseline]"
                        else:
                            title = f"{st.session_state.country} - Total Population ({proj_year}) [Projected]"
                    else:
                        if proj_year == year:
                            title = f"{st.session_state.country} - {age_group_name}, {sex_name} ({proj_year}) [Baseline]"
                        else:
                            title = f"{st.session_state.country} - {age_group_name}, {sex_name} ({proj_year}) [Projected]"
                    
                    ax.set_title(title, fontweight='bold', fontsize=14, color='black', pad=20)
                    ax.set_axis_off()
                    
                    # Style the legend text to be black
                    legend = ax.get_legend()
                    if legend:
                        # Set legend text color to black
                        for text in legend.get_texts():
                            text.set_color('black')
                        # Set legend title color to black
                        legend.get_title().set_color('black')
                        # Set legend frame to match white theme
                        frame = legend.get_frame()
                        frame.set_facecolor('white')
                        frame.set_edgecolor('black')
                        frame.set_alpha(0.9)
                    
                    plt.tight_layout()
                    all_figures[proj_year] = fig
                
                # Complete the analysis
                progress_bar.progress(100)
                status_text.text("Analysis complete!")
                time.sleep(0.5)
                status_text.empty()
                
                st.success(f"Population analysis completed successfully! Generated maps for {len(all_figures)} year(s)")
                
                # Display all maps
                st.markdown("## Population Maps")
                
                for proj_year in sorted(all_figures.keys()):
                    st.markdown(f"### Year {proj_year}")
                    st.pyplot(all_figures[proj_year])
                
                # Add download all maps button (as PDF)
                st.markdown("### Download All Maps")
                
                col_pdf, col_images = st.columns(2)
                
                with col_pdf:
                    # Create PDF with all maps
                    pdf_buffer = BytesIO()
                    with PdfPages(pdf_buffer) as pdf:
                        for proj_year in sorted(all_figures.keys()):
                            pdf.savefig(all_figures[proj_year], dpi=300, bbox_inches='tight', facecolor='white')
                    
                    pdf_buffer.seek(0)
                    
                    # Create filename
                    pdf_filename = f"worldpop_maps_{st.session_state.country_code}"
                    if enable_projection:
                        pdf_filename += f"_{min(all_years_data.keys())}-{max(all_years_data.keys())}"
                    else:
                        pdf_filename += f"_{year}"
                    if analysis_type == "Age/Sex Disaggregated":
                        pdf_filename += f"_{age_group}_{sex}"
                    pdf_filename += ".pdf"
                    
                    st.download_button(
                        label=f"Download All Maps (PDF - {len(all_figures)} pages)",
                        data=pdf_buffer,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                with col_images:
                    st.info(f"**PDF Contains**:\n- {len(all_figures)} high-resolution maps\n- White background\n- Black text & legend\n- Print-ready quality (300 DPI)")

                # Show statistics if requested
                if show_statistics:
                    st.markdown("## Population Statistics")
                    
                    # Show stats for each year
                    for proj_year in sorted(all_years_data.keys()):
                        year_gdf = all_years_data[proj_year]
                        
                        st.markdown(f"### Year {proj_year} {' (Baseline)' if proj_year == year else ' (Projected)'}")
                        
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

                # Data download section
                st.markdown("## Download Data")
                
                # Prepare combined dataset for all years
                all_years_combined = []
                
                for proj_year in sorted(all_years_data.keys()):
                    year_gdf = all_years_data[proj_year].copy()
                    year_gdf = year_gdf.drop(columns='geometry')
                    year_gdf['year'] = proj_year
                    year_gdf['is_baseline'] = (proj_year == year)
                    year_gdf['is_projected'] = (proj_year != year)
                    all_years_combined.append(year_gdf)
                
                download_df = pd.concat(all_years_combined, ignore_index=True)
                
                # Add metadata columns
                download_df['area_name'] = st.session_state.country
                download_df['data_source'] = st.session_state.data_source
                download_df['analysis_type'] = analysis_type
                download_df['base_year'] = year
                
                if enable_projection:
                    download_df['projection_enabled'] = True
                    download_df['growth_rate_percent'] = growth_rate
                    download_df['projection_years'] = projection_years
                else:
                    download_df['projection_enabled'] = False
                    download_df['growth_rate_percent'] = None
                    download_df['projection_years'] = None
                
                if analysis_type == "Age/Sex Disaggregated":
                    download_df['age_group'] = age_group_name
                    download_df['sex'] = sex_name
                
                if st.session_state.data_source == "GADM Database":
                    download_df['country_code'] = st.session_state.country_code
                    download_df['admin_level'] = st.session_state.admin_level
                else:
                    download_df['country_code'] = "CUSTOM"
                    download_df['admin_level'] = "Custom"
                    if prj_file:
                        download_df['projection_source'] = "PRJ file provided"
                    else:
                        download_df['projection_source'] = "Assumed WGS84"
                
                # Reorder columns
                column_order = ['area_name', 'data_source', 'base_year', 'year', 'is_baseline', 'is_projected', 
                               'analysis_type', 'projection_enabled', 'growth_rate_percent', 'projection_years']
                
                if analysis_type == "Age/Sex Disaggregated":
                    column_order.extend(['age_group', 'sex'])
                
                if st.session_state.data_source == "GADM Database":
                    column_order.extend(['country_code', 'admin_level'])
                else:
                    column_order.extend(['country_code', 'admin_level', 'projection_source'])
                
                # Add name columns
                name_cols = [col for col in download_df.columns if col.startswith('NAME_')]
                column_order.extend(sorted(name_cols))
                
                # Add population columns
                column_order.extend(['total_population', 'mean_density', 'valid_pixels'])
                
                # Add remaining columns
                remaining_cols = [col for col in download_df.columns if col not in column_order]
                column_order.extend(remaining_cols)
                
                # Reorder
                available_cols = [col for col in column_order if col in download_df.columns]
                download_df = download_df[available_cols]
                
                # Create download buttons
                col_csv, col_excel = st.columns(2)
                
                with col_csv:
                    csv_data = download_df.to_csv(index=False)
                    filename_base = f"worldpop_population_{st.session_state.country_code}"
                    if enable_projection:
                        filename_base += f"_{min(all_years_data.keys())}-{max(all_years_data.keys())}"
                    else:
                        filename_base += f"_{year}"
                    
                    if st.session_state.data_source == "Upload Custom Shapefile":
                        filename_base = f"worldpop_population_custom"
                        if enable_projection:
                            filename_base += f"_{min(all_years_data.keys())}-{max(all_years_data.keys())}"
                        else:
                            filename_base += f"_{year}"
                    elif st.session_state.data_source == "GADM Database":
                        filename_base = f"worldpop_population_{st.session_state.country_code}"
                        if enable_projection:
                            filename_base += f"_{min(all_years_data.keys())}-{max(all_years_data.keys())}"
                        else:
                            filename_base += f"_{year}"
                        filename_base += f"_admin{st.session_state.admin_level}"
                    
                    if analysis_type == "Age/Sex Disaggregated":
                        filename_base += f"_{age_group}_{sex}"
                    
                    st.download_button(
                        label="Download as CSV",
                        data=csv_data,
                        file_name=f"{filename_base}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_excel:
                    # Create Excel file in memory
                    excel_buffer = BytesIO()
                    
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        # Main data sheet
                        download_df.to_excel(writer, sheet_name='Population_Data', index=False)
                        
                        # Summary statistics sheet (for all years)
                        summary_data = []
                        for proj_year in sorted(all_years_data.keys()):
                            year_data = download_df[download_df['year'] == proj_year]
                            summary_data.append({
                                'Year': proj_year,
                                'Type': 'Baseline' if proj_year == 2020 else 'Projected',
                                'Total Population': f"{year_data['total_population'].sum():,.0f}",
                                'Mean per Unit': f"{year_data['total_population'].mean():,.0f}",
                                'Std Dev': f"{year_data['total_population'].std():,.0f}",
                                'Minimum': f"{year_data['total_population'].min():,.0f}",
                                'Maximum': f"{year_data['total_population'].max():,.0f}",
                                'Units Analyzed': len(year_data)
                            })
                        
                        summary_stats = pd.DataFrame(summary_data)
                        summary_stats.to_excel(writer, sheet_name='Summary_Stats', index=False)
                        
                        # Metadata sheet
                        metadata_values = [
                            st.session_state.country,
                            st.session_state.data_source,
                            st.session_state.country_code,
                            str(st.session_state.admin_level) if st.session_state.data_source == "GADM Database" else "Custom",
                            year,
                            "Yes" if enable_projection else "No",
                            f"{growth_rate}%" if enable_projection else "N/A",
                            f"{projection_years} years" if enable_projection else "N/A",
                            ', '.join(map(str, sorted(all_years_data.keys()))),
                            analysis_type,
                            'WorldPop Unconstrained',
                            'GADM v4.1' if st.session_state.data_source == "GADM Database" else 'User Upload',
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            len(download_df),
                            'WorldPop Population Analysis Tool v2.0'
                        ]
                        
                        metadata_params = [
                            'Area Name', 'Data Source', 'Country Code', 'Admin Level', 'Base Year',
                            'Projection Enabled', 'Growth Rate', 'Projection Period', 'Years Included',
                            'Analysis Type', 'Population Source', 'Boundary Source', 'Generated On',
                            'Total Records', 'Tool Version'
                        ]
                        
                        if analysis_type == "Age/Sex Disaggregated":
                            metadata_values.extend([age_group_name, sex_name])
                            metadata_params.extend(['Age Group', 'Sex'])
                        
                        if st.session_state.data_source == "Upload Custom Shapefile":
                            metadata_values.extend([
                                crs_source if 'crs_source' in locals() else "Unknown",
                                "Yes" if prj_file else "No"
                            ])
                            metadata_params.extend(['Coordinate System', 'PRJ File Included'])
                        
                        metadata = pd.DataFrame({
                            'Parameter': metadata_params,
                            'Value': metadata_values
                        })
                        metadata.to_excel(writer, sheet_name='Metadata', index=False)
                    
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="Download as Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"{filename_base}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                # Show data preview
                with st.expander("Preview Downloaded Data"):
                    st.dataframe(download_df.head(20), use_container_width=True)
                    st.caption(f"Showing first 20 rows of {len(download_df)} total records ({len(all_years_data)} years × {len(all_years_data[year])} units)")

            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
                st.error("Please try again or contact support if the issue persists.")
                
                with st.expander("Debug Information"):
                    st.write(f"Data Source: {st.session_state.data_source}")
                    if st.session_state.data_source == "GADM Database":
                        st.write(f"Country: {st.session_state.country}")
                        st.write(f"Country Code: {st.session_state.country_code}")
                        st.write(f"Admin Level: {st.session_state.admin_level}")
                    st.write(f"Year: {year}")
                    st.write(f"Analysis Type: {analysis_type}")
                    st.write(f"Projection Enabled: {enable_projection}")
                    if enable_projection:
                        st.write(f"Growth Rate: {growth_rate}%")
                        st.write(f"Projection Years: {projection_years}")
                    if analysis_type == "Age/Sex Disaggregated":
                        st.write(f"Age Group: {age_group_name}")
                        st.write(f"Sex: {sex_name}")

with col2:
    st.markdown("## About This Tool")
    st.markdown("""
    **WorldPop Population Analysis Tool**
    
    This tool analyzes high-resolution population distribution data for public health planning and intervention targeting.
    
    **Data Sources:**
    - **WorldPop**: High-resolution global population datasets
    - **GADM**: Global Administrative Areas database
    
    **Coverage:**
    - All African countries supported
    - Administrative levels 0-4
    - Base years: 2000-2020 (any year can be selected)
    - Multi-year projections (forward/backward)
    - Age/sex disaggregated data available
    - ~100m spatial resolution
    
    **NEW: Multi-Year Projection**
    - Select ANY year 2000-2020 as your baseline
    - Project population forward or backward from baseline
    - User-defined growth rates (positive/negative)
    - Up to 20 years projection from baseline
    - Compound growth formula: P(t) = P(base) × (1 + r)^t
    - Download all years in single dataset
    - Generate maps for all projected years
    
    **Use Cases:**
    - Intervention targeting & resource allocation
    - Disease burden estimation
    - Campaign planning (SMC, ITN distribution)
    - Health facility catchment analysis
    - Denominator estimation for surveys
    - Multi-year program planning
    - Population trend analysis
    
    **Technical Notes:**
    - Resolution: ~100m per pixel
    - Base year: 2020 (WorldPop data)
    - UN-adjusted estimates available
    - Age groups: 0-80+ in 5-year bands
    - Sex-specific estimates available
    - Projection uses compound growth formula
    
    **Performance Notes:**
    - **First run**: 30-120 seconds (downloading 50-200 MB files)
    - **Subsequent runs**: 5-15 seconds (cached data)
    - **Large countries** (Nigeria, DRC, Ethiopia): Longer processing
    - Data is cached automatically for faster repeat analysis
    """)
    
    with st.expander("Usage Tips"):
        st.markdown("""
        - **Admin levels**: Use level 2-3 for district analysis
        - **Base year**: Always 2020 (most recent complete data)
        - **Projections**: Enable for future/past estimates
        - **Growth rates**: Can be negative for population decline
        - **Age/sex data**: Use for targeted interventions
        - **Total population**: Best for overall planning
        - **Custom shapefiles**: Include .prj files
        - **Large areas**: May take longer to process
        - **Downloads**: Excel includes all years + summary stats
        - **First time slow?** Normal! File is 50-200 MB (then cached)
        - **Repeat analysis**: Much faster with cached data
        """)
    
    with st.expander("Multi-Year Projection Guide"):
        st.markdown("""
        **How it works:**
        - Select ANY year 2000-2020 as your baseline
        - Applies compound growth formula from that baseline
        - Projects forward (positive rate) or backward (negative rate)
        
        **Growth Rate Examples:**
        - **2.5%**: Average African population growth
        - **3.5%**: High growth countries (Niger, Mali)
        - **1.5%**: Moderate growth (Ghana, Kenya)
        - **-0.5%**: Population decline scenarios
        
        **Formula:**
        ```
        Population(year) = Population(baseline) × (1 + rate/100)^years
        ```
        
        **Example:**
        - Base year: 2015
        - Base population: 100,000 people
        - Growth: 2.5% annual
        - Year 2020 (5 years): 100,000 × (1.025)^5 = 113,141
        
        **Outputs:**
        - Individual maps for each year
        - Combined PDF with all maps
        - Single dataset with all years
        - Year-by-year statistics
        """)
    
    with st.expander("Performance Tips"):
        st.markdown("""
        **Why is it slow the first time?**
        - WorldPop files are 50-200 MB (vs CHIRPS 2-5 MB)
        - High-resolution population data = larger files
        - Network download speed dependent
        
        **How to speed up:**
        - Data caches automatically after first download
        - Use same country/year for repeat analyses
        - Start with higher admin levels (faster processing)
        - Good internet connection helps first download
        - Subsequent runs are 5-10x faster!
        - Projections add minimal time (calculated, not downloaded)
        
        **File Size by Country (approximate):**
        - Small countries (Gambia, Lesotho): 20-40 MB
        - Medium countries (Sierra Leone, Benin): 50-80 MB
        - Large countries (Nigeria, DRC, Ethiopia): 150-250 MB
        """)
    
    with st.expander("Population Analysis Types"):
        st.markdown("""
        **Total Population:**
        - All ages, both sexes
        - UN-adjusted estimates
        - Best for overall planning
        - Most reliable estimates
        
        **Age/Sex Disaggregated:**
        - Specific age groups (5-year bands)
        - Male/female/both options
        - Target specific demographics
        - Useful for:
          * U5 programs (under-5)
          * SMC eligibility (3-59 months)
          * Reproductive health (15-49 years)
          * Elderly care (65+ years)
        """)
    
    with st.expander("Public Health Applications"):
        st.markdown("""
        **Malaria Programs:**
        - SMC target population (3-59 months)
        - ITN distribution planning
        - IRS coverage estimation
        
        **Immunization:**
        - U5 population for vaccine targets
        - Coverage denominator estimation
        
        **General Health:**
        - Health facility planning
        - Catchment area analysis
        - Resource allocation
        - Survey sample size calculation
        - Multi-year program planning
        """)
    
    with st.expander("Download Features"):
        st.markdown("""
        **CSV Download:**
        - Clean tabular data
        - All administrative attributes
        - Population totals & densities
        - All years in single file
        - Ready for GIS/analysis tools
        
        **Excel Download:**
        - Population data sheet (all years)
        - Summary statistics by year
        - Metadata documentation
        - Projection parameters
        - Professional format
        
        **PDF Maps:**
        - All years in single document
        - High resolution (300 DPI)
        - White background
        - Print-ready quality
        """)
    
    with st.expander("Troubleshooting"):
        st.markdown("""
        - **No data**: Try different year/age group
        - **Slow loading**: Normal for large countries
        - **Custom shapefile**: Requires country selection
        - **Projection errors**: Check growth rate input
        - **Missing areas**: Check admin level
        - **Large downloads**: Try higher admin levels
        """)

    # System info
    with st.expander("System Information"):
        st.write(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Available base years: 2000-2020")
        st.write(f"Projection range: Up to 20 years forward/backward from base")
        st.write(f"Countries available: {len(COUNTRY_OPTIONS)}")
        st.write(f"Age groups: {len(AGE_GROUPS)}")
        st.write("Resolution: ~100m")
        st.write("Source: WorldPop (www.worldpop.org)")
        st.write("Tool version: v2.0 (with multi-year projection)")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6b7280; padding: 2rem 0;'>
    <p style='margin-bottom: 0.5rem;'><strong>Built for public health professionals and researchers</strong></p>
    <p style='margin-bottom: 0.5rem;'><strong>Contact</strong>: Mohamed Sillah Kanu | Informatics Consultancy Firm - Sierra Leone (ICF-SL)</p>
    <p style='margin-bottom: 0.5rem;'><strong>Email</strong>: mohamed.kanu@informaticsconsultancyfirm.com</p>
    <p><strong>Data Sources</strong>: WorldPop (www.worldpop.org) | GADM (gadm.org)</p>
</div>
""", unsafe_allow_html=True)
