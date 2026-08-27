# Semiconductor Data Storage Repository

This directory holds the raw, processed, and synthetic semiconductor datasets used across the Early Warning & Decision Support Platform.

## Directory Structure

- `raw/`: Unmodified incoming datasets (e.g., UCI SECOM dataset, WM-811K wafer maps, tool telemetry).
- `processed/`: Validated, imputed, scaled, and feature-selected datasets ready for training and runtime scoring.
- `synthetic/`: Controlled industrial simulation scenarios (tool degradation, process drift, material shortages, environmental excursions).

## Data Integrity Rules

1. **No Data Leakage**: All scalers, imputers, and feature selectors must be fitted exclusively on training splits.
2. **Transparent Labeling**: Datasets are tagged as `REAL DATA`, `PUBLIC DATASET`, `SYNTHETIC DATA`, or `SIMULATED`.
