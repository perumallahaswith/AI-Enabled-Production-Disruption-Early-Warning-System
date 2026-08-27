# Machine Learning Model Registry

This directory contains versioned artifacts for the multi-model semiconductor early warning engine.

## Subdirectories

- `trained/`: Serialized models (Isolation Forest, Random Forest, HistGradientBoosting, Logistic Regression Baseline).
- `preprocessing/`: Serialized feature transformers, standard scalers, variance threshold selectors, and imputation pipelines.
- `metadata/`: JSON metadata capturing training timestamps, cross-validation metrics, PR-AUC, ROC-AUC, F1 scores, and version tags.
