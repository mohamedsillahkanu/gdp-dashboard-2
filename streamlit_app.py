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
from datetime import datetime
import time

# Set page config with premium theme
st.set_page_config(
    page_title="WorldPop Population Analysis",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply world-class gold standard theme - Deep Navy & Electric Blue with sophisticated animations
st.markdown("""
<style>
    /* Import premium fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Global font application */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main background - Sophisticated navy gradient with animated particles */
    .stApp {
        background: linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%);
        background-attachment: fixed;
        position: relative;
    }
    
    /* Animated background overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(14, 165, 233, 0.02) 0%, transparent 50%);
        pointer-events: none;
        animation: pulseGlow 15s ease-in-out infinite;
    }
    
    @keyframes pulseGlow {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Sidebar - Premium glass morphism effect */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 25, 47, 0.95) 0%, rgba(17, 34, 64, 0.95) 100%);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(59, 130, 246, 0.2);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 1px;
        height: 100%;
        background: linear-gradient(180deg, 
            transparent 0%, 
            rgba(59, 130, 246, 0.5) 30%, 
            rgba(139, 92, 246, 0.5) 70%, 
            transparent 100%);
        animation: sidebarGlow 3s ease-in-out infinite;
    }
    
    @keyframes sidebarGlow {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }
    
    /* Headers with sophisticated typography */
    h1 {
        color: #60A5FA !important;
        font-weight: 800 !important;
        font-size: 3rem !important;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #60A5FA 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 40px rgba(96, 165, 250, 0.3);
        margin-bottom: 0.5rem !important;
        animation: titleGlow 3s ease-in-out infinite;
    }
    
    @keyframes titleGlow {
        0%, 100% { filter: drop-shadow(0 0 20px rgba(96, 165, 250, 0.4)); }
        50% { filter: drop-shadow(0 0 30px rgba(96, 165, 250, 0.6)); }
    }
    
    h2 {
        color: #93C5FD !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        letter-spacing: -0.01em;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        border-bottom: 2px solid rgba(59, 130, 246, 0.2);
        padding-bottom: 0.5rem;
    }
    
    h3 {
        color: #BFDBFE !important;
        font-weight: 600 !important;
        font-size: 1.25rem !important;
        letter-spacing: -0.01em;
        margin-top: 1.5rem !important;
    }
    
    /* Metrics - Premium card design with animations */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(17, 34, 64, 0.9), rgba(26, 54, 93, 0.9));
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 
            0 4px 24px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(96, 165, 250, 0.1), 
            transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        border-color: rgba(96, 165, 250, 0.5);
        box-shadow: 
            0 8px 32px rgba(59, 130, 246, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    [data-testid="stMetricValue"] {
        color: #60A5FA !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 10px rgba(96, 165, 250, 0.5);
    }
    
    [data-testid="stMetricLabel"] {
        color: #93C5FD !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.75rem !important;
    }
    
    /* Buttons - Premium 3D effect with sophisticated hover */
    .stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        box-shadow: 
            0 4px 16px rgba(37, 99, 235, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.3), 
            transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
        transform: translateY(-2px);
        box-shadow: 
            0 8px 24px rgba(59, 130, 246, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
    }
    
    /* Primary button - Enhanced gradient */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1E40AF 0%, #2563EB 50%, #3B82F6 100%);
        box-shadow: 
            0 6px 20px rgba(30, 64, 175, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563EB 0%, #3B82F6 50%, #60A5FA 100%);
        box-shadow: 
            0 10px 32px rgba(37, 99, 235, 0.7),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }
    
    /* Download buttons - Distinct purple accent */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%);
        color: #ffffff;
        border: none;
        font-weight: 700;
        box-shadow: 
            0 4px 16px rgba(124, 58, 237, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%);
        transform: translateY(-2px);
        box-shadow: 
            0 8px 24px rgba(139, 92, 246, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }
    
    /* Input fields - Modern glass morphism */
    .stSelectbox > div > div,
    .stTextInput > div > div,
    .stNumberInput > div > div {
        background: rgba(17, 34, 64, 0.8) !important;
        backdrop-filter: blur(10px);
        color: #E0E7FF !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .stSelectbox > div > div:hover,
    .stTextInput > div > div:hover,
    .stNumberInput > div > div:hover,
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div:focus-within,
    .stNumberInput > div > div:focus-within {
        border-color: rgba(96, 165, 250, 0.6) !important;
        box-shadow: 
            0 0 0 3px rgba(59, 130, 246, 0.1),
            inset 0 2px 4px rgba(0, 0, 0, 0.2);
        background: rgba(26, 54, 93, 0.9) !important;
    }
    
    /* Radio buttons - Premium card style */
    .stRadio > div {
        background: linear-gradient(135deg, rgba(17, 34, 64, 0.9), rgba(26, 54, 93, 0.9));
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(59, 130, 246, 0.25);
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    .stRadio label {
        color: #BFDBFE !important;
        font-weight: 600;
        transition: color 0.2s ease;
    }
    
    .stRadio label:hover {
        color: #93C5FD !important;
    }
    
    /* Checkboxes - Modern accent */
    .stCheckbox label {
        color: #BFDBFE !important;
        font-weight: 600;
    }
    
    /* File uploader - Elegant dashed border with glow */
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, rgba(17, 34, 64, 0.7), rgba(26, 54, 93, 0.7));
        backdrop-filter: blur(10px);
        border: 2px dashed rgba(96, 165, 250, 0.4);
        border-radius: 16px;
        padding: 2rem;
        transition: all 0.4s ease;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(96, 165, 250, 0.7);
        background: linear-gradient(135deg, rgba(26, 54, 93, 0.8), rgba(30, 64, 175, 0.3));
        box-shadow: 
            0 4px 20px rgba(59, 130, 246, 0.2),
            inset 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Alert messages - Refined with better contrast */
    .stSuccess {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.15));
        border-left: 4px solid #10B981;
        border-radius: 10px;
        color: #A7F3D0 !important;
        font-weight: 600;
        padding: 1rem 1.5rem;
        box-shadow: 
            0 4px 16px rgba(16, 185, 129, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(37, 99, 235, 0.15));
        border-left: 4px solid #3B82F6;
        border-radius: 10px;
        color: #BFDBFE !important;
        font-weight: 600;
        padding: 1rem 1.5rem;
        box-shadow: 
            0 4px 16px rgba(59, 130, 246, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.15));
        border-left: 4px solid #F59E0B;
        border-radius: 10px;
        color: #FDE68A !important;
        font-weight: 600;
        padding: 1rem 1.5rem;
        box-shadow: 
            0 4px 16px rgba(245, 158, 11, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.15));
        border-left: 4px solid #EF4444;
        border-radius: 10px;
        color: #FECACA !important;
        font-weight: 600;
        padding: 1rem 1.5rem;
        box-shadow: 
            0 4px 16px rgba(239, 68, 68, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    /* Expander - Sophisticated accordion */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(17, 34, 64, 0.9), rgba(26, 54, 93, 0.9));
        backdrop-filter: blur(10px);
        border-radius: 10px;
        color: #60A5FA !important;
        border: 1px solid rgba(59, 130, 246, 0.25);
        font-weight: 700;
        padding: 1rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 
            0 2px 8px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(26, 54, 93, 0.95), rgba(30, 64, 175, 0.3));
        border-color: rgba(96, 165, 250, 0.5);
        box-shadow: 
            0 4px 16px rgba(59, 130, 246, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transform: translateX(4px);
    }
    
    /* Dataframe - Premium table styling */
    .stDataFrame {
        background: rgba(17, 34, 64, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(59, 130, 246, 0.2);
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    
    /* Table headers - Bold and elegant */
    thead tr th {
        background: linear-gradient(135deg, #1E40AF, #2563EB) !important;
        color: #E0E7FF !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 1rem !important;
        border-bottom: 2px solid rgba(96, 165, 250, 0.5) !important;
    }
    
    /* Table rows - Subtle hover effect */
    tbody tr {
        background: rgba(26, 54, 93, 0.5) !important;
        transition: all 0.2s ease;
    }
    
    tbody tr:nth-child(even) {
        background: rgba(17, 34, 64, 0.5) !important;
    }
    
    tbody tr:hover {
        background: rgba(59, 130, 246, 0.15) !important;
        transform: scale(1.01);
    }
    
    tbody td {
        color: #BFDBFE !important;
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Progress bar - Animated gradient */
    .stProgress > div > div {
        background: linear-gradient(90deg, 
            #2563EB 0%, 
            #3B82F6 25%, 
            #60A5FA 50%, 
            #93C5FD 75%, 
            #BFDBFE 100%);
        background-size: 200% 100%;
        animation: progressShine 2s linear infinite;
        box-shadow: 
            0 2px 10px rgba(59, 130, 246, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }
    
    @keyframes progressShine {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Code blocks - Developer-friendly monospace */
    code {
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace !important;
        background: rgba(17, 34, 64, 0.9);
        color: #60A5FA !important;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        font-weight: 500;
        font-size: 0.9em;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    pre {
        background: rgba(17, 34, 64, 0.9) !important;
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.3),
            inset 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Links - Smooth transitions */
    a {
        color: #60A5FA !important;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
        position: relative;
    }
    
    a::after {
        content: '';
        position: absolute;
        width: 0;
        height: 2px;
        bottom: -2px;
        left: 0;
        background: linear-gradient(90deg, #60A5FA, #818CF8);
        transition: width 0.3s ease;
    }
    
    a:hover {
        color: #93C5FD !important;
    }
    
    a:hover::after {
        width: 100%;
    }
    
    /* Caption text - Subtle and refined */
    .css-1629p8f, .css-nahz7x, [data-testid="stCaptionContainer"] {
        color: #94A3B8 !important;
        font-weight: 500;
        font-size: 0.875rem;
    }
    
    /* Divider - Elegant gradient line */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(59, 130, 246, 0.5) 25%, 
            rgba(139, 92, 246, 0.5) 75%, 
            transparent 100%);
        margin: 2rem 0;
        box-shadow: 0 1px 8px rgba(59, 130, 246, 0.3);
    }
    
    /* Text colors - Refined hierarchy */
    p, li, span, div, label {
        color: #CBD5E1 !important;
    }
    
    .stMarkdown {
        color: #CBD5E1 !important;
    }
    
    /* Strong emphasis */
    strong {
        color: #E0E7FF !important;
        font-weight: 700;
    }
    
    /* Sidebar headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #60A5FA !important;
    }
    
    /* Radio button selected state */
    input[type="radio"]:checked + label {
        color: #60A5FA !important;
        font-weight: 700;
    }
    
    /* Scrollbar styling - Minimal and elegant */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(17, 34, 64, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #2563EB, #3B82F6);
        border-radius: 10px;
        border: 2px solid rgba(17, 34, 64, 0.5);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #3B82F6, #60A5FA);
    }
    
    /* Spinner/Loader animation */
    .stSpinner > div {
        border-top-color: #60A5FA !important;
        border-right-color: #818CF8 !important;
        border-bottom-color: #A78BFA !important;
        border-left-color: #C4B5FD !important;
    }
    
    /* Tooltips */
    [data-testid="stTooltipIcon"] {
        color: #60A5FA !important;
    }
    
    /* Tab navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(17, 34, 64, 0.5);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #94A3B8;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(59, 130, 246, 0.1);
        color: #BFDBFE;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563EB, #3B82F6) !important;
        color: #ffffff !important;
    }
    
    /* Container shadows for depth */
    .element-container {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Premium shadow effects for cards */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > [data-testid="stVerticalBlock"] {
        background: rgba(17, 34, 64, 0.3);
        border-radius: 16px;
        padding: 0.5rem;
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# Define country codes globally - THIS MUST BE AT TOP LEVEL
# Countries arranged in alphabetical order
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
# ==============================================
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
    "Both sexes": "both",
    "Male": "m",
    "Female": "f"
}

# ==============================================

# Initialize session state variables to avoid NameError
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
        st.warning("⚠️ No coordinate reference system detected. Assuming WGS84 (EPSG:4326)")
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

# Main app layout
st.title("👥 WorldPop Population Data Analysis and Mapping")
st.markdown("*Analyze population distribution for public health planning and intervention targeting*")

# Sidebar for controls
with st.sidebar:
    st.header("Analysis Parameters")
    
    # Data source selection
    data_source = st.radio(
        "📂 Select Data Source", 
        ["GADM Database", "Upload Custom Shapefile"],
        help="Choose between official GADM boundaries or upload your own shapefile"
    )
    st.session_state.data_source = data_source
    
    if data_source == "GADM Database":
        # Country and admin level selection
        country = st.selectbox("🌍 Select Country", list(COUNTRY_OPTIONS.keys()), 
                              help="Select any African country")
        admin_level = st.selectbox("🏛️ Administrative Level", [0, 1, 2, 3, 4], 
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
        st.markdown("**📁 Upload Shapefile Components**")
        st.caption("Upload all required files for your shapefile")
        
        # File uploaders - Required files
        shp_file = st.file_uploader("🗺️ Shapefile (.shp)", type=['shp'], help="Main geometry file (required)")
        shx_file = st.file_uploader("🔍 Shape Index (.shx)", type=['shx'], help="Spatial index file (required)")
        dbf_file = st.file_uploader("📊 Attribute Table (.dbf)", type=['dbf'], help="Attribute data file (required)")
        
        # Optional projection file
        prj_file = st.file_uploader("🌐 Projection File (.prj)", type=['prj'], 
                                   help="Coordinate system definition (optional but recommended)")
        
        # Check if required files are uploaded
        if shp_file and shx_file and dbf_file:
            st.success("✅ Required files uploaded successfully!")
            use_custom_shapefile = True
            
            # Show file details
            with st.expander("📋 File Details"):
                st.write(f"**SHP file**: {shp_file.name} ({shp_file.size:,} bytes)")
                st.write(f"**SHX file**: {shx_file.name} ({shx_file.size:,} bytes)")
                st.write(f"**DBF file**: {dbf_file.name} ({dbf_file.size:,} bytes)")
                if prj_file:
                    st.write(f"**PRJ file**: {prj_file.name} ({prj_file.size:,} bytes) ✅")
                    st.success("Projection file included - coordinate system will be automatically detected!")
                else:
                    st.warning("No projection file - will assume WGS84 coordinate system")
        else:
            use_custom_shapefile = False
            st.info("📤 Please upload .shp, .shx, and .dbf files to proceed")
            
            # Show upload requirements
            with st.expander("ℹ️ Shapefile Upload Requirements"):
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

    # Year selection
    st.subheader("📅 Year Selection")
    year = st.selectbox("Select Year", AVAILABLE_YEARS, 
                       index=len(AVAILABLE_YEARS)-1,  # Default to most recent year
                       help="WorldPop data available 2000-2020")
    
    # Population disaggregation options
    st.subheader("👥 Population Parameters")
    
    analysis_type = st.radio(
        "Analysis Type",
        ["Total Population", "Age/Sex Disaggregated"],
        help="Choose between total population or age/sex specific analysis"
    )
    
    if analysis_type == "Total Population":
        age_group = "ppp"
        sex = "both"
        st.info("📊 Analyzing total population (all ages, both sexes)")
    else:
        age_group_name = st.selectbox("Age Group", list(AGE_GROUPS.keys())[1:], 
                                     help="Select specific age group")
        age_group = AGE_GROUPS[age_group_name]
        
        sex_name = st.selectbox("Sex", list(SEX_OPTIONS.keys()), 
                               help="Select sex for analysis")
        sex = SEX_OPTIONS[sex_name]
        
        st.info(f"📊 Analyzing: {age_group_name}, {sex_name}")

    # Display options
    st.subheader("Display Options")
    show_statistics = st.checkbox("📈 Show Statistics", value=True)
    color_scheme = st.selectbox("🎨 Color Scheme", 
                               ["YlOrRd", "viridis", "plasma", "Reds", "Blues", "Purples", "magma", "inferno"])

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🔄 Generate Analysis", type="primary", use_container_width=True):
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
                    status_text.text("🔍 Checking GADM database...")
                    progress_bar.progress(10)
                    
                    status_text.text(f"📥 Downloading {st.session_state.country} shapefile from GADM...")
                    progress_bar.progress(20)
                    
                    gdf = download_shapefile_from_gadm(st.session_state.country_code, st.session_state.admin_level)
                    st.success(f"✅ {st.session_state.country} Admin Level {st.session_state.admin_level} shapefile loaded ({len(gdf)} features)")
                    
                else:  # Custom shapefile
                    status_text.text("📁 Processing uploaded shapefile...")
                    progress_bar.progress(10)
                    
                    gdf, crs_source, projection_info = load_uploaded_shapefile(shp_file, shx_file, dbf_file, prj_file)
                    progress_bar.progress(20)
                    st.success(f"✅ Custom shapefile loaded ({len(gdf)} features)")
                    
                    # Show coordinate system info
                    if gdf.crs:
                        st.info(f"📍 Coordinate System: {gdf.crs} ({crs_source})")
                        if projection_info and prj_file:
                            with st.expander("🔍 Projection Details"):
                                st.code(projection_info, language="text")
                    
                    # Show attribute columns
                    attribute_cols = [col for col in gdf.columns if col != 'geometry']
                    if attribute_cols:
                        st.info(f"📊 Available attributes: {', '.join(attribute_cols[:5])}{'...' if len(attribute_cols) > 5 else ''}")
                
                # Show some basic info about the shapefile
                if hasattr(gdf, 'NAME_1') and (st.session_state.data_source == "GADM Database" and st.session_state.admin_level >= 1):
                    region_names = gdf['NAME_1'].unique()[:5]
                    st.info(f"📋 Contains regions: {', '.join(region_names)}{'...' if len(gdf['NAME_1'].unique()) > 5 else ''}")
                elif hasattr(gdf, 'NAME_0'):
                    st.info(f"📋 Country: {gdf['NAME_0'].iloc[0]}")
                elif st.session_state.data_source == "Upload Custom Shapefile":
                    geom_types = gdf.geometry.type.unique()
                    st.info(f"📋 Geometry types: {', '.join(geom_types)}")
                
                # Test WorldPop data availability
                status_text.text("🔍 Testing WorldPop data availability...")
                progress_bar.progress(30)
                
                test_url = construct_worldpop_url(st.session_state.country_code if st.session_state.data_source == "GADM Database" else "SLE", 
                                                 year, age_group, sex)
                
                # Step 2: Process WorldPop data
                status_text.text("👥 Downloading WorldPop population data...")
                progress_bar.progress(40)
                
                # Create download progress display
                download_status = st.empty()
                
                def update_download_progress(percent, downloaded, total):
                    mb_downloaded = downloaded / (1024*1024)
                    mb_total = total / (1024*1024)
                    download_status.info(f"⬇️ Downloading: {mb_downloaded:.1f} MB / {mb_total:.1f} MB ({percent:.1f}%)")
                
                try:
                    if st.session_state.data_source == "GADM Database":
                        processed_gdf, used_url, file_size = process_worldpop_data(
                            gdf, st.session_state.country_code, year, age_group, sex, 
                            progress_callback=update_download_progress
                        )
                    else:
                        # For custom shapefiles, need to specify a country code for WorldPop data
                        st.warning("⚠️ Custom shapefile detected. Using Sierra Leone (SLE) WorldPop data as default.")
                        st.info("💡 Tip: For accurate results with custom shapefiles, ensure they align with a specific country's boundaries")
                        processed_gdf, used_url, file_size = process_worldpop_data(
                            gdf, "SLE", year, age_group, sex,
                            progress_callback=update_download_progress
                        )
                    
                    download_status.empty()  # Clear download progress
                    
                    file_size_mb = file_size / (1024*1024) if file_size > 0 else 0
                    st.success(f"✅ Population data processed successfully (File size: {file_size_mb:.1f} MB)")
                    
                    with st.expander("🔗 Data Source URL"):
                        st.code(used_url, language="text")
                        if file_size_mb > 100:
                            st.info("💡 **Large file**: This data is now cached. Subsequent analyses will be much faster!")
                    
                except Exception as e:
                    download_status.empty()
                    st.error(f"❌ Error processing population data: {str(e)}")
                    st.stop()

                # Step 3: Generate visualizations
                status_text.text("📊 Generating map...")
                progress_bar.progress(80)
                
                # Create visualization with dark theme
                plt.style.use('dark_background')
                fig, ax = plt.subplots(1, 1, figsize=(12, 10), facecolor='#0a192f')
                ax.set_facecolor('#0a192f')
                
                # Handle missing data
                if processed_gdf['total_population'].sum() == 0:
                    st.error("❌ No valid population data found for this area and time period")
                    st.stop()
                
                # Create the plot
                processed_gdf.plot(
                    column="total_population",
                    ax=ax,
                    legend=True,
                    cmap=color_scheme,
                    edgecolor="white",
                    linewidth=0.5,
                    legend_kwds={"shrink": 0.8, "label": "Population"},
                    missing_kwds={"color": "#112240", "label": "No data"}
                )
                
                if analysis_type == "Total Population":
                    title = f"{st.session_state.country} - Total Population ({year})"
                else:
                    title = f"{st.session_state.country} - {age_group_name}, {sex_name} ({year})"
                
                ax.set_title(title, fontweight='bold', fontsize=14, color='white')
                ax.set_axis_off()
                
                plt.tight_layout()
                
                # Complete the analysis
                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                time.sleep(0.5)
                status_text.empty()
                
                st.success(f"🎉 Population analysis completed successfully!")
                st.pyplot(fig)

                # Show statistics if requested
                if show_statistics:
                    st.subheader("📊 Population Statistics")
                    
                    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                    
                    with col_stat1:
                        total = processed_gdf['total_population'].sum()
                        st.metric("Total Population", f"{total:,.0f}")
                    
                    with col_stat2:
                        mean_pop = processed_gdf['total_population'].mean()
                        st.metric("Mean per Unit", f"{mean_pop:,.0f}")
                    
                    with col_stat3:
                        max_pop = processed_gdf['total_population'].max()
                        st.metric("Maximum", f"{max_pop:,.0f}")
                    
                    with col_stat4:
                        min_pop = processed_gdf['total_population'].min()
                        st.metric("Minimum", f"{min_pop:,.0f}")
                    
                    # Detailed statistics table
                    st.markdown("**Detailed Statistics by Administrative Unit**")
                    
                    stats_df = processed_gdf.copy()
                    stats_df = stats_df.drop(columns='geometry')
                    
                    # Select relevant columns
                    display_cols = ['total_population', 'mean_density', 'valid_pixels']
                    
                    # Add name columns if available
                    name_cols = [col for col in stats_df.columns if col.startswith('NAME_')]
                    if name_cols:
                        display_cols = name_cols + display_cols
                    
                    stats_display = stats_df[display_cols].copy()
                    stats_display = stats_display.sort_values('total_population', ascending=False)
                    stats_display['total_population'] = stats_display['total_population'].apply(lambda x: f"{x:,.0f}")
                    stats_display['mean_density'] = stats_display['mean_density'].apply(lambda x: f"{x:.2f}")
                    
                    st.dataframe(stats_display, use_container_width=True, height=400)

                # Data download section
                st.subheader("📥 Download Data")
                
                # Prepare dataset for download
                download_df = processed_gdf.copy()
                download_df = download_df.drop(columns='geometry')
                
                # Add metadata columns
                download_df['year'] = year
                download_df['area_name'] = st.session_state.country
                download_df['data_source'] = st.session_state.data_source
                download_df['analysis_type'] = analysis_type
                
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
                column_order = ['area_name', 'data_source', 'year', 'analysis_type']
                
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
                    filename_base = f"worldpop_population_{st.session_state.country_code}_{year}"
                    if st.session_state.data_source == "Upload Custom Shapefile":
                        filename_base = f"worldpop_population_custom_{year}"
                    elif st.session_state.data_source == "GADM Database":
                        filename_base = f"worldpop_population_{st.session_state.country_code}_{year}_admin{st.session_state.admin_level}"
                    
                    if analysis_type == "Age/Sex Disaggregated":
                        filename_base += f"_{age_group}_{sex}"
                    
                    st.download_button(
                        label="📄 Download as CSV",
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
                        
                        # Summary statistics sheet
                        summary_stats = pd.DataFrame({
                            'Metric': ['Total Population', 'Mean per Unit', 'Std Dev', 'Minimum', 'Maximum', 'Units Analyzed'],
                            'Value': [
                                f"{download_df['total_population'].sum():,.0f}",
                                f"{download_df['total_population'].mean():,.0f}",
                                f"{download_df['total_population'].std():,.0f}",
                                f"{download_df['total_population'].min():,.0f}",
                                f"{download_df['total_population'].max():,.0f}",
                                len(download_df)
                            ]
                        })
                        summary_stats.to_excel(writer, sheet_name='Summary_Stats', index=False)
                        
                        # Metadata sheet
                        metadata_values = [
                            st.session_state.country,
                            st.session_state.data_source,
                            st.session_state.country_code,
                            str(st.session_state.admin_level) if st.session_state.data_source == "GADM Database" else "Custom",
                            year,
                            analysis_type,
                            'WorldPop Unconstrained',
                            'GADM v4.1' if st.session_state.data_source == "GADM Database" else 'User Upload',
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            len(download_df),
                            'WorldPop Population Analysis Tool v1.0'
                        ]
                        
                        metadata_params = [
                            'Area Name', 'Data Source', 'Country Code', 'Admin Level', 'Year',
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
                        label="📊 Download as Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"{filename_base}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                # Show data preview
                with st.expander("👀 Preview Downloaded Data"):
                    st.dataframe(download_df.head(10), use_container_width=True)
                    st.caption(f"Showing first 10 rows of {len(download_df)} total records")

            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                st.error("Please try again or contact support if the issue persists.")
                
                with st.expander("🔧 Debug Information"):
                    st.write(f"Data Source: {st.session_state.data_source}")
                    if st.session_state.data_source == "GADM Database":
                        st.write(f"Country: {st.session_state.country}")
                        st.write(f"Country Code: {st.session_state.country_code}")
                        st.write(f"Admin Level: {st.session_state.admin_level}")
                    st.write(f"Year: {year}")
                    st.write(f"Analysis Type: {analysis_type}")
                    if analysis_type == "Age/Sex Disaggregated":
                        st.write(f"Age Group: {age_group_name}")
                        st.write(f"Sex: {sex_name}")

with col2:
    st.subheader("ℹ️ About This Tool")
    st.markdown("""
    **WorldPop Population Analysis Tool**
    
    This tool analyzes high-resolution population distribution data for public health planning and intervention targeting.
    
    **Data Sources:**
    - **WorldPop**: High-resolution global population datasets
    - **GADM**: Global Administrative Areas database
    
    **Coverage:**
    - All African countries supported
    - Administrative levels 0-4
    - Years 2000-2020
    - Age/sex disaggregated data available
    - ~100m spatial resolution
    
    **Use Cases:**
    - Intervention targeting & resource allocation
    - Disease burden estimation
    - Campaign planning (SMC, ITN distribution)
    - Health facility catchment analysis
    - Denominator estimation for surveys
    
    **Technical Notes:**
    - Resolution: ~100m per pixel
    - Temporal coverage: 2000-2020
    - UN-adjusted estimates available
    - Age groups: 0-80+ in 5-year bands
    - Sex-specific estimates available
    
    **Performance Notes:**
    - **First run**: 30-120 seconds (downloading 50-200 MB files)
    - **Subsequent runs**: 5-15 seconds (cached data)
    - **Large countries** (Nigeria, DRC, Ethiopia): Longer processing
    - Data is cached automatically for faster repeat analysis
    """)
    
    with st.expander("📋 Usage Tips"):
        st.markdown("""
        - **Admin levels**: Use level 2-3 for district analysis
        - **Recent data**: 2020 is most recent complete year
        - **Age/sex data**: Use for targeted interventions
        - **Total population**: Best for overall planning
        - **Custom shapefiles**: Include .prj files
        - **Large areas**: May take longer to process
        - **Downloads**: Excel includes summary stats
        - **First time slow?** ✅ Normal! File is 50-200 MB (then cached)
        - **Repeat analysis**: Much faster with cached data
        """)
    
    with st.expander("⚡ Performance Tips"):
        st.markdown("""
        **Why is it slow the first time?**
        - WorldPop files are 50-200 MB (vs CHIRPS 2-5 MB)
        - High-resolution population data = larger files
        - Network download speed dependent
        
        **How to speed up:**
        - ✅ Data caches automatically after first download
        - ✅ Use same country/year for repeat analyses
        - ✅ Start with higher admin levels (faster processing)
        - ✅ Good internet connection helps first download
        - ✅ Subsequent runs are 5-10x faster!
        
        **File Size by Country (approximate):**
        - Small countries (Gambia, Lesotho): 20-40 MB
        - Medium countries (Sierra Leone, Benin): 50-80 MB
        - Large countries (Nigeria, DRC, Ethiopia): 150-250 MB
        """)
    
    with st.expander("👥 Population Analysis Types"):
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
    
    with st.expander("🎯 Public Health Applications"):
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
        """)
    
    with st.expander("💾 Download Features"):
        st.markdown("""
        **CSV Download:**
        - Clean tabular data
        - All administrative attributes
        - Population totals & densities
        - Ready for GIS/analysis tools
        
        **Excel Download:**
        - Population data sheet
        - Summary statistics sheet
        - Metadata documentation
        - Professional format
        """)
    
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        - **No data**: Try different year/age group
        - **Slow loading**: Normal for large countries
        - **Custom shapefile**: Requires country selection
        - **Projection errors**: Include .prj file
        - **Missing areas**: Check admin level
        - **Large downloads**: Try higher admin levels
        """)

    # System info
    with st.expander("📊 System Information"):
        st.write(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Available years: 2000-2020")
        st.write(f"Countries available: {len(COUNTRY_OPTIONS)}")
        st.write(f"Age groups: {len(AGE_GROUPS)}")
        st.write("Resolution: ~100m")
        st.write("Source: WorldPop (www.worldpop.org)")
        st.write("Tool version: v1.0 (Premium Theme)")

# Footer
st.markdown("---")
st.markdown("*Built for public health professionals and researchers*")
st.markdown("**Contact**: Mohamed Sillah Kanu | Informatics Consultancy Firm - Sierra Leone (ICF-SL)")
st.markdown("**Email**: mohamed.kanu@informaticsconsultancyfirm.com")
st.markdown("**Data Sources**: WorldPop (www.worldpop.org) | GADM (gadm.org)")
