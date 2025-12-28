# Macro-Financial Stress Testing Framework (UK)

## Overview

This repository implements a macro-financial stress testing framework that projects bank capital under baseline and adverse macroeconomic scenarios over a 12-quarter horizon.

The framework follows the standard supervisory logic used in central-bank and regulatory stress tests:

- macroeconomic scenarios  
- portfolio-level exposure mapping  
- credit loss projections  
- capital depletion mechanics  
- system-level shortfall assessment  

The model produces **conditional outcomes**, not forecasts. Results answer the question:

> *Given a specified macroeconomic stress path, how does bank capital evolve and where do regulatory constraints bind?*


## Key takeaways

Under a common adverse macroeconomic stress, capital depletion differs materially across banks due to differences in starting capital positions and portfolio composition. Losses are front-loaded and drive binding capital constraints within the stress horizon, resulting in system-wide capital shortfalls under the adverse scenario. Results are robust to baseline assumptions and highlight relative resilience rather than point forecasts.

---

## Motivation

Stress testing is used in financial stability, risk management, and regulatory capital planning to:

- assess capital adequacy under severe macro shocks  
- compare resilience across institutions under a common stress  
- identify timing and magnitude of capital shortfalls  
- evaluate system-wide vulnerability rather than point forecasts  

This project provides a transparent, reproducible implementation of those mechanics using UK data and stylised balance sheets.

---

## Project structure
```text
src/stress_test/
├── balance_sheet.py   # Bank balance sheets and portfolio segmentation
├── scenarios.py       # Baseline and adverse macro scenarios
├── satellite.py       # Macro → credit loss mapping
├── engine.py          # Loss aggregation and CET1 dynamics
├── reporting.py       # Tables and figures
├── data.py            # Processed UK macro data loader
└── config.py          # Constants and naming conventions
```

`scripts/run_stress_test.py` orchestrates the pipeline from the command line.

---

## Balance sheets and portfolio segmentation

Banks are represented with stylised but heterogeneous balance sheets, differing in:

- total exposures and RWAs  
- starting CET1 ratios  
- portfolio composition  

Exposures are segmented into portfolio buckets:

- owner-occupied mortgages  
- consumer unsecured credit  
- SME lending  
- large corporate lending  

Structural overlays (e.g. high-LTV mortgages, export-oriented corporates, energy-intensive firms) modify how macro stress feeds into losses.

Results are reported at the **bank level**, but portfolio segmentation determines the **transmission of macro shocks into losses** and drives cross-bank differences.

Balance sheets are segmented into stylised portfolio buckets (e.g. mortgages, SMEs, corporates) with heterogeneous sensitivities to macroeconomic conditions. While results are reported at the bank level, this segmentation governs how macroeconomic shocks transmit into credit losses and underpins cross-bank differences in stress outcomes. Portfolio-level loss attribution is a natural extension but is not reported here to maintain focus on system-level capital resilience.


### Bank selection

The framework is applied to three UK-headquartered banks selected to represent distinct business models rather than to provide an exhaustive coverage of the banking system. HSBC, Lloyds Banking Group, and Standard Chartered differ materially in portfolio composition, geographic orientation, and sources of credit risk exposure. This allows the stress test to highlight how a common macroeconomic shock transmits differently across institutions with contrasting balance-sheet structures, while keeping the analysis focused and interpretable.

In particular, the selection contrasts a retail-focused lender, a globally diversified universal bank, and a wholesale- and trade-oriented bank, which is sufficient to generate meaningful cross-bank variation without introducing unnecessary complexity.

### Data sources

Bank balance-sheet inputs are constructed using publicly available Pillar 3 disclosures, including reported CET1 capital, risk-weighted assets, and high-level portfolio breakdowns. Where granular exposures are not directly disclosed, stylised allocations are used to map reported totals into portfolio buckets in a manner consistent with each bank’s published business model. Balance-sheet figures are UK-focused and intended to be illustrative rather than supervisory-grade.

Macroeconomic inputs are sourced from official UK statistical releases and central-bank databases:

- UK GDP (quarterly): Office for National Statistics, series IHYQ  
  (ONS UK Economic Accounts)
- Unemployment rate: Office for National Statistics, Labour Market Statistics, series MGSX  
- House prices: Office for National Statistics, UK House Price Index  
- Policy rate and gilt yields: Bank of England Interactive Database  
  (series IUMABEDR, IUMAMNZC)

Raw macroeconomic series are downloaded, cleaned, and transformed to a consistent quarterly frequency prior to scenario construction. The most recent observed data point is used to anchor the baseline scenario.

The data directory is organised as follows:

```text
data/
|-- bank reports/   # Pillar 3 disclosures
|-- raw/            # Raw downloaded macroeconomic data
|-- processed/      # Cleaned and transformed CSV outputs
```

This approach mirrors common practice in exploratory stress testing and policy analysis, combining disclosed regulatory data with stylised assumptions to preserve internal consistency while avoiding the use of confidential supervisory information.

---

## Macro scenarios

### Baseline
- Quarterly frequency  
- 12-quarter horizon  
- Anchored to the most recent observed UK macro data  
- Extended forward as a flat conditional baseline  

The baseline is **not a forecast**. It represents continuation of prevailing macro conditions.

### Adverse
The adverse scenario applies persistent shocks around the baseline:

- GDP growth declines  
- Unemployment rises  
- House prices fall  
- Policy rates and gilt yields decline  

Shocks decay over time, producing front-loaded stress with gradual recovery. The scenario is deterministic and internally consistent.

---

## Satellite models

Satellite models map macro conditions into **credit loss rates** using linear regressions:

$$
\text{LossRate}_t = \alpha + \beta^\top X_t
$$

Loss-rate satellites are used instead of a full PD/LGD decomposition to:

- keep assumptions transparent  
- avoid over-parameterisation  
- reflect common practice in macro stress testing  

Loss histories used for estimation are **synthetic/illustrative** rather than calibrated to confidential supervisory data.

---

## Loss aggregation and capital mechanics

### Credit losses
For each bank and quarter, total losses are computed as the exposure-weighted sum of portfolio losses.

### CET1 evolution
Capital evolves according to:

$$
\text{CET1}_{t+1} = \text{CET1}_t - \text{Losses}_t
$$

Assumptions:
- no pre-impairment operating profits  
- no management actions (dividends, capital issuance, RWA optimisation)  
- no balance-sheet growth  

This isolates the **credit-loss transmission channel**.

### Trough and shortfall
For each bank and scenario:
- the minimum CET1 ratio over the horizon is identified  
- capital shortfall relative to a 7% CET1 hurdle is computed  

This mirrors how regulatory stress tests assess capital adequacy.

---

## Outputs

### Tables (CSV)
- `bank_starting_positions.csv`  
- `system_results.csv` (bank × scenario × quarter panel)  
- `trough_summary.csv` (worst-point CET1 and shortfall)

### Figures (PNG)
- CET1 ratio paths (baseline vs adverse)  
- Total credit loss paths  
- Worst-case CET1 ratios under adverse stress  
- Capital shortfalls at the trough  

Figures emphasise **relative resilience, timing of constraint breaches, and system-level impact**, rather than point predictions.

---

## Interpreting results

The results are intentionally driven by a single transmission channel: macroeconomic stress → credit losses → capital depletion. This isolates differences in balance sheet structure and starting capital positions across banks. Absolute levels of capital are not intended to be forecasts; instead, the analysis focuses on relative resilience, timing of capital depletion, and system-wide capital shortfalls under a common stress.

- Linear CET1 paths reflect the absence of income and management actions  
- Flat baseline losses reflect stable macro conditions  
- Declining adverse losses reflect shock persistence and recovery  
- Cross-bank differences arise from portfolio composition and starting capital  

Negative CET1 values indicate insolvency under pure loss absorption and are allowed by design.

---

## Limitations

- No income channel  
- No provisioning dynamics  
- No balance-sheet growth  
- No management actions  
- Satellite models not calibrated to real bank loss data  
- Portfolio-level loss attribution not reported  

These simplifications are deliberate and documented.

---

## Running the model

Install dependencies:
```bash
pip install -e .
```
Run full stress test:
```bash
python3 scripts/run_stress_test.py --run-stress --write-results-csv --plot-figures
```
Outputs are written to outputs/tables/ and outputs/figures/.


## Next steps (out of scope)

The current framework deliberately focuses on the credit-loss transmission channel. The following extensions are natural but excluded to maintain model transparency and scope discipline:

- explicit income and provisioning dynamics (e.g. PPOP, staged loss recognition)
- portfolio-level loss attribution by exposure bucket
- calibration of satellite models to real bank loss data
- alternative stress narratives and scenario severities

These extensions can be incorporated without altering the core balance-sheet, scenario, or capital mechanics.