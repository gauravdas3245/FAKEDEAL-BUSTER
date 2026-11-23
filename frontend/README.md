# FakeDeal Buster frontend

React/Vite interface with bounded product search, dataset identity confirmation, price entry, optional seller/listing metadata, Isolation Forest anomaly and FDI results, a separately labelled synthetic-scenario classifier card, actual observed price history, and conditional forecast where supported.

## User flow and data limits

The form asks for product name, platform, category, original price, and current price. Product ID stays internal. Supported filters are loaded without product records; autocomplete calls the bounded catalogue search endpoint for actual dataset identities, with compatible category/platform filters and title/brand matching. Multiple matches require explicit selection. No match returns `PRODUCT_NOT_FOUND`.

An Amazon product URL can confirm identity only when its ASIN exactly matches an actual dataset ASIN and agrees with the selected name, category, and Amazon platform. Other HTTP(S) URLs are stored only as optional request metadata and do not verify identity. Seller name and seller rating are optional validated metadata; ratings must be between 1 and 5 and neither field is used by the model.

Ordinary analysis uses the actual current timestamp. Historical analysis is an advanced option where the user may select a past time. The available observations end on 2024-12-30; current-date analysis therefore reports insufficient history. The UI shows only actual price observations and never fills gaps. A 14-day baseline forecast is conditional on 180 consecutive observed days and a chronological backtest; see `../docs/forecasting-methodology.md`. FDI is unavailable when central inference lacks required signals. The supervised classifier card describes generated-scenario resemblance only, not real-world fraud or probability; see `../docs/synthetic-discount-experiment.md`. Isolation Forest output indicates an unusual price pattern, not fraud proof. Seller fields are user-provided and unverified.

## API setup

Copy `.env.example` to `.env.local` if configuration is needed. By default, Vite proxies `/api` to `http://127.0.0.1:8000`; set `VITE_DEV_API_TARGET` to change this. For a separately hosted API, set `VITE_API_BASE_URL` to its origin and configure CORS at deployment.

## Run

Start the API from the repository root:

```powershell
& 'C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe' -m uvicorn app.main:app --app-dir backend --reload
```

Then start Vite:

```powershell
Set-Location frontend
npm.cmd run dev
```

## Tests and build

```powershell
npm.cmd test
npm.cmd run build
```

The API response and product inspection behavior are documented in `../backend/API_CONTRACT.md`.
