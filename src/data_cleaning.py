"""
data_cleaning.py
----------------
Handles the ingestion and normalization of IRS Form 990 Core, EZ, and PF data.

LIMITATION: As of May 2026, the 2023 Financial Extracts are the most complete 
available. This script accounts for the ~10% salary variance from the 
CNE 2026 Report by standardizing join keys across disparate IRS schemas.
"""
import pandas as pd
import numpy as np

def clean_nonprofit_data(file_path, ntee_map_path='../data/ntee_simple.csv'):
    """
    Ingests raw IRS BMF data and filters for the 503c VA charitable nonprofits.
    """
    # Use low_memory=False for BMF CSVs to avoid type guessing errors
    df = pd.read_csv(file_path, low_memory=False)
    
    # Filtering upon organizations in Virginia
    df = df[df['STATE'] == 'VA'].copy()
    
    # Subsection 3 = 501(c)(3); Status 1 = Active
    mask = (df['SUBSECTION'] == 3) & (df['STATUS'] == 1)
    df = df[mask].copy()
    
    # Using the NTEE Code to group nonprofits into broad sectors
    # Extract the first letter (Prefix) to get the broad sector
    def get_ntee_prefix(val):
        if isinstance(val, str) and len(val) > 0:
            return val[0]
        return 'Z' # 'Z' represents the "Unclassified" groups
        
    df['type_prefix'] = df['NTEE_CD'].apply(get_ntee_prefix)
    
    # 5. Mapping Human-Readable Labels
    try:
        codes = pd.read_csv(ntee_map_path)
        label_map = codes.set_index('Code')['Category'].to_dict()
        df['Organization_Type'] = df['type_prefix'].map(label_map)
    except FileNotFoundError:
        print(f"Warning: {ntee_map_path} not found. Skipping label mapping.")
    
    # Focusing on financial columns for economic impact analysis
    finance_cols = ['REVENUE_AMT', 'ASSET_AMT', 'INCOME_AMT']
    for col in finance_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            # arcsinh handles high variance (large hospitals vs small charities)
            df[f'{col}_transformed'] = np.arcsinh(df[col])
            
    return df

def enrich_with_financials(df_bmf, finance_df):
    """
    The final merge step with string cleaning and deduplication.
    Standardizes EINs to ensure a high match rate between the Masterfile 
    and the stacked financial extracts.
    """
    # Standardize EINs to 9-digit strings to ensure they match
    # This handles cases where EINs are read as floats (123.0) or ints
    df_bmf['EIN'] = df_bmf['EIN'].astype(str).str.split('.').str[0].str.zfill(9)
    finance_df['EIN'] = finance_df['EIN'].astype(str).str.split('.').str[0].str.zfill(9)
    
    # Deduplicate Finance Data
    # If an organization appears twice, we keep the most recent tax period
    if 'tax_pd' in finance_df.columns:
        finance_df = finance_df.sort_values('tax_pd', ascending=False).drop_duplicates('EIN')
    else:
        finance_df = finance_df.drop_duplicates('EIN')
    
    # Perform the Left Join
    # We keep all VA nonprofits from the BMF and add financial data where available
    merged_df = pd.merge(df_bmf, finance_df, on='EIN', how='left')
    
    # Fill missing financials with 0 for organizations that didn't have an extract.
    fill_cols = ['Total_Comp_Unified', 'Employee_Count_Unified', 'Revenue_Grants_Unified', 'Total_Exp_Unified']
    for col in fill_cols:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].fillna(0)
            
    return merged_df
def standardize_and_stack_financials(core_path, ez_path, pf_path):
    """
    Loads, maps, and stacks the three different IRS filing types (Core, EZ, PF).
    Harmonizes disparate schemas into a unified financial dataset.
    """
    
    # IRS CORE Dataset (Large Organizations - Form 990)
    df_core = pd.read_csv(core_path, low_memory=False)
    df_core.columns = df_core.columns.str.strip()
    
    # Mapping Core Financials
    df_core['Revenue_Grants_Unified'] = pd.to_numeric(df_core['totcntrbgfts'], errors='coerce').fillna(0) if 'totcntrbgfts' in df_core.columns else 0
    df_core['Total_Revenue_Unified'] = pd.to_numeric(df_core['totrevenue'], errors='coerce').fillna(0) if 'totrevenue' in df_core.columns else 0
    df_core['Total_Exp_Unified'] = pd.to_numeric(df_core['totfuncexpns'], errors='coerce').fillna(0) if 'totfuncexpns' in df_core.columns else 0
    
    # Mapping Core Compensation
    core_comp_cols = ['compnsatncurrofcr', 'othrsalwages', 'pensionplancontrb', 'othremplyeebenef']
    for c in core_comp_cols:
        df_core[c] = pd.to_numeric(df_core[c], errors='coerce').fillna(0) if c in df_core.columns else 0
    df_core['Total_Comp_Unified'] = df_core[core_comp_cols].sum(axis=1)
    df_core['Employee_Count_Unified'] = pd.to_numeric(df_core['noemplyeesw3cnt'], errors='coerce').fillna(0) if 'noemplyeesw3cnt' in df_core.columns else 0

    # IRS EZ Dataset (Mid-Sized Organizations - Form 990-EZ)
    df_ez = pd.read_csv(ez_path, low_memory=False)
    df_ez.columns = df_ez.columns.str.strip()
    
    # Mapping EZ Financials
    df_ez['Revenue_Grants_Unified'] = pd.to_numeric(df_ez['totcntrb'], errors='coerce').fillna(0) if 'totcntrb' in df_ez.columns else 0
    df_ez['Total_Revenue_Unified'] = pd.to_numeric(df_ez['totrevnue'], errors='coerce').fillna(0) if 'totrevnue' in df_ez.columns else 0
    df_ez['Total_Exp_Unified'] = pd.to_numeric(df_ez['totexpns'], errors='coerce').fillna(0) if 'totexpns' in df_ez.columns else 0
    
    # Mapping EZ Compensation (Often aggregated in salaries_amt)
    ez_comp_col = 'salaries_amt' if 'salaries_amt' in df_ez.columns else 'totexpns'
    df_ez['Total_Comp_Unified'] = pd.to_numeric(df_ez.get(ez_comp_col, 0), errors='coerce').fillna(0)
    df_ez['Employee_Count_Unified'] = 0 # EZ forms rarely provide a reliable W3 count

    # 3. IRS PF Dataset (Private Foundations - Form 990-PF)
    df_pf = pd.read_csv(pf_path, low_memory=False)
    df_pf.columns = df_pf.columns.str.strip()
    
    # Mapping PF Financials
    df_pf['Revenue_Grants_Unified'] = pd.to_numeric(df_pf['GRSCONTRGIFTS'], errors='coerce').fillna(0) if 'GRSCONTRGIFTS' in df_pf.columns else 0
    df_pf['Total_Revenue_Unified'] = pd.to_numeric(df_pf['TOTRCPTPERBKS'], errors='coerce').fillna(0) if 'TOTRCPTPERBKS' in df_pf.columns else 0
    df_pf['Total_Exp_Unified'] = pd.to_numeric(df_pf['TOTEXPNSPBKS'], errors='coerce').fillna(0) if 'TOTEXPNSPBKS' in df_pf.columns else 0
    
    # Mapping PF Compensation
    pf_comp_cols = ['COMPOFFICERS', 'PENSPLEMPLBENF'] 
    for c in pf_comp_cols:
        df_pf[c] = pd.to_numeric(df_pf[c], errors='coerce').fillna(0) if c in df_pf.columns else 0
    df_pf['Total_Comp_Unified'] = df_pf[pf_comp_cols].sum(axis=1)
    df_pf['Employee_Count_Unified'] = 0

    # 4. STACK AND UNIFY
    # Ensure EIN is treated consistently across all dataframes
    for df_temp in [df_core, df_ez, df_pf]:
        df_temp.columns = [c.upper() if c.lower() == 'ein' else c for c in df_temp.columns]

    # These are the columns that will survive the concatenation
    keep_cols = [
        'EIN', 
        'Revenue_Grants_Unified', 
        'Total_Revenue_Unified', 
        'Total_Exp_Unified',
        'Total_Comp_Unified', 
        'Employee_Count_Unified', 
        'tax_pd'
    ]
    
    all_extracts = []
    for df_temp in [df_core, df_ez, df_pf]:
        # Filter for only the columns that exist in the temporary dataframe
        available_cols = [c for c in keep_cols if c in df_temp.columns]
        all_extracts.append(df_temp[available_cols])

    return pd.concat(all_extracts, axis=0, ignore_index=True)