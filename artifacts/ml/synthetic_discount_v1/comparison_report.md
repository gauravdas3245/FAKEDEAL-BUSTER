# Synthetic Discount Scenario Classifier Evaluation

**Evaluation scope: held-out synthetic test data only. These metrics are not real-world fraud accuracy.**

Selected using validation only: `random_forest` at threshold `0.4100`.
Threshold rule: Validation recall maximized subject to false-positive rate <= 0.10 on synthetic genuine examples; PR-AUC and precision break ties.

| Model | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC (AP) | Gini (2*AUC-1) | FP rate on synthetic genuine | Test n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logistic_regression | 0.6800 | 0.8799 | 0.6670 | 0.7588 | 0.8891 | 0.9019 | 0.7782 | 0.0910 | 6000 |
| random_forest | 0.4100 | 0.8954 | 0.7360 | 0.8079 | 0.9160 | 0.9308 | 0.8320 | 0.0860 | 6000 |

Confusion matrices are encoded in `evaluation.json` as TN/FP/FN/TP for synthetic labels 0/1.
Label 1 is the generator-assigned artificially inflated reference-price scenario; label 0 is the generator-assigned genuine-discount scenario.

Preprocessing (median imputation, categorical one-hot encoding, and LR scaling) is fitted inside each model pipeline on the training split only. The validation split selects each decision threshold and the model; the test split is held out until final metrics.

These generated examples and labels do not establish real listing fraud or seller intent. Production Isolation Forest output remains separate. Synthetic classifier output is labelled as scenario resemblance only.
