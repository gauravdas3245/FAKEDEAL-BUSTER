
# FakeDeal Buster — System Workflow

## 1. User Workflow

1. The user opens the FakeDeal Buster web application.
2. The user enters the available product information.
3. The user submits the information for analysis.
4. The frontend sends the request to the backend API.
5. The backend validates the submitted information.
6. The backend performs the required data processing.
7. The machine learning component analyses the available pricing features, if a validated model is available.
8. The backend prepares the analysis response.
9. The frontend displays the result to the user.

## 2. Data Processing Workflow

### Step 1: Data Collection

The project uses the approved E-Commerce Product Price Tracker Dataset from Kaggle.

The dataset contains product pricing information collected across multiple e-commerce platforms in a synthetic environment.

### Step 2: Data Inspection

- Examine dataset structure and columns.
- Check missing values and duplicate records.
- Inspect price and discount fields.
- Verify the meaning and distribution of available labels.

### Step 3: Data Cleaning

- Handle missing or invalid values.
- Remove duplicate records where appropriate.
- Check inconsistent pricing information.
- Prepare relevant columns for analysis.

### Step 4: Feature Engineering

Potential features include:

- Current product price.
- Original product price.
- Discount percentage.
- Product category.
- Platform.
- Historical price statistics, where sufficient records are available.

Final feature selection will depend on dataset inspection and model requirements.

### Step 5: Model Development

Candidate machine learning algorithms:

- Logistic Regression.
- Random Forest Classifier.

Model training and supervised evaluation will proceed only if the dataset labels are verified as suitable for the intended classification task.

### Step 6: Model Evaluation

Evaluate the model using appropriate metrics such as:

- Accuracy.
- Precision.
- Recall.
- F1-score.
- Confusion matrix.

Evaluation will use an appropriate validation strategy and avoid data leakage.

## 3. Backend Workflow

1. Receive the frontend request.
2. Validate input fields.
3. Prepare the required features.
4. Load the trained model when available.
5. Generate the prediction or analytical result.
6. Return a structured JSON response.

## 4. Frontend Workflow

1. Display the product input form.
2. Accept product pricing details.
3. Send the request to the backend.
4. Handle loading and error states.
5. Display the analysis result.
6. Show relevant pricing information in a readable format.

## 5. Expected Result

The application will provide an analytical assessment of the submitted product pricing information.

Possible result categories:

- **Verified Real Deal:** The available analysis supports a genuine discount assessment.
- **Potential Fake Discount:** The available analysis indicates a potentially misleading discount pattern.

These labels are analytical outputs, not proof of fraud. Their use depends on successful validation of the underlying data and model.

## 6. Workflow Limitations

- Results depend on the quality and availability of product information.
- Historical analysis requires sufficient price records.
- Supervised classification requires valid labels.
- The initial version does not guarantee live marketplace price verification.
