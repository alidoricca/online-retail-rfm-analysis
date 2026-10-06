# Online Retail Customer Analytics: RFM Segmentation, Clustering & Retention Analysis

**A data analyst portfolio project | Tools: SQL (SQLite), Python (pandas, scikit-learn), Power BI**

---

## Executive Summary

Analysis of 1.06M cleaned transactions from a UK online retailer (5,939 customers, Dec 2009–Dec 2011) found that **22.5% of customers ("Champions") generate 70.8% of total revenue** — at ~60x the average value of the lowest-value segment. Independent K-Means clustering validated this concentration but revealed that RFM's 11-label taxonomy overstates real behavioral distinction among mid-value customers, who cluster into a single natural group despite carrying five different RFM labels. Cohort analysis showed only 25% of new customers return within their first month, despite 75.5% eventually repeat-purchasing — pointing to a specific, addressable retention gap in the first 30 days. These findings translate into three concrete, prioritized recommendations below.

---

## 1. Business Question

Online retailers generate enormous volumes of transactional data, but raw transactions alone don't tell a business who its most valuable customers are, whether it's retaining them, or where revenue is concentrated. This project analyzes two years of transaction data (Dec 2009–Dec 2011) from a UK-based online retailer to answer three questions:

1. **Who are our most valuable customers, and how much of our revenue do they represent?**
2. **How well do we retain customers over time, and does retention change across acquisition cohorts?**
3. **Does traditional RFM segmentation actually capture meaningful, distinct customer groups — or does it create artificial distinctions?**

---

## 2. Data & Cleaning

**Source:** UCI "Online Retail II" dataset — 1,067,371 raw transaction line items across two sheets (2009–2010, 2010–2011).

Before any analysis, the raw data was profiled and cleaned in SQL. Several categories of non-sale rows were identified and excluded, each verified with targeted queries rather than assumed:

| Issue found | Rows | Action |
|---|---|---|
| Bad debt write-offs (Invoice prefix "A", accounting entries) | 5 | Excluded — not customer transactions |
| Internal stock adjustments (negative quantity, non-cancellation invoice, £0 price — e.g. "damaged", "lost") | 3,457 | Excluded — not customer transactions |
| Test data (TEST001/TEST002 SKUs, "test" in description) | 5 | Excluded |
| Zero-price rows (promotional/free full orders, misc. stock movement notes) | 2,740 | Excluded from revenue analysis |
| Cancellations (Invoice prefix "C") | 19,494 | **Retained**, flagged separately as returns |
| Guest checkouts (no Customer ID) | 243,007 (~22.8%) | Excluded from customer-level analysis (RFM, cohorts); retained for total revenue figures |

This left **1,061,149 clean transaction rows** and **5,939 identified customers** as the foundation for all downstream analysis.

**A notable finding during cleaning:** ~1,692 zero-price rows were traced to large multi-item orders (up to 114 line items on a single invoice) with real Customer IDs — consistent with promotional or wholesale sample orders rather than data errors. These were excluded from revenue calculations but represent a legitimate, distinct category worth flagging to the business.

---

## 3. RFM Segmentation

### Methodology

Each customer was scored on three dimensions, calculated relative to the dataset's final transaction date (2011-12-09):
- **Recency** — days since last purchase
- **Frequency** — number of distinct orders
- **Monetary** — net total spend (returns/cancellations netted in, not excluded — a customer who orders heavily and returns most of it is not, in fact, a high-value customer)

Each dimension was scored 1–5 using **quintile-based ranking** (`NTILE(5)` in SQL) rather than fixed dollar/day thresholds. This decision was evidence-based: a widely-referenced RFM scoring table (Christy et al., 2021, citing thresholds in USD) was tested against this dataset and rejected, because this dataset's Monetary values range from -£25,111 to £598,215 — several orders of magnitude wider than the reference table's £3,000–£12,000 range, and in a different currency. Applying those fixed thresholds would have placed nearly all customers into a single score bucket. Quintile scoring adapts to the actual distribution of the data and avoids this failure mode.

Combined R/F/M scores were mapped to an 11-segment framework matching common industry convention (Champions, Loyal Customers, At Risk, Lost, etc.).

### Validation: does the segmentation mean anything?

Rather than assume the quintile-based segments were meaningful, they were validated directly against revenue:

| Segment | % of Customers | Total Revenue | Avg Revenue/Customer |
|---|---|---|---|
| **Champions** | 22.5% | **£11,784,287** (70.8%) | £8,807 |
| Loyal Customers | 19.6% | £2,504,059 (15.0%) | £2,148 |
| ... (9 other segments) | 57.9% | £2,359,743 (14.2%) | varies |
| **Lost** | 18.6% | £158,076 (0.9%) | £143 |

Champions — 22.5% of customers — generate **70.8% of total revenue**, at an average value **~60x higher** than the Lost segment. This is a clear, real confirmation of the Pareto principle in this customer base, and confirms the RFM segmentation captures a genuine, economically significant distinction, not just an artifact of forcing customers into equal-sized buckets.

![Revenue by segment](images/revenue_by_segment.png)
*Revenue and customer share by RFM segment. Champions dominate revenue contribution despite being under a quarter of the customer base.*

---

## 4. Clustering: Testing RFM Against an Independent Method

RFM's quintile scoring is inherently *relative* — a score of 5 means "top 20% of this dataset," not "genuinely high value by any absolute standard." To test whether RFM's 11 labels reflect real, distinct customer behavior, **K-Means clustering** was applied independently to the same R/F/M data (following the methodology in Christy et al., 2021, "RFM ranking – An effective approach to customer segmentation").

**Process:**
1. **Outlier handling:** 70 customers (1.18%) were flagged via Z-score (|Z| > 3) as extreme outliers — mostly high-volume, wholesale-style buyers (one customer alone: 153 orders, £598,215 spent). These were excluded from clustering only (K-Means is sensitive to extreme values) but retained in all other analysis, since they represent real, valuable customers.
2. **Normalization:** Recency, Frequency, and Monetary were min-max scaled to a 0–1 range, preventing Monetary's larger numeric scale from dominating distance calculations.
3. **Choosing k:** Multiple validity metrics were tested (silhouette score, Davies-Bouldin index, Calinski-Harabasz index) across k=2 through k=10. The metrics did not agree: silhouette and Davies-Bouldin favored simpler 2-cluster solutions, while Calinski-Harabasz favored more granular ~6-cluster solutions. **k=5 was selected** as a defensible middle ground — reasonably strong across all three metrics (silhouette: 0.508, close to the commonly-cited 0.5 "acceptable" threshold) and, critically, producing a business-interpretable result: distinguishing not just "engaged vs. lapsed" but two meaningfully different stages of customer lapse.

**Resulting clusters:**

| Cluster | Recency (avg) | Frequency (avg) | Monetary (avg) | Interpretation |
|---|---|---|---|---|
| Best Customers | 27.8 days | 27.1 orders | £9,155 | Highly active, high-value |
| Good Customers | 40.3 days | 5.9 orders | £1,810 | Engaged, moderate value |
| Cooling Off | 213.1 days | 3.9 orders | £1,050 | Early-stage lapse |
| Lapsing | 411.2 days | 2.9 orders | £746 | Late-stage lapse |
| Lost | 622.6 days | 1.7 orders | £320 | Inactive |

### Key finding: RFM's granularity may overstate real distinctions

Cross-tabulating clusters against RFM segments revealed strong agreement at the extremes — "Best Customers" mapped cleanly onto "Champions" + "Loyal Customers," and "Lost" mapped onto "Lost" + "At Risk" + "Hibernating." **However, the "Good Customers" cluster — found by an unsupervised method with no prior labels — absorbed customers from five separate RFM labels** (Champions, Loyal Customers, Potential Loyalist, Promising, New Customers), suggesting these five RFM categories are not as behaviorally distinct as their separate names imply.

**Implication:** RFM's 11-label framework is a useful, industry-standard communication tool, but the underlying data in this case naturally clusters into roughly 4–5 meaningfully different groups, not 11. This is a genuine methodological insight, not a criticism of RFM as a concept — it demonstrates the value of validating any relative scoring method against an independent, unsupervised technique before treating its labels as ground truth.

---

## 5. Cohort Retention Analysis

Monthly acquisition cohorts were tracked to measure how many customers from each cohort returned in subsequent months.

**Key metrics:**
- **Average Month-1 retention: 25.0%** — roughly 1 in 4 customers return within a month of their first purchase.
- **Overall repeat purchase rate: 75.5%** (4,481 of 5,939 customers made more than one purchase across the full ~2-year period) — indicating strong *eventual* loyalty even where immediate return rates are more modest.
- Retention curves were broadly consistent across cohorts (typically settling into a 10–20% range after month 3–4), with no strong evidence of retention worsening over the ~2-year period.
- **One notable limitation:** the December 2009 cohort (the dataset's first month) showed unusually high long-term retention (still 20–40% active 20+ months later) — likely because this "cohort" includes pre-existing customers whose earlier purchase history predates the dataset, artificially inflating its apparent loyalty. This cohort's figures should be treated as an artifact of the data window, not a genuine trend.

![Cohort retention heatmap](images/cohort_heatmap_dashboard.png)
*Monthly cohort retention (%). Darker cells indicate higher retention. The Dec 2009 cohort's persistently elevated retention (top row) reflects the left-censoring artifact described above.*

---

## 6. Dashboard

An interactive Power BI dashboard was built to communicate these findings, including headline KPIs, revenue and customer distribution by RFM segment, monthly revenue trend with a 3-month moving average, and a cohort retention heatmap.

![Dashboard overview](images/dashboard_overview.png)
*Full dashboard: KPI header, segment revenue breakdown, monthly trend, customer distribution, and cohort retention.*

---

## 7. Recommendations

1. **Prioritize retention of the Champions segment** (22.5% of customers, 70.8% of revenue). Even a small increase in churn among this group would have an outsized revenue impact — losing just 5% of Champions to churn would put roughly £590,000 of annual-equivalent revenue at risk, more than the *entire* revenue contribution of the bottom six segments combined.

2. **Focus retention efforts within the first 30 days** of a customer's first purchase, since Month-1 retention (25%) is meaningfully lower than the eventual repeat-purchase rate (75.5%) — suggesting many customers who *would* return are not being prompted to do so quickly enough. *Illustrative estimate:* if a first-30-days campaign (e.g. a follow-up email or second-purchase incentive) lifted Month-1 retention from 25% to 30% — a 5-point gain — that would represent roughly 300 additional retained customers per cohort month, based on typical cohort sizes in this dataset. This is a directional estimate to size the opportunity, not a forecast; actual impact would need to be measured via a controlled test.

3. **Plan retention/upsell campaigns ahead of the November seasonal peak**, when order volume is highest and customer attention is naturally elevated — capturing customers during a period of naturally high engagement is typically more cost-effective than re-engagement during a quiet period.

4. **Reconsider mid-tier RFM segment granularity** for operational use (e.g., email campaign targeting). The clustering analysis suggests Champions, Loyal Customers, Potential Loyalist, Promising, and New Customers may not warrant five separate treatment strategies; a simplified 3–4 tier structure may be more operationally practical without losing meaningful distinction — reducing campaign design overhead without a corresponding loss in targeting precision.

---

## 7a. Future Work

Given project scope and timeline, the following were identified as valuable extensions but deliberately not pursued in this iteration:

- **Predictive churn model** (e.g. logistic regression on early-lifecycle behavior) to flag at-risk Champions before they lapse, rather than relying on retrospective segmentation alone.
- **Product-level basket analysis** (market basket / association rules) to identify cross-sell opportunities within the Champions segment specifically, where the revenue upside per successful recommendation is highest.
- **Investigating the December 2009 cohort anomaly** with additional data (if available) predating this dataset's window, to confirm whether its inflated retention is purely a left-censoring artifact or partly genuine.

---

## 8. Methodology Notes & Limitations

- **Scope decision:** a predictive churn model was considered as a natural extension of this analysis but was deliberately scoped out to prioritize a fully validated, well-documented core analysis within the project timeline. This is noted as future work.
- RFM's Monetary quintiles are *relative* rankings (top 20% of this dataset), not absolute value judgments — a limitation inherent to quantile-based scoring, addressed here through independent clustering validation rather than assumed away.
- The December 2009 cohort's retention figures are likely inflated by left-censoring (pre-existing customers whose full history isn't captured in this dataset).
- Guest checkout transactions (~22.8% of all transactions) are included in total revenue figures but necessarily excluded from all customer-level analysis (RFM, cohorts, clustering), since no customer identifier exists to track them.

---

## 9. Tools & Techniques

- **SQL (SQLite):** data profiling, cleaning, view-based transformation pipeline, window functions (`NTILE`), RFM base table construction
- **Python (pandas, scikit-learn, scipy):** Z-score outlier detection, min-max scaling, K-Means clustering, multi-metric cluster validation (silhouette, Davies-Bouldin, Calinski-Harabasz), cohort retention calculation
- **Power BI:** DAX measures, interactive dashboard with KPIs, segment breakdowns, and cohort heatmap

**Reference:** Christy, A.J., Umamakeswari, A., Priyatharsini, L., & Neyaa, A. (2021). RFM ranking – An effective approach to customer segmentation. *Journal of King Saud University – Computer and Information Sciences*, 33, 1251–1257.
