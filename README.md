# Crypto Data Pipeline

## Overview

This project simulates a modern data engineering pipeline for cryptocurrency data using public APIs.

## Data Sources

- CoinGecko API (crypto prices)
- Reddit API (crypto discussions)

## Ingestion Layer

- Fetch data using Python (requests)
- Store raw JSON files
- Partition data by date

## Project Structure

data/raw/{source}/{date}/data.json

## How to Run

```bash
python ingestion/run_pipeline.py
```

## Tech Stack

- Python
- Requests
- JSON
