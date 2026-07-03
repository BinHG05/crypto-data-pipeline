# Dashboard Enhancement Guide

## Goal

Turn the project dashboard into a stronger analytics product instead of a simple
chart collection.

The dashboard should answer three questions quickly:

1. What is happening to crypto prices?
2. What is happening in Reddit discussion activity?
3. Is the underlying pipeline healthy and fresh?

## Target Audience

- Recruiters reviewing a portfolio project
- Hiring managers for data engineering or analytics engineering roles
- Technical interviewers who want to see end-to-end thinking
- Stakeholders who need a simple daily crypto snapshot

## Recommended Dashboard Layout

### Section 1. Executive Summary

Top KPI cards:

- Latest BTC average price
- Latest ETH average price
- 7-day change in average price
- Reddit posts today
- Reddit engagement today
- Streaming freshness status

Why it helps:

- Gives an immediate project outcome
- Makes the dashboard readable in under 10 seconds

### Section 2. Daily Price Trends

Suggested visuals:

- Line chart: daily average price by coin
- Comparison chart: BTC vs ETH over time

Design notes:

- Use a clear time-range filter
- Label the latest values directly on the chart when possible

### Section 3. Reddit Activity Trends

Suggested visuals:

- Bar chart: daily Reddit post count
- Line or area chart: daily Reddit engagement score

Story to tell:

- Price movement and discussion volume do not always move together
- Community attention can increase even when price is flat

### Section 4. Market + Community View

Suggested visual:

- Dual-axis or side-by-side view of price vs Reddit post volume

Why it helps:

- Shows relationship thinking, not just isolated reporting
- Makes the dashboard feel more analytical

### Section 5. Pipeline Health

Suggested visuals:

- Freshness badge for realtime BTC feed
- Latest batch run status
- Data completeness status for expected coins

Suggested statuses:

- Healthy
- Warning
- Failed

This is a strong portfolio differentiator because it shows that the dashboard
does not ignore data reliability.

## Recommended Metrics

Use the following metrics consistently:

- `avg_price`
- `reddit_posts`
- `reddit_score`
- `report_date`
- latest `event_time` in realtime table

Optional derived metrics:

- day-over-day price change
- 7-day rolling average price
- price volatility band
- engagement per post

## UX Improvements

### Filters

Recommended filters:

- Date range
- Coin selector

### Visual hierarchy

Priority order:

1. KPI cards
2. Trend charts
3. Relationship charts
4. Pipeline health section

### Color strategy

Suggested approach:

- BTC: warm color
- ETH: cool color
- Health states: green / amber / red

Keep the palette intentional and avoid overcrowding with too many chart colors.

## Portfolio Presentation Tips

To make the dashboard stronger in a portfolio:

- Include one screenshot in the README
- Add a short caption for what each section demonstrates
- Mention that pipeline health is surfaced alongside business metrics
- Show that the dashboard is backed by validated dbt marts, not raw tables

## Best Story Angle

The best story for this dashboard is:

This is not just a crypto dashboard. It is a monitored analytics product with
validated upstream data, alerting, and reproducible transformations.

That framing is stronger than saying only that the project shows prices and
Reddit posts.

## Suggested Next Additions

- Publish the Looker Studio link in the README
- Add annotations for major price spikes
- Add a freshness timestamp on the dashboard header
- Add a small text panel explaining data sources and update cadence
