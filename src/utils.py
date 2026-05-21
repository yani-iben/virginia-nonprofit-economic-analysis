import folium
import plotly.express as px
import matplotlib.pyplot as plt
import textwrap
import os
import seaborn as sns
from IPython.display import IFrame

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
    Finds the top 3 highest grant-dependent sectors for a specific region 
    and formats them with HTML string styling for dynamic Folium tooltip injections.
    
    Expected schema for 'sector_stats': ['VDOE_Region', 'Category', 'grant_to_expense_ratio']
    """
    # Defensive programming: Handle edge cases where spatial regions lack financial data
    if region not in sector_stats['VDOE_Region'].unique():
        return "Insufficient data for sector breakdown"
        
    # Isolate localized regional subset
    region_data = sector_stats[sector_stats['VDOE_Region'] == region]
    
    # Extract the top 3 highest grant-dependent profiles
    top_3 = region_data.sort_values('grant_to_expense_ratio', ascending=False).head(3)
    
    # Construct clean, text-wrapped HTML string components for the UI rendering
    summary_lines = []
    for _, row in top_3.iterrows():
        cat_name = str(row['Category'])
        # Gracefully handle overflow text on long NTEE category strings
        display_name = (cat_name[:22] + '..') if len(cat_name) > 22 else cat_name
        
        summary_lines.append(f"&bull; {display_name}: {row['grant_to_expense_ratio']:.2f}")
    
    # Return a singlular string block separated by HTML break tags
    return "<br>".join(summary_lines)

def create_impact_dashboard(geo_df, title_html, tooltip_style, save_name='vdoe_impact_dashboard.html'):
    """
    Generates a professional Folium choropleth with centered regional labels 
    and custom nudging logic for Virginia's unique geography.
    """

    m = folium.Map(location=[37.8, -78.5], zoom_start=7, tiles='cartodbpositron')
    m.get_root().html.add_child(folium.Element(title_html))

    # Add Choropleth Layer
    folium.Choropleth(
        geo_data=geo_df.to_json(),
        data=geo_df,
        columns=['VDOE_Region', 'grant_to_expense_ratio'],
        key_on='feature.properties.VDOE_Region',
        fill_color='GnBu',
        fill_opacity=0.8,
        line_color="#cbc8c8", 
        line_weight=1.5,
        legend_name='Grants per $1.00 Spent'
    ).add_to(m)

    # Add Precision Centered Labels with Manual Nudges
    for _, row in geo_df.iterrows():
        geom = row.geometry
        center = geom.centroid.coords[0]
        lat, lon = center[1], center[0]
        region = row['VDOE_Region']
        
        # cartographic adjustments
        if 'Northern Neck' in region:
            lat -= 0.18; lon += 0.25
        elif 'Tidewater' in region:
            lat -= 0.10; lon += 0.15
        elif 'Northern Virginia' in region:
            lat += 0.05; lon -= 0.05
        elif 'Southwest' in region:
            lon -= 0.10

        folium.map.Marker(
            [lat, lon],
            icon=folium.DivIcon(
                icon_size=(120, 40),
                icon_anchor=(60, 20),
                html=f'''<div style="font-size: 8.5pt; font-weight: bold; color: #232d4b; 
                        text-align: center; line-height: 1.1; text-shadow: 1px 1px 3px white;">
                        {region.replace(' ', '<br>')}</div>'''
            )
        ).add_to(m)

    # Interactive Hover Layer (Enriched with Top Sectors)
    folium.GeoJson(
        geo_df.to_json(),
        style_function=lambda x: {'fillColor': '#ffffff00', 'color': 'white', 'weight': 0.5},
        tooltip=folium.GeoJsonTooltip(
            fields=['VDOE_Region', 'grant_to_expense_ratio', 'hover_info'],
            aliases=['<b>Region:</b>', '<b>Ratio:</b>', '<b>Top Economic Sectors:</b>'],
            style=tooltip_style,
            sticky=False
        )
    ).add_to(m)

    # 5. Export
    m.save(save_name)
    return save_name

def plot_sector_diversity(data, save_path=None):
    """
    Generates a professional horizontal bar chart for nonprofit sectors.
    """
    plt.figure(figsize=(12, 10))
    # Use a consistent, professional palette
    sns.barplot(
        data=data.sort_values('Org_Count', ascending=True), 
        x='Org_Count', y='Sector', 
        palette='viridis', edgecolor='gray', linewidth=0.5
    )
    
    # Add data labels
    for i, v in enumerate(data.sort_values('Org_Count', ascending=True)['Org_Count']):
        plt.text(v + 100, i, f'{int(v):,}', va='center', fontweight='medium')

    plt.title('Nonprofit Diversity by Sector', fontsize=20, loc='left', pad=20, fontweight='bold')
    sns.despine(left=True, bottom=False)
    plt.tight_layout()
    plt.legend(
    title='Category Focus', 
    bbox_to_anchor=(1.02, 1), 
    loc='upper left', 
    frameon=False    
)
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

def plot_revenue_distribution(counts, labels, colors, save_path=None):
    """
    Generates a high-fidelity donut chart for revenue distribution.
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    patches, texts, autotexts = ax.pie(
        counts, 
        autopct='%1.0f%%', 
        startangle=140, 
        colors=colors,
        pctdistance=1.1
    )

    ax.legend(
        patches, 
        labels, 
        title="Annual Revenue (in USD $)", 
        loc="center left", 
        bbox_to_anchor=(1, 0, 0.5, 1),
        frameon=False
    )

    plt.title('Distribution of Virginia 501(c)(3) Organizations by Annual Revenue', fontsize=16, fontweight='bold')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight',transparent=False, facecolor='white')
    plt.show()
def plot_tech_ecosystem_landscape(data, save_path=None):
    """
    Generates a dual-axis visualization comparing the regional count of 
    tech-adjacent nonprofits against their total operational expenditures.
    Uses the project's consistent GnBu/Teal color theme.
    """
    fig, ax1 = plt.subplots(figsize=(13, 6.5))

    # Primary Axis: Deep Teal bars for the Fiscal Footprint
    sns.barplot(
        data=data, 
        x='VDOE_Region', 
        y='Tech_Capital_Billions', 
        ax=ax1, 
        color='#0E5859',  # Deep Teal
        alpha=0.85
    )
    ax1.set_ylabel('Total Operating Expenditures (Billions $)', color='#0E5859', fontweight='bold', fontsize=12)
    ax1.set_xlabel('VDOE Region', fontweight='bold', fontsize=12)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=25, ha='right')
    ax1.grid(axis='y', linestyle='--', alpha=0.3)

    # Secondary Axis: Soft Mint line overlay for the raw Numerical Density
    ax2 = ax1.twinx()
    sns.lineplot(
        data=data, 
        x='VDOE_Region', 
        y='Tech_Count', 
        ax=ax2, 
        color='#72BDC0',  # Soft Mint
        marker='o', 
        markersize=8,
        linewidth=3
    )
    ax2.set_ylabel('Number of Tech-Adjacent Entities (Count)', color='#3792A4', fontweight='bold', fontsize=12)

    plt.title('Virginia Tech-Adjacent Nonprofits: Regional Density vs. Fiscal Footprint (2023)', 
              fontsize=14, fontweight='bold', pad=25, color='#222222')

    sns.despine(ax=ax1, top=True, right=False)
    sns.despine(ax=ax2, top=True, right=False)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

pillar_map = {
    "Advanced R&D & Computing": "Tech, R&D & Policy",
    "National Security & Tech Policy": "Tech, R&D & Policy",
    "STEM Talent Pipelines": "Tech, R&D & Policy",
    "Science and Technology Research": "Tech, R&D & Policy",
    "Social Science Research": "Tech, R&D & Policy",
    "Healthcare Infrastructure": "Healthcare Infrastructure",
    "Direct Community Human Services": "Core Human Services",
    "Human Services": "Core Human Services",
    "Housing/Shelter": "Core Human Services",
    "Food/Agriculture": "Core Human Services",
    "Educational Institutions": "Institutional Foundations",
    "Education": "Institutional Foundations",
    "Religion Related": "Institutional Foundations",
    "Arts, Culture, Humanities": "Institutional Foundations",
    "Mutual Benefit": "Institutional Foundations",
    "Unclassified Administrative Gaps": "Institutional Foundations",
    "Unknown": "Institutional Foundations"
}
def process_regional_pillar_shares(df, pillar_mapping=pillar_map):
    """
    Cleans, aggregates, and normalizes expenditures into macro-pillar shares
    sorted by Tech & Policy intensity.
    
    Args:
        df (pd.DataFrame): The main masterfile dataframe.
        pillar_mapping (dict): Dictionary mapping granular categories to macro pillars.
        
    Returns:
        pd.DataFrame: A normalized percentage dataframe ready for visualization.
    """
    # Filter out inactive organizations
    df_active = df[df['Employee_Count_Unified'] > 0].copy()
    
    # Map to macro pillars
    df_active['Macro_Pillar'] = df_active['Category'].map(pillar_mapping).fillna("Institutional Foundations")
    
    # Aggregate and pivot
    pillar_audit = df_active.groupby(['VDOE_Region', 'Macro_Pillar'])['Total_Exp_Unified'].sum().reset_index()
    pivot_df = pillar_audit.pivot(index='VDOE_Region', columns='Macro_Pillar', values='Total_Exp_Unified').fillna(0)
    
    # Normalize to 100%
    pivot_perc = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
    
    # Sort by Tech share
    pivot_perc['Sorting_Key'] = pivot_perc.get('Tech, R&D & Policy', 0)
    return pivot_perc.sort_values(by='Sorting_Key', ascending=True)


def plot_regional_distribution(pivot_perc, save_path=None):
    """
    Renders the anti-collision stacked horizontal bar chart for regional capital profiles.
    """
    fig, ax = plt.subplots(figsize=(14, 9))
    sns.set_theme(style="white")

    custom_palette = {
        "Tech, R&D & Policy": "#0A4D68",          
        "Healthcare Infrastructure": "#748DA6",   
        "Core Human Services": "#9CB4CC",         
        "Institutional Foundations": "#F2F2F2"   
    }

    categories_order = list(custom_palette.keys())
    
    # Filter plot to columns that exist in the custom palette
    plot_cols = [col for col in categories_order if col in pivot_perc.columns]
    
    pivot_perc[plot_cols].plot(
        kind='barh', stacked=True, ax=ax, 
        color=[custom_palette[c] for c in plot_cols],
        width=0.6, edgecolor='white', linewidth=1.2
    )

    # Labeling and anti-collision tracking
    for i, (region, row) in enumerate(pivot_perc.iterrows()):
        current_left = 0
        for category in plot_cols:
            val = row[category]
            midpoint = current_left + (val / 2)
            
            if category == "Tech, R&D & Policy" and val > 0.05:
                ax.text(
                    x=val + 1.2, y=i + 0.18, s=f"★ {val:.1f}% Strategic Tech", 
                    va='center', ha='left', fontsize=10, weight='bold', color='#0A4D68',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.95),
                    zorder=5
                )
            elif category != "Tech, R&D & Policy" and val >= 10.0:
                text_color = 'white' if category != "Institutional Foundations" else '#555555'
                ax.text(
                    x=midpoint, y=i - 0.02, s=f"{val:.0f}%", 
                    va='center', ha='center', fontsize=10, weight='bold', color=text_color,
                    zorder=4
                )
            current_left += val

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.set_xlim(0, 100)
    ax.xaxis.grid(True, linestyle='--', alpha=0.5, color='#e0e0e0')
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}%'))

    plt.title('Virginia Regional Capital Priorities: Strategic Tech & Policy Concentration vs. Infrastructure Baseline', 
              fontsize=14, weight='bold', pad=25, loc='left')
    plt.xlabel('Proportional Share of Total Regional Expenditures (%)', fontsize=11, labelpad=10)
    plt.ylabel('VDOE Region', fontsize=11, labelpad=10)

    plt.legend(title='Macro Expenditure Pillar', bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False, fontsize=11, title_fontsize=11)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300)
    plt.show()