import folium
import plotly.express as px
import textwrap


# This ensures every county name from the Census matches a VDOE region
vdoe_mapping = {
    # REGION 1: Central Virginia
    'CHARLES CITY': 'Central Virginia', 'CHESTERFIELD': 'Central Virginia', 'DINWIDDIE': 'Central Virginia', 
    'GOOCHLAND': 'Central Virginia', 'HANOVER': 'Central Virginia', 'HENRICO': 'Central Virginia', 
    'NEW KENT': 'Central Virginia', 'POWHATAN': 'Central Virginia', 'PRINCE GEORGE': 'Central Virginia', 
    'SURRY': 'Central Virginia', 'SUSSEX': 'Central Virginia', 'COLONIAL HEIGHTS': 'Central Virginia', 
    'HOPEWELL': 'Central Virginia', 'PETERSBURG': 'Central Virginia', 'RICHMOND CITY': 'Central Virginia',

    # REGION 2: Tidewater
    'ACCOMACK': 'Tidewater', 'ISLE OF WIGHT': 'Tidewater', 'NORTHAMPTON': 'Tidewater', 'SOUTHAMPTON': 'Tidewater', 
    'YORK': 'Tidewater', 'CHESAPEAKE': 'Tidewater', 'FRANKLIN CITY': 'Tidewater', 'HAMPTON': 'Tidewater', 
    'NEWPORT NEWS': 'Tidewater', 'NORFOLK': 'Tidewater', 'POQUOSON': 'Tidewater', 'PORTSMOUTH': 'Tidewater', 
    'SUFFOLK': 'Tidewater', 'VIRGINIA BEACH': 'Tidewater', 'WILLIAMSBURG': 'Tidewater', 'JAMES CITY': 'Tidewater',

    # REGION 3: Northern Neck (Including missing Middle Peninsula)
    'CAROLINE': 'Northern Neck', 'ESSEX': 'Northern Neck', 'GLOUCESTER': 'Northern Neck', 'KING GEORGE': 'Northern Neck', 
    'LANCASTER': 'Northern Neck', 'SPOTSYLVANIA': 'Northern Neck', 'STAFFORD': 'Northern Neck', 'FREDERICKSBURG': 'Northern Neck',
    'KING AND QUEEN': 'Northern Neck', 'KING WILLIAM': 'Northern Neck', 'MATHEWS': 'Northern Neck', 'MIDDLESEX': 'Northern Neck',
    'NORTHUMBERLAND': 'Northern Neck', 'RICHMOND': 'Northern Neck', 'WESTMORELAND': 'Northern Neck',

    # REGION 4: Northern Virginia
    'ALEXANDRIA': 'Northern Virginia', 'ARLINGTON': 'Northern Virginia', 'FAIRFAX': 'Northern Virginia', 
    'LOUDOUN': 'Northern Virginia', 'PRINCE WILLIAM': 'Northern Virginia', 'FALLS CHURCH': 'Northern Virginia',
    'MANASSAS': 'Northern Virginia', 'MANASSAS PARK': 'Northern Virginia', 'FAUQUIER': 'Northern Virginia',
    'CLARKE': 'Northern Virginia', 'WARREN': 'Northern Virginia', 'SHENANDOAH': 'Northern Virginia',
    'PAGE': 'Northern Virginia', 'FREDERICK': 'Northern Virginia', 'WINCHESTER': 'Northern Virginia',

    # REGION 5: Blue Ridge (and Central Ridge)
    'ALBEMARLE': 'Blue Ridge and Valley', 'CHARLOTTESVILLE': 'Blue Ridge and Valley', 'AMHERST': 'Blue Ridge and Valley',
    'APPOMATTOX': 'Blue Ridge and Valley', 'BEDFORD': 'Blue Ridge and Valley', 'CAMPBELL': 'Blue Ridge and Valley',
    'LYNCHBURG': 'Blue Ridge and Valley', 'NELSON': 'Blue Ridge and Valley', 'FLUVANNA': 'Blue Ridge and Valley',
    'GREENE': 'Blue Ridge and Valley', 'LOUISA': 'Blue Ridge and Valley', 'MADISON': 'Blue Ridge and Valley',
    'ORANGE': 'Blue Ridge and Valley', 'CULPEPER': 'Blue Ridge and Valley', 'RAPPAHANNOCK': 'Blue Ridge and Valley',

    # REGION 6: Western Virginia (Roanoke/Valley Area)
    'ROANOKE CITY': 'Western Virginia', 'ROANOKE': 'Western Virginia', 'SALEM': 'Western Virginia',
    'ALLEGHANY': 'Western Virginia', 'COVINGTON': 'Western Virginia', 'BOTETOURT': 'Western Virginia',
    'CRAIG': 'Western Virginia', 'FRANKLIN': 'Western Virginia', 'HENRY': 'Western Virginia',
    'MARTINSVILLE': 'Western Virginia', 'PATRICK': 'Western Virginia', 'PITTSYLVANIA': 'Western Virginia',
    'DANVILLE': 'Western Virginia',

    # REGION 7: Southwest
    'BRISTOL': 'Southwest', 'WISE': 'Southwest', 'WASHINGTON': 'Southwest', 'LEE': 'Southwest', 'SCOTT': 'Southwest',
    'BUCHANAN': 'Southwest', 'DICKENSON': 'Southwest', 'RUSSELL': 'Southwest', 'TAZEWELL': 'Southwest',
    'SMYTH': 'Southwest', 'WYTHE': 'Southwest', 'BLAND': 'Southwest', 'GILES': 'Southwest',
    'PULASKI': 'Southwest', 'RADFORD': 'Southwest', 'MONTGOMERY': 'Southwest', 'FLOYD': 'Southwest',
    'CARROLL': 'Southwest', 'GALAX': 'Southwest', 'GRAYSON': 'Southwest', 'NORTON': 'Southwest',

    # REGION 8: Southside
    'EMPORIA': 'Southside', 'PRINCE EDWARD': 'Southside', 'AMELIA': 'Southside', 'BRUNSWICK': 'Southside',
    'BUCKINGHAM': 'Southside', 'CHARLOTTE': 'Southside', 'CUMBERLAND': 'Southside', 'GREENSVILLE': 'Southside',
    'HALIFAX': 'Southside', 'LUNENBURG': 'Southside', 'MECKLENBURG': 'Southside', 'NOTTOWAY': 'Southside',

    # REGION Valley (Commonly grouped with 5/6 depending on dataset)
    'AUGUSTA': 'Blue Ridge and Valley', 'STAUNTON': 'Blue Ridge and Valley', 'WAYNESBORO': 'Blue Ridge and Valley',
    'HARRISONBURG': 'Blue Ridge and Valley', 'ROCKINGHAM': 'Blue Ridge and Valley', 'BATH': 'Blue Ridge and Valley',
    'HIGHLAND': 'Blue Ridge and Valley', 'ROCKBRIDGE': 'Blue Ridge and Valley', 'LEXINGTON': 'Blue Ridge and Valley',
    'BUENA VISTA': 'Blue Ridge and Valley'
}

# DASHBOARD VISUAL CONSTANTS
TITLE_HTML = '''
             <h3 align="center" style="font-size:16px; font-family: Arial; margin-bottom:0px;"><b>Nonprofit Fiscal Load: Grant Dependence by VDOE Region</b></h3>
             <p align="center" style="font-size:12px; font-family: Arial; margin-top:2px;"><i>Portion of expenses covered by government grants (2023)</i></p>
             '''

TOOLTIP_STYLE = """
    font-family: Arial;
    font-size: 11px; 
    background-color: white;
    border: 2px solid #232d4b;
    border-radius: 4px;
    padding: 5px;
    width: 180px; 
    white-space: normal;
"""

# THE HOVER LOGIC FUNCTION
def get_sector_summary(region, sector_stats):
    """
    Finds the top 3 sectors for a specific region and formats them for the tooltip.
    'sector_stats' must be a DataFrame with columns: ['VDOE_Region', 'Category', 'grant_ratio']
    """
    # Defensive check: if region is missing in data
    if region not in sector_stats['VDOE_Region'].unique():
        return "Insufficient data for sector breakdown"
        
    region_data = sector_stats[sector_stats['VDOE_Region'] == region]
    
    top_3 = region_data.sort_values('grant_ratio', ascending=False).head(3)
    
   #Format into HTML bullet points
    summary_lines = []
    for _, row in top_3.iterrows():
        # Clean up sector names: 'Human Services' -> 'Human Services'
        cat_name = str(row['Category'])
        display_name = (cat_name[:22] + '..') if len(cat_name) > 22 else cat_name
        
        summary_lines.append(f"&bull; {display_name}: ${row['grant_ratio']:.2f}")
    
    return "<br>".join(summary_lines)
def create_regional_map(final_map):
    # Reset index to ensure we have a clean 'VDOE_Region' column
    df_plot = final_map.copy().reset_index()

    fig = px.choropleth_mapbox(
        df_plot,
        geojson=df_plot.geometry.__geo_interface__, # Use the raw interface
        locations=df_plot.index,
        color='grant_to_expense_ratio',
        hover_name='VDOE_Region',
        hover_data={'index': False, 'grant_to_expense_ratio': ':.2f'},
        color_continuous_scale="GnBu",
        mapbox_style="carto-positron",
        center={"lat": 37.5, "lon": -78.5},
        zoom=5.8,
        opacity=0.9 # Higher opacity hides the map underneath more effectively
    )

    # THE "GROUT" FIX:
    # We add a thin border that matches the 'GnBu' scale's middle color.
    # This fills the white gaps with a neutral 'seam' that looks intentional.
    fig.update_traces(
    marker_line_width=1, 
    marker_line_color='white' # A crisp white line between the 8 regions looks very professional
    )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    return fig