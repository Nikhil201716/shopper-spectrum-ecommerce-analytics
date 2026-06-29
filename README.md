# 🛒 Shopper Spectrum

### Customer Segmentation and Product Recommendations in E-Commerce

I am **Nikhil Sinha**, and I built Shopper Spectrum as an end-to-end retail decision system using Python, SQL, machine learning, data analysis, and Streamlit. I did not want this project to become a gallery of disconnected charts. Every analysis answers a commercial question, shows the underlying table, states the finding, and recommends a practical action.

The supplied data contains **541,909 transaction lines from 1 December 2022 to 9 December 2023**. My processed layer retains **100% of those rows**. Instead of deleting missing IDs, cancellations, returns, duplicate records, zero-price lines, or adjustments, I preserve them and add transparent quality flags and analytical eligibility rules.

## What the application includes

- A polished portfolio command centre with revenue, returns, orders, customer value, and product-risk views.
- **21 real-world business problem statements**, each with a dynamic Plotly visual, result table, measured finding, business action, and reproducible SQL.
- A raw-versus-cleaned data explorer with downloadable source and full cleaned datasets.
- A complete preprocessing audit explaining what I did, why I did it, and the business benefit.
- RFM customer segmentation using log transformation, standardisation, K-Means, inertia, silhouette scores, and business-profile labels.
- Real-time RFM segment prediction from Recency, Frequency, and Monetary inputs.
- Item-based collaborative filtering with five product recommendations, cosine similarity, and shared-customer support.
- A read-only SQL Studio backed by SQLite summary tables.
- A reproducible analysis notebook, automated tests, GitHub Actions, VS Code tasks, and an optional local GitHub auto-sync watcher.

## Key measured findings

- The preserved ledger produces **£10.64M gross revenue**, **£0.89M return value**, and **£9.75M net revenue**.
- The **United Kingdom** contributes approximately **£9.00M** in gross revenue, showing material home-market concentration.
- **November 2023** is the strongest month at approximately **£1.50M** in gross revenue.
- The top 20% of identified customers contribute approximately **74.8%** of identified-customer revenue.
- **Champions** represent 16.5% of eligible customers but approximately 64.9% of identified-customer value.
- **At Risk** is the largest customer-count segment (1,584 customers) and represents approximately **£557K** in historical value.
- The four-cluster model has a silhouette score of **0.334**. K=2 separates more cleanly, but K=4 creates four commercially distinct CRM treatments; I document that trade-off in the app.

## Project structure

```text
shopper-spectrum/
├── app.py                         # Streamlit application
├── src/                           # Data, modeling, UI, and 21 business views
├── scripts/                       # Build, notebook, launch, and Git sync automation
├── sql/business_queries.sql       # 21 reproducible business SQL statements
├── data/raw/online_retail.csv     # Unchanged source of truth
├── data/processed/                # Cleaned data, RFM, neighbors, SQL results, SQLite
├── artifacts/                     # Saved scaler, K-Means model, cluster label map
├── notebooks/                     # Reproducible Python analysis notebook
├── tests/                         # Row, model, SQL, and Streamlit tests
├── docs/source/                   # Supplied PDF brief and Word notes
├── .vscode/                       # VS Code launch/build/auto-sync tasks
└── .github/workflows/             # GitHub Actions quality checks
```

## Run in VS Code on Windows

Open this project folder in VS Code, then run the following in the integrated PowerShell terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

The processed data and model artifacts are already included, so the app can start immediately after dependency installation.

If the raw CSV changes, rebuild every downstream artifact before launching:

```powershell
python scripts\build_artifacts.py
python scripts\generate_notebook.py
pytest
streamlit run app.py
```

The same commands are available from **Terminal → Run Task** in VS Code.

## My no-deletion preprocessing contract

| Source condition | What I do | Business reason and benefit |
|---|---|---|
| Missing CustomerID | Keep the null and create `GUEST-<InvoiceNo>` only in the derived `CustomerKey`. Exclude guests from identified-customer RFM. | Guest demand and revenue remain visible without inventing a customer history. |
| Missing Description | Keep the null and create `UNKNOWN PRODUCT [StockCode]` in `DescriptionClean`. | Revenue reconciles and the stock code stays traceable. |
| Exact duplicates | Keep every copy, assign `DuplicateRank`, and give analytical revenue weight only to rank 1. | Auditability is preserved without double-counting KPIs. |
| Cancelled invoices / negative quantities | Keep and classify as returns or cancellations. | Reversals become product, service, and margin signals. |
| Zero or negative prices | Keep and classify as free items or price adjustments. | Promotions and price-master leakage can be governed. |
| Service charges | Keep the row and revenue, but set `IsMerchandise=False`. | Postage, fees, and commissions do not masquerade as sellable product winners. |
| Completed positive sales | Mark canonical, dated, positive-price, positive-quantity, non-cancelled lines as `IsAnalysisReadySale`. | Demand and gross-sales metrics use a stable, explainable cohort. |

The complete treatment log is in [PREPROCESSING_LOG.md](PREPROCESSING_LOG.md).

## The 21 business problems

1. Retail health pulse
2. Market concentration
3. Seasonality and momentum
4. Weekday demand
5. Trading-hour intensity
6. Product winners
7. Product portfolio roles
8. Product return exposure
9. Market return exposure
10. Basket economics
11. Customer revenue concentration
12. New versus repeat growth
13. RFM segment portfolio
14. Segment behaviour
15. At-risk recovery
16. Purchase cadence
17. Cohort retention
18. Price-band productivity
19. Zero-price governance
20. Data-quality exposure
21. Product affinity recommendations

See [PROJECT_REPORT.md](PROJECT_REPORT.md) for the question, measured finding, and business response for every problem.

## SQL design

During `build_artifacts.py`, I load the full preserved-row analytical layer into an in-memory SQLite database and execute all 21 queries in `sql/business_queries.sql`. I save each full-data result as CSV and into `shopper_spectrum_summary.db`. The Streamlit SQL Studio displays the production query and result, then allows additional read-only `SELECT`/`WITH` queries against the compact summary database.

## GitHub auto-sync from VS Code

The project includes `scripts/watch_and_sync.ps1` and a VS Code task named **Watch & sync to GitHub**. When VS Code opens the trusted folder, the task watches project files, waits for changes to settle, then stages, commits, and pushes to the current remote branch.

Important operational truth: GitHub cannot detect an unsaved or purely local change by itself. Automatic push works **only while the watcher is running**, the files are saved, Git has an authenticated `origin`, and the machine has network access. VS Code may ask once whether automatic tasks are allowed for the folder.

Run it manually if needed:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\watch_and_sync.ps1
```

## Analytical boundaries

- The app responds to filters and user inputs in real time, but the supplied dataset is a historical snapshot—not a live commerce feed.
- I display monetary values as pounds because this is a UK-centred retail dataset; the raw file does not include an explicit currency-code column.
- Product similarity measures shared purchasing behaviour. It should be A/B tested before claiming causal sales uplift.
- RFM uses identified customers with completed canonical sales. Guest transactions remain in sales analytics but do not enter customer segmentation.
- Extreme wholesale-style orders can materially affect product statistics, which is why the app exposes support counts, distributions, and return risk rather than only rankings.

## Author

**Nikhil Sinha**  
Shopper Spectrum — Customer Segmentation and Product Recommendations in E-Commerce

