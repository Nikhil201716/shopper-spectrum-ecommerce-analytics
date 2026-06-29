# Preprocessing and Data-Quality Log

I designed this preprocessing layer around one rule: **I do not delete the commercial record to make the dataset look cleaner.** The raw CSV stays unchanged, and the processed dataset retains all **541,909** rows. I add fields that explain whether and how each row should participate in a specific analysis.

## 1. Schema validation

I verify that all eight required source fields are present: `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, and `Country`.

**Reason:** a silent schema change can shift or corrupt every downstream metric.  
**Benefit:** the build fails early and clearly instead of producing a polished but wrong dashboard.

## 2. Row-level audit key

I create a sequential `RowID` while keeping the original columns unchanged.

**Reason:** source invoice numbers are not unique at line level.  
**Benefit:** every processed row can be traced back to one source line.

## 3. Invoice date parsing

I preserve `InvoiceDate` and add parsed `InvoiceTimestamp`, `PurchaseDate`, `YearMonth`, `Weekday`, and `Hour`. No dates are missing or invalid in this file.

**Reason:** time analysis needs a true datetime type, while the source text remains useful for audit.  
**Benefit:** monthly, weekday, hourly, cohort, and recency calculations are reproducible.

## 4. Missing CustomerID — 135,080 rows (24.93%)

I retain the original null. In the derived `CustomerKey`, I assign `GUEST-<InvoiceNo>` so guest invoice activity stays grouped. These rows remain in revenue, market, product, basket, and data-quality analysis, but `IsRFMEligible=False`.

**Why I do not statistically impute an ID:** a median, mode, or nearest customer would falsely join purchases to a real person.  
**Business benefit:** I retain guest demand without contaminating customer lifetime behaviour, segmentation, or personalised outreach.

## 5. Missing Description — 1,454 rows (0.27%)

I retain the null and create `DescriptionClean = UNKNOWN PRODUCT [StockCode]`.

**Reason:** the stock code is the strongest auditable identifier still available.  
**Business benefit:** revenue, quantity, and operational exceptions remain reconciled while the unresolved product is visible for master-data repair.

## 6. Exact duplicates — 10,147 duplicate-member rows (1.87%)

I retain all copies, set `IsDuplicate`, calculate `DuplicateRank`, and mark only rank 1 as `IsCanonicalRecord=True`. Gross revenue, return value, and model eligibility use the canonical record.

**Reason:** deleting duplicates erases the evidence that an ingestion or export issue occurred. Counting every copy inflates sales.  
**Business benefit:** KPIs are not duplicated, but the data-engineering problem remains measurable and auditable.

## 7. Cancellations and negative quantities

- Cancelled invoices: **9,288** rows.
- Negative-quantity / return lines: **10,624** rows.

I preserve them and classify them as `Return / Cancellation`. Their absolute commercial value contributes to `ReturnValue`; they do not contribute to `GrossRevenue`.

**Reason:** a return is not meaningless bad data—it is a customer-experience and margin event.  
**Business benefit:** I can quantify product return risk, market return exposure, and net revenue.

## 8. Zero and negative prices

- Zero-price lines: **2,515**.
- Negative-price adjustments: **2**.

I keep and classify them separately. They do not enter completed positive-sale demand.

**Reason:** zero-price activity may be a legitimate sample, promotion, replacement, or price-master error; negative prices may be accounting adjustments.  
**Business benefit:** authorised activity can be tagged, while leakage and control failures remain visible.

## 9. Merchandise versus operational charges

I add `IsMerchandise=False` for descriptions containing postage, carriage, bank charges, Amazon fees, manual adjustments, commissions, bad-debt adjustments, DOTCOM charges, or samples.

**Reason:** fees can create high revenue or return values but are not products a customer should be recommended.  
**Business benefit:** product winner, portfolio, and recommender outputs describe sellable merchandise without losing financial reconciliation.

## 10. Revenue measures

- `ObservedLineValue = Quantity × UnitPrice` keeps the signed source economics.
- `GrossRevenue` counts canonical completed positive sales.
- `ReturnValue` records the absolute canonical reversal value.
- `NetRevenue = GrossRevenue − ReturnValue`.

The full snapshot measures approximately **£10.64M gross**, **£0.89M returns**, and **£9.75M net**.

**Reason:** one ambiguous “sales” measure cannot represent both demand and reversals.  
**Business benefit:** growth, customer value, return risk, and accounting impact can be discussed without denominator confusion.

## 11. RFM eligibility and feature engineering

I use identified customers with canonical, dated, positive-price, positive-quantity, non-cancelled sales. I calculate:

- **RecencyDays:** one day after the latest dataset date minus the customer's latest purchase date. Lower means more recent.
- **FrequencyOrders:** distinct completed invoices.
- **MonetaryValue:** canonical gross revenue.
- Supporting fields: first/last purchase, units, active months, AOV, tenure, and cadence.

I apply `log1p` to reduce extreme skew, standardise the three RFM features, evaluate K=2–8, and fit K-Means with K=4. K=4 has silhouette **0.334**; I select it for four operationally distinct treatments and clearly disclose that K=2 has stronger pure separation.

## 12. Product recommendation eligibility

I use canonical completed sales with an identified customer, a known description, and `IsMerchandise=True`. Products need at least five distinct customers. I aggregate customer-product quantities, apply `log1p`, build a sparse matrix, and use cosine nearest neighbours to return five products.

**Reason:** collaborative filtering needs real shared-customer behaviour; single-customer and fee items create unstable or nonsensical neighbours.  
**Business benefit:** recommendations have both a similarity score and shared-customer support for responsible testing.

## 13. Output validation

The build asserts:

- Input rows = processed rows = **541,909**.
- `SourceRowPreserved=True` for every row.
- Original columns remain available.
- Gross revenue minus return value reconciles to net revenue.
- Four named segments exist.
- Every recommendation-ready product has five ranked neighbours.
- All 21 SQL result tables exist.

