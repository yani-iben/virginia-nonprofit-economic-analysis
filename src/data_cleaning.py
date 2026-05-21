import pandas as pd
import numpy as np
import os
from transformers import pipeline
import logging

# Setting up logging for pipeline transparency
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def safe_load_csv(path):
    """Utility to load CSV with error handling and logging."""
    if not os.path.exists(path):
        logging.error(f"File not found: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, low_memory=False)
        df.columns = df.columns.str.strip()
        logging.info(f"Successfully loaded {path} with {len(df)} records.")
        return df
    except Exception as e:
        logging.error(f"Failed to load {path}: {e}")
        return pd.DataFrame()

#Schema Mapping
IRS_SCHEMA_MAP = {
    'CORE': {
        'Revenue_Grants_Unified': 'totcntrbgfts',
        'Total_Revenue_Unified': 'totrevenue',
        'Total_Exp_Unified': 'totfuncexpns',
        'Employee_Count_Unified': 'noemplyeesw3cnt',
        'comp_cols': ['compnsatncurrofcr', 'othrsalwages', 'pensionplancontrb', 'othremplyeebenef']
    },
    'EZ': {
        'Revenue_Grants_Unified': 'totcntrb',
        'Total_Revenue_Unified': 'totrevnue',
        'Total_Exp_Unified': 'totexpns',
        'Employee_Count_Unified': None,
        'comp_cols': ['salaries_amt']
    },
    'PF': {
        'Revenue_Grants_Unified': 'GRSCONTRGIFTS',
        'Total_Revenue_Unified': 'TOTRCPTPERBKS',
        'Total_Exp_Unified': 'TOTEXPNSPBKS',
        'Employee_Count_Unified': None,
        'comp_cols': ['COMPOFFICERS', 'PENSPLEMPLBENF']
    }
}

def _process_numeric(df, raw_col):
    """Internal helper to safely convert IRS strings to floats."""
    if raw_col and raw_col in df.columns:
        return pd.to_numeric(df[raw_col], errors='coerce').fillna(0)
    return 0

def standardize_and_stack_financials(core_path, ez_path, pf_path):
    """
    Harmonizes disparate IRS schemas (Core, EZ, PF) into a unified dataset.
    Uses dynamic mapping to ensure infrastructure stability.
    """
    path_map = {'CORE': core_path, 'EZ': ez_path, 'PF': pf_path}
    all_extracts = []

    for form_type, path in path_map.items():
        df = safe_load_csv(path)
        if df.empty:
            continue
            
        mapping = IRS_SCHEMA_MAP[form_type]
        processed_df = pd.DataFrame()
        
        # Standardize join key
        df.columns = [c.upper() if c.lower() == 'ein' else c for c in df.columns]
        processed_df['EIN'] = df['EIN'].astype(str).str.split('.').str[0].str.zfill(9)
        
        # Map Unified Financials
        processed_df['Revenue_Grants_Unified'] = _process_numeric(df, mapping['Revenue_Grants_Unified'])
        processed_df['Total_Revenue_Unified'] = _process_numeric(df, mapping['Total_Revenue_Unified'])
        processed_df['Total_Exp_Unified'] = _process_numeric(df, mapping['Total_Exp_Unified'])
        processed_df['Employee_Count_Unified'] = _process_numeric(df, mapping['Employee_Count_Unified'])
        
        # Map Compensation (Summing multiple columns if necessary)
        comp_data = pd.DataFrame(
            {c: _process_numeric(df, c) for c in mapping['comp_cols']},
            index=df.index
        )
        processed_df['Total_Comp_Unified'] = comp_data.sum(axis=1)
        
        # Carry over tax period if available
        if 'tax_pd' in df.columns:
            processed_df['tax_pd'] = df['tax_pd']
        elif 'TAX_PERIOD' in df.columns:
            processed_df['tax_pd'] = df['TAX_PERIOD']

        all_extracts.append(processed_df)

    if not all_extracts:
        return pd.DataFrame()

    return pd.concat(all_extracts, axis=0, ignore_index=True)

def clean_nonprofit_data(file_path, ntee_map_path='../data/ntee_simple.csv'):
    """
    Ingests raw IRS BMF data and filters for 501c3 VA nonprofits.
    Extracts the single-character NTEE prefix to map macro categories cleanly,
    preventing multi-character alphanumeric string collisions.
    """
    df = safe_load_csv(file_path)
    if df.empty: 
        return df

    # Enforce administrative universe constraints
    df = df[(df['STATE'] == 'VA') & (df['SUBSECTION'] == 3) & (df['STATUS'] == 1)].copy()
    
    # Extract the foundational first letter (e.g., 'B43' -> 'B')
    df['type_prefix'] = df['NTEE_CD'].str[0].fillna('Z').str.upper()
    
    try:
        # Load look-up index matrix
        codes = pd.read_csv(ntee_map_path)
        
        # Build dictionary from Code letter to Category name
        label_map = codes.set_index('Code')['Category'].to_dict()
        
        # Map the single prefix letter to the text category name
        df['Category'] = df['type_prefix'].map(label_map).fillna('Unknown')
    except FileNotFoundError:
        logging.warning(f"Label map not found at {ntee_map_path}. Defaulting categories to 'Unknown'.")
        df['Category'] = 'Unknown'
        
    return df

def enrich_with_financials(df_bmf, finance_df):
    """Deduplicates and merges Masterfile with financial extracts."""
    if finance_df.empty: return df_bmf
    
    # Ensure EIN consistency
    df_bmf['EIN'] = df_bmf['EIN'].astype(str).str.split('.').str[0].str.zfill(9)
    
    # Deduplicate: Keep most recent tax filing
    sort_col = 'tax_pd' if 'tax_pd' in finance_df.columns else 'EIN'
    finance_df = finance_df.sort_values(sort_col, ascending=False).drop_duplicates('EIN')
    
    merged_df = pd.merge(df_bmf, finance_df, on='EIN', how='left')
    
    # Vectorized fillna for performance
    fill_cols = ['Total_Comp_Unified', 'Employee_Count_Unified', 'Revenue_Grants_Unified', 'Total_Exp_Unified']
    merged_df[fill_cols] = merged_df[fill_cols].fillna(0)
            
    return merged_df

def classify_tech_policy_nlp(df, sample_size=100):
    """
    Leverages a Pre-trained NLP Transformer model 
    to classify the strategic mission orientation of high-impact entities.
    """
    logging.info("Initializing Hugging Face Zero-Shot Classification Pipeline...")
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    
    # Filter for top entities by expenditure to optimize compute time
    top_entities = df.nlargest(sample_size, 'Total_Exp_Unified').copy()
    candidate_labels = ["Technology Policy and Research", "Traditional Community Service", "Healthcare and Education"]
    
    classifications = []
    for idx, row in top_entities.iterrows():
        # Clean text string combining name and operational category
        text_to_classify = f"{row['NAME']} - Sector: {row['Category']}"
        try:
            res = classifier(text_to_classify, candidate_labels)
            # Capture the highest probability label
            top_label = res['labels'][0]
            classifications.append(top_label)
        except Exception:
            classifications.append("Unclassified")
            
    top_entities['NLP_Model_Classification'] = classifications
    return top_entities

def remediate_unknown_categories_granular(df):
    """
    Programmatically remediates 'Unknown' data gaps
    and general classifications using a granular, policy-aligned taxonomy
    via a pre-trained Zero-Shot Transformer pipeline.
    """
    # Define an explicit, granular target matrix for the NLP model
    policy_labels = [
        "National Security & Tech Policy",
        "Advanced R&D & Computing",
        "STEM Talent Pipelines",
        "Direct Community Human Services",
        "Healthcare Infrastructure"
    ]
    
    # Isolate rows that are unmapped or tagged generic "Unknown"
    target_mask = (df['Category'] == 'Unknown') | (df['Category'].fillna('').str.upper() == 'UNKNOWN')
    target_count = target_mask.sum()
    
    if target_count == 0:
        logging.info("No unmapped entities detected for granular remediation.")
        return df
        
    logging.info(f"NLP Deep-Dive: Classifying {target_count} records into advanced taxonomy...")
    
    # Initialize the robust BART classification model
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    
    # Batch process or iterate over target slices to handle predictions safely
    for idx, row in df[target_mask].iterrows():
        # Combine entity name and NTEE sub-code string text if available for maximum model context
        text_context = f"Organization Name: {row['NAME']}. Primary Tax Metadata: {row['NTEE_CD']}"
        
        try:
            res = classifier(text_context, policy_labels)
            # Impute the highest probability semantic category directly back into the dataset
            df.at[idx, 'Category'] = res['labels'][0]
        except Exception as e:
            continue
            
    logging.info("Advanced taxonomy expansion complete.")
    return df