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

def standardize_and_stack_financials(core_path, ez_path, pf_path):
    """
    Loads, maps, and stacks the three different IRS filing types.
    """
    # IRS CORE Dataset (Large Organizations)
    df_core = pd.read_csv(core_path, low_memory=False)
    df_core.columns = df_core.columns.str.strip()
    core_cols = ['compnsatncurrofcr', 'othrsalwages', 'pensionplancontrb', 'othremplyeebenef']
    for c in core_cols: df_core[c] = pd.to_numeric(df_core.get(c, 0), errors='coerce').fillna(0)
    df_core['Total_Comp_Unified'] = df_core[core_cols].sum(axis=1)
    df_core['Employee_Count_Unified'] = pd.to_numeric(df_core.get('noemplyeesw3cnt', 0), errors='coerce').fillna(0)
    
    # IRS EZ Dataset (Mid-Sized)
    df_ez = pd.read_csv(ez_path, low_memory=False)
    df_ez.columns = df_ez.columns.str.strip()
    ez_col = 'salaries_amt' if 'salaries_amt' in df_ez.columns else 'totexpns' # fallback to expenses if line 12 missing
    df_ez['Total_Comp_Unified'] = pd.to_numeric(df_ez.get(ez_col, 0), errors='coerce').fillna(0)
    df_ez['Employee_Count_Unified'] = 0
    
    # IRS PF Dataset(Private Foundations)
    df_pf = pd.read_csv(pf_path, low_memory=False)
    df_pf.columns = df_pf.columns.str.strip()
    pf_cols = ['COMPOFFICERS', 'PENSPLEMPLBENF'] 
    for c in pf_cols: df_pf[c] = pd.to_numeric(df_pf.get(c, 0), errors='coerce').fillna(0)
    df_pf['Total_Comp_Unified'] = df_pf[pf_cols].sum(axis=1)
    df_pf['Employee_Count_Unified'] = 0

    # STACK THEM
    # Keeping the unified columns and EIN for the join
    keep_cols = ['ein', 'EIN', 'Total_Comp_Unified', 'Employee_Count_Unified', 'tax_pd']
    all_extracts = []
    for df in [df_core, df_ez, df_pf]:
        # Handling case-insensitive EIN
        df.columns = [c.upper() if c.lower() == 'ein' else c for c in df.columns]
        all_extracts.append(df[[c for c in keep_cols if c in df.columns]])

    return pd.concat(all_extracts, axis=0, ignore_index=True)

def enrich_with_financials(df_bmf, finance_df):
    """
    The final merge step with string cleaning and deduplication.
    """
    # Standardize EINs to 9-digit strings
    df_bmf['EIN'] = df_bmf['EIN'].astype(str).str.split('.').str[0].str.zfill(9)
    finance_df['EIN'] = finance_df['EIN'].astype(str).str.split('.').str[0].str.zfill(9)
    
    # Deduplicate: Keep most recent tax period
    finance_df = finance_df.sort_values('tax_pd', ascending=False).drop_duplicates('EIN')
    return pd.merge(df_bmf, finance_df, on='EIN', how='left').fillna(0)