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

# Set page config
st.set_page_config(
    page_title="WorldPop Population Analysis - ICF-SL",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ICF-SL Blue & White Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Oswald', sans-serif !important;
    }
    
    .stApp {
        background: #ffffff;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stSidebar"] {
        background: #004080;
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #004080 !important;
    }
    
    .stButton > button {
        background: #004080;
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
    }
    
    .stButton > button:hover {
        background: #003366;
    }
    
    .stDownloadButton > button {
        background: #c4a000;
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    
    .stDownloadButton > button:hover {
        background: #9a7d00;
    }
    
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border: 2px solid #004080 !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox label,
    .stMultiSelect label {
        color: #004080 !important;
        font-weight: 600;
    }
    
    input {
        border: 2px solid #004080 !important;
        border-radius: 8px !important;
    }
    
    .stRadio > div {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #004080;
    }
    
    .stCheckbox label {
        color: #333333 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #004080 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #333333 !important;
    }
    
    div[data-testid="metric-container"] {
        background: #ffffff;
        padding: 1.25rem;
        border-radius: 8px;
        border: 2px solid #004080;
    }
    
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 4px 15px rgba(0, 64, 128, 0.2);
    }
    
    .stSuccess {
        background: #d4edda !important;
        color: #155724 !important;
        border-radius: 8px;
    }
    
    .stInfo {
        background: #e7f3ff !important;
        color: #004080 !important;
        border-radius: 8px;
    }
    
    .stWarning {
        background: #fff3cd !important;
        color: #856404 !important;
        border-radius: 8px;
    }
    
    .stError {
        background: #f8d7da !important;
        color: #721c24 !important;
        border-radius: 8px;
    }
    
    .stProgress > div > div > div {
        background: #004080;
    }
    
    [data-testid="stExpander"] {
        border: 2px solid #004080;
        border-radius: 8px;
    }
    
    .streamlit-expanderHeader {
        background: #004080 !important;
        color: #ffffff !important;
        font-weight: 600;
    }
    
    p, li, span, label {
        color: #333333 !important;
    }
    
    strong {
        color: #004080 !important;
    }
    
    a {
        color: #004080 !important;
    }
    
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #e7f3ff;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #004080;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Constants
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
AVAILABLE_YEARS = list(range(2000, 2021))

AGE_GROUPS = {
    "Total Population": "ppp", "0-1 years": "0", "1-4 years": "1",
    "5-9 years": "5", "10-14 years": "10", "15-19 years": "15",
    "20-24 years": "20", "25-29 years": "25", "30-34 years": "30",
    "35-39 years": "35", "40-44 years": "40", "45-49 years": "45",
    "50-54 years": "50", "55-59 years": "55", "60-64 years": "60",
    "65-69 years": "65", "70-74 years": "70", "75-79 years": "75",
    "80+ years": "80"
}

SEX_OPTIONS = {"Male": "m", "Female": "f"}

# Session state
if 'country' not in st.session_state:
    st.session_state.country = "Sierra Leone"
if 'country_code' not in st.session_state:
    st.session_state.country_code = "SLE"
if 'admin_level' not in st.session_state:
    st.session_state.admin_level = 2

# Functions
@st.cache_data
def download_shapefile_from_gadm(country_code, admin_level):
    gadm_url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_{country_code}_shp.zip"
    
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
            raise FileNotFoundError(f"Admin level {admin_level} not found for {country_code}")
        
        gdf = gpd.read_file(shapefile_path)
    
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    
    return gdf


def construct_worldpop_url(country_code, year, age_group, sex):
    country_lower = WORLDPOP_CODES[country_code]
    
    if age_group == "ppp" and sex == "both":
        url = f"https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/{country_code.upper()}/{country_lower}_ppp_{year}_UNadj_constrained.tif"
    else:
        url = f"https://data.worldpop.org/GIS/AgeSex_structures/Global_2000_2020/{year}/{country_code.upper()}/{country_lower}_{sex}_{age_group}_{year}.tif"
    
    return url


@st.cache_data
def download_worldpop_data(country_code, year, age_group, sex):
    url = construct_worldpop_url(country_code, year, age_group, sex)
    
    try:
        response = requests.get(url, timeout=180, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        chunks = []
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                chunks.append(chunk)
        
        return b''.join(chunks), url, total_size
        
    except:
        country_lower = WORLDPOP_CODES[country_code]
        alt_url = f"https://data.worldpop.org/GIS/Population/Global_2000_2020/{year}/{country_code.upper()}/{country_lower}_ppp_{year}.tif"
        
        response = requests.get(alt_url, timeout=180, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        chunks = []
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                chunks.append(chunk)
        
        return b''.join(chunks), alt_url, total_size


def process_worldpop_data(_gdf, country_code, year, age_group, sex):
    gdf = _gdf.copy()
    worldpop_data, used_url, file_size = download_worldpop_data(country_code, year, age_group, sex)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tif_file_path = os.path.join(tmpdir, "worldpop.tif")
        
        with open(tif_file_path, "wb") as f:
            f.write(worldpop_data)
        
        with rasterio.open(tif_file_path) as src:
            gdf_reproj = gdf.to_crs(src.crs)
            
            total_pop = []
            mean_density = []
            
            for idx, geom in enumerate(gdf_reproj.geometry):
                try:
                    masked_data, _ = rasterio.mask.mask(src, [geom], crop=True, nodata=src.nodata)
                    masked_data = masked_data.flatten()
                    
                    if src.nodata is not None:
                        valid_data = masked_data[masked_data != src.nodata]
                    else:
                        valid_data = masked_data
                    valid_data = valid_data[~np.isnan(valid_data)]
                    valid_data = valid_data[valid_data >= 0]
                    
                    if len(valid_data) > 0:
                        total_pop.append(np.sum(valid_data))
                        mean_density.append(np.mean(valid_data))
                    else:
                        total_pop.append(0)
                        mean_density.append(0)
                except:
                    total_pop.append(0)
                    mean_density.append(0)
            
            gdf["total_population"] = total_pop
            gdf["mean_density"] = mean_density
    
    return gdf, used_url, file_size


def project_population(base_gdf, base_year, growth_rate, num_years):
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


# Header
st.markdown("""
<div style="background: #004080; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center;">
    <div style="background: white; display: inline-block; padding: 0.5rem 1.5rem; border-radius: 8px; margin-bottom: 1rem;">
        <span style="font-weight: 700; font-size: 1.5rem; color: #004080;">ICF-SL</span>
    </div>
    <h1 style="color: white !important; margin: 0;">WorldPop Population Analysis</h1>
    <p style="color: #e7f3ff !important; margin: 0.5rem 0 0 0;">Analyze population distribution for public health planning</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <div style="background: white; padding: 0.5rem 1rem; border-radius: 8px; display: inline-block;">
            <span style="font-weight: 700; color: #004080;">ICF-SL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## Analysis Parameters")
    
    country = st.selectbox("Select Country", list(COUNTRY_OPTIONS.keys()), 
                          index=list(COUNTRY_OPTIONS.keys()).index("Sierra Leone"))
    
    admin_level = st.selectbox("Administrative Level", [0, 1, 2, 3, 4], index=2,
                              format_func=lambda x: f"Level {x}")
    
    st.caption({
        0: "Country boundary",
        1: "Regions/States",
        2: "Districts/Provinces", 
        3: "Communes/Counties",
        4: "Localities/Wards"
    }.get(admin_level, ""))
    
    country_code = COUNTRY_OPTIONS[country]
    st.session_state.country = country
    st.session_state.country_code = country_code
    st.session_state.admin_level = admin_level

    st.markdown("---")
    
    st.markdown("### Year & Projection")
    
    enable_projection = st.checkbox("Enable Multi-Year Projection", value=False)
    
    if enable_projection:
        year = 2020
        st.info("2020 selected as baseline")
        
        projection_years = st.number_input("Years to Project", min_value=1, max_value=20, value=5)
        growth_rate = st.number_input("Growth Rate (%)", min_value=-10.0, max_value=10.0, value=2.5, step=0.1)
    else:
        year = st.selectbox("Select Year", AVAILABLE_YEARS, index=len(AVAILABLE_YEARS)-1)
        projection_years = 0
        growth_rate = 0.0

    st.markdown("---")
    
    st.markdown("### Population Type")
    
    analysis_type = st.radio("Analysis Type", ["Total Population", "Age/Sex Disaggregated"])
    
    if analysis_type == "Total Population":
        age_group = "ppp"
        sex = "both"
    else:
        age_group_name = st.selectbox("Age Group", list(AGE_GROUPS.keys())[1:])
        age_group = AGE_GROUPS[age_group_name]
        sex_name = st.selectbox("Sex", list(SEX_OPTIONS.keys()))
        sex = SEX_OPTIONS[sex_name]

    st.markdown("---")
    
    color_scheme = st.selectbox("Color Scheme", ["YlOrRd", "viridis", "plasma", "Reds", "Blues"])
    show_statistics = st.checkbox("Show Statistics", value=True)

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    if st.button("Generate Analysis", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text(f"Downloading {country} shapefile...")
            progress_bar.progress(20)
            
            gdf = download_shapefile_from_gadm(country_code, admin_level)
            st.success(f"Loaded {len(gdf)} administrative units")
            
            status_text.text(f"Downloading WorldPop data ({year})...")
            progress_bar.progress(50)
            
            processed_gdf, used_url, file_size = process_worldpop_data(gdf, country_code, year, age_group, sex)
            
            file_size_mb = file_size / (1024*1024) if file_size > 0 else 0
            st.success(f"Population data processed ({file_size_mb:.1f} MB)")
            
            all_years_data = {year: processed_gdf}
            
            if enable_projection:
                status_text.text("Generating projections...")
                progress_bar.progress(70)
                
                projected_data = project_population(processed_gdf, year, growth_rate, projection_years)
                all_years_data.update(projected_data)
                st.success(f"Projected {len(projected_data)} additional years")
            
            status_text.text("Generating maps...")
            progress_bar.progress(90)
            
            all_figures = {}
            
            for proj_year in sorted(all_years_data.keys()):
                year_gdf = all_years_data[proj_year]
                
                fig, ax = plt.subplots(1, 1, figsize=(12, 10), facecolor='white')
                ax.set_facecolor('white')
                
                year_gdf.plot(
                    column="total_population",
                    ax=ax,
                    legend=True,
                    cmap=color_scheme,
                    edgecolor="black",
                    linewidth=0.5,
                    legend_kwds={"shrink": 0.8, "label": "Population"}
                )
                
                label = "[Baseline]" if proj_year == year else "[Projected]"
                ax.set_title(f"{country} - Population ({proj_year}) {label}", fontweight='bold', fontsize=14, color='#004080')
                ax.set_axis_off()
                plt.tight_layout()
                all_figures[proj_year] = fig
            
            progress_bar.progress(100)
            status_text.empty()
            
            st.success(f"Analysis complete! {len(all_figures)} map(s) generated")
            
            # Display maps
            st.markdown("## Population Maps")
            
            for proj_year in sorted(all_figures.keys()):
                label = "(Baseline)" if proj_year == year else "(Projected)"
                st.markdown(f"### Year {proj_year} {label}")
                st.pyplot(all_figures[proj_year])
            
            # Downloads
            st.markdown("## Download Results")
            
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                pdf_buffer = BytesIO()
                with PdfPages(pdf_buffer) as pdf:
                    for proj_year in sorted(all_figures.keys()):
                        pdf.savefig(all_figures[proj_year], dpi=300, bbox_inches='tight', facecolor='white')
                pdf_buffer.seek(0)
                
                st.download_button(
                    label="Download Maps (PDF)",
                    data=pdf_buffer,
                    file_name=f"worldpop_{country_code}_{year}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col_dl2:
                all_years_combined = []
                for proj_year in sorted(all_years_data.keys()):
                    year_gdf = all_years_data[proj_year].copy()
                    year_gdf = year_gdf.drop(columns='geometry')
                    year_gdf['year'] = proj_year
                    year_gdf['is_baseline'] = (proj_year == year)
                    all_years_combined.append(year_gdf)
                
                download_df = pd.concat(all_years_combined, ignore_index=True)
                
                st.download_button(
                    label="Download Data (CSV)",
                    data=download_df.to_csv(index=False),
                    file_name=f"worldpop_{country_code}_{year}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # Statistics
            if show_statistics:
                st.markdown("## Population Statistics")
                
                for proj_year in sorted(all_years_data.keys()):
                    year_gdf = all_years_data[proj_year]
                    label = "(Baseline)" if proj_year == year else "(Projected)"
                    
                    st.markdown(f"### Year {proj_year} {label}")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    
                    with c1:
                        st.metric("Total Population", f"{year_gdf['total_population'].sum():,.0f}")
                    with c2:
                        st.metric("Mean per Unit", f"{year_gdf['total_population'].mean():,.0f}")
                    with c3:
                        st.metric("Maximum", f"{year_gdf['total_population'].max():,.0f}")
                    with c4:
                        st.metric("Minimum", f"{year_gdf['total_population'].min():,.0f}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col2:
    st.markdown("## About")
    
    st.markdown("""
    **WorldPop Analysis Tool**
    
    Analyze high-resolution population data for public health planning.
    
    ---
    
    **Data Sources:**
    - WorldPop
    - GADM
    
    ---
    
    **Coverage:**
    - All African countries
    - Admin levels 0-4
    - Years: 2000-2020
    - ~100m resolution
    
    ---
    
    **Tips:**
    - Level 2-3 for districts
    - 2020 = most recent
    - First download is slow
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="background: #004080; padding: 1.5rem; border-radius: 10px; text-align: center;">
    <p style="color: white !important; margin: 0;"><strong style="color: #c4a000 !important;">ICF-SL</strong> | Informatics Consultancy Firm - Sierra Leone</p>
    <p style="color: #e7f3ff !important; margin: 0.5rem 0 0 0; font-size: 0.9rem;">Contact: Mohamed Sillah Kanu | mohamed.kanu@informaticsconsultancyfirm.com</p>
    <p style="color: #e7f3ff !important; margin: 0.25rem 0 0 0; font-size: 0.85rem;">Data: WorldPop | GADM | Supported by NMCP</p>
</div>
""", unsafe_allow_html=True)
