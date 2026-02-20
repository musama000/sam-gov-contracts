# SAM.gov Contract Opportunities Scraper

Python scraper for finding federal government contract opportunities on [SAM.gov](https://sam.gov) using the official Opportunities API (v2). Tailored for veteran-owned small businesses getting started in government contracting.

## Setup

1. Get a free API key: log in at [sam.gov](https://sam.gov) → Account Details → Request Public API Key
2. `cp .env.example .env` and paste your key
3. `pip install -r requirements.txt`
4. `python3 scraper.py`

## Files

| File | Description |
|------|-------------|
| `scraper.py` | Main scraper — searches SAM.gov API by keyword, NAICS code, set-aside type, and date range |
| `requirements.txt` | Python dependencies (requests, python-dotenv, pandas) |
| `.env.example` | Template for your SAM.gov API key |
| `.gitignore` | Keeps `.env` and cache files out of git |

## Output CSVs

| File | Description |
|------|-------------|
| `output/sam_beginner_friendly_*.csv` | 590 low-barrier opportunities: sources sought, SDVOSB set-asides, and small business set-asides |
| `output/sam_best_matches.csv` | 181 opportunities filtered for aerospace, engineering, CAD, and software skills |
| `output/sam_mohammed_targeted_*.csv` | 262 opportunities across engineering services, CAD modeling, software dev, and aerospace |
| `output/sam_opportunities_engineering_services_*.csv` | Engineering services contracts (NAICS 541330) |
| `output/sam_opportunities_cad_modeling_*.csv` | CAD modeling and drafting contracts |
| `output/sam_opportunities_software_development_*.csv` | Software development contracts (NAICS 541512) |
| `output/sam_opportunities_aerospace_*.csv` | Aerospace-related contracts |
| `output/sam_opportunities_all_*.csv` | Raw pulls from sources sought, SDVOSB, and SBA searches |
