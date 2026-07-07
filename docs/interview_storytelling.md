# Interview Storytelling Guide

## 30-Second Pitch

I built an end-to-end crypto data pipeline on GCP that ingests batch and
realtime data, transforms it with dbt, orchestrates it with Airflow, validates
data quality, and sends alerts when pipelines fail or streaming freshness
degrades. I treated it like a production-minded portfolio project rather than
just a notebook or ETL demo.

## 2-Minute Project Story

The project combines two batch sources, CoinGecko and Reddit, with a realtime
Binance BTC stream. Batch data is saved locally as JSONL, uploaded to GCS,
loaded into BigQuery raw tables, and transformed into curated marts with dbt.
Airflow orchestrates both the batch DAG and a separate streaming freshness
monitor DAG.

What makes the project stronger than a standard ETL exercise is the attention
to reliability:

- local raw file validation
- raw table row-count validation
- dbt tests for schema and completeness
- daily mart completeness checks
- streaming freshness monitoring
- failure alerts through email and Slack
- CI checks for formatting, linting, and dbt validation

## Problem -> Action -> Result Framing

### Problem

Many portfolio pipelines show ingestion and transformation, but stop before
monitoring, alerting, or CI. That makes them difficult to position as
production-ready work.

### Action

I added observability and quality controls across the stack:

- Airflow validation tasks before and after warehouse loads
- dbt tests on curated models
- dedicated monitoring logic for missing daily mart rows
- dedicated monitoring logic for stale streaming data
- shared failure callbacks for email and Slack alerts
- GitHub Actions for code quality and dbt verification

### Result

The project became a more realistic data engineering system that demonstrates
both data movement and operational discipline.

## Architecture Walkthrough

Use this sequence in interviews:

1. Explain the business objective
2. Explain the batch path
3. Explain the streaming path
4. Explain the transformation layer
5. Explain quality checks
6. Explain alerting
7. Explain CI and maintainability

That order keeps the story clear and avoids jumping too early into tools.

## Strong Talking Points

### Why Airflow?

Because the project needed orchestration, retries, task dependencies, failure
callbacks, and a natural way to insert validation steps between ingestion,
loading, transformation, and monitoring.

### Why dbt?

Because dbt makes the transformation layer transparent, testable, and easier to
document. It also cleanly separates raw ingestion from curated analytics models.

### Why BigQuery?

Because it simplifies warehousing for analytics workflows, works well with dbt,
and is easy to pair with Looker Studio and Python-based ingestion.

### Why separate monitoring logic from transformation logic?

Because business transformations and operational health checks serve different
purposes. Keeping them separate makes failures easier to reason about and debug.

## Good “Challenge” Story

One strong challenge story from this project is the gap between a pipeline that
works locally and one that is reliable enough for repeated runs. The hard part
was not only moving data into BigQuery, but adding checks for empty files,
schema correctness, expected mart coverage, and stale streaming records. That
is where the project became much more realistic.

## Good “Debugging” Story

Another strong story is the CI and dbt debugging work:

- fixing schema test syntax issues
- fixing mismatched schema targets in dbt
- fixing GitHub Actions profile and credential handling
- adding code quality tooling and fail-fast workflow ordering

This shows that you worked through operational issues, not only happy-path
coding.

## Tradeoffs to Mention Honestly

- The project is portfolio-scale, not a full production platform
- Some infrastructure is configured manually rather than through IaC
- There is room to add more automated unit testing
- The realtime path focuses on freshness monitoring rather than complex stream
  processing

These are honest limitations that still show maturity.

## Interview Questions You Should Expect

### “What part of the project are you most proud of?”

Best angle:

The monitoring and alerting layer, because it turns the project from a data
movement demo into an operational analytics pipeline.

### “What would you improve next?”

Best angle:

- add Terraform
- add incremental dbt models
- add automated test coverage for ingestion utilities
- publish the dashboard with production-like environment separation

### “How do you know the data is trustworthy?”

Best angle:

Because trust is enforced at multiple layers:

- source file non-empty checks
- raw load validation
- dbt tests
- expected daily mart coverage checks
- streaming freshness checks

### “What happens when the pipeline fails?”

Best angle:

The task fails early, Airflow logs the failure, the shared callback sends email
and Slack alerts, and the DAG structure makes it easy to identify whether the
issue happened in ingestion, load, transformation, or monitoring.

## Demo Flow for a Live Interview

If you need to demo the project live:

1. Show the README summary
2. Show the Airflow DAG graph
3. Show one dbt model and one dbt test
4. Show monitoring documentation
5. Show the dashboard or screenshots
6. Explain the CI workflow

That sequence keeps both business and technical audiences engaged.

## Final Positioning

The best way to position this project is:

I built a compact but production-minded analytics pipeline with orchestration,
testing, monitoring, alerting, and CI. It demonstrates not just how to move
data, but how to make analytics workflows more reliable and maintainable.
