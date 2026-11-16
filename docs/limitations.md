
# FakeDeal Buster – Project Limitations

## 1. Dataset Limitations

- The project uses a synthetic e-commerce product price dataset.
- The dataset represents simulated pricing behaviour and may not fully reflect actual marketplace pricing practices.
- Results obtained from this dataset should not be treated as proof of real-world discount fraud.
- Model performance depends on the quality, completeness, and reliability of the available data.

## 2. Machine Learning Limitations

- Machine learning predictions are estimates and may contain errors.
- Classification performance depends on the validity and distribution of training labels.
- If reliable labels are unavailable, supervised fake-discount classification cannot be considered validated.
- Anomaly detection may identify unusual price patterns, but unusual pricing does not necessarily indicate fraud.

## 3. Historical Data Limitations

- Historical price analysis requires sufficient product-level price records.
- Products with limited historical observations may not support reliable trend analysis.
- Forecasting accuracy may decrease when price patterns change unexpectedly.
- A 14-day forecast will only be provided if sufficient historical data and a suitable forecasting method are available.

## 4. Marketplace Integration Limitations

- The initial version does not guarantee live integration with e-commerce platforms.
- Automatic product data extraction from marketplace URLs may not be supported.
- Product information may need to be entered manually by the user.
- The system does not verify prices directly with marketplace databases.

## 5. Technical Limitations

- The initial application is designed for local development and demonstration.
- Performance may vary depending on system resources and dataset size.
- The application is not designed for large-scale commercial deployment.

## 6. Future Improvements

- Integration with reliable live marketplace data sources.
- Collection of real historical product price records.
- Improved model validation using verified labels.
- More robust price forecasting methods.
- Deployment as a scalable web application.

## 7. Disclaimer

FakeDeal Buster is an academic project intended for educational and analytical purposes. Its results indicate potentially unusual discount patterns and should not be treated as a definitive accusation of fraudulent activity.
