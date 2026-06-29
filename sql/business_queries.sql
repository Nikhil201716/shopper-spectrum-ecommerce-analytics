-- Shopper Spectrum: 21 decision-oriented SQL analyses
-- Generated against the full preserved-row transactions table during the build.

-- [PROBLEM 01] Retail health pulse
SELECT
    COUNT(*) AS PreservedRows,
    COUNT(DISTINCT InvoiceNo) AS Invoices,
    COUNT(DISTINCT CASE WHEN CustomerID IS NOT NULL THEN CustomerKey END) AS IdentifiedCustomers,
    ROUND(SUM(GrossRevenue), 2) AS GrossRevenue,
    ROUND(SUM(ReturnValue), 2) AS ReturnValue,
    ROUND(SUM(NetRevenue), 2) AS NetRevenue,
    ROUND(SUM(GrossRevenue) / NULLIF(COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN InvoiceNo END), 0), 2) AS AverageOrderValue,
    ROUND(100.0 * SUM(ReturnValue) / NULLIF(SUM(GrossRevenue), 0), 2) AS ReturnValueRatePct
FROM transactions;

-- [PROBLEM 02] Market concentration
SELECT
    CountryClean,
    COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN InvoiceNo END) AS Orders,
    COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN CustomerKey END) AS Customers,
    ROUND(SUM(GrossRevenue), 2) AS Revenue,
    ROUND(SUM(ReturnValue), 2) AS ReturnValue,
    ROUND(100.0 * SUM(GrossRevenue) / NULLIF(SUM(SUM(GrossRevenue)) OVER (), 0), 2) AS RevenueSharePct
FROM transactions
GROUP BY CountryClean
ORDER BY Revenue DESC;

-- [PROBLEM 03] Monthly revenue trend
SELECT
    YearMonth,
    COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN InvoiceNo END) AS Orders,
    ROUND(SUM(GrossRevenue), 2) AS Revenue,
    ROUND(SUM(ReturnValue), 2) AS ReturnValue,
    ROUND(SUM(NetRevenue), 2) AS NetRevenue
FROM transactions
WHERE YearMonth IS NOT NULL
GROUP BY YearMonth
ORDER BY Revenue DESC;

-- [PROBLEM 04] Weekday demand pattern
SELECT
    Weekday,
    COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN InvoiceNo END) AS Orders,
    ROUND(SUM(GrossRevenue), 2) AS Revenue,
    ROUND(SUM(GrossRevenue) / NULLIF(COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN InvoiceNo END), 0), 2) AS AverageOrderValue
FROM transactions
WHERE Weekday IS NOT NULL
GROUP BY Weekday
ORDER BY Revenue DESC;

-- [PROBLEM 05] Trading-hour intensity
SELECT
    Hour,
    COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN InvoiceNo END) AS Orders,
    ROUND(SUM(GrossRevenue), 2) AS Revenue,
    ROUND(SUM(GrossRevenue) / NULLIF(COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN InvoiceNo END), 0), 2) AS RevenuePerOrder
FROM transactions
WHERE Hour IS NOT NULL
GROUP BY Hour
ORDER BY Revenue DESC;

-- [PROBLEM 06] Product winners
SELECT
    DescriptionClean,
    SUM(CASE WHEN IsAnalysisReadySale = 1 THEN Quantity ELSE 0 END) AS UnitsSold,
    COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN InvoiceNo END) AS Orders,
    COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN CustomerKey END) AS Customers,
    ROUND(SUM(GrossRevenue), 2) AS Revenue
FROM transactions
WHERE IsMerchandise = 1
GROUP BY DescriptionClean
HAVING UnitsSold > 0 AND Orders >= 10 AND Customers >= 5
ORDER BY Revenue DESC
LIMIT 25;

-- [PROBLEM 07] Product velocity-value matrix
SELECT
    DescriptionClean,
    SUM(CASE WHEN IsAnalysisReadySale = 1 THEN Quantity ELSE 0 END) AS UnitsSold,
    ROUND(SUM(GrossRevenue), 2) AS Revenue,
    COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN CustomerKey END) AS Customers,
    ROUND(SUM(GrossRevenue) / NULLIF(SUM(CASE WHEN IsAnalysisReadySale = 1 THEN Quantity ELSE 0 END), 0), 2) AS RevenuePerUnit
FROM transactions
WHERE IsMerchandise = 1
GROUP BY DescriptionClean
HAVING UnitsSold >= 20 AND Customers >= 5
ORDER BY Revenue DESC
LIMIT 200;

-- [PROBLEM 08] Product return exposure
SELECT
    DescriptionClean,
    ROUND(SUM(GrossRevenue), 2) AS GrossRevenue,
    ROUND(SUM(ReturnValue), 2) AS ReturnValue,
    ROUND(100.0 * SUM(ReturnValue) / NULLIF(SUM(GrossRevenue), 0), 2) AS ReturnValueRatePct,
    COUNT(DISTINCT CASE WHEN ReturnValue > 0 THEN InvoiceNo END) AS ReturnInvoices
FROM transactions
WHERE IsMerchandise = 1
GROUP BY DescriptionClean
HAVING SUM(GrossRevenue) >= 1000 AND SUM(ReturnValue) > 0
ORDER BY ReturnValue DESC
LIMIT 30;

-- [PROBLEM 09] Market return exposure
SELECT
    CountryClean,
    ROUND(SUM(GrossRevenue), 2) AS GrossRevenue,
    ROUND(SUM(ReturnValue), 2) AS ReturnValue,
    ROUND(100.0 * SUM(ReturnValue) / NULLIF(SUM(GrossRevenue), 0), 2) AS ReturnValueRatePct,
    COUNT(DISTINCT CASE WHEN ReturnValue > 0 THEN InvoiceNo END) AS ReturnInvoices
FROM transactions
GROUP BY CountryClean
HAVING SUM(GrossRevenue) >= 5000
ORDER BY ReturnValue DESC;

-- [PROBLEM 10] Basket economics
WITH baskets AS (
    SELECT
        InvoiceNo,
        CustomerKey,
        SUM(CASE WHEN IsAnalysisReadySale = 1 THEN Quantity ELSE 0 END) AS BasketUnits,
        SUM(GrossRevenue) AS BasketValue,
        COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN DescriptionClean END) AS DistinctProducts
    FROM transactions
    GROUP BY InvoiceNo, CustomerKey
    HAVING BasketValue > 0
)
SELECT
    CASE
        WHEN BasketValue < 25 THEN 'Under £25'
        WHEN BasketValue < 75 THEN '£25-£75'
        WHEN BasketValue < 150 THEN '£75-£150'
        WHEN BasketValue < 500 THEN '£150-£500'
        ELSE '£500+'
    END AS BasketBand,
    COUNT(*) AS Orders,
    ROUND(AVG(BasketValue), 2) AS AverageBasketValue,
    ROUND(AVG(BasketUnits), 2) AS AverageUnits,
    ROUND(AVG(DistinctProducts), 2) AS AverageDistinctProducts
FROM baskets
GROUP BY BasketBand
ORDER BY AverageBasketValue;

-- [PROBLEM 11] Customer revenue concentration
WITH customer_value AS (
    SELECT CustomerKey, SUM(GrossRevenue) AS Revenue
    FROM transactions
    WHERE CustomerID IS NOT NULL
    GROUP BY CustomerKey
), ranked AS (
    SELECT
        CustomerKey,
        Revenue,
        ROW_NUMBER() OVER (ORDER BY Revenue DESC) AS RevenueRank,
        COUNT(*) OVER () AS CustomerCount,
        SUM(Revenue) OVER () AS TotalRevenue
    FROM customer_value
)
SELECT
    ROUND(100.0 * SUM(CASE WHEN RevenueRank <= CAST(CustomerCount * 0.2 AS INTEGER) THEN Revenue ELSE 0 END) / NULLIF(MAX(TotalRevenue), 0), 2) AS Top20RevenueSharePct,
    MAX(CustomerCount) AS IdentifiedCustomers,
    ROUND(MAX(TotalRevenue), 2) AS IdentifiedCustomerRevenue
FROM ranked;

-- [PROBLEM 12] New versus repeat customer growth
WITH customer_month AS (
    SELECT CustomerKey, MIN(YearMonth) AS FirstMonth
    FROM transactions
    WHERE CustomerID IS NOT NULL AND IsAnalysisReadySale = 1
    GROUP BY CustomerKey
)
SELECT
    t.YearMonth,
    ROUND(SUM(CASE WHEN t.YearMonth = c.FirstMonth THEN t.GrossRevenue ELSE 0 END), 2) AS NewCustomerRevenue,
    ROUND(SUM(CASE WHEN t.YearMonth > c.FirstMonth THEN t.GrossRevenue ELSE 0 END), 2) AS RepeatCustomerRevenue,
    COUNT(DISTINCT CASE WHEN t.YearMonth = c.FirstMonth THEN t.CustomerKey END) AS NewCustomers,
    COUNT(DISTINCT CASE WHEN t.YearMonth > c.FirstMonth THEN t.CustomerKey END) AS RepeatCustomers
FROM transactions t
JOIN customer_month c ON t.CustomerKey = c.CustomerKey
WHERE t.IsAnalysisReadySale = 1
GROUP BY t.YearMonth
ORDER BY t.YearMonth;

-- [PROBLEM 13] RFM segment portfolio
SELECT
    Segment,
    COUNT(*) AS Customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS CustomerSharePct,
    ROUND(SUM(MonetaryValue), 2) AS HistoricalRevenue,
    ROUND(100.0 * SUM(MonetaryValue) / SUM(SUM(MonetaryValue)) OVER (), 2) AS RevenueSharePct
FROM rfm_customers
GROUP BY Segment
ORDER BY HistoricalRevenue DESC;

-- [PROBLEM 14] Segment behaviour profiles
SELECT
    Segment,
    COUNT(*) AS Customers,
    ROUND(AVG(RecencyDays), 1) AS AvgRecencyDays,
    ROUND(AVG(FrequencyOrders), 1) AS AvgOrders,
    ROUND(AVG(MonetaryValue), 2) AS AvgCustomerValue,
    ROUND(AVG(AverageOrderValue), 2) AS AvgOrderValue,
    ROUND(AVG(PurchaseCadenceDays), 1) AS AvgCadenceDays
FROM rfm_customers
GROUP BY Segment
ORDER BY AvgCustomerValue DESC;

-- [PROBLEM 15] At-risk recovery opportunity
SELECT
    Segment,
    COUNT(*) AS Customers,
    ROUND(SUM(MonetaryValue), 2) AS HistoricalValueAtRisk,
    ROUND(AVG(MonetaryValue), 2) AS AvgValuePerCustomer,
    ROUND(AVG(RecencyDays), 1) AS AvgDaysSincePurchase
FROM rfm_customers
WHERE Segment = 'At Risk'
GROUP BY Segment;

-- [PROBLEM 16] Purchase cadence distribution
SELECT
    CASE
        WHEN PurchaseCadenceDays IS NULL THEN 'Single purchase'
        WHEN PurchaseCadenceDays <= 7 THEN 'Weekly'
        WHEN PurchaseCadenceDays <= 30 THEN 'Monthly'
        WHEN PurchaseCadenceDays <= 90 THEN 'Quarterly'
        ELSE 'Long cycle'
    END AS CadenceBand,
    COUNT(*) AS Customers,
    ROUND(AVG(MonetaryValue), 2) AS AvgCustomerValue,
    ROUND(AVG(RecencyDays), 1) AS AvgRecencyDays
FROM rfm_customers
GROUP BY CadenceBand
ORDER BY Customers DESC;

-- [PROBLEM 17] Cohort retention
WITH activity AS (
    SELECT DISTINCT CustomerKey, YearMonth
    FROM transactions
    WHERE CustomerID IS NOT NULL AND IsAnalysisReadySale = 1
), cohorts AS (
    SELECT CustomerKey, MIN(YearMonth) AS CohortMonth
    FROM activity
    GROUP BY CustomerKey
), indexed AS (
    SELECT
        a.CustomerKey,
        c.CohortMonth,
        a.YearMonth,
        (CAST(substr(a.YearMonth, 1, 4) AS INTEGER) - CAST(substr(c.CohortMonth, 1, 4) AS INTEGER)) * 12
        + (CAST(substr(a.YearMonth, 6, 2) AS INTEGER) - CAST(substr(c.CohortMonth, 6, 2) AS INTEGER)) AS CohortIndex
    FROM activity a
    JOIN cohorts c ON a.CustomerKey = c.CustomerKey
), sizes AS (
    SELECT CohortMonth, COUNT(DISTINCT CustomerKey) AS CohortSize
    FROM indexed
    WHERE CohortIndex = 0
    GROUP BY CohortMonth
)
SELECT
    i.CohortMonth,
    i.CohortIndex,
    COUNT(DISTINCT i.CustomerKey) AS ActiveCustomers,
    s.CohortSize,
    ROUND(100.0 * COUNT(DISTINCT i.CustomerKey) / s.CohortSize, 2) AS RetentionPct
FROM indexed i
JOIN sizes s ON i.CohortMonth = s.CohortMonth
WHERE i.CohortIndex BETWEEN 0 AND 12
GROUP BY i.CohortMonth, i.CohortIndex, s.CohortSize
ORDER BY i.CohortMonth, i.CohortIndex;

-- [PROBLEM 18] Price-band productivity
SELECT
    PriceBand,
    SUM(CASE WHEN IsAnalysisReadySale = 1 THEN Quantity ELSE 0 END) AS Units,
    COUNT(DISTINCT CASE WHEN IsAnalysisReadySale = 1 THEN InvoiceNo END) AS Orders,
    ROUND(SUM(GrossRevenue), 2) AS Revenue,
    ROUND(100.0 * SUM(GrossRevenue) / NULLIF(SUM(SUM(GrossRevenue)) OVER (), 0), 2) AS RevenueSharePct
FROM transactions
WHERE PriceBand IS NOT NULL
GROUP BY PriceBand
ORDER BY Revenue DESC;

-- [PROBLEM 19] Zero-price governance
SELECT
    COUNT(*) AS Lines,
    SUM(CASE WHEN IsCanonicalRecord = 1 THEN Quantity ELSE 0 END) AS Units,
    COUNT(DISTINCT InvoiceNo) AS Invoices,
    COUNT(DISTINCT DescriptionClean) AS Products,
    COUNT(DISTINCT CustomerKey) AS CustomerKeys
FROM transactions
WHERE UnitPrice = 0;

-- [PROBLEM 20] Data-quality exposure
SELECT 'Missing CustomerID' AS Issue, SUM(IsMissingCustomerID) AS Rows FROM transactions
UNION ALL
SELECT 'Missing Description', SUM(IsMissingDescription) FROM transactions
UNION ALL
SELECT 'Exact duplicate membership', SUM(IsDuplicate) FROM transactions
UNION ALL
SELECT 'Returns / cancellations', SUM(CASE WHEN TransactionStatus = 'Return / Cancellation' THEN 1 ELSE 0 END) FROM transactions
UNION ALL
SELECT 'Zero-price lines', SUM(CASE WHEN UnitPrice = 0 THEN 1 ELSE 0 END) FROM transactions
ORDER BY Rows DESC;

-- [PROBLEM 21] Product affinity recommendations
SELECT
    Product,
    Rank,
    RecommendedProduct,
    ROUND(Similarity, 4) AS Similarity,
    SharedCustomers
FROM product_neighbors
ORDER BY Product, Rank;
