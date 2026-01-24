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

## Core Questions

- How did global natural gas trade evolve before and after 2022?
- How do LNG and pipeline gas differ in transport modes, prices, and network structure?
- How concentrated and dependent are global gas import relationships?
- Did seasonality and trade timing change structurally after the crisis?
- Can pre-crisis seasonal models still explain post-crisis behavior?
- Did the energy crisis alter globalization, efficiency, and centrality in gas trade networks?

---

## Data Description and Preparation

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
- Export dominance remains concentrated:
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
