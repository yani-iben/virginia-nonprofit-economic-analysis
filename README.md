# Virginia Nonprofit Economic Intelligence Engine

## 1. Project Framing

### **Project Overview**
This project provides an end-to-end data engineering and predictive analytics pipeline designed to quantify the financial footprint, government-grant dependency, and strategic technology asset distribution within Virginia's non-profit sector. 

### **Problem Statement**
Standard administrative classification registries—specifically the IRS National Taxonomy of Exempt Entities (NTEE) codes—frequently misclassify or mask specialized technology research ecosystems, advanced computing labs, and STEM talent pipelines under broad legacy catch-alls (e.g., *Education* or *Social Science Research*). This taxonomic data gap limits the ability of public sector researchers to accurately measure localized technical capacity and regional financial reliance profiles.

### **Data Sources**
* **IRS Business Master File (BMF):** 44,634 active entity records providing baseline administrative metadata for tax-exempt organizations in Virginia.
* **IRS Form 990 Series Extracts (2023):** Consolidated financial returns spanning Form 990 (Core), 990-EZ (Short Form), and 990-PF (Private Foundation) schemas to extract line-by-line financial data.
* **GIS Virginia County Boundaries:** Spatial vector datasets mapping localized latitude/longitude data to Virginia Department of Education (VDOE) administrative planning boundaries.

### **High-Level Objective**
To build a reproducible, automated infrastructure that ingests heterogeneous administrative tax schemas, performs deterministic entity resolution, remediates unclassified sector registries using deep-learning semantic classification, and maps regional financial dependency metrics across administrative planning boundaries.

---

## 2. System Architecture

### **Pipeline Execution Flow**
The pipeline operates as a decoupled four-stage lifecycle. Raw data flows from ingestion through semantic remediation to spatial aggregation and interactive display.

```text
[Raw Ingestion] ──> [Entity Resolution] ──> [Transformer Inference] ──> [Spatial Aggregation]
  - IRS BMF           - EIN Join              - Zero-Shot Classifier   - County Dissolve
  - 990 Core/EZ/PF    - Schema Alignment      - Confidence Filtering   - Multiplier Mapping
```
Module Breakdown
src/data_cleaning.py: Implements core ETL processes, schema harmonization rules, and the natural language processing (NLP) category remediation loop.

src/utils.py: Contains geospatial geometry operations, matrix transformations, regional multiplier mappings, and plotting wrappers.

notebooks/economic_intelligence_pipeline.ipynb: Evaluates the end-to-end execution pipeline, logs runtime diagnostics, and outputs the final statistical evaluations.

Module Breakdown
src/data_cleaning.py: Implements core ETL processes, schema harmonization rules, and the natural language processing (NLP) category remediation loop.

src/utils.py: Contains geospatial geometry operations, matrix transformations, regional multiplier mappings, and plotting wrappers.

notebooks/economic_intelligence_pipeline.ipynb: Evaluates the end-to-end execution pipeline, logs runtime diagnostics, and outputs the final statistical evaluations.

## 3. Pipeline Methodology & Scale

**Data Orchestration & Ingestion**
The transformation engine ingests separate, variable-width IRS extracts, filtering the data to isolate active 501(c)(3) entities registered within Virginia. Financial data across disparate 990, 990-EZ, and 990-PF forms are programmatically mapped and stacked into a unified financial ledger, standardizing reporting schemas into uniform target arrays: Total_Exp_Unified, Total_Revenue_Unified, Revenue_Grants_Unified, and Employee_Count_Unified.

**Entity Resolution**
Data integration is performed via a deterministic, index-based join matching the filtered Business Master File with the consolidated financial extracts utilizing the unique 9-digit Employer Identification Number (EIN). This process accommodates multi-million row arrays and provides disambiguation across entities reporting under multiple legal names or DBA aliases by prioritizing standardized index variables.

**NLP Classification & Semantic Remediation**
To resolve the taxonomic data gap, the pipeline filters out rows where initial NTEE lookups resulted in an unclassified registry status ("Other/Unclassified"), isolating 9,585 unmapped rows across 6,724 unique organizational names.

The pipeline runs a multi-class semantic classification using a pre-trained BART-Large-MNLI transformer model. Unique organizational names are evaluated against a custom, five-vector operational taxonomy:

National Security & Tech Policy

Advanced R&D & Computing

STEM Talent Pipelines

Direct Community Human Services

Healthcare Infrastructure

To eliminate arbitrary imputation noise, a strict 40% confidence score threshold is enforced. Form inputs falling below this boundary are binned neutrally as "Unknown". High-confidence predictions are vectorized and mapped back to the primary database.

**Geospatial Analysis**
Using Shapefile metadata and spatial data frames (GeoPandas), county-level geometries are parsed and merged via a geometric union operation (dissolve) based on VDOE regional bounds. To prevent topological gaps or sliver polygon artifacts during the dissolve phase, a spatial buffer of 0.0005 degrees is programmatically applied to the boundary coordinates prior to geometric intersection. Regional "Fiscal Load" is subsequently calculated as the aggregate ratio of government grant revenue relative to total operating expenditures.

## 4. Key Outputs & Descriptive Findings
Data Coverage & Representation
The deterministic join achieved a 27.4% match rate between the baseline Virginia BMF and the financial extracts, yielding a high-integrity core cohort of 12,226 operating organizations. The remaining unmatched entities represent small-scale or newly formed organizations operating below the mandatory $50,000 threshold required for comprehensive Form 990 filing (Form 990-N "Postcards").

**Macro-Workforce Footprint**
Total Aggregated Salary Footprint: $22.921 Billion

Total Reported Active Workforce (W-2/Personnel): 428,023 Employees

**Proportional Capital Distributions**
Evaluating capital allocation shares across the consolidated macro-pillars demonstrates an asymmetric geographic concentration of technology assets:

| VDOE Region | Tech, R&D & Policy Share | Healthcare Infrastructure Share | Core Human Services Share | Institutional Foundations Share |
| :--- | :---: | :---: | :---: | :---: |
| **Northern Virginia** | **8.2%** | 11.0% | 28.0% | 52.8% |
| **Central Virginia** | **1.6%** | 34.0% | 22.0% | 42.4% |
| **All Other Regions** | **<0.1%** | 50.0% – 56.0% | 20.0% – 30.0% | 14.0% – 20.0% |

**Statistical Synthesis & Correlation**

Cross-examining the NLP-remediated sector classifications against geospatial grant dependency profiles indicates a strong inverse linear relationship. Merging the regional datasets and calculating a Pearson product-moment correlation coefficient yields:$$\text{Pearson Correlation } (r) = -0.718$$This coefficient indicates that a higher proportional concentration of Technology, R&D, and Policy capital within a region strongly co-occurs with a lower reliance on public grant funding to cover baseline operational expenditures. Conversely, regions dominated by clinical healthcare overhead display high baseline grant-reliance multipliers.

## 5. Repository Structure
```text
.
├── data/
│   ├── eo_va.csv                          # Raw IRS Business Master File extract
│   ├── 23eoextract990.csv                  # Raw IRS Form 990 Core financial records
│   ├── 23eoextractez.csv                  # Raw IRS Form 990-EZ financial records
│   ├── 23eoextract990pf.csv                # Raw IRS Form 990-PF financial records
│   └── GIS___Virginia_County_Boundaries.csv # Raw spatial shapefile metadata
├── notebooks/
│   └── economic_intelligence_pipeline.ipynb # End-to-end visualization execution environment
├── results_and_visualizations/
│   ├── final_clean_distribution.png       # Labeled horizontal share chart
│   └── vdoe_impact_dashboard_FINAL.html   # Interactive folium map asset
├── src/
│   ├── __init__.py
│   ├── data_cleaning.py                   # Data transformation, stacking, and NLP functions
│   └── utils.py                           # Spatial unioning, matrix math, and plot styles
└── requirements.txt                       # Project dependency configuration manifest
```
## 6. Execution & Deployment Guide

**Initialize virtual environment**
```text
python3 -m venv venv
source venv/bin/activate
```
**Install required dependencies**
```text
pip install -r requirements.txt
```
