# Raw data manifest

Every raw file, where it comes from and where it goes. Status is updated as files are downloaded.

| Status | Meaning |
|---|---|
| ⬜ | Not yet downloaded |
| ✅ | Downloaded; checksum recorded in `checksums.csv` |
| ✋ | Manual download (login or licence); see instructions |

## 1. FRED series (automated)

Download URL pattern: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>`. Save as `raw/fred/<folder>/<SERIES_ID>.csv`.

| Status | Series ID | Folder | Description | Frequency | Used in |
|---|---|---|---|---|---|
| ✅ | [`CORBLACBS`](https://fred.stlouisfed.org/series/CORBLACBS) | `fred/credit_cycle/` | Charge-off rate on business loans, all commercial banks | Quarterly | NB03 |
| ✅ | [`DRBLACBS`](https://fred.stlouisfed.org/series/DRBLACBS) | `fred/credit_cycle/` | Delinquency rate on business loans, all commercial banks | Quarterly | NB03 |
| ✅ | [`CORCACBS`](https://fred.stlouisfed.org/series/CORCACBS) | `fred/credit_cycle/` | Charge-off rate on credit card loans, all commercial banks | Quarterly | NB03 |
| ✅ | [`USREC`](https://fred.stlouisfed.org/series/USREC) | `fred/macro/` | NBER-based recession indicator | Monthly | NB03, NB10 |
| ✅ | [`UNRATE`](https://fred.stlouisfed.org/series/UNRATE) | `fred/macro/` | Unemployment rate | Monthly | NB03 |
| ✅ | [`GDPC1`](https://fred.stlouisfed.org/series/GDPC1) | `fred/macro/` | Real gross domestic product | Quarterly | NB03 |
| ✅ | [`NFCI`](https://fred.stlouisfed.org/series/NFCI) | `fred/macro/` | Chicago Fed National Financial Conditions Index | Weekly | NB03 |
| ✅ | [`DGS1`](https://fred.stlouisfed.org/series/DGS1) | `fred/rates/` | 1-year Treasury constant maturity | Daily | NB02 |
| ✅ | [`DGS5`](https://fred.stlouisfed.org/series/DGS5) | `fred/rates/` | 5-year Treasury constant maturity | Daily | NB09 |
| ✅ | [`DGS10`](https://fred.stlouisfed.org/series/DGS10) | `fred/rates/` | 10-year Treasury constant maturity | Daily | NB09 |
| ✅ | [`T10Y2Y`](https://fred.stlouisfed.org/series/T10Y2Y) | `fred/rates/` | 10-year minus 2-year Treasury spread | Daily | NB03 |
| ✅ | [`AAA`](https://fred.stlouisfed.org/series/AAA) | `fred/spreads/` | Moody's seasoned Aaa corporate bond yield (from 1919) | Monthly | NB03, NB09 |
| ✅ | [`BAA`](https://fred.stlouisfed.org/series/BAA) | `fred/spreads/` | Moody's seasoned Baa corporate bond yield (from 1919) | Monthly | NB03, NB09 |
| ✅ | [`AAA10Y`](https://fred.stlouisfed.org/series/AAA10Y) | `fred/spreads/` | Moody's Aaa yield minus 10-year Treasury | Daily | NB09 |
| ✅ | [`BAA10Y`](https://fred.stlouisfed.org/series/BAA10Y) | `fred/spreads/` | Moody's Baa yield minus 10-year Treasury | Daily | NB03, NB09 |
| ✅ | [`BAMLC0A0CM`](https://fred.stlouisfed.org/series/BAMLC0A0CM) | `fred/spreads/` | ICE BofA US Corporate Index OAS | Daily | NB09 |
| ✅ | [`BAMLC0A1CAAA`](https://fred.stlouisfed.org/series/BAMLC0A1CAAA) | `fred/spreads/` | ICE BofA AAA US Corporate Index OAS | Daily | NB09 |
| ✅ | [`BAMLC0A2CAA`](https://fred.stlouisfed.org/series/BAMLC0A2CAA) | `fred/spreads/` | ICE BofA AA US Corporate Index OAS | Daily | NB09 |
| ✅ | [`BAMLC0A3CA`](https://fred.stlouisfed.org/series/BAMLC0A3CA) | `fred/spreads/` | ICE BofA Single-A US Corporate Index OAS | Daily | NB09 |
| ✅ | [`BAMLC0A4CBBB`](https://fred.stlouisfed.org/series/BAMLC0A4CBBB) | `fred/spreads/` | ICE BofA BBB US Corporate Index OAS | Daily | NB09 |
| ✅ | [`BAMLH0A0HYM2`](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) | `fred/spreads/` | ICE BofA US High Yield Index OAS | Daily | NB03, NB09 |
| ✅ | [`BAMLH0A1HYBB`](https://fred.stlouisfed.org/series/BAMLH0A1HYBB) | `fred/spreads/` | ICE BofA BB US High Yield Index OAS | Daily | NB09 |
| ✅ | [`BAMLH0A2HYB`](https://fred.stlouisfed.org/series/BAMLH0A2HYB) | `fred/spreads/` | ICE BofA Single-B US High Yield Index OAS | Daily | NB09 |
| ✅ | [`BAMLH0A3HYC`](https://fred.stlouisfed.org/series/BAMLH0A3HYC) | `fred/spreads/` | ICE BofA CCC & Lower US High Yield Index OAS | Daily | NB09 |
| ✅ | [`DRCRELEXFACBS`](https://fred.stlouisfed.org/series/DRCRELEXFACBS) | `fred/commercial_real_estate/` | Delinquency rate on CRE loans (excl. farmland), commercial banks | Quarterly | NB07 |
| ✅ | [`CORCREXFACBS`](https://fred.stlouisfed.org/series/CORCREXFACBS) | `fred/commercial_real_estate/` | Charge-off rate on CRE loans (excl. farmland), commercial banks | Quarterly | NB07 |
| ✅ | [`COMREPUSQ159N`](https://fred.stlouisfed.org/series/COMREPUSQ159N) | `fred/commercial_real_estate/` | Commercial real estate prices for United States (BIS) | Quarterly | NB07 |

Note: on FRED, ICE BofA index series show a limited recent history only. Long-history spread proxies are Moody's `AAA` and `BAA` (from 1919).

## 2. SEC EDGAR company facts (automated)

✅ Ticker-to-CIK map: `https://www.sec.gov/files/company_tickers.json` → `raw/sec_edgar/company_tickers.json`.
Company facts: `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` (10-digit, zero-padded CIK) → `raw/sec_edgar/companyfacts/<TICKER>.json`.
Requests must send a `User-Agent` of the form `Name email@example.com` (set in `.env`). Keep to fewer than 10 requests per second.

Starter universe for NB02 (rating shown is indicative only; confirm before use). Downloaded 10 Oct 2026.

Note: XOM's current CIK (2115436, ExxonMobil Holdings Corp) only has filings from 2024. The legacy Exxon Mobil Corporation filings (CIK 34088, 2006–2026) are saved as `XOM_CIK0000034088.json`; use that file for Merton.

| Status | Ticker | Sector | Indicative rating |
|---|---|---|---|
| ✅ | AAPL | Technology | AA+ |
| ✅ | MSFT | Technology | AAA |
| ✅ | JNJ | Health care | AAA |
| ✅ | XOM | Energy | AA- |
| ✅ | T | Telecom | BBB |
| ✅ | F | Autos | BBB- |
| ✅ | BA | Aerospace | BBB- |
| ✅ | OXY | Energy | BBB- |
| ✅ | KHC | Consumer staples | BBB |
| ✅ | HCA | Health care | BBB- |
| ✅ | CCL | Leisure | BB+ |
| ✅ | AAL | Airlines | B+ |
| ✅ | M | Retail | BB+ |
| ✅ | NFLX | Media | A |
| ✅ | DAL | Airlines | BBB- |

## 3. SEC EDGAR CMBS asset-level data, Form ABS-EE (semi-automated)

| Status | Item | Instructions | Target |
|---|---|---|---|
| ⬜ | CMBS deal list | EDGAR full-text search, form type `ABS-EE`, query "commercial mortgage": `https://efts.sec.gov/LATEST/search-index?forms=ABS-EE&q=%22commercial%20mortgage%22` | `raw/sec_edgar/cmbs_abs_ee/deal_index.csv` |
| ⬜ | Loan-level files (EX-102 XML) for 3–5 conduit CMBS deals | From each ABS-EE filing index, download the EX-102 exhibit | `raw/sec_edgar/cmbs_abs_ee/<deal>/<yyyymm>_ex102.xml` |

## 4. Rating-agency studies (manual ✋)

| Status | Document | Where | Tables to extract into `external/` |
|---|---|---|---|
| ✋ | S&P *Default, Transition, and Recovery: Annual Global Corporate Default and Rating Transition Study* (latest year) | spglobal.com/ratings (free registration) | One-year average transition matrix (with NR); annual default rates by rating since 1981; average cumulative default rates (1–15 years) |
| ✋ | Fitch *Global Corporate Finance Transition and Default Study* (latest year) | fitchratings.com (free registration) | Cross-check of the S&P matrix and cumulative default rates |
| ✋ | Moody's *Annual Default Study* (optional) | moodys.com (subscription) | Recovery rates by seniority; issuer-weighted default rates |

## 5. Statutory capital (manual ✋)

| Status | Document | Where | Tables to extract into `external/` |
|---|---|---|---|
| ✋ | American Academy of Actuaries, life RBC bond factor proposal to the NAIC (2021-10-L) | content.naic.org | Pre-tax C-1 factors for NAIC designations 1.A–6 |
| ✋ | NAIC Life Risk-Based Capital forecasting and instructions (current year) | naic.org | Commercial mortgage categories CM1–CM7: DSC and LTV thresholds and factors |
| ✋ | NAIC RBC Investment Risk and Analysis (E) Working Group, CLO factor materials (2026) | content.naic.org | CLO tranche factors and thickness rule |

## 6. Fannie Mae Multifamily Loan Performance Data (manual ✋)

| Status | Item | Where | Target |
|---|---|---|---|
| ✋ | Multifamily Loan Performance Data (MFLPD) | capitalmarkets.fanniemae.com, Data Dynamics (free registration) | `raw/fannie_mae_mflpd/` (never committed) |

## 7. Market data (automated, not redistributed)

| Status | Item | How | Target |
|---|---|---|---|
| ✅ | Daily OHLC, adjusted close and volume for the 15 NB02 names, 2005-01-03 to 2026-10-09 (or from listing date: KHC 2015, HCA 2011, AAL 2005-09, DAL 2007-05) | Yahoo Finance chart API (same source as `yfinance`) | `raw/market/prices/<TICKER>.csv`; dividends and splits in `raw/market/events/<TICKER>.csv` (not committed) |
| ⬜ | Shares outstanding history | SEC company facts (`dei:EntityCommonStockSharesOutstanding`) | derived in `interim/` |
