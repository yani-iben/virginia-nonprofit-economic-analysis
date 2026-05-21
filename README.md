# Virginia Nonprofit Economic Intelligence Engine

## **Project Overview**
This repository houses an end-to-end data engineering and predictive policy pipeline designed to quantify the fiscal footprint, government-grant dependency, and strategic technology assets of Virginia's nonprofit sector. By merging administrative tax registries with advanced natural language processing (NLP), this project identifies regional economic vulnerabilities and maps single-points-of-failure within the Commonwealth's innovation and national security corridors.

### **Core Data Insights**
* **The "Two Virginias" Bifurcation:** A powerful inverse relationship ($\text{Pearson } r \approx -0.72$) exists between civic grant dependency and technology incubation capacity. Only Northern and Central Virginia possess statistically significant strategic technology and policy footprints.
* **The Clinical Overhead Bottleneck:** In rural and frontline care corridors, up to **80% of regional capital** is entirely consumed by baseline healthcare infrastructure and immediate human services, leaving a zero-margin ceiling for localized technical talent incubation or industrial asset growth.

---

## **Technical Architecture**

The project is built on a highly modular, decoupled object-oriented architecture split into distinct ingestion, predictive remediation, and geospatial analysis phases.

```text
├── data/                                 # Raw IRS extracts and GIS county boundary shapefiles
├── results_and_visualizations/          # High-fidelity visual distribution and interactive assets
├── src/
│   ├── __init__.py
│   ├── data_cleaning.py                  # Core ETL, schema harmonization, and entity resolution
│   └── utils.py                         # Matrix aggregation, GIS unioning, and plot styles
└── notebooks/
    └── economic_intelligence_pipeline.ipynb # Primary executive analysis environment
```
## **Pipeline Flow & Engineering Mechanics**
Data Orchestration & Harmonization: The core ETL engine (data_cleaning.py) ingests and normalizes disparate data fields across heterogeneous tax schemas (IRS Forms 990, 990-EZ, and 990-PF) into a single unified financial ledger.

Deterministic Entity Resolution: 
Performs high-integrity string mapping and programmatic disambiguation over 44k+ rows in the IRS Business Masterfile (BMF) using standardized Employer Identification Numbers (EIN) to safely verify major institutional networks.

Zero-Shot Semantic Inference: 
Isolates administrative data gaps ("Other/Unclassified" registries). It deploys a pre-trained BART-Large-MNLI transformer model to dynamically map organization legal names into five strategy-aligned operational vectors. It applies a strict 40% confidence threshold safeguard to explicitly bin ambiguous entities as "Unclassified Administrative Gaps" to completely eliminate imputation bias.

Geospatial Intelligence & Disaggregation: Unions localized polygon structures via a geometric county dissolution buffer (utils.py) to map county-level data into regional administrative boundaries, calculating localized "Fiscal Load" (grant-to-expenditure ratios).

## **Key Analytical Takeaways**
**The Macro Economic Divide**
The visualization architecture surfaces an undeniable structural concentration of innovation capital. Northern Virginia stands completely alone as a hyper-concentrated innovation engine, allocating 8.2% of its entire regional non-profit footprint toward strategic Technology, R&D, and Policy tracks. Central Virginia represents the only secondary tech-policy cluster at 1.6%, anchored by premier higher-education research networks.

**The Grant Dependency Trap**
The remaining seven regions function as frontline care corridors, where up to 56% of capital is permanently locked up in legacy medical infrastructure overhead. The strong negative correlation ($r \approx -0.72$) proves that regions lacking technological asset allocation are the most deeply dependent on public grants to sustain daily operations.
**Industrial Policy Insight**
This intelligence proves that standalone technology grants issued to rural zones are insufficient for long-term tech incubation. Because their localized economies are completely strained by the frontline care bottleneck, any incoming capital is immediately absorbed by baseline survival needs. State planners must stabilize baseline regional infrastructure before true technological asset diversification can take root.