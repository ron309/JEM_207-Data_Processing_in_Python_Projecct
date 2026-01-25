# Global Natural Gas Trade Analysis (2010–2024)
## Transport, Prices, Network Structure, Trade evolution, seasonal and structural Regime Change

## Project Overview

This project analyzes global natural gas trade from 2010 to 2024 using UN Comtrade data. The objective is to understand how global gas trade changed, it's structure, prices, transport modes, network connectivity, and seasonality evolved over time, and how these dynamics were fundamentally altered by the 2022 energy crisis.

The analysis explicitly distinguishes between:

- **Liquefied Natural Gas (LNG)** — HS 271111
- **Gaseous (Pipeline) Natural Gas** — HS 271121

The project integrates two analysis components:

- Trade structure and evolution, seasonality, and regime analysis
- Transport modes, prices, and network topology analysis

Together, these perspectives assess whether post-2022 developments represent a temporary shock or a structural regime shift in global natural gas trade.

---
## How to run

### 1. Set up the environment
Install dependencies:

-- pip install -r requirements.txt

### 2. Run the full analysis (recommended)

The full analysis is executed via main.py.

-- Loads the processed dataset
-- Runs all analysis bundles
-- Stores all tables and figures once

Run:

-- python main.py

Outputs are saved to:

-- data/processed/figures/
-- data/processed/tables/

No API key is required for this step.

### 3. Download and rebuild the dataset (iF REQUIRED)

To reproduce the processed dataset from raw UN Comtrade data, run:

-- python -m src.get_data

This step:

- Downloads raw global trade data (2010–2025) from UN Comtrade
- Requires a valid UN Comtrade API key
- Takes approximately 60–70 minutes
- Writes the cleaned dataset to:

- data/processed/comtrade_natural_gas_clean.csv

After this step, rerun the analysis using:

-- python main.py

If the command above does not work, use:

-- python src/get_data.py

Notes

- Raw UN Comtrade files are not stored in the repository due to size constraints
- Full reproducibility is preserved via the ingestion script and analysis pipeline

## Results and Outputs Guide

Running `main.py` generates a complete and reproducible set of tables and figures.
Each output corresponds to a specific analytical question addressed in the project.

The results are organized into the following thematic groups:

### 1. Global Trade Evolution
Files prefixed with:
- `global_trade_value_*.png`
- `annual_trade_global_by_product.csv`

These outputs show long-term import and export dynamics for LNG and pipeline gas,
highlighting trend growth and the structural break observed after 2022.

---

### 2. Continental and Geographic Reallocation
Files prefixed with:
- `continental_imports_*.png`
- `continental_exports_*.png`
- `continent_shares_*.png`
- `annual_continent_trade.csv`

These results analyze how global trade flows are redistributed across continents,
with particular focus on Europe’s post-2022 LNG reallocation.

---

### 3. Country-Level Dominance
Files prefixed with:
- `top_countries_import_export_*.png`
- `same_countries_import_export_*.png`
- `annual_country_trade.csv`

These figures identify dominant importing and exporting countries and track
how their relative positions changed before and after the energy crisis.

---

### 4. Seasonality and Structural Change
Files prefixed with:
- `seasonality_heatmap_*.png`
- `seasonal_profile_*.png`
- `winter_vs_nonwinter_*.png`
- `monthly_imports_*.csv`

These outputs examine whether historical seasonal patterns persist or
break down after 2022, distinguishing LNG flexibility from pipeline rigidity.

---

### 5. Regime and Scenario Analysis
Files prefixed with:
- `regime_levels_*.png`
- `baseline_seasonal_profile_*.csv`
- `winter_stress_*.png`
- `diversification_*.png`

These results simulate stress and diversification scenarios under different
economic regimes to assess system resilience and adaptability.

## Core Questions

- How did global natural gas trade evolve before and after 2022?
- How do LNG and pipeline gas differ in transport modes, prices, and network structure?
- How concentrated and dependent are global gas import relationships?
- Did seasonality and trade timing change structurally after the crisis?
- Can pre-crisis seasonal models still explain post-crisis behavior?
- Did the energy crisis alter globalization, efficiency, and centrality in gas trade networks?

---

## Data Description and Preparation


### Raw Data Handling

The original raw data is retrieved directly from the UN Comtrade API using an authenticated API key.
Due to the size of the dataset (2000–2025 global trade) and long download times (≈60–70 minutes),
the raw API output is not stored in the repository.

Instead, the project includes:
- the complete data ingestion script (`src/get_data.py`), and
- a cleaned and processed dataset (`data/processed/comtrade_natural_gas_clean.csv`) used for analysis.

This approach preserves full reproducibility while avoiding unnecessary storage of large files.

### Data Source
- UN Comtrade
- Time period: 2010–2024

### Products Analyzed
- LNG (HS 271111)
- Gaseous natural gas (HS 271121)

### Key Variables
- Trade value (USD)
- Country Specific Codes
- Transport mode
- Trade partner
- Reporter country
- Network links (bilateral trade flows)

### Data Cleaning and Validation

Extensive preprocessing was required:

- Removal of aggregated reporters (`isAggregate = True`)
- Removal of “World” partner entries
- Retention of standard Import and Export flows only
- Validation of consistent reporting behavior after 2010
- Diagnostic assessment of quantity data (`netWgt`):
  - Pipeline quantities are unreliable at a global level
  - LNG quantities are usable only at aggregated reporter–year level

**Conclusion:**  
All structural, network, and regime analysis relies primarily on trade values, not physical quantities. Additionlly, more emphasis was given on imports 

---

## Part 1 — Transport, Prices, and Network Analysis  

### Transport Mode Structure

**Key Findings**
- Most trade is reported under “Total Modes of Transport” or “Other”.
- For gaseous natural gas:
  - Pipelines dominate
  - Road and land-with-sea combinations appear as secondary modes
- For LNG:
  - Sea transport is the dominant mode
  - Pipelines and air transport appear as marginal or emergency channels

---

### Transport Modes and Price Formation

**Key Findings**
- Pipelines, rail, road, and sea transport exhibit the lowest average prices.
- Land and air routes are the most expensive.
- LNG prices are structurally higher than pipeline gas prices.
- The 2022 crisis is clearly visible:
  - Pipeline gas availability collapses
  - Sea-borne LNG prices spike sharply
  - Price dispersion widens substantially
- Post-2022 prices stabilize at higher levels.

---

### Network Analysis of Global Gas Trade

#### Network Topology and Connectivity
- LNG networks show higher clustering than pipeline gas.
- LNG clustering declines temporarily during 2020–2021.
- LNG consistently exhibits higher network density.
- Weighted metrics reveal persistent concentration:
  - More links exist, but trade volumes remain unevenly distributed.

#### Efficiency and Centrality
- Network efficiency gains are temporary.
- Log-normalized efficiency improves in the long run.
- Post-2022 efficiency declines for pipeline gas.
- No single dominant hub exists:
  - Canada ranks high for pipeline gas
  - The United States ranks high for LNG

---

## Part 2 — Trade Structure, Seasonality, and Regime Analysis  


### Global Trade Evolution

**Key Findings**
- A clear structural break occurs in 2022.
- The crisis is price-driven, not volume-driven.
- LNG acts as a global balancing mechanism.
- Pipeline gas remains regionally rigid.

---

### Geographic Reallocation

**Key Findings**
- Europe sharply increases LNG imports post-2022.
- Asia temporarily reduces LNG share.
- Pipeline gas remains region-locked.

---

### Country Dominance and Import Dependency

**Key Findings**
- Strong importer–exporter asymmetry exists.
- Europe emerges as a major LNG importer.
- Export dominance remains concentrated:
  - United States
  - Australia
  - Nigeria
- Re-exports are negligible.
- Import dominance remains concentrated:
  - China
  - Japan 
  - Republic of Korea

---

**Key Findings**
- LNG import concentration declines after 2022.
- Pipeline gas concentration remains high.

---

### Seasonality Analysis

**Key Findings**
- LNG seasonality flattens after 2022.
- Pipeline gas remains strongly winter-driven.
- Seasonal profiles change structurally post-crisis.

---

### Regime and Scenario Analysis

**Defined Regimes**
- Pre-COVID: 2010–2019
- COVID: 2020–2021
- Crisis: 2022–2024

**Scenarios**
- Baseline
- Winter stress
- Diversification

**Key Findings**
- LNG responds strongly to stress and diversification.
- Pipeline gas shows limited adaptability.
- LNG is the primary resilience mechanism.

---

### Diagnostic Time-Series Validation

A seasonal naive benchmark is used:
- Prediction equals the same month in the previous year

**Results**
- Model performs well pre-2020.
- Performance collapses after 2022.
- Confirms structural regime change.

---

## Key Conclusions

- 2022 marks a structural break in global gas trade.
- LNG becomes the primary adjustment channel.
- Pipeline gas remains rigid and concentrated.
- Globalization increases topologically, not in weighted terms.
- Historical seasonal models fail post-crisis.

---

## Tools and Technologies

- Python
- pandas, numpy
- matplotlib, seaborn
- networkx

No machine learning models were used. Emphasis was given more on interpretation and economic reasoning, along with focus on data handling and processing in Python.

---

## Limitations and Future Work

### Limitations
- Trade values reflect prices more than volumes.
- Quantity data quality varies across products.

### Potential Extensions
- Formal structural break tests
- Scenario-based forecasting
- Continent-level network analysis

---

## Authors and Contributions

- **Raunak Handa**  
  Trade structure and evolution, seasonality, regime analysis, scenarios, diagnostic time-series

- **Oleksandr Hulianskyi**  
  Transport modes, price analysis, network topology, network metrics
