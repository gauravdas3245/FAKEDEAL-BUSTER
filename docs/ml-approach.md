# FakeDeal Buster – Machine Learning Approach

## 1. Overview

FakeDeal Buster uses data analysis and machine learning techniques to examine e-commerce product pricing information and identify patterns that may indicate potentially misleading artificial discounts.

The machine learning component will be developed using Python, Pandas, NumPy, and Scikit-learn.

## 2. Dataset

**Dataset Name:** E-Commerce Product Price Tracker Dataset

**Source:** Kaggle

**Dataset URL:** https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset

**Dataset Type:** Synthetic e-commerce pricing data.

The dataset contains product pricing observations from multiple e-commerce platforms over time.

The dataset will be inspected before model training to understand its structure, missing values, feature distributions, and available labels.

## 3. Data Inspection

The following checks will be performed:

- Identify available columns and data types.
- Check missing and duplicate records.
- Examine current prices and original prices.
- Inspect discount percentages.
- Analyse historical price observations.
- Check the distribution and validity of available target labels.
- Identify possible data leakage between input features and target labels.

Large dataset files will be processed using memory-efficient techniques rather than loading the entire dataset into memory at once.

## 4. Data Preprocessing

Preprocessing may include:

1. Removing duplicate records where appropriate.
2. Handling missing values.
3. Converting timestamps into a consistent date format.
4. Checking invalid or inconsistent price values.
5. Selecting relevant features.
6. Preparing numerical and categorical variables for model training.

All preprocessing decisions will be documented.

## 5. Feature Engineering

Potential features include:

| Feature | Description |
|---|---|
| Current Price | Present selling price |
| Original Price | Displayed original price |
| Discount Percentage | Calculated discount percentage |
| Price Difference | Difference between original and current price |
| Historical Average Price | Average price over available history |
| Historical Minimum Price | Lowest observed historical price |
| Historical Maximum Price | Highest observed historical price |
| Price Change | Change in price over time |

Only features supported by the available dataset will be used.

## 6. Machine Learning Models

The following models are planned for evaluation:

### 6.1 Logistic Regression

A classification algorithm that may be used as a baseline model if valid classification labels are available.

### 6.2 Random Forest Classifier

An ensemble learning algorithm that may be evaluated for identifying pricing patterns associated with misleading discounts, provided that the target labels are suitable.

### 6.3 Anomaly Detection

If reliable classification labels are unavailable, an anomaly detection approach such as Isolation Forest or an appropriate statistical outlier method may be considered.

Anomaly detection identifies unusual pricing patterns. It does not independently prove that a discount is fraudulent.

## 7. Model Training and Evaluation

The model development process will include:

- Preparing training and testing datasets.
- Avoiding data leakage between training and testing.
- Selecting appropriate features.
- Training candidate models where valid labels exist.
- Comparing model performance.
- Recording evaluation results.

For classification tasks, evaluation may include:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion Matrix

For anomaly detection, the evaluation approach will depend on the availability of reliable reference labels and suitable validation methods.

No model performance score will be reported until actual testing has been completed.

## 8. Model Integration

After validation, the selected model may be saved using Joblib and integrated into the FastAPI backend.

The backend will:

1. Receive product pricing information.
2. Validate the input.
3. Prepare the required features.
4. Load the validated model, if available.
5. Generate an analysis result.
6. Return the result to the React frontend.

## 9. Limitations

- The selected dataset is synthetic and does not represent verified real-world marketplace transactions.
- Model performance depends on the quality and validity of the available labels.
- Unusual pricing patterns do not necessarily indicate fraud.
- Historical analysis requires sufficient product price observations.
- The initial version does not guarantee live marketplace data integration.
- Predictions should be treated as analytical guidance, not definitive proof of a scam.

## 10. Development Responsibility

**Responsible Member:** Gaurav Das – ML Developer

**Supporting Member:** Lakhyajyoti Phukan – Data Preparation Analyst

Data preparation, model development, validation, and integration will be coordinated between the responsible team members.
