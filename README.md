# Virginia Nonprofit Economic Intelligence Pipeline

## 1. Project Overview

This project implements an end-to-end data engineering and analytics pipeline for integrating IRS nonprofit administrative datasets with geospatial boundary data to produce a unified framework for analyzing organizational financial structure, sector classification, and regional distribution patterns within Virginia.

The system performs:
- Multi-source IRS data ingestion (Form 990, 990-EZ, 990-PF, and Business Master File)
- Deterministic entity resolution across administrative registries
- NLP-based classification of unstructured organizational metadata
- Geospatial aggregation of nonprofit activity by county and region
- Generation of analytical outputs for sectoral and regional analysis

The pipeline is modular, reproducible, and designed for extensibility in policy-relevant data workflows.

---

## 2. Data Sources

### IRS Administrative Datasets
- **IRS Business Master File (BMF):** ~44,600 Virginia nonprofit entities with standardized organizational metadata
- **IRS Form 990 Series (2023):**
  - Form 990 (core filings)
  - Form 990-EZ (short form filings)
  - Form 990-PF (private foundation filings)

These datasets provide financial, organizational, and categorical information at varying levels of granularity.

### Geospatial Data
- **Virginia County Boundary Shapefiles / GIS Metadata**
  - Used for mapping organizational records to administrative regions
  - Enables county-level aggregation and regional comparison

---

## 3. System Architecture

The pipeline is implemented as a modular ETL + inference + spatial analytics system.

```text
[IRS BMF + 990 Extracts]
          |
          v
[ETL & Schema Harmonization]
          |
          v
[Deterministic Entity Resolution (EIN Matching)]
          |
          v
[NLP Classification Layer (Zero-Shot Transformer)]
          |
          v
[Geospatial Aggregation (GeoPandas County Dissolve)]
          |
          v
[Analytical Outputs & Visualizations]

### **Core Modules**

* `src/data_cleaning.py`
  * ETL pipeline for IRS dataset ingestion and schema normalization
  * Financial field standardization across Form 990 variants
  * NLP-based classification utilities
* `src/utils.py`
  * Geospatial processing utilities using GeoPandas
  * Spatial joins and boundary aggregation
  * Visualization helper functions
* `notebooks/economic_intelligence_pipeline.ipynb`
  * End-to-end pipeline execution
  * Exploratory analysis and validation
  * Output generation and visualization

---

## 4. Pipeline Methodology

### **4.1 Data Ingestion & Harmonization**
IRS Form 990 datasets are normalized into a unified schema to standardize financial reporting fields across variants. Unified fields include:
* `Total_Revenue_Unified`
* `Total_Expenditure_Unified`
* `Revenue_Grants_Unified`
* `Employee_Count_Unified`

Records are filtered to active Virginia-based 501(c)(3) organizations.

### **4.2 Entity Resolution**
Entity matching is performed using deterministic joins on Employer Identification Number (EIN) across the IRS Business Master File and Form 990 datasets. This enables:
* Cross-dataset identity alignment
* Deduplication of organizations appearing across multiple filing types
* Consistent entity-level aggregation

### **4.3 NLP Classification Layer**
Unclassified organizational records (`NTEE = "Other/Unclassified"`) are processed using a zero-shot classification model.
* **Model:** `BART-Large-MNLI`
* **Task:** Multi-class classification of organizational descriptions
* **Label space:**
  1. *National Security & Tech Policy*
  2. *Advanced R&D & Computing*
  3. *STEM Talent Pipelines*
  4. *Healthcare Infrastructure*
  5. *Community Human Services*

A confidence threshold of `0.40` is applied:
* $\ge 0.40 \rightarrow$ assigned predicted category
* $< 0.40 \rightarrow$ assigned `"Unclassified"`

This approach prioritizes classification precision and reduces noise in ambiguous cases.

### **4.4 Geospatial Aggregation**
Organizational records are joined with Virginia county boundary geometries using GeoPandas. Key operations include:
* Spatial join of entities to counties
* County aggregation into VDOE regional groupings
* Boundary buffering to reduce geometric artifacts

A regional fiscal metric is computed as:

$$\text{Fiscal Load} = \frac{\text{Grant Revenue}}{\text{Total Operating Expenditures}}$$


## 5. Outputs

### **Dataset Coverage**
* **Total matched entities:** 12,226 organizations
* **Match rate (BMF $\rightarrow$ financial filings):** 27.4%

Unmatched records primarily correspond to:
* Form 990-N (e-Postcard) filers
* Small nonprofits below reporting thresholds
* Newly registered organizations with incomplete filings

### **Aggregate Statistics**
* **Total payroll footprint:** \$22.92B
* **Total reported workforce:** 428,023 employees

### **Geospatial Distribution Summary**

| VDOE Region | Tech / R&D Share | Healthcare Share | Human Services Share | Institutional Base |
| :--- | :---: | :---: | :---: | :---: |
| **Northern Virginia** | 8.2% | 11.0% | 28.0% | 52.8% |
| **Central Virginia** | 1.6% | 34.0% | 22.0% | 42.4% |
| **Other Regions** | <0.1% | 50.0% – 56.0% | 20.0% – 30.0% | 14.0% – 20.0% |

### **Statistical Output**
Pearson correlation between regional technology-sector share and grant dependency:

$$r = -0.718$$

---

## 6. Repository Structure

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
│   ├── data_cleaning.py                   # Data transformation, stacking, and NLP functions
│   └──
```
## 7. Execution Guide

```text
# Initialize virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

## 8. Limitations

**Data Freshness:** IRS Business Master File and Form 990 datasets are updated on a weekly to monthly cadence. This introduces lag between organizational changes and their reflection in the dataset.

**Coverage Constraints:** Form 990-N filers are excluded from most financial fields, resulting in underrepresentation of small and very low-revenue nonprofits.

**Entity Resolution Constraints:** Deterministic EIN-based matching does not capture subsidiaries, DBA variations, or organizations with inconsistent registry naming conventions across datasets.

**NLP Classification Uncertainty:** Zero-shot classification using BART-Large-MNLI is sensitive to label design and domain shift. A fixed confidence threshold (0.40) reduces noise but may exclude valid low-confidence classifications.

**Geospatial Aggregation Assumptions:** County-level aggregation may obscure intra-county variation. Minor boundary buffering used for topology correction may introduce negligible spatial distortion.

**Temporal Scope:** Analysis is based on a single fiscal year (2023) and does not capture longitudinal trends in nonprofit activity or funding distribution.

## 9. Reproducibility
All transformations are deterministic and reproducible. Given identical IRS and GIS inputs, the pipeline produces consistent outputs across runs:

Entity resolution uses fixed EIN-based joins.

NLP classification uses a fixed pretrained checkpoint (BART-Large-MNLI).

Classification thresholds are constant (0.40).

Geospatial aggregation is deterministic given input geometries.
