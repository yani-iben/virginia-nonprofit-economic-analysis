# app.py
import streamlit as st
import pandas as pd
import geopandas as gpd
from src.utils import create_sector_chart, TITLE_HTML

st.set_page_config(layout="wide")
st.title("Virginia Nonprofit Fiscal Load Dashboard")

# 1. Load your pre-processed 'final_map' and 'sector_stats'
# (You would save these as .geojson and .csv in your cleaning notebook)
@st.cache_data
def load_data():
    geo = gpd.read_file('data/processed/final_map.geojson')
    stats = pd.read_csv('data/processed/sector_stats.csv')
    return geo, stats

final_map, sector_stats = load_data()

# 2. Sidebar for Selection
region = st.sidebar.selectbox("Select a VDOE Region", sorted(final_map['VDOE_Region'].unique()))

# 3. Display the Plotly Chart directly
st.plotly_chart(create_sector_chart(region, sector_stats), use_container_width=True)

# 4. Display the Map
st.components.v1.html(open('vdoe_impact_dashboard_FINAL.html', 'r').read(), height=600)