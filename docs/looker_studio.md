# Looker Studio Integration Guide

This guide documents the step-by-step configuration required to connect the Google Cloud BigQuery data mart (`crypto_marts.fct_market_insights` materialized table) to Looker Studio to create the official project reporting dashboard.

---

## 🏗️ Architecture Flow

```text
  BigQuery (DWH)        →      Looker Studio       →      Executive Report
(crypto_marts layer)        (Direct BI Connector)      (Real-time Insights)
```

---

## 🔌 Connection Setup

Follow these steps to connect your BigQuery data mart to Looker Studio:

### Step 1: Initialize Looker Studio Data Source
1. Navigate to [Looker Studio](https://lookerstudio.google.com/).
2. Click **Create** in the top-left corner and select **Data Source**.
3. Choose the **BigQuery** connector from the Google Connectors list.

### Step 2: Select the Data Mart Table
1. Under **My Projects**, select your GCP Project ID (from your `.env` configuration).
2. Select the dataset: **`crypto_marts`**.
3. Select the table: **`fct_market_insights`**.
4. Leave **Use report_date as partition field** checked (Looker Studio automatically optimizes queries using BigQuery partition boundaries to reduce query costs).
5. Click **Connect** in the top-right corner.

---

## 🗃️ Field Mapping & Configuration

Looker Studio will automatically detect the columns. Verify and update the field types and default aggregations as listed below:

| Field Name | Source Column | Semantic Type | Default Aggregation |
| :--- | :--- | :--- | :--- |
| **Record ID** | `record_id` | Text | None |
| **Report Date** | `report_date` | Date (YYYYMMDD) | None |
| **Coin ID** | `coin_id` | Text | None |
| **Average Price** | `avg_price` | Currency (USD) | Average |
| **Reddit Posts** | `reddit_posts` | Number | Sum |
| **Reddit Engagement** | `reddit_engagement` | Number | Sum |
| **Fear & Greed Value** | `fng_value` | Number | Average |
| **Fear & Greed Class** | `fng_classification` | Text | None |
| **Is Trending** | `is_trending` | Boolean | None |
| **Trending Score** | `trending_score` | Number | Average |
| **Composite Sentiment** | `sentiment_score` | Number | Average |
| **7D Avg Price** | `avg_price_7d` | Currency (USD) | Average |
| **7D Avg Reddit Posts** | `avg_reddit_posts_7d` | Number | Average |
| **Price Social Correlation** | `price_social_corr_7d` | Number | Average |

> [!TIP]
> Make sure `report_date` is configured as the default **Date Range Dimension** for all visualizations on the canvas.

---

## 📊 Recommended Dashboard Visualizations

To replicate and enhance the Streamlit insights, configure the following charts in Looker Studio:

### 1. Market Sentiment Scorecard (Composite Score)
* **Chart Type**: Scorecard
* **Metric**: `sentiment_score`
* **Aggregation**: Average
* **Style**: Use a conditional formatting rule:
  * Green if value `≥ 70` (Bullish)
  * Yellow if value `between 30 and 70` (Neutral)
  * Red if value `< 30` (Bearish)

### 2. Dual-Axis Price & Discussion Trend
* **Chart Type**: Combo Chart (Line + Bar)
* **Dimension**: `report_date`
* **Metrics**:
  * Bar: `reddit_posts` (Left Y-Axis)
  * Line: `avg_price` (Right Y-Axis)
* **Breakdown Dimension**: `coin_id`
* **Purpose**: Correlate peaks in discussion volume against price action.

### 3. Price & Social Mentions Rolling Correlation
* **Chart Type**: Time Series Chart
* **Dimension**: `report_date`
* **Metric**: `price_social_corr_7d`
* **Filter**: Add a page-level filter control for `coin_id` (so users can switch between BTC, ETH, and SOL).
* **Reference Line**: Add a horizontal reference line at `y = 0` to easily distinguish positive and negative correlation periods.

### 4. Coin Discussion Share vs. Trending Status
* **Chart Type**: Treemap or Stacked Column Chart
* **Dimension**: `coin_id`
* **Metric**: `reddit_engagement`
* **Style**: Highlight coins that have `is_trending = True` to see if trending coins capture the majority of social discussion.

---

## 💰 Query Cost Optimization

Looker Studio queries BigQuery directly on every interaction. Follow these best practices to minimize GCP query costs:

1. **Leverage Partitioning**: Ensure every chart uses the **Date Range Control** to filter data. Looker Studio will push down the date filter to BigQuery, scanning only the partitions matching the date filter instead of the full table.
2. **Adjust Cache Settings**: In Looker Studio, go to **Resource > Manage added data sources**, edit the connector, and set the Cache freshness to **4 hours** or **12 hours** (data updates daily via Airflow, so real-time querying is unnecessary).
3. **Avoid Custom SQL Connectors**: Use the native table selector connector instead of writing Custom SQL queries, as the native connector utilizes Looker Studio's internal optimizations better.
