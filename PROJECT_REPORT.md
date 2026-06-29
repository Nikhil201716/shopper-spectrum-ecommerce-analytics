# Shopper Spectrum — Business Findings and Solutions

I am **Nikhil Sinha**, and this report explains how I translate the supplied transaction history into 21 practical e-commerce decisions. The findings below use the full data snapshot; the Streamlit app can re-slice most views by date, country, and customer segment.

## 1. Retail health pulse

**Problem:** Is revenue growth healthy after returns?  
**Finding:** £10.64M gross becomes £9.75M net after £0.89M in return exposure.  
**My solution:** I would manage gross revenue, return value, net revenue, AOV, customers, and orders as one scorecard. A campaign that grows sales but grows return value faster is not healthy growth.

## 2. Market concentration

**Problem:** Which countries deserve protection, expansion, or remediation?  
**Finding:** The United Kingdom contributes approximately £9.00M and dominates the portfolio.  
**My solution:** I would protect the home-market operating model while ranking international markets on revenue scale, repeat behaviour, and return quality—not revenue alone.

## 3. Seasonality and momentum

**Problem:** When should inventory and campaign bets be placed?  
**Finding:** November 2023 is the strongest observed month at approximately £1.50M gross revenue.  
**My solution:** I would move stock, staffing, creative, and CRM preparation ahead by at least one replenishment lead time.

## 4. Weekday demand

**Problem:** Which days carry the strongest buying intent?  
**Finding:** Friday is the highest-revenue weekday in the complete snapshot.  
**My solution:** I would concentrate conversion campaigns and warehouse capacity around the strongest days, then test incremental uplift against quieter-day controls.

## 5. Trading-hour intensity

**Problem:** When should campaigns and support teams be live?  
**Finding:** 10:00 is the peak revenue hour in the complete transaction history.  
**My solution:** I would align flash offers, live chat, operational monitoring, and paid-media bid adjustments with the high-intent window.

## 6. Product winners

**Problem:** Which sellable products create both demand and revenue?  
**Finding:** `REGENCY CAKESTAND 3 TIER` leads supported merchandise revenue at approximately £174K.  
**My solution:** I exclude fees and require customer/order support, then use winner products as inventory priorities, acquisition creative, and cross-sell anchors.

## 7. Product portfolio roles

**Problem:** Which items are scalable stars, traffic drivers, premium earners, or long tail?  
**Finding:** Revenue alone hides whether performance comes from units, price, customer reach, or a single extreme basket.  
**My solution:** I use a velocity-value bubble chart and create separate reorder, merchandising, and promotional rules by quadrant.

## 8. Product return exposure

**Problem:** Which products create the largest material return exposure?  
**Finding:** `PAPER CRAFT, LITTLE BIRDIE` shows a full large-order reversal, while several supported products combine meaningful revenue and recurring returns.  
**My solution:** I surface both absolute return value and rate, then audit listing accuracy, packaging, supplier quality, and customer expectation setting.

## 9. Market return exposure

**Problem:** Where are returns a material market problem?  
**Finding:** The United Kingdom has the largest absolute exposure because it also has the largest revenue base.  
**My solution:** I compare both return value and return rate, then investigate carriers, promises, duties, and localisation in material outlier markets.

## 10. Basket economics

**Problem:** What does a normal order look like, and where are the extremes?  
**Finding:** The basket distribution is right-skewed, so averages are pulled by large wholesale-style orders.  
**My solution:** I use the median and percentile bands for everyday targets and route extreme baskets to separate fraud, fulfilment, and account-service controls.

## 11. Customer revenue concentration

**Problem:** How dependent is revenue on the top customer tier?  
**Finding:** The top 20% of identified customers contribute approximately 74.8% of identified-customer revenue.  
**My solution:** I would build tiered retention but also nurture the next-value band to reduce concentration risk.

## 12. New versus repeat growth

**Problem:** Is acquisition producing retained growth?  
**Finding:** Monthly first-month versus later-month revenue separates acquisition spikes from durable relationships.  
**My solution:** I would evaluate campaigns on second-purchase conversion and repeat revenue, not only first-order ROAS.

## 13. RFM segment portfolio

**Problem:** How is customer value distributed across actionable segments?  
**Finding:** Champions are 717 customers (16.5%) but contribute approximately 64.9% of identified value. At Risk is the largest count group with 1,584 customers.  
**My solution:** I assign four distinct treatments: protect Champions, grow Loyal customers, accelerate Occasional customers, and prioritise high-value At-Risk recovery.

## 14. Segment behaviour

**Problem:** How do the segments actually behave?  
**Finding:** Champions average about 12.5 recency days, 13.7 orders, and £8.0K value; At Risk averages about 187 recency days, 1.3 orders, and £352 value.  
**My solution:** I design CRM from these behavioural profiles rather than arbitrary cluster IDs.

## 15. At-risk recovery

**Problem:** How much historical value is exposed to churn?  
**Finding:** The At-Risk segment represents approximately £557K of historical value.  
**My solution:** I rank win-back by customer value and affinity, then escalate incentives only when lower-cost reminders fail.

## 16. Purchase cadence

**Problem:** When is a customer genuinely late for a purchase?  
**Finding:** Customer cycles range from weekly to long-cycle, while single-purchase customers have no observed cadence.  
**My solution:** I trigger outreach relative to the customer's own expected cadence instead of using one blanket inactivity rule.

## 17. Cohort retention

**Problem:** Are later acquisition cohorts becoming more loyal?  
**Finding:** The heatmap exposes retention by months since first purchase and prevents newer cohorts from being unfairly compared with older ones.  
**My solution:** I investigate offer, channel, onboarding, or product-mix changes behind cohort deterioration.

## 18. Price-band productivity

**Problem:** Which price bands drive units, revenue, and order reach?  
**Finding:** Unit volume and revenue contribution do not peak in the same bands.  
**My solution:** I balance accessible conversion products with premium attach opportunities and manage margin targets by price band.

## 19. Zero-price governance

**Problem:** How much free-item or price-master activity needs control?  
**Finding:** The ledger contains 2,515 zero-price lines.  
**My solution:** I would tag authorised samples, replacements, and promotions; every untagged exception becomes a price-master or revenue-leakage investigation.

## 20. Data-quality exposure

**Problem:** Which source problems most threaten decision quality?  
**Finding:** Missing CustomerID is the largest exception at 135,080 rows (24.93%), followed by returns/cancellations and duplicate membership.  
**My solution:** I treat data quality as a commercial KPI while preserving the exception record and measuring remediation at source.

## 21. Product affinity

**Problem:** Which products belong together in a cross-sell journey?  
**Finding:** The collaborative-filtering layer provides five behavioural neighbours plus similarity and shared-customer support for recommendation-ready merchandise.  
**My solution:** I would A/B test high-confidence pairs in product pages, baskets, bundles, and post-purchase communication, measuring conversion and margin—not clicks alone.

