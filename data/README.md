# Data

All data used by this project is public. No proprietary or employer data is used. This folder follows a one-way flow:

```
raw/  ──►  interim/  ──►  processed/
(immutable)  (cleaned, typed)  (model-ready inputs, calibrated parameters)
         external/  (hand-entered reference tables, each with a citation)
```

| Folder | Contents | Committed to Git? |
|---|---|---|
| `raw/` | Files exactly as downloaded. Never edited by hand. | Small public files yes; large or licence-restricted files no (see `.gitignore`) |
| `interim/` | Cleaned and aligned tables (Parquet) | No, reproducible |
| `processed/` | Model inputs and calibrated parameters | No, reproducible |
| `external/` | Hand-entered tables from PDFs (transition matrices, RBC factors, recovery rates) | Academy/NAIC factor tables yes; S&P tables local only (see `external/README.md`) |

## Sources

| Source | Folder | Access | Licence notes |
|---|---|---|---|
| FRED, Federal Reserve Bank of St. Louis | `raw/fred/` | Free, no login (API key optional) | Public; some series (ICE BofA) carry the provider's terms and limited history on FRED |
| SEC EDGAR XBRL company facts | `raw/sec_edgar/companyfacts/` | Free; requires a User-Agent header | Public domain (US government) |
| SEC EDGAR Form ABS-EE (CMBS asset-level data, EX-102) | `raw/sec_edgar/cmbs_abs_ee/` | Free; requires a User-Agent header | Public domain; files are large, so they are not committed |
| Equity prices (for Merton) | `raw/market/` | Via `yfinance` | Yahoo terms of use; not redistributed |
| Rating-agency default and transition studies (S&P, Fitch, Moody's) | `raw/rating_agency/` | Free with registration (S&P, Fitch); Moody's needs a subscription | Do not commit the PDFs; enter the needed tables into `external/` with a citation |
| NAIC Life RBC instructions; Academy of Actuaries bond-factor proposal | `raw/naic/` | NAIC documents (some paid); Academy proposal free | Do not commit the PDFs; enter factors into `external/` with a citation |
| Fannie Mae Multifamily Loan Performance Data | `raw/fannie_mae_mflpd/` | Free with Fannie Mae registration | Fannie Mae terms; never committed |

**ICE BofA spread series** (FRED `BAML*`) are used for the pricing comparison only. ICE's terms limit redistribution, so the downloaded CSVs are git-ignored; run `python scripts/download_fred.py` to fetch them.

Full file list, URLs and target paths: [`raw/MANIFEST.md`](raw/MANIFEST.md).
Field definitions: [`../docs/data_dictionary.md`](../docs/data_dictionary.md).
