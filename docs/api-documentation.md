# FakeDeal Buster – API Documentation

## 1. Overview

This document describes the communication between the React frontend and the FastAPI backend of FakeDeal Buster.

The backend receives product pricing information, validates the input, performs the available analysis, and returns the result in JSON format.

## 2. Base URL

During local development:

```text
http://localhost:8000
```

The actual port and API URL may be updated during integration.

## 3. API Endpoints

### 3.1 Health Check

**Endpoint:** `/health`

**Method:** `GET`

**Purpose:** Checks whether the backend server is running.

**Expected Response:**

```json
{
  "status": "healthy",
  "message": "FakeDeal Buster API is running"
}
```

### 3.2 Product Discount Analysis

**Endpoint:** `/api/analyze`

**Method:** `POST`

**Purpose:** Receives product pricing information and returns an analysis of the advertised discount.

**Request Body:**

```json
{
  "product_name": "Example Smartphone",
  "current_price": 14999,
  "original_price": 19999,
  "historical_prices": []
}
```

**Input Parameters:**

| Parameter | Type | Description |
|---|---|---|
| product_name | String | Name of the product |
| current_price | Number | Current selling price |
| original_price | Number | Displayed original price |
| historical_prices | Array | Optional historical price observations |

**Expected Response Structure:**

```json
{
  "product_name": "Example Smartphone",
  "current_price": 14999,
  "original_price": 19999,
  "discount_percentage": 25.0,
  "verdict": "Potential Fake Discount",
  "confidence": null,
  "analysis_message": "Analysis result will be generated using available pricing information."
}
```

The response is a proposed structure. Actual fields and values will be finalized after backend and machine learning integration.

## 4. Input Validation

The backend should validate the following:

- Product name must not be empty.
- Current price must be greater than zero.
- Original price must be greater than zero.
- Current price should not exceed original price for a standard advertised discount.
- Historical price data must follow the expected format.

Invalid requests should return an appropriate HTTP error response.

## 5. HTTP Status Codes

| Status Code | Meaning |
|---|---|
| 200 | Request processed successfully |
| 400 | Invalid input data |
| 422 | Request validation failed |
| 500 | Internal server error |

## 6. Frontend–Backend Communication

1. The user enters product pricing information in the React frontend.
2. The frontend sends a POST request to the FastAPI backend.
3. The backend validates the submitted information.
4. The analysis component processes the available pricing data.
5. The backend returns the result in JSON format.
6. The frontend displays the analysis to the user.

## 7. Important Notes

- The API will initially operate in a local development environment.
- No live marketplace integration is guaranteed in the initial version.
- Historical price analysis depends on the availability of sufficient historical observations.
- Machine learning predictions will be used only after the dataset labels and model have been validated.
- The final API contract may be updated during integration.
